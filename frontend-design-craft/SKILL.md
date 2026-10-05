---
name: frontend-design-craft
description: W3C ARIAアクセシビリティ仕様およびMaterial 3 Expressiveデザインシステムに準拠したUI構築用Agent Skill。技術スタック非依存の段階的開示（Progressive Disclosure）設計。
---

# Frontend Design Craft Skill

ユーザーインターフェース（UI）の構築・改修において、W3C ARIA APGのアクセシブル構造とMaterial 3 (M3) Expressiveのトークン規約を適用するための実行プロセスを定義する。

## 概要と前提
- **技術スタック非依存**: HTML/CSS、React、Vue、Flutter、Jetpack Compose、Tailwind CSS等、プロジェクトの既存技術スタックを自動認識して適用すること。
- **プロジェクトルールの分離**: スキル自体は汎用規約のみを保持する。プロジェクト固有の設定が必要な場合は、リポジトリ直下の `.ui-rules.json` を参照・適用すること。

## 段階的実行フェーズ（Phase Protocol）

### Phase 0: 構造定義（Foundation & Semantic Skeleton）
UI実装を開始する前に、まずHTML/DOMの骨組みを決定する。
1. **ARIA ランドマークの配置**: `<header>` (banner), `<nav>` (navigation), `<main>` (main), `<aside>` (complementary), `<footer>` (contentinfo) を正しく分離すること。
2. **レスポンシブブレイクポイントの確認**:
   - Compact (< 600dp): 4カラム
   - Medium (600dp - 839dp): 8カラム
   - Expanded (>= 840dp): 12カラム
3. **参照ドキュメント**: 詳細構造ルールは `references/00-foundation/semantic-skeleton.md` および `responsive-grid.md` を読み込み適用せよ。

### Phase 1: 静的スタイリング（M3 Static Tokens）
骨組み確定後、M3デザインシステムトークンを適用する。
1. **Color Rolesの割り当て**: HEX直接指定を禁止し、Primary, On Primary, Primary Container, Surface, On Surface 等の役割ベースでカラーを割り当てること。
2. **Typography Scale**: Display, Headline, Title, Body, Label の5分類・スケールに従うこと。
3. **Shape Scale**: Extra Small (4px) 〜 Full (9999px) の角丸スケールを適用すること。
4. **参照ドキュメント**: `references/01-design-system/m3-expressive/color-roles.md`, `expressive-shapes.md`, `component-specs.md` を読み込み適用せよ。

### Phase 2: 動的表現（M3 Expressive Motion）
静的スタイリング完了後、アニメーションと状態変化を定義する。
1. **イージング・スプリング適用**: Emphasized Easing, Spring Physics を状態遷移・モーフィングに適用すること。
2. **参照ドキュメント**: `references/01-design-system/m3-expressive/expressive-motion.md` を読み込み適用せよ。

### Phase 3: 検証とフィードバック（Verification Protocol）
1. **Layer 1 (静的コード検証)**:
   - スクリプト実行環境が存在する場合、`scripts/verify-ui.js` を実行し、WCAG 2.2基準（対比比率 4.5:1以上、タップターゲットサイズ 48x48dp以上）の検証結果を取得せよ。
   - 規約違反が検出された場合、違反箇所に対応するコード改修案を生成し、該当ファイルを上書き更新せよ。
2. **Layer 2 (描画視覚検証)**:
   - 実行環境に画面撮影および視覚認識（VLM）対応ツールが存在する場合、ローカル画面キャプチャを取得し、「要素の重なり（Overflow）」「グリッドアライメントのずれ」「カラーコントラスト違反」の有無を検証せよ。
   - 違反が判定された場合、コード改修を行い、再キャプチャ・評価手順を実行せよ。
3. **Layer 3 (人間実機確認の要請)**:
   - Layer 1（および利用可能な場合の Layer 2）の検証項目をすべてパスした後、変更点および確認要求項目を整理して人間に実機確認を依頼せよ。
