---
name: frontend-design-craft
description: W3C ARIAアクセシビリティ仕様、国際化タイポグラフィ、およびMaterial 3 Expressiveデザインシステムに準拠したUI構築用Agent Skill。技術スタック非依存の段階的開示（Progressive Disclosure）設計。
---

# Frontend Design Craft Skill

ユーザーインターフェース（UI）の構築・改修において、W3C ARIA APGのアクセシブル構造、言語に応じたタイポグラフィ/アクセシビリティ規格、およびMaterial 3 (M3) Expressiveのトークン規約を適用するための実行プロセスを定義する。

## 概要と前提

- **技術スタック非依存**: HTML/CSS、React、Vue、Flutter、Jetpack Compose、Tailwind CSS等、プロジェクトのファイル構成やパッケージ設定（`package.json`, `pubspec.yaml` 等）を分析し、既存の技術スタックを特定した上で適用すること。
- **プロジェクトルールの分離と判定プロトコル**:
  1. リポジトリ直下に `.ui-rules.json` が存在する場合は、その設定を最優先で読み込んで適用すること。
  2. `.ui-rules.json` が存在しない場合は、本スキルのデフォルト規約のみを使用してコードを生成すること。
  3. デザイン構築中、標準規約に含まれないプロジェクト固有のカスタムトークン（ブランドカラー、独自余白ルール等）が決定した場合、リポジトリ直下に標準スキーマ準拠の `.ui-rules.json` を作成または追記保存すること。
  4. コアシステム設定ファイル（`tailwind.config.js`, `package.json`, `tsconfig.json` 等）の改修が必要な場合は直接上書きせず、差分（Diff）を提示して人間に指示・承認を求めること。

## 段階的実行フェーズ（Phase Protocol）

### Phase 0: 構造・アクセシビリティ定義（Foundation, Semantic Skeleton & Content Accessibility）
UI実装を開始する前に、HTML/DOMの骨組みと言語に応じたテキストアクセシビリティルールを確定すること。対象言語が日本語・英語・多言語のいずれであっても、本フェーズの参照ルールをすべて適用すること。

1. **ARIA ランドマークの配置**: `<header>` (banner), `<nav>` (navigation), `<main>` (main), `<aside>` (complementary), `<footer>` (contentinfo) を正しく分離すること。
2. **レスポンシブブレイクポイントの確認**:
   - Compact (< 600dp): 4カラム
   - Medium (600dp - 839dp): 8カラム
   - Expanded (>= 840dp): 12カラム
3. **文章・テキストアクセシビリティの適用**: 言語ごとの最適な行高、1行あたりの文字数制限、平易なエラー指示、および文脈の伝わるボタン命名ルールを適用すること。
4. **参照ドキュメント**: 詳細構造およびテキストルールは以下のファイルを読み込み適用すること。
   - `references/00-foundation/semantic-skeleton.md`
   - `references/00-foundation/responsive-grid.md`
   - `references/00-foundation/content-accessibility.md`

### Phase 1: 静的スタイリング（M3 Static Tokens）
骨組み確定後、M3デザインシステムトークンを適用すること。

1. **Color Rolesの割り当て**: HEX直接指定を禁止し、Primary, On Primary, Primary Container, Surface, On Surface 等の役割ベースでカラーを割り当てること。
2. **Typography Scale**: Display, Headline, Title, Body, Label の5分類・スケールに従うこと。
3. **Shape Scale**: Extra Small (4px) 〜 Full (9999px) の角丸スケールを適用すること。
4. **参照ドキュメント**: 以下のファイルを読み込み適用すること。
   - `references/01-design-system/m3-expressive/color-roles.md`
   - `references/01-design-system/m3-expressive/expressive-shapes.md`
   - `references/01-design-system/m3-expressive/component-specs.md`

### Phase 2: 動的表現（M3 Expressive Motion）
静的スタイリング完了後、アニメーションと状態変化を定義すること。

1. **イージング・スプリング適用**: Emphasized Easing, Spring Physics を状態遷移・モーフィングに適用すること。
2. **参照ドキュメント**: `references/01-design-system/m3-expressive/expressive-motion.md` を読み込み適用すること。

### Phase 3: 検証とフィードバック（Verification Protocol）

1. **Layer 1 (静的コード検証)**:
   - スクリプト実行環境が存在する場合、`scripts/verify-ui.js` を実行し、WCAG 2.2基準（対比比率 4.5:1以上、タップターゲットサイズ 48x48dp以上）の検証結果を取得すること。
   - 規約違反が検出された場合、違反箇所に対応するコード改修案を生成し、該当ファイルを上書き更新すること。
2. **Layer 2 (描画視覚検証)**:
   - 実行環境に画面撮影および視覚認識（VLM）対応ツールが存在する場合、ローカル画面キャプチャを取得し、「要素の重なり（Overflow）」「グリッドアライメントのずれ」「カラーコントラスト違反」の有無を検証すること。
   - 違反が判定された場合、コード改修を行い、再キャプチャ・評価手順を実行すること。
3. **Layer 3 (人間実機確認の要請)**:
   - Layer 1（および利用可能な場合の Layer 2）の検証項目をすべてパスした後、変更点および確認要求項目を整理して人間に実機確認を依頼すること。
