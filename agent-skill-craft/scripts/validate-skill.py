#!/usr/bin/env python3
"""Agent Skills 公式仕様および運用ルールへの適合を検証する。

Usage:
    python3 scripts/validate-skill.py SKILL_DIR [--format json|text] [--strict]
    python3 scripts/validate-skill.py SKILL_DIR --vocabulary PATH

SKILL_DIR は検証対象のスキルディレクトリ（SKILL.md を含むディレクトリ）。
--vocabulary を指定すると、語彙表に対して語族の混在を検証する。

仕様上の数値（name の規則、description の長さ、段階的開示の予算、参照の深さ）は
`assets/agent-skills-spec.json` が正本であり、このスクリプトはハードコードしない。

出力は stdout に JSON（--format text を指定した場合はテキスト）、
診断は stderr へ分離する。

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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SPEC_FILE = "assets/agent-skills-spec.json"
TOKEN_FILE = "assets/foreign-tokens.json"
VOCAB_FILE = "assets/vocabulary.json"

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def load_spec():
    """公式仕様の正本を読み込む。正本がない場合は例外を送出し、検証を弱めない。"""
    path = os.path.join(SKILL_DIR, SPEC_FILE)
    data = load_json(path)
    if not isinstance(data, dict):
        raise FileNotFoundError(f"仕様の正本が見つかりません: {path}")
    return data


def load_token_data():
    """言語の混在の検出を補助する語彙データを読み込む。

    戻り値: (allow_cjk, foreign_cjk, latin_allow, foreign_chars)
    """
    path = os.path.join(SKILL_DIR, TOKEN_FILE)
    allow_cjk, foreign_cjk, latin_allow, foreign_chars = set(), set(), [], set()
    data = load_json(path)
    if not isinstance(data, dict):
        return allow_cjk, foreign_cjk, latin_allow, foreign_chars
    allow_cjk = set(data.get("cjk_allowlist", []))
    foreign_cjk = set(data.get("foreign_cjk_words", []))
    foreign_chars = set(data.get("cjk_variant_forms", ""))
    latin_allow = list(data.get("latin_allowlist", []))
    return allow_cjk, foreign_cjk, latin_allow, foreign_chars


# ---------------------------------------------------------------------------
# 言語の混在検出
# ---------------------------------------------------------------------------


def is_japanese_standard_kanji(ch):
    """JIS X 0208（日本語の標準漢字集合）に収録されているかを判定する。

    ISO-2022-JP へエンコードできるかで判定する。簡体字・繁体字など
    日本語の標準形と異なる字形は、収録されていないため NG になる。
    """
    try:
        ch.encode("iso2022_jp")
        return True
    except UnicodeEncodeError:
        return False


# 引用として明示する区切り。ここに囲まれた異言語の連続塊は意図された引用とみなす。
QUOTE_PATTERNS = [
    r"「[^」]*」",
    r"『[^』]*』",
    r'"[^"]*"',
    r"'[^']*'",
    r"（[^）]*）",
    r"\([^()]*\)",
    r"\[[^\[\]]*\]",
    r"`[^`]*`",
]


def _quoted_spans(line):
    """行内で引用として明示された区間の (開始, 終了) 一覧を返す。"""
    spans = []
    for pat in QUOTE_PATTERNS:
        for m in re.finditer(pat, line):
            spans.append((m.start(), m.end()))
    return spans


def _within_spans(start, end, spans):
    """連続塊全体が単一の引用区間内に収まる場合に True。"""
    return any(s <= start and end <= e for s, e in spans)


# 基準言語ごとの文字体系の期待値。組込みの設定は代表例であり、言語の種類に制限は設けない。
# 未知の言語コードは区切り構造のみを手掛かりに警告する。新たな言語には表を拡張する。
# base: 行に基準言語の文があるかを判定する正規表現
# han: 漢字の連続塊の扱い（jis=JIS oracle＋語リスト / flag=無条件に異言語 / allow=基準言語として許可）
# kana: かなの扱い（base=基準言語の一部 / foreign=異言語）
# latin_base: 基準言語がラテン文字を主用する場合は True（ラテン語の検証を省く）
# native_res: 基準言語の固有文字体系に属する連続塊の正規表現（該当分は異言語とみなさない）
BASE_SCRIPTS = {
    "ja": {"base_re": r"[\u3040-\u309f]", "han": "jis", "kana": "base", "latin_base": False, "native_res": []},
    "en": {"base_re": r"[A-Za-z]{2,}", "han": "flag", "kana": "foreign", "latin_base": True, "native_res": []},
    "fr": {"base_re": r"[A-Za-zÀ-ÿ]{2,}", "han": "flag", "kana": "foreign", "latin_base": True, "native_res": []},
    "zh": {"base_re": r"[\u4e00-\u9fff]", "han": "allow", "kana": "foreign", "latin_base": False, "native_res": []},
    "ko": {"base_re": r"[\uac00-\ud7af]", "han": "allow", "kana": "foreign", "latin_base": False, "native_res": [r"[\uac00-\ud7af]+"]},
}

DEDICATED_RE = r"[\u0400-\u04FF\uAC00-\uD7AF\u0370-\u03FF\u0600-\u06FF]+"
KANA_RE = r"[\u3040-\u30ff]+"


def detect_foreign_scripts(text, allow_cjk, foreign_cjk, foreign_chars, base="ja"):
    """言語の混在を検出する。戻り値: [(区分, 行番号, 語, 行の全文)]

    不変条件: 対象文書の基準言語を 1 つ決める。異なる言語の語は引用として
    明示する（引用符・コードスパン・独立行・括弧）。引用として明示されずに
    基準言語の文中に埋め込まれた語は欠陥とする。

    区分は "error"（基準言語の文中に区切りなく埋め込まれた異言語）
    または "warning"（行全体が異言語で、引用として明示されていない）。
    引用として明示された異言語の連続塊は許可する。

    漢字の判定の順序（基準言語が日本語の場合）:
      1. JIS X 0208 に収録されない漢字は異言語とみなす。判定は文字集合で行い、
         語リストに依存しない。
      2. 収録されるが基準言語で使わない字形・語は語リストで検出する（補助）。
    """
    cfg = BASE_SCRIPTS.get(base, {})
    base_re = cfg.get("base_re")
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        spans = _quoted_spans(line)
        masked = list(line)
        for s, e in spans:
            for j in range(s, e):
                masked[j] = " "
        bare = "".join(masked)
        base_present = bool(re.search(base_re, bare)) if base_re else False

        def note(token, start, end):
            if _within_spans(start, end, spans):
                return
            kind = "error" if base_present else "warning"
            hits.append((kind, i, token, line.strip()))

        if cfg.get("dedicated", "foreign") == "foreign":
            for m in re.finditer(DEDICATED_RE, line):
                # 基準言語の固有文字体系に属する連続塊は除外する
                if any(re.fullmatch(p, m.group()) for p in cfg.get("native_res", [])):
                    continue
                note(m.group(), m.start(), m.end())
        if cfg.get("kana") == "foreign":
            for m in re.finditer(KANA_RE, line):
                note(m.group(), m.start(), m.end())
        for m in re.finditer(r"[\u4E00-\u9FFF]+", line):
            run, start, end = m.group(), m.start(), m.end()
            if _within_spans(start, end, spans):
                continue
            han = cfg.get("han", "jis")
            if han == "allow":
                continue
            if han == "flag":
                note(run, start, end)
                continue
            for ch in run:
                if ch in allow_cjk:
                    continue
                if not is_japanese_standard_kanji(ch):
                    note(ch, start, end)
                    break
                if ch in foreign_chars:
                    note(ch, start, end)
                    break
            else:
                for w in sorted(foreign_cjk, key=len, reverse=True):
                    if w in run:
                        note(w, start, end)
                        break
    return hits


LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_./-]{1,}")
CODE_SPAN = re.compile(r"`[^`]*`")


def detect_latin_in_japanese(text, latin_allow, base="ja", latin_base=False):
    """基準言語の行に、正体の知れないラテン文字の単語が埋め込まれた箇所を検出する。

    判定は単語ごとに行う。引用として明示された区間内の語は許可する。
    基準言語がラテン文字を主用する場合は検証しない。
    """
    if latin_base:
        return []
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
        spans = _quoted_spans(line)
        masked = CODE_SPAN.sub(lambda m: " " * len(m.group()), line)
        for m in LATIN_WORD.finditer(masked):
            g = m.group()
            if g in latin_allow:
                continue
            if _within_spans(m.start(), m.end(), spans):
                continue
            bare = "".join(
                " " if any(s <= j < e for s, e in spans) else ch
                for j, ch in enumerate(line)
            )
            kind = "error" if re.search(r"[\u3040-\u309f]", bare) else "warning"
            hits.append((kind, i, g, line.strip()))
    return hits


def detect_replacement_chars(text):
    """文字化け文字 (U+FFFD) を検出する。"""
    return [
        (i, "U+FFFD", line.strip())
        for i, line in enumerate(text.split("\n"), 1)
        if "\ufffd" in line
    ]


# ---------------------------------------------------------------------------
# 語彙検証
# ---------------------------------------------------------------------------


def check_vocabulary(skill_dir, vocab):
    """語彙表に対して語族の混在を検証する。

    語彙表の形式:
      { "term_families": [["利用者", "ユーザー", "依頼者"], ...] }
    各家族の先頭要素が正式な語である。

    判定:
      - 同じ家族から 2 種類以上が現れた場合: error（表記の混在）
      - 正式な語が現れず異形だけ現れた場合: warning（正式な語へ統一されていない）
    家族を 1 度定義すれば、禁止形を漏れなく列挙する必要はない。
    除外ファイルのうち Markdown は定義表の行だけを除外し、散文部は検査する
    （定義ファイルの自己適用確認）。JSON の値は定義そのものであるため除外する。
    """
    errors, warnings = [], []
    families = vocab.get("term_families", [])
    if not families:
        return errors, warnings
    exempt = set(vocab.get("_scan_exempt_files", []))
    for path in iter_text_files(skill_dir, (".md", ".json"), set()):
        rel = os.path.relpath(path, skill_dir)
        if rel in exempt and path.endswith(".json"):
            continue
        text = read_prose_no_tables(path) if rel in exempt else read_prose(path)
        for family in families:
            if not family:
                continue
            canonical = family[0]
            present = []
            masked = text
            for w in sorted(family, key=len, reverse=True):
                if w in masked:
                    present.append(w)
                    masked = masked.replace(w, " " * len(w))
            if len(present) >= 2:
                errors.append(
                    f"{rel} 語彙の混在: {' / '.join(present)} は同じ対象を指す別語です"
                    f"（正式な語: {canonical}）"
                )
            elif len(present) == 1 and present[0] != canonical:
                warnings.append(
                    f"{rel} 正式な語「{canonical}」ではなく「{present[0]}」を使っています"
                )
    return errors, warnings


def check_vocab_consistency(skill_dir, vocab):
    """語彙表の定義表と正本 JSON の一致を検証する。

    - 2 節の表（統一語｜禁止形）と `term_families` の完全一致を確認する。
    - `distinct_terms` の各語が 3 節の表に定義されていることを確認する。
    定義表と正本の二重管理のずれを検出する。
    """
    errors = []
    md = os.path.join(skill_dir, "references", "vocabulary.md")
    if not os.path.isfile(md):
        return errors
    try:
        lines = open(md, encoding="utf-8").read().split("\n")
    except OSError:
        return errors

    in_sec2, in_sec3 = False, False
    table_families = {}
    sec3_terms = set()
    for line in lines:
        s = line.strip()
        if s.startswith("## "):
            in_sec2 = s.startswith("## 2.")
            in_sec3 = s.startswith("## 3.")
            continue
        if not s.startswith("|"):
            continue
        cells = [c.strip().strip("*") for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0] in ("語", "統一語") or set(cells[0]) <= set("-: "):
            continue
        if in_sec2 and len(cells) >= 3:
            table_families[cells[0]] = {w.strip() for w in cells[1].split("／") if w.strip()}
        elif in_sec3 and len(cells) >= 2:
            sec3_terms.add(cells[0])

    json_families = {}
    for family in vocab.get("term_families", []):
        if family:
            json_families[family[0]] = set(family[1:])
    if set(table_families) != set(json_families):
        errors.append(
            "語彙表 2 節と正本の家族が一致しません"
            f"（表のみ: {sorted(set(table_families) - set(json_families))} / "
            f"正本のみ: {sorted(set(json_families) - set(table_families))}）"
        )
    for canon, variants in table_families.items():
        if canon in json_families and variants != json_families[canon]:
            errors.append(
                f"語彙表 2 節と正本の家族「{canon}」の禁止形が一致しません"
                f"（表: {sorted(variants)} / 正本: {sorted(json_families[canon])}）"
            )
    for e in vocab.get("distinct_terms", []):
        terms = e.get("terms") if isinstance(e, dict) else e
        if not isinstance(terms, list):
            continue
        for t in terms:
            if t not in sec3_terms:
                errors.append(
                    f"distinct_terms の語「{t}」が語彙表 3 節に定義されていません"
                )
    return errors


# ---------------------------------------------------------------------------
# 重複検証
# ---------------------------------------------------------------------------

LIST_MARKER = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
MD_NOISE = re.compile(r"[`*_#>|\[\]（）「」]|\s+")


def read_prose(path):
    """Markdown/JSON から散文部分を取り出す。コードフェンスと表の区切り行は除く。"""
    if path.endswith(".json"):
        data = load_json(path)
        if data is None:
            return ""
        return "\n".join(json_values(data))
    out = []
    in_fence = False
    for line in open(path, encoding="utf-8").read().split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"^\s*\|?[\s:|-]+\|?\s*$", line) and "-" in line:
            continue
        out.append(line)
    return "\n".join(out)


def read_prose_no_tables(path):
    """定義ファイルの自己適用確認用に、表の行を除いた散文部分を取り出す。

    定義表は禁止形の列挙を必然的に含むため、表の行（`|` で始まる行）を除く。
    それ以外の処理は `read_prose` と同じである。
    """
    out = []
    in_fence = False
    for line in open(path, encoding="utf-8").read().split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.lstrip().startswith("|"):
            continue
        if re.match(r"^\s*\|?[\s:|-]+\|?\s*$", line) and "-" in line:
            continue
        out.append(line)
    return "\n".join(out)


def json_values(obj):
    """JSON の値（キーは除く）だけを列挙する。"""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from json_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from json_values(v)
    elif isinstance(obj, str):
        yield obj


def iter_text_files(skill_dir, exts, exempt):
    for root, _dirs, files in os.walk(skill_dir):
        for f in sorted(files):
            if f.startswith(".") or not f.endswith(exts):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, skill_dir)
            if rel in exempt:
                continue
            yield full


def normalize_sentence(line):
    """比較用に文を正規化する。"""
    s = LIST_MARKER.sub("", line)
    s = MD_NOISE.sub("", s)
    return s.strip().rstrip("。.")


def collect_sentences(skill_dir, exempt):
    """散文から比較対象の文を集める。戻り値: [(key, ファイル, 行番号, 正規化文)]"""
    result = []
    for path in iter_text_files(skill_dir, (".md",), exempt):
        rel = os.path.relpath(path, skill_dir)
        in_fence = False
        for i, line in enumerate(open(path, encoding="utf-8").read().split("\n"), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not line.strip():
                continue
            if line.lstrip().startswith("#"):
                continue
            if re.match(r"^\s*\|?[\s:|-]+\|?\s*$", line) and "-" in line:
                continue
            norm = normalize_sentence(line)
            if len(norm) < 20:
                continue
            result.append((norm, rel, i, line.strip()))
    return result


def bigrams(s):
    return {s[i : i + 2] for i in range(len(s) - 1)}


def jaccard(a, b):
    ga, gb = bigrams(a), bigrams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def _strip_distinct(norm, distinct_sets):
    """distinct_terms の語を取り除いた文を返す。残りが一致すれば差は宣言済みの使い分けだけである。"""
    out = norm
    for s in distinct_sets:
        for w in s:
            out = out.replace(w, "\u0001")
    return out


def check_duplication(skill_dir, exempt, vocab=None):
    """記述の重複と、矛盾の候補（表現が近い文）を検出する。

    - 正規化文が 2 箇所以上に出現: warning（重複定義）
    - 正規化文の字bigram 類似度が 0.75 以上の 2 文: warning（矛盾の候補）。
      差が distinct_terms で宣言済みの使い分けだけの場合は警告しない。
    - 類似度が 0.6 以上 0.75 未満の 2 文: warning（語族の候補として検討する。
      機械は無断で追加しない。整理案への採用・却下は人間が判断する）。
    """
    warnings = []
    distinct = []
    if isinstance(vocab, dict):
        for e in vocab.get("distinct_terms", []):
            terms = e.get("terms") if isinstance(e, dict) else e
            if isinstance(terms, list) and len(terms) >= 2:
                distinct.append(terms)
    sentences = collect_sentences(skill_dir, exempt)
    by_key = {}
    for norm, rel, lineno, raw in sentences:
        by_key.setdefault(norm, []).append((rel, lineno, raw))
    for norm, places in by_key.items():
        if len(places) < 2:
            continue
        locs = "、".join(f"{r}:{n}" for r, n, _ in places)
        warnings.append(f"記述が重複しています（{locs}）: {places[0][2][:60]}")

    candidates = []
    for i in range(len(sentences)):
        norm_a, rel_a, line_a, raw_a = sentences[i]
        for j in range(i + 1, len(sentences)):
            norm_b, rel_b, line_b, raw_b = sentences[j]
            if rel_a == rel_b and abs(line_a - line_b) < 3:
                continue
            sim = jaccard(norm_a, norm_b)
            if sim >= 0.75:
                if _strip_distinct(norm_a, distinct) == _strip_distinct(norm_b, distinct):
                    continue
                warnings.append(
                    f"表現が近い文があります。矛盾していないか確認する"
                    f"（{rel_a}:{line_a} と {rel_b}:{line_b}）: {raw_a[:50]}"
                )
            elif sim >= 0.6 and len(candidates) < 5:
                ta = set(re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fffA-Za-z]{2,}", norm_a))
                tb = set(re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fffA-Za-z]{2,}", norm_b))
                diff = sorted((ta | tb) - (ta & tb))[:4]
                if diff:
                    candidates.append(
                        f"語族の候補として検討する（{rel_a}:{line_a} と {rel_b}:{line_b}）: "
                        f"異なる語 {', '.join(diff)}"
                    )
    warnings.extend(candidates)
    return warnings


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
    return int(cjk * 1.2 + ascii_chars * 0.25 + other * 1.2)


def check_frontmatter(fm, skill_dir, spec):
    errors, warnings = [], []
    req = spec["frontmatter"]["required"]
    opt = spec["frontmatter"].get("optional", {})
    disc = spec.get("progressive_disclosure", {})

    name_rule = req["name"]
    name = fm.get("name", "")
    if not name:
        errors.append("frontmatter に name がありません")
    else:
        if len(name) > name_rule["max_length"]:
            errors.append(
                f"name が {name_rule['max_length']} 文字を超えています（実際 {len(name)}）"
            )
        if not re.match(name_rule["pattern"], name):
            errors.append(
                "name が不正です。a-z 0-9 と単独のハイフンのみ使用でき、"
                "先頭・末尾のハイフンと連続ハイフンは禁止されます"
            )
        if name_rule.get("must_match_directory_name") and (
            name != os.path.basename(os.path.abspath(skill_dir))
        ):
            errors.append(
                f"name（{name}）が親ディレクトリ名"
                f"（{os.path.basename(os.path.abspath(skill_dir))}）と一致しません"
            )

    desc_rule = req["description"]
    desc = fm.get("description", "")
    if not desc:
        errors.append("frontmatter に description がありません")
    elif len(desc) > desc_rule["max_length"]:
        errors.append(
            f"description が {desc_rule['max_length']} 文字を超えています"
            f"（実際 {len(desc)}）"
        )
    else:
        lowered = desc.lower()
        signals = ["use this skill", "use when", "apply this skill", "whenever", "use it when"]
        has_signal = any(s in lowered for s in signals)
        if not has_signal and re.search(r"[\u3040-\u309f\u4e00-\u9fff]", desc):
            has_signal = bool(
                re.search(
                    r"(とき|際|場合|たら|れば|なら).{0,10}"
                    r"(使う|使用|利用|参照|読み込|実行|作成|適用|発動)",
                    desc,
                )
            )
        if not has_signal:
            warnings.append(
                "description に命令形の使用指示"
                "（use this skill when ...／〜ときに使う ... など）がありません。"
                "説明型では発動しにくくなります"
            )
        target = disc.get("metadata_target_tokens", 100)
        desc_tokens = estimate_tokens(desc)
        if desc_tokens > target:
            warnings.append(
                f"description の概算 token 数が {desc_tokens} です。"
                f"目安は {target} token 程度であり、全スキル分のセッション開始時に読み込まれます"
            )

    for key, rule in opt.items():
        if key not in fm:
            continue
        val = fm.get(key, "")
        maxlen = rule.get("max_length")
        if maxlen and len(val) > maxlen:
            errors.append(f"{key} が {maxlen} 文字を超えています（実際 {len(val)}）")
        if val == "":
            warnings.append(f"frontmatter の {key} が空です")
        if rule.get("type") == "string_map" and ":" not in val:
            warnings.append(
                f"frontmatter の {key} がマップ形式に見えません。"
                "文字列から文字列へのマップで記述すること"
            )

    return errors, warnings


def collect_refs(body):
    """本文からファイル参照を抽出する。戻り値: [(path, lineno)]"""
    refs = []
    patterns = [
        r"`((?:references|scripts|assets|evals)/[^`\s]+)`",
        r"\]\(((?:references|scripts|assets|evals)/[^)\s]+)\)",
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


def check_structure(skill_dir, body, spec):
    errors, warnings = [], []
    disc = spec.get("progressive_disclosure", {})
    max_depth = spec.get("file_references", {}).get("max_depth", 1)
    max_lines = disc.get("skill_md_max_lines", 500)
    max_tokens = disc.get("skill_md_max_tokens", 5000)

    lines = body.split("\n")
    if len(lines) > max_lines:
        errors.append(f"SKILL.md 本文が {max_lines} 行を超えています（実際 {len(lines)}）")
    tokens = estimate_tokens(body)
    if tokens > max_tokens:
        warnings.append(f"SKILL.md 本文の概算 token 数が {tokens} です（推奨 {max_tokens} 未満）")

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
        if depth > max_depth:
            errors.append(
                f"{path}（SKILL.md:{lineno}）は {depth} 段深さです。"
                f"公式仕様に従い {max_depth} 段深さ（references/foo.md 形式）に収めてください"
            )

    for d in spec.get("directories", {}).get("optional", []):
        dpath = os.path.join(skill_dir, d)
        if not os.path.isdir(dpath):
            continue
        for root, _dirs, files in os.walk(dpath):
            for f in files:
                if f.startswith("."):
                    continue
                rel = os.path.relpath(os.path.join(root, f), skill_dir)
                if rel not in referenced:
                    warnings.append(
                        f"{rel} は SKILL.md から参照されていません"
                        "（読まれないファイルはコンテキスト予算の無駄）"
                    )

    refdir = os.path.join(skill_dir, "references")
    if os.path.isdir(refdir):
        for root, _dirs, files in os.walk(refdir):
            for f in sorted(files):
                if not f.endswith(".md") or f.startswith("."):
                    continue
                p = os.path.join(root, f)
                try:
                    nlines = len(open(p, encoding="utf-8").read().split("\n"))
                except OSError:
                    continue
                ref_max = spec.get("reference_files", {}).get("max_lines", 300)
                if nlines > ref_max:
                    warnings.append(
                        f"{os.path.relpath(p, skill_dir)} は {nlines} 行です。"
                        f"{ref_max} 行を超える場合は目次を付けるか分割を検討すること"
                    )
    return errors, warnings


# ファイルパスが読み込み動詞の目的語になっている場合のみ、読み込み指示とみなす。
# 「を SKILL.md に明記する」「SKILL.md から」「SKILL.md への」のような
# 言及だけの記述は対象外。目的語を示す「を」「の」の直後に動詞が続く形を要求する。
LOAD_EDGE = re.compile(
    r"(references/[^\s`）」\"']+\.md|SKILL\.md)\s*(を|の)[^。\n]{0,20}"
    r"(読み込む|読み込み|読んで|ロード|load)",
    re.IGNORECASE,
)


def check_reference_graph(skill_dir):
    """参照ファイル間の読み込み指示の循環を検出する。

    読み込み指示は SKILL.md から参照ファイルへの一方向でなければならない。
    参照ファイルからほかの参照ファイル、または SKILL.md への読み込み指示は
    循環の原因になるため error とする。ファイル名の言及だけは対象外。
    """
    errors = []
    nodes = ["SKILL.md"]
    refdir = os.path.join(skill_dir, "references")
    if os.path.isdir(refdir):
        for root, _dirs, files in os.walk(refdir):
            for f in sorted(files):
                if f.endswith(".md") and not f.startswith("."):
                    nodes.append(os.path.relpath(os.path.join(root, f), skill_dir))
    edges = {n: [] for n in nodes}
    for node in nodes:
        p = os.path.join(skill_dir, node)
        try:
            text = open(p, encoding="utf-8").read()
        except OSError:
            continue
        in_fence = False
        for line in text.split("\n"):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in LOAD_EDGE.finditer(line):
                target = m.group(1)
                if target == node:
                    continue
                if target not in edges:
                    continue
                edges[node].append(target)

    for src, dsts in edges.items():
        for dst in dsts:
            if src != "SKILL.md":
                errors.append(
                    f"{src} が {dst} への読み込み指示を含んでいます。"
                    "読み込み指示は SKILL.md から参照ファイルへの一方向にすること"
                )

    visited, stack, path = set(), set(), []

    def dfs(node):
        visited.add(node)
        stack.add(node)
        path.append(node)
        for nxt in edges.get(node, []):
            if nxt not in visited:
                if dfs(nxt):
                    return True
            elif nxt in stack:
                cyc = path[path.index(nxt):] + [nxt]
                errors.append(f"参照が循環しています: {' → '.join(cyc)}")
                return True
        stack.discard(node)
        path.pop()
        return False

    for n in nodes:
        if n not in visited:
            dfs(n)
    return errors


def check_scripts(skill_dir, spec):
    errors, warnings = [], []
    sdir = os.path.join(skill_dir, "scripts")
    if not os.path.isdir(sdir):
        return errors, warnings
    required = set(spec.get("script_requirements", []))
    for f in sorted(os.listdir(sdir)):
        if f.startswith(".") or not f.endswith((".py", ".sh", ".js", ".mjs", ".ts")):
            continue
        p = os.path.join(sdir, f)
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError as e:
            errors.append(f"scripts/{f} を読めません: {e}")
            continue
        if "help_option_documented" in required:
            if "--help" not in text and "argparse" not in text and "add_argument" not in text:
                warnings.append(f"scripts/{f} に --help の記述がありません")
        if "meaningful_exit_codes" in required:
            if not re.search(r"exit\s*\(\s*[012]", text) and "sys.exit" not in text:
                warnings.append(f"scripts/{f} に終了コードの指定が見当たりません")
        if "dry_run_for_destructive_operations" in required:
            if "dry" not in text.lower() and ("open(" in text or "write" in text):
                warnings.append(f"scripts/{f} に状態変更の操作があるため --dry-run がない可能性があります")
    return errors, warnings


# 仮名書きの対象語と推奨形。副詞・接続詞の用法に限り、熟語・固有名詞は対象外とする。
# 正規表現で助詞・活用語尾の接続を要求し、熟語（他人・既存・全力など）を除外する。
KANA_WORDS = [
    (r"他(?=[のにへとはがをもで])", "ほか"),
    (r"既に", "すでに"),
    (r"全て", "すべて"),
    (r"及び", "および"),
    (r"又は", "または"),
    (r"但し", "ただし"),
]


def check_kana_usage(text):
    """仮名書きすべき語の漢字使用を検出する。戻り値: [(行番号, 語, 推奨形, 行の全文)]

    引用として明示された区間・コードフェンス内は対象外とする。文脈依存の
    ため warning 相当の候補として返す。熟語は正規表現で除外する。
    """
    hits = []
    in_fence = False
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        spans = _quoted_spans(line)
        for pat, sug in KANA_WORDS:
            for m in re.finditer(pat, line):
                if _within_spans(m.start(), m.end(), spans):
                    continue
                hits.append((i, m.group(), sug, line.strip()))
    return hits


def check_text_files(skill_dir, allow_cjk, foreign_cjk, latin_allow, foreign_chars, base="ja"):
    """テキストファイル全体の言語の混在と文字化けを検証する。

    検証の向き:
      - Markdown: 全文を対象に検証する。
      - JSON: キーは検証対象から除外し、値のみを検証する。
      - Python: 英語識別子が正当であるため、言語の混在と文字化けのみを検証する。
      - evals/ 配下: 言語検査の対象外とする。トリガークエリは利用者発話の
        模写であり、パス・技術語・誤字を含むことが正当なためである。
        構造は check_evals で検証する。
    引用として明示された異言語の連続塊は許可する。区切りなく埋め込まれた
    語は error、行全体が異言語で引用の明示がないものは warning とする。
    """
    errors, warnings = [], []

    def emit(kind, rel, i, token, line, suffix=""):
        msg = f"{rel}:{i} 言語の混在「{token}」があります{suffix}: {line[:80]}"
        (errors if kind == "error" else warnings).append(msg)

    exempt = {os.path.relpath(os.path.join(SKILL_DIR, TOKEN_FILE), SKILL_DIR)}
    latin_base = BASE_SCRIPTS.get(base, {}).get("latin_base", False)
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
            if rel.startswith("evals/"):
                for i, token, line in detect_replacement_chars(text):
                    errors.append(f"{rel}:{i} 文字化け文字 (U+FFFD) が含まれています: {line[:80]}")
                continue
            for i, token, line in detect_replacement_chars(text):
                errors.append(f"{rel}:{i} 文字化け文字 (U+FFFD) が含まれています: {line[:80]}")
            for kind, i, token, line in detect_foreign_scripts(
                text, allow_cjk, foreign_cjk, foreign_chars, base
            ):
                emit(kind, rel, i, token, line)

            if f.endswith(".py"):
                continue
            if f.endswith(".json"):
                data = load_json(p)
                if data is not None:
                    for value in json_values(data):
                        for kind, i, token, line in detect_latin_in_japanese(
                            value, latin_allow, base, latin_base
                        ):
                            emit(kind, rel, i, token, line, suffix="（JSON の値）")
                    continue
            for kind, i, token, line in detect_latin_in_japanese(text, latin_allow, base, latin_base):
                emit(kind, rel, i, token, line)
            if f.endswith((".md", ".py")):
                for i, token, sug, line in check_kana_usage(text):
                    warnings.append(
                        f"{rel}:{i} 仮名書きの語「{token}」があります"
                        f"（推奨: {sug}）: {line[:80]}"
                    )
    return errors, warnings


def check_spec_consistency(skill_dir, spec):
    """references/specification.md の数値が正本と一致するかを確認する。

    正本に値がなく md 側だけに値がある項目は「正本にない」として報告する。
    """
    errors = []
    md = os.path.join(skill_dir, "references", "specification.md")
    if not os.path.isfile(md):
        return errors
    text = open(md, encoding="utf-8").read()
    fm = spec.get("frontmatter", {})
    disc = spec.get("progressive_disclosure", {})

    def row_of(field):
        for line in text.split("\n"):
            if line.startswith("| `" + field + "`"):
                return line
        return None

    def number_in(field, pattern):
        row = row_of(field)
        if row is None:
            return None
        m = re.search(pattern, row)
        return int(m.group(1)) if m else None

    checks = [
        ("name", r"\d+ 〜 (\d+) 文字", fm.get("required", {}).get("name", {}).get("max_length"), "name の最大文字数"),
        ("description", r"\d+ 〜 (\d+) 文字", fm.get("required", {}).get("description", {}).get("max_length"), "description の最大文字数"),
        ("compatibility", r"(\d+) 文字以下", fm.get("optional", {}).get("compatibility", {}).get("max_length"), "compatibility の最大文字数"),
    ]
    for field, pattern, expected, label in checks:
        if expected is None:
            continue
        found = number_in(field, pattern)
        if found is None:
            errors.append(f"references/specification.md に{label}の記述がありません（正本: {expected}）")
        elif found != expected:
            errors.append(
                f"references/specification.md の{label}が正本と不一致です"
                f"（記述: {found} / 正本: {expected}）"
            )

    for pattern, expected, label in [
        (r"(\d+) token 未満", disc.get("skill_md_max_tokens"), "SKILL.md の token 予算"),
        (r"(\d+) 行未満", disc.get("skill_md_max_lines"), "SKILL.md の行数予算"),
        (r"(\d+) 段深さ", spec.get("file_references", {}).get("max_depth"), "参照の深さ"),
    ]:
        if expected is None:
            continue
        m = re.search(pattern, text)
        if not m:
            errors.append(f"references/specification.md に{label}の記述がありません（正本: {expected}）")
        elif int(m.group(1)) != expected:
            errors.append(
                f"references/specification.md の{label}が正本と不一致です"
                f"（記述: {m.group(1)} / 正本: {expected}）"
            )

    desc_max = fm.get("required", {}).get("description", {}).get("max_length")
    if desc_max is not None:
        ev = os.path.join(skill_dir, "references", "evaluation.md")
        if os.path.isfile(ev):
            try:
                etext = open(ev, encoding="utf-8").read()
            except OSError:
                etext = ""
            m = re.search(r"(\d+) 文字以内", etext)
            if not m:
                errors.append(
                    f"references/evaluation.md に description 上限の記述がありません"
                    f"（正本: {desc_max}）"
                )
            elif int(m.group(1)) != desc_max:
                errors.append(
                    f"references/evaluation.md の description 上限が正本と不一致です"
                    f"（記述: {m.group(1)} / 正本: {desc_max}）"
                )
    return errors


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
        data = load_json(p)
        if data is None:
            errors.append(f"evals/{fname} の JSON を解析できません")
            continue
        if fname == "evals.json":
            for k in ("skill_name", "evaluation_mode", "mode_reason"):
                if k not in data:
                    errors.append(f"evals/evals.json に {k} がありません")
            if data.get("evaluation_mode") not in ("assertion", "human", "both"):
                errors.append(
                    "evals/evals.json の evaluation_mode が無効です"
                    "（assertion / human / both のいずれか）"
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
            if yes < 10 or no < 10:
                warnings.append(
                    f"evals/trigger-queries.json のクエリ数が不足しています"
                    f"（should_trigger {yes} 件 / should_not_trigger {no} 件）"
                )
            if not all("split" in x for x in data):
                warnings.append(
                    "evals/trigger-queries.json に split 欄（train / validation）がない"
                    " 学習用と検証用の分割が固定されていない"
                )
            bad = sorted({x.get("split") for x in data if x.get("split") not in ("train", "validation")})
            if bad:
                errors.append(
                    f"evals/trigger-queries.json の split 値が無効です: {bad}"
                    "（train か validation のいずれか）"
                )
    return errors, warnings


def validate(skill_dir, strict=False, vocabulary=None, base="ja"):
    skill_dir = os.path.abspath(skill_dir)
    result = {"skill_dir": skill_dir, "errors": [], "warnings": []}
    if not os.path.isdir(skill_dir):
        result["errors"].append(f"スキルディレクトリが存在しません: {skill_dir}")
        return result
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        result["errors"].append("SKILL.md が存在しません")
        return result

    try:
        spec = load_spec()
    except FileNotFoundError as e:
        result["errors"].append(str(e))
        result["summary"] = {"errors": 1, "warnings": 0, "skill_md_lines": 0,
                              "skill_md_tokens_estimate": 0, "references": 0}
        result["failed"] = True
        return result
    allow_cjk, foreign_cjk, latin_allow, foreign_chars = load_token_data()
    text = open(skill_md, encoding="utf-8").read()
    fm, body, fm_errors = parse_frontmatter(text)
    result["errors"].extend(fm_errors)

    for fn in (lambda: check_frontmatter(fm, skill_dir, spec),):
        e, w = fn()
        result["errors"].extend(e)
        result["warnings"].extend(w)
    e, w = check_structure(skill_dir, body, spec)
    result["errors"].extend(e)
    result["warnings"].extend(w)
    result["errors"].extend(check_reference_graph(skill_dir))
    e, w = check_scripts(skill_dir, spec)
    result["errors"].extend(e)
    result["warnings"].extend(w)
    e, w = check_text_files(skill_dir, allow_cjk, foreign_cjk, latin_allow, foreign_chars, base)
    result["errors"].extend(e)
    result["warnings"].extend(w)
    result["errors"].extend(check_spec_consistency(skill_dir, spec))
    e, w = check_evals(skill_dir)
    result["errors"].extend(e)
    result["warnings"].extend(w)
    if vocabulary:
        e, w = check_vocabulary(skill_dir, vocabulary)
        result["errors"].extend(e)
        result["warnings"].extend(w)
        result["errors"].extend(check_vocab_consistency(skill_dir, vocabulary))

    exempt = set()
    if vocabulary:
        exempt = set(vocabulary.get("_scan_exempt_files", []))
    result["warnings"].extend(check_duplication(skill_dir, exempt, vocabulary))

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
            "  2  使用法エラー（対象ディレクトリがない、引数が不正など）\n"
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
    ap.add_argument("--vocabulary", help="語彙表 JSON のパス（指定すると語族の混在を検証する）")
    ap.add_argument(
        "--base",
        default="ja",
        help="対象文書の基準言語（既定: ja）。任意の言語コードを指定できる（例: ja、en）。組込みの設定がない言語は、引用の区切りを手掛かりに警告のみ行う",
    )
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 2

    if not os.path.isdir(args.skill_dir):
        print(f"Error: スキルディレクトリが存在しません: {args.skill_dir}", file=sys.stderr)
        return 2

    vocabulary = None
    if args.vocabulary:
        path = args.vocabulary
        if not os.path.isabs(path) and not os.path.isfile(path):
            alt = os.path.join(SKILL_DIR, path)
            if os.path.isfile(alt):
                path = alt
        vocabulary = load_json(path)
        if not isinstance(vocabulary, dict):
            print(f"Error: 語彙表を読み込めません: {args.vocabulary}", file=sys.stderr)
            return 2

    res = validate(args.skill_dir, strict=args.strict, vocabulary=vocabulary, base=args.base)

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
