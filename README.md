# agent-skills

自作 Agent skills の管理・作成・検証・修正用リポジトリ。

## 目的

- 管理: skills の一元管理・バージョニング
- 作成: 新規 skill の作成
- 検証: 動作確認・レビュー
- 修正: 改善・バグ修正

## 構成

```text
agent-skill-craft/        # Agent Skill を作成・監査・改修・評価するメタスキル
frontend-design-craft/    # フロントエンド UI の構築・監査・改修
```

各 skill は Agent Skills 公式仕様（https://agentskills.io/specification.md）に準拠する。

## 運用

- 1 skill = 1 ディレクトリ
- 変更は PR ベース（private でも履歴を残す）
- 検証手順は各 skill の SKILL.md に記載

### agent-skill-craft を発動する義務

**Agent Skill の作成・監査・改修・評価を指示された場合は、先に `agent-skill-craft` を発動する。**

本リポジトリの運用では、これを行わなかった結果として、同一の汎用的な不備（自己監査の偽 positives の再掲、実行範囲の過剰表示、適用範囲の勝手なる狭め、語彙の揺れ）が個別の skill ファイルに対して 9 度にわたって繰り返し修正される事態が発生した。**修正すべき対象は skill の個別記述ではなく、規律側（メタスキル）にある。**

手順:

1. `agent-skill-craft` を発動する（`skill` ツール、または SKILL.md の直接読み込み）。
2. Phase 0〜4 に従い、対象 skill の設計・執筆・検証・実行時規律の埋め込みを行う。
3. 検証は下記を実行する。

### 検証コマンド

```bash
# 公式仕様と運用ルールへの適合を検証する
python3 agent-skill-craft/scripts/validate-skill.py agent-skill-craft --format text

# 語彙揺れも検査する
python3 agent-skill-craft/scripts/validate-skill.py agent-skill-craft \
  --vocabulary agent-skill-craft/assets/vocabulary.json --format text

# 公式検証ライブラリ
skills-ref validate ./agent-skill-craft
```

### 監査の台帳

```bash
# 未決済事項の追加（引用と行番号は必須）
python3 agent-skill-craft/scripts/audit-ledger.py --ledger ledger.json add \
  --file SKILL.md --line 42 --kind terminology \
  --summary "語彙の揺れ" --evidence "SKILL.md:42 「原文の引用」"

# 未決済の残存確認（残っていれば終了コード 1）
python3 agent-skill-craft/scripts/audit-ledger.py --ledger ledger.json check
```

台帳ファイルは**対象スキルとは別の作業領域**に置く。既定の置き場所は対象スキルと同階層の `ledger.json` である。

### 公式検証ライブラリのインストール

```bash
git clone https://github.com/agentskills/agentskills.git
cd agentskills/skills-ref && python3 -m venv .venv && source .venv/bin/activate && pip install -e .
```
