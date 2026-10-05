# Agent Skills Specifications & Structural Rules

## 1. ディレクトリ構成原則
Agent Skill は以下の階層構造に従って配置すること。

- `SKILL.md` (必須): スキルのエントリーポイント。YAMLフロントマターと段階的フェーズ手順のみを記載すること。
- `references/` (任意): ドメイン固有の詳細仕様、スタイルガイド、チェックリスト等を格納すること。
- `assets/` (任意): テンプレートファイルや静的アセットを格納すること。
- `scripts/` (任意): 検証用スクリプト等を格納すること。

## 2. YAMLフロントマター規定
`SKILL.md` の冒頭には必ず以下のフォーマットで記述すること。

```yaml
---
name: agent-skill-name
description: スキルの適用条件および発動シナリオを記述すること。
---
```

- `name`: kebab-caseで記述すること。
- `description`: 人間向け解説を排し、「どんな状況で自律適用すべきか」のトリガー条件を直接記述すること。

## 3. 相対パス参照規則
`SKILL.md` から他ファイルを読み込む際は、必ずスキルのルートからの相対パス（例: `references/00-foundation/...`）で参照すること。
