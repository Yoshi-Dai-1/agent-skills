#!/usr/bin/env python3
"""監査の未決済台帳（ledger）を管理する。

Usage:
    python3 scripts/audit-ledger.py list   --ledger PATH
    python3 scripts/audit-ledger.py add    --ledger PATH --file PATH --line N --kind KIND --summary TEXT [--evidence TEXT]
    python3 scripts/audit-ledger.py resolve --ledger PATH --id ID --reason TEXT
    python3 scripts/audit-ledger.py check  --ledger PATH
    python3 scripts/audit-ledger.py report --ledger PATH

台帳は JSON ファイルで保持する。実行結果は stdout、診断は stderr へ分離する。

終了コード:
    0  成功
    1  台帳エラー（不正な JSON、存在しない ID、未決済が残っているなど）
    2  使用法エラー
"""
import argparse
import json
import os
import sys

KINDS = (
    "structure",
    "terminology",
    "consistency",
    "accuracy",
    "coverage",
    "spec",
    "evaluation",
    "other",
)
STATUSES = ("open", "closed")


def load(path):
    if not os.path.exists(path):
        return {"ledger_version": 1, "skill": None, "items": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("items", [])
    return data


def save(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def next_id(items):
    n = 0
    for it in items:
        try:
            n = max(n, int(it.get("id", 0)))
        except (TypeError, ValueError):
            continue
    return n + 1


def cmd_list(args):
    data = load(args.ledger)
    items = data["items"]
    if args.status:
        items = [it for it in items if it.get("status") == args.status]
    payload = {
        "ledger": os.path.abspath(args.ledger),
        "count": len(items),
        "open_count": sum(1 for it in data["items"] if it.get("status") == "open"),
        "items": items,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_add(args):
    data = load(args.ledger)
    # 冪等: 同一の file / line / kind / summary / evidence がすでにあるときは既存を返す
    for it in data["items"]:
        if (
            it.get("file") == args.file
            and it.get("line") == args.line
            and it.get("kind") == args.kind
            and it.get("summary") == args.summary
            and it.get("evidence") == args.evidence
        ):
            print(json.dumps({"added": None, "existing": it}, ensure_ascii=False, indent=2))
            return 0
    item = {
        "id": next_id(data["items"]),
        "status": "open",
        "file": args.file,
        "line": args.line,
        "kind": args.kind,
        "summary": args.summary,
        "evidence": args.evidence,
    }
    if args.dry_run:
        print(json.dumps({"dry_run": True, "would_add": item}, ensure_ascii=False, indent=2))
        return 0
    data["items"].append(item)
    save(args.ledger, data)
    print(json.dumps({"added": item}, ensure_ascii=False, indent=2))
    return 0


def cmd_resolve(args):
    data = load(args.ledger)
    for it in data["items"]:
        if str(it.get("id")) == str(args.id):
            if args.dry_run:
                print(
                    json.dumps(
                        {"dry_run": True, "would_resolve": dict(it, status="closed", resolution=args.reason)},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            it["status"] = "closed"
            it["resolution"] = args.reason
            save(args.ledger, data)
            print(json.dumps({"resolved": it}, ensure_ascii=False, indent=2))
            return 0
    print(f"Error: id {args.id} が台帳に存在しません", file=sys.stderr)
    return 1


def cmd_check(args):
    data = load(args.ledger)
    open_items = [it for it in data["items"] if it.get("status") == "open"]
    missing_evidence = [
        it for it in open_items if not str(it.get("evidence", "")).strip()
    ]
    payload = {
        "ledger": os.path.abspath(args.ledger),
        "open_count": len(open_items),
        "missing_evidence_count": len(missing_evidence),
        "open_ids": [it.get("id") for it in open_items],
        "complete": len(open_items) == 0,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if missing_evidence:
        print(
            f"Warning: 証拠のない未決済事項が {len(missing_evidence)} 件あります"
            f"（id: {[it.get('id') for it in missing_evidence]}）",
            file=sys.stderr,
        )
    if open_items:
        print(
            f"Error: 未決済事項が {len(open_items)} 件残っています。"
            "清算するか、対象スキルの修正を先に適用してください",
            file=sys.stderr,
        )
        return 1
    return 0


def cmd_report(args):
    data = load(args.ledger)
    lines = []
    lines.append(f"# 未決済台帳レポート: {os.path.abspath(args.ledger)}")
    lines.append("")
    open_items = [it for it in data["items"] if it.get("status") == "open"]
    lines.append(f"未決済: {len(open_items)} 件 / 全件: {len(data['items'])} 件")
    lines.append("")
    if open_items:
        lines.append("## 未決済")
        for it in open_items:
            loc = f"{it.get('file', '')}:{it.get('line', '')}".strip(":")
            lines.append(f"- #{it.get('id')} [{it.get('kind')}] {loc} {it.get('summary')}")
            if it.get("evidence"):
                lines.append(f"  - 証拠: {it['evidence']}")
        lines.append("")
    closed_items = [it for it in data["items"] if it.get("status") == "closed"]
    if closed_items and args.include_closed:
        lines.append("## 決済済み")
        for it in closed_items:
            lines.append(
                f"- #{it.get('id')} [{it.get('kind')}] {it.get('summary')} → {it.get('resolution', '')}"
            )
    print("\n".join(lines))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(
        prog="audit-ledger.py",
        description="監査の未決済台帳を管理する",
        epilog=(
            "終了コード:\n"
            "  0  成功\n"
            "  1  台帳エラー（不正な JSON、未決済の残存、存在しない ID など）\n"
            "  2  使用法エラー\n"
            "\n"
            "使用例:\n"
            "  python3 scripts/audit-ledger.py --ledger ledger.json list\n"
            "  python3 scripts/audit-ledger.py --ledger ledger.json add \\\n"
            "      --file SKILL.md --line 42 --kind terminology \\\n"
            "      --summary \"語彙の揺れ\" --evidence \"SKILL.md:42 「...」\"\n"
            "  python3 scripts/audit-ledger.py --ledger ledger.json resolve --id 1 --reason \"修正済み\"\n"
            "  python3 scripts/audit-ledger.py --ledger ledger.json check"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--ledger", required=True, help="台帳 JSON ファイルのパス")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="台帳を一覧表示する")
    p.add_argument("--status", choices=STATUSES, help="状態による絞り込み")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("add", help="未決済事項を追加する")
    p.add_argument("--file", required=True, help="対象ファイル")
    p.add_argument("--line", type=int, default=0, help="対象行番号")
    p.add_argument("--kind", required=True, choices=KINDS, help="種別")
    p.add_argument("--summary", required=True, help="要約")
    p.add_argument("--evidence", required=True, help="証拠（現行の原文引用と行番号。必須）")
    p.add_argument("--dry-run", action="store_true", help="台帳を書き込まず、書き込み内容のみ表示する")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("resolve", help="事項を決済済みにする")
    p.add_argument("--id", required=True, help="対象の ID")
    p.add_argument("--reason", required=True, help="決済理由")
    p.add_argument("--dry-run", action="store_true", help="台帳を書き込まず、書き込み内容のみ表示する")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("check", help="未決済の残存を確認する")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("report", help="人間向けのレポートを出力する")
    p.add_argument("--include-closed", action="store_true", help="決済済みも表示する")
    p.set_defaults(func=cmd_report)

    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        # --help は正常終了（0）。引数誤りは使用法エラー（2）。
        return 0 if e.code == 0 else 2

    try:
        return args.func(args)
    except json.JSONDecodeError as e:
        print(f"Error: 台帳 JSON を解析できません: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: 台帳を操作できません: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
