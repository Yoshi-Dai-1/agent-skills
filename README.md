# agent-skills

自作 Agent skills の管理・作成・検証・修正用リポジトリ。

## 目的

- 管理: skills の一元管理・バージョニング
- 作成: 新規 skill の作成
- 検証: 動作確認・レビュー
- 修正: 改善・バグ修正

## 構成（予定）

```text
skills/
  <skill-name>/
    SKILL.md
    scripts/
    references/
    assets/
```

## 運用

- 1 skill = 1 ディレクトリ
- 変更は PR ベース（private でも履歴を残す）
- 検証手順は各 skill の SKILL.md に記載
