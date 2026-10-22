#!/usr/bin/env python3
"""Agent Skills 公式仕様および本スキルの運用ルールへの適合を検証する。

Usage:
    python3 scripts/validate-skill.py SKILL_DIR [--format json|text] [--strict]
    python3 scripts/validate-skill.py SKILL_DIR --vocabulary PATH

SKILL_DIR は検証対象のスキルディレクトリ（SKILL.md を含むディレクトリ）。
--vocabulary を指定すると、その語彙表（JSON）に対して本文の語彙揺れを検証する。
出力は stdout に JSON（--format text を指定した場合はテキスト）、
診断・進捗は stderr へ分離する。

終了コード:
    0  適合（error なし）
    1  不適合（error 1 件以上、または --strict 指定時に warning 1 件以上）
    2  使用法エラー
"""
import argparse
import json
import os
import re
import sys
import unicodedata

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESOURCE_DIRS = ("references", "scripts", "assets", "evals")
# 公式仕様: "Keep file references one level deep from SKILL.md."
MAX_REF_DEPTH = 1
MAX_SKILL_LINES = 500
MAX_DESC = 1024
MAX_COMPAT = 500
# 公式仕様: "Instructions (< 5000 tokens recommended)"
# 日本語は 1 文字あたり概ね 1.2 token、ASCII は概ね 0.25 token と概算する。
TOKEN_CJK = 1.2
TOKEN_ASCII = 0.25
MAX_SKILL_TOKENS = 5000

# ---------------------------------------------------------------------------
# 異物混入検出
# ---------------------------------------------------------------------------
# 日本語のテキスト中に他言語の語が混入すると、文として成立しなくなる。
# U+FFFD（文字化け）だけでは検出できないため、スクリプト単位で検出する。
# 語の一覧は assets/foreign-tokens.json に置く（検出データファイル自体の誤検知を避けるため）。

DEFAULT_TOKEN_FILE = "assets/foreign-tokens.json"


def load_token_data(skill_dir):
    """検出用の語彙データを読み込む。

    データ源は 2 つで、両方を合成する。
      1. 本スクリプトに隣接する `assets/foreign-tokens.json`（既定の語）
      2. 検証対象の `assets/foreign-tokens.json`（対象スキル固有の追加分）

    戻り値: (allow_cjk, foreign_cjk, latin_allow, foreign_chars)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sources = [
        os.path.normpath(os.path.join(script_dir, "..", DEFAULT_TOKEN_FILE)),
        os.path.join(skill_dir, DEFAULT_TOKEN_FILE),
    ]
    allow_cjk = set()
    foreign_cjk = set()
    foreign_chars = set()
    latin_allow = []
    for path in sources:
        if not os.path.isfile(path):
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        allow_cjk |= set(data.get("cjk_allowlist", []))
        foreign_cjk |= set(data.get("foreign_cjk_words", []))
        foreign_chars |= set(data.get("cjk_simplified_only", ""))
        foreign_chars |= set(data.get("cjk_traditional_only", ""))
        for w in data.get("latin_allowlist", []):
            if w not in latin_allow:
                latin_allow.append(w)
    return allow_cjk, foreign_cjk, latin_allow, foreign_chars


def detect_foreign_scripts(text, allow_cjk, foreign_cjk, foreign_chars):
    """日本語のテキスト中の他言語混入を検出する。戻り値: [(行番号, 語, 行の全文)]

    1) 中国語・ロシア語・韓国語など、専用スクリプトの語を検出する。
    2) 日本語と字形が異なる簡体字を 1 文字単位で検出する。
    3) 中国語の常用語を単語単位で検出する。
    """
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        for m in re.finditer(r"[\u0400-\u04FF\uAC00-\uD7AF\u0370-\u03FF\u0600-\u06FF]+", line):
            hits.append((i, m.group(), line.strip()))
        for m in re.finditer(r"[\u4E00-\u9FFF]+", line):
            run = m.group()
            for ch in run:
                if ch in foreign_chars:
                    hits.append((i, ch, line.strip()))
                    break
            for w in sorted(foreign_cjk, key=len, reverse=True):
                if w in run:
                    hits.append((i, w, line.strip()))
                    break
    return hits


# 日本語の文中に現れる英単語（1 語以上）。直前の日本語文字は不要とする。
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_./-]{1,}")
# コード.span・ファイルパス・識別子として現れるものは検証対象外
CODE_SPAN = re.compile(r"`[^`]*`")


def detect_latin_in_japanese(text, latin_allow):
    """日本語の行に正体の知れない英単語が混入している箇所を検出する。

    判定は**単語ごと**に行う。行に許容語が 1 つでもあれば行全体を除外しない。
    """
    hits = []
    in_fence = False
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", line):
            continue
        masked = CODE_SPAN.sub(lambda m: " " * len(m.group()), line)
        for m in LATIN_WORD.finditer(masked):
            g = m.group()
            if g in latin_allow:
                continue
            hits.append((i, g, line.strip()))
    return hits


def detect_replacement_chars(text):
    """文字化け文字 (U+FFFD) を検出する。"""
    return [
        (i, "U+FFFD", line.strip())
        for i, line in enumerate(text.split("\n"), 1)
        if "\ufffd" in line
    ]


# ---------------------------------------------------------------------------
# 語彙揺れ検出
# ---------------------------------------------------------------------------


def load_vocabulary(path):
    """語彙表 JSON を読み込む。戻り値: (dict, error_message)"""
    if not os.path.isfile(path):
        return None, f"語彙表が見つかりません: {path}"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, f"語彙表 JSON を解析できません: {e}"
    if not isinstance(data, dict):
        return None, "語彙表のトップレベルはオブジェクトである必要があります"
    return data, None


def check_vocabulary(skill_dir, vocab):
    """語彙表に対して本文の語彙揺れを検証する。

    語彙表の形式:
      {
        "canonical_terms": ["読む", "使う", ...],
        "forbidden_variants": {"読む": ["読込", "読み込み"]},
        "distinct_terms": {"利用者": "依頼者", "人間": "文書の読み手"}
      }
    """
    errors, warnings = [], []
    forbidden = vocab.get("forbidden_variants", {})
    exempt = set(vocab.get("_scan_exempt_files", []))
    targets = []
    for root, _dirs, files in os.walk(skill_dir):
        for f in sorted(files):
            if not (f.endswith(".md") or f.endswith(".json") or f.endswith(".py")):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, skill_dir)
            if rel in exempt:
                continue
            targets.append(full)
    for path in targets:
        rel = os.path.relpath(path, skill_dir)
        text = open(path, encoding="utf-8").read()
        for canon, variants in forbidden.items():
            for v in variants:
                n = text.count(v)
                if n:
                    for i, line in enumerate(text.split("\n"), 1):
                        if v in line:
                            errors.append(
                                f"{rel}:{i} 統一語「{canon}」と表記揺れ「{v}」が併存しています"
                                f"（{canon} {text.count(canon)} 件 / {v} {n} 件）"
                            )
    return errors, warnings


# ---------------------------------------------------------------------------
# フロントマター
# ---------------------------------------------------------------------------


def parse_frontmatter(text):
    """フロントマターを解析する。依存ライブラリを使わず LLM の出力を壊さない最小限の解析を行う。

    戻り値: (dict, body_text, errors)
    """
    errors = []
    if not text.startswith("---"):
        return {}, text, ["SKILL.md が YAML フロントマターで始まっていません"]
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return {}, text, ["フロントマターの終端 --- が見つかりません"]
    raw = m.group(1)
    body = text[m.end():]

    data = {}
    key = None
    for line in raw.split("\n"):
        if not line.strip():
            continue
        indented = line[:1] in (" ", "\t")
        if not indented:
            km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
            if km:
                key = km.group(1)
                val = km.group(2).strip()
                if val in (">", "|", ">-", "|-", ">+", "|+"):
                    data[key] = ""
                else:
                    # YAML コメントを除去する
                    val = re.sub(r"\s+#.*$", "", val)
                    data[key] = val.strip("'\"")
            else:
                key = None
        elif key is not None:
            data[key] = (data.get(key, "") + " " + line.strip()).strip()
    return data, body, errors


def estimate_tokens(text):
    """テキストの token 数を概算する。日本語 1 文字 ≒ 1.2 token、ASCII 1 文字 ≒ 0.25 token。"""
    cjk = sum(1 for ch in text if "\u3000" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef")
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    other = len(text) - cjk - ascii_chars
    return int(cjk * TOKEN_CJK + ascii_chars * TOKEN_ASCII + other * TOKEN_CJK)


def check_frontmatter(fm, skill_dir):
    errors, warnings = [], []

    name = fm.get("name", "")
    if not name:
        errors.append("frontmatter に name がありません")
    else:
        if len(name) > 64:
            errors.append(f"name が 64 文字を超えています（実際 {len(name)}）")
        if not NAME_RE.match(name):
            errors.append(
                "name が不正です。a-z 0-9 と単独のハイフンのみ使用でき、"
                "先頭・末尾のハイフンと連続ハイフンは禁止されます"
            )
        if name != os.path.basename(os.path.abspath(skill_dir)):
            errors.append(
                f"name（{name}）が親ディレクトリ名（{os.path.basename(os.path.abspath(skill_dir))}）と一致しません"
            )

    desc = fm.get("description", "")
    if not desc:
        errors.append("frontmatter に description がありません")
    elif len(desc) > MAX_DESC:
        errors.append(f"description が {MAX_DESC} 文字を超えています（実際 {len(desc)}）")
    else:
        lowered = desc.lower()
        signals = ["use this skill", "use when", "apply this skill", "whenever", "use it when"]
        if not any(s in lowered for s in signals):
            warnings.append(
                "description に命令形の使用指示（use this skill when ... 等）がありません。"
                "説明型では発動しにくくなります"
            )
        desc_tokens = estimate_tokens(desc)
        if desc_tokens > 150:
            warnings.append(
                f"description の概算 token 数が {desc_tokens} です。"
                "公式の目安は 100 token 程度であり、全スキル分のセッション開始時に読み込まれます"
            )

    compat = fm.get("compatibility", "")
    if compat and len(compat) > MAX_COMPAT:
        errors.append(f"compatibility が {MAX_COMPAT} 文字を超えています（実際 {len(compat)}）")

    for key in ("license", "compatibility", "allowed-tools"):
        if key in fm and fm[key] == "":
            warnings.append(f"frontmatter の {key} が空です")

    return errors, warnings


def collect_refs(body):
    """本文からファイル参照を抽出する。戻り値: [(path, lineno)]"""
    refs = []
    patterns = [
        r"`((?:references|scripts|assets|evals)/[^`\s]+)`",
        r"\]\(((?:references|scripts|assets|evals)/[^)\s]+)\)",
        # バッククォートなしの平文表記（公式仕様が示す記法之一）
        r"(?<![\w/.-])((?:references|scripts|assets|evals)/[\w./-]+\.(?:json|yaml|yml|mjs|md|py|sh|ts|txt))",
    ]
    seen = set()
    for pat in patterns:
        for m in re.finditer(pat, body):
            path = m.group(1)
            if path in seen:
                continue
            seen.add(path)
            refs.append((path, body[: m.start()].count("\n") + 1))
    return refs


def check_structure(skill_dir, body):
    errors, warnings = [], []
    lines = body.split("\n")
    if len(lines) > MAX_SKILL_LINES:
        errors.append(f"SKILL.md 本文が {MAX_SKILL_LINES} 行を超えています（実際 {len(lines)}）")
    tokens = estimate_tokens(body)
    if tokens > MAX_SKILL_TOKENS:
        warnings.append(
            f"SKILL.md 本文の概算 token 数が {tokens} です（推奨 {MAX_SKILL_TOKENS} 未満）"
        )

    refs = collect_refs(body)
    if not refs:
        warnings.append("SKILL.md からファイル参照がありません。段階的開示が機能しません")

    referenced = set()
    for path, lineno in refs:
        referenced.add(path)
        target = os.path.join(skill_dir, path)
        if not os.path.exists(target):
            errors.append(f"{path}（SKILL.md:{lineno}）が存在しません")
            continue
        depth = path.count("/")
        if depth > MAX_REF_DEPTH:
            errors.append(
                f"{path}（SKILL.md:{lineno}）は {depth} 段深さです。"
                "公式仕様に従い 1 段深さ（references/foo.md 形式）に収めてください"
            )

    for d in RESOURCE_DIRS:
        dpath = os.path.join(skill_dir, d)
        if not os.path.isdir(dpath):
            continue
        for root, _dirs, files in os.walk(dpath):
            for f in files:
                if f.startswith("."):
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, skill_dir)
                if rel not in referenced:
                    warnings.append(
                        f"{rel} は SKILL.md から参照されていません"
                        "（読まれないファイルはコンテキスト予算の無駄）"
                    )

    return errors, warnings


def check_scripts(skill_dir):
    errors, warnings = [], []
    sdir = os.path.join(skill_dir, "scripts")
    if not os.path.isdir(sdir):
        return errors, warnings
    for f in sorted(os.listdir(sdir)):
        if f.startswith(".") or not f.endswith((".py", ".sh", ".js", ".mjs", ".ts")):
            continue
        p = os.path.join(sdir, f)
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError as e:
            errors.append(f"scripts/{f} を読めません: {e}")
            continue
        if "--help" not in text and "argparse" not in text and "add_argument" not in text:
            warnings.append(f"scripts/{f} に --help の記述がありません")
        if "dry" not in text.lower() and ("write" in text or "open" in text):
            warnings.append(f"scripts/{f} に状態変更を伴う操作があるため --dry-run がない可能性があります")
    return errors, warnings


def _json_values(obj):
    """JSON の値（キーは除く）だけを列挙する。"""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _json_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _json_values(v)
    elif isinstance(obj, str):
        yield obj


def check_text_files(skill_dir, allow_cjk, foreign_cjk, latin_allow, foreign_chars):
    """テキストファイル全体の異物混入・文字化けを検証する。

    検証の向き:
      - Markdown: 全文を対象に検証する。
      - JSON: キーは検証対象から除外し、値のみを検証する（キーは英語が正当）。
      - Python: 英語識別子が正当であるため、言語混入と文字化けのみを検証する。
    """
    errors, warnings = [], []
    exempt = set()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for token_path in (
        os.path.join(skill_dir, DEFAULT_TOKEN_FILE),
        os.path.normpath(os.path.join(script_dir, "..", DEFAULT_TOKEN_FILE)),
    ):
        if not os.path.isfile(token_path):
            continue
        try:
            exempt.add(os.path.relpath(token_path, skill_dir))
        except ValueError:
            pass
    for root, _dirs, files in os.walk(skill_dir):
        for f in sorted(files):
            if f.startswith("."):
                continue
            if not f.endswith((".md", ".json", ".py", ".txt", ".yaml", ".yml")):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, skill_dir)
            if rel in exempt:
                continue
            try:
                text = open(p, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            for i, token, line in detect_replacement_chars(text):
                errors.append(f"{rel}:{i} 文字化け文字 (U+FFFD) が含まれています: {line[:80]}")
            for i, token, line in detect_foreign_scripts(text, allow_cjk, foreign_cjk, foreign_chars):
                errors.append(f"{rel}:{i} 他言語の語「{token}」が混入しています: {line[:80]}")

            if f.endswith(".py"):
                # コード内の英語識別子は正当であるため、言語混入の検証だけを行う
                continue
            if f.endswith(".json"):
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    data = None
                if data is not None:
                    for value in _json_values(data):
                        for i, token, line in detect_latin_in_japanese(value, latin_allow):
                            errors.append(
                                f"{rel} 他言語の語「{token}」が混入しています（JSON の値）: {line[:80]}"
                            )
                    continue
            for i, token, line in detect_latin_in_japanese(text, latin_allow):
                errors.append(f"{rel}:{i} 日本語文中に正体の不明な英単語「{token}」があります: {line[:80]}")
    return errors, warnings


def check_evals(skill_dir):
    errors, warnings = [], []
    evals_dir = os.path.join(skill_dir, "evals")
    if not os.path.isdir(evals_dir):
        warnings.append("evals/ がありません。トリガー評価と出力評価の設定ができません")
        return errors, warnings
    for fname in ("evals.json", "trigger-queries.json"):
        p = os.path.join(evals_dir, fname)
        if not os.path.isfile(p):
            warnings.append(f"evals/{fname} がありません")
            continue
        try:
            data = json.load(open(p, encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"evals/{fname} の JSON を解析できません: {e}")
            continue
        if fname == "evals.json":
            if "skill_name" not in data:
                errors.append("evals/evals.json に skill_name がありません")
            if "evaluation_mode" not in data:
                errors.append("evals/evals.json に evaluation_mode がありません")
            if "mode_reason" not in data:
                errors.append(
                    "evals/evals.json に mode_reason がありません（評価方式の選択理由の記録が必須）"
                )
            for i, ev in enumerate(data.get("evals", []), 1):
                for k in ("id", "prompt", "expected_output"):
                    if k not in ev:
                        errors.append(f"evals/evals.json の eval {i} に {k} がありません")
        else:
            if not isinstance(data, list):
                errors.append("evals/trigger-queries.json は配列である必要があります")
                continue
            yes = sum(1 for x in data if x.get("should_trigger") is True)
            no = sum(1 for x in data if x.get("should_trigger") is False)
            if yes < 5 or no < 5:
                warnings.append(
                    f"evals/trigger-queries.json のクエリ数が不足しています"
                    f"（should_trigger {yes} 件 / should_not_trigger {no} 件）"
                )
    return errors, warnings


def validate(skill_dir, strict=False, vocabulary=None):
    skill_dir = os.path.abspath(skill_dir)
    result = {"skill_dir": skill_dir, "errors": [], "warnings": []}
    if not os.path.isdir(skill_dir):
        result["errors"].append(f"スキルディレクトリが存在しません: {skill_dir}")
        return result
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        result["errors"].append("SKILL.md が存在しません")
        return result
    allow_cjk, foreign_cjk, latin_allow, foreign_chars = load_token_data(skill_dir)
    text = open(skill_md, encoding="utf-8").read()
    fm, body, fm_errors = parse_frontmatter(text)
    result["errors"].extend(fm_errors)

    for fn in (check_frontmatter,):
        e, w = fn(fm, skill_dir)
        result["errors"].extend(e)
        result["warnings"].extend(w)
    e, w = check_structure(skill_dir, body)
    result["errors"].extend(e)
    result["warnings"].extend(w)
    e, w = check_scripts(skill_dir)
    result["errors"].extend(e)
    result["warnings"].extend(w)
    e, w = check_text_files(skill_dir, allow_cjk, foreign_cjk, latin_allow, foreign_chars)
    result["errors"].extend(e)
    result["warnings"].extend(w)
    e, w = check_evals(skill_dir)
    result["errors"].extend(e)
    result["warnings"].extend(w)
    if vocabulary:
        e, w = check_vocabulary(skill_dir, vocabulary)
        result["errors"].extend(e)
        result["warnings"].extend(w)

    result["summary"] = {
        "errors": len(result["errors"]),
        "warnings": len(result["warnings"]),
        "skill_md_lines": len(body.split("\n")),
        "skill_md_tokens_estimate": estimate_tokens(body),
        "references": len(collect_refs(body)),
    }
    result["failed"] = bool(result["errors"]) or (strict and bool(result["warnings"]))
    return result


def main(argv):
    ap = argparse.ArgumentParser(
        prog="validate-skill.py",
        description="Agent Skills 公式仕様および運用ルールへの適合を検証する",
        epilog=(
            "終了コード:\n"
            "  0  適合（error なし）\n"
            "  1  不適合（error 1 件以上、または --strict 指定時に warning 1 件以上）\n"
            "  2  使用法エラー（対象ディレクトリが無い、引数が不正等）\n"
            "\n"
            "使用例:\n"
            "  python3 scripts/validate-skill.py ../my-skill\n"
            "  python3 scripts/validate-skill.py ../my-skill --format text\n"
            "  python3 scripts/validate-skill.py . --vocabulary assets/vocabulary.json --strict"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("skill_dir", help="検証対象のスキルディレクトリ")
    ap.add_argument("--format", choices=["json", "text"], default="json", help="出力形式（既定: json）")
    ap.add_argument("--strict", action="store_true", help="warning があっても終了コード 1 を返す")
    ap.add_argument("--vocabulary", help="語彙表 JSON のパス（指定すると語彙揺れを検証する）")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        # --help は正常終了（0）。引数誤りは使用法エラー（2）。
        return 0 if e.code == 0 else 2

    if not os.path.isdir(args.skill_dir):
        print(f"Error: スキルディレクトリが存在しません: {args.skill_dir}", file=sys.stderr)
        return 2

    vocabulary = None
    if args.vocabulary:
        vocabulary, err = load_vocabulary(args.vocabulary)
        if err:
            print(f"Error: {err}", file=sys.stderr)
            return 2

    res = validate(args.skill_dir, strict=args.strict, vocabulary=vocabulary)

    if args.format == "json":
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        s = res["summary"]
        print(f"Skill: {res['skill_dir']}")
        print(
            f"Summary: errors={s['errors']} warnings={s['warnings']} "
            f"lines={s['skill_md_lines']} tokens~{s['skill_md_tokens_estimate']} refs={s['references']}"
        )
        for item in res["errors"]:
            print(f"[Error] {item}")
        for item in res["warnings"]:
            print(f"[Warning] {item}")
        if not res["failed"]:
            print("Result: pass")

    for item in res["errors"]:
        print(f"Error: {item}", file=sys.stderr)
    for item in res["warnings"]:
        print(f"Warning: {item}", file=sys.stderr)

    return 1 if res["failed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
