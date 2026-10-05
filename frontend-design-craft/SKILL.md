---
name: frontend-design-craft
description: W3C ARIAアクセシビリティ仕様、デジタル庁デザインシステム/アクセシビリティガイドライン、およびMaterial 3 Expressiveデザインシステムに準拠したUI構築用Agent Skill。技術スタック非依存の段階的開示（Progressive Disclosure）設計。
---

# Frontend Design Craft Skill

ユーザーインターフェース（UI）の構築・改修において、W3C ARIA APGのアクセシブル構造、デジタル庁ガイドラインに基づく日本語アクセシビリティ仕様、およびMaterial 3 (M3) Expressiveのトークン規約を適用するための実行プロセスを定義する。

## 概要と前提
- **技術スタック非依存**: プロジェクトのファイル構成やパッケージ設定（`package.json`, `pubspec.yaml` 等）を分析し、既存の技術スタック（HTML/CSS, React, Vue, Flutter, Tailwind CSS等）を特定した上で適用すること。
- **プロジェクト規約の統合と分離**:
  - Phase 0において、プロジェクトルートに存在する既存設定ファイル（`tailwind.config.*`, `.eslintrc*`, `theme.*`, `tokens.json`, `.ui-rules.json` 等）を分析し、カラー定義・余白・命名規約を事前に読み込んで適用すること。
  - リポジトリ直下に `.ui-rules.json` が存在する場合はその設定を最優先で適用すること。存在しない場合、プロジェクト固有のUIカスタムトークンが確定したタイミングで `.ui-rules.json` をスキーマに準拠して新規作成・保存すること。
  - ビルドや基盤に関わる主要設定ファイル（`tailwind.config.js`, `package.json` 等）の変更が必要な場合は、自律的な上書きを行わず、変更差分（Diff）を提示して人間に指示・承認を求めること。

## 段階的実行フェーズ（Phase Protocol）

### Phase 0: 構造定義とアクセシビリティ基礎（Foundation & Semantic Skeleton）
UI実装を開始する前に、HTML/DOMの骨組みおよび日本語アクセシビリティ規約を確定すること。
1. **ARIA ランドマークの配置**: `<header>` (banner), `<nav>` (navigation), `<main>` (main), `<aside>` (complementary), `<footer>` (contentinfo) を正しく分離して配置すること。
2. **レスポンシブブレイクポイントの確認**:
   - Compact (< 600dp): 4カラム
   - Medium (600dp - 839dp): 8カラム
   - Expanded (>= 840dp): 12カラム
3. **日本語アクセシビリティ・フォーム仕様の適用**:
   - 行高 `1.5`〜`1.75`、1行あたり 35〜45文字 の可読性制限を適用すること。
   - フォームエラー時は指示対象を明記し、平易な改善方法を添えること。
   - 単体で目的が不明なリンク・ボタンテキスト（「こちら」「詳細」等）を禁止すること。
4. **参照ドキュメント**: 詳細構造および日本語ガイドラインルールは `references/00-foundation/semantic-skeleton.md`, `responsive-grid.md`, `japanese-accessibility.md` を読み込んで適用すること。

### Phase 1: 静的スタイリング（M3 Static Tokens）
骨組み確定後、M3デザインシステムトークンを適用すること。
1. **Color Rolesの割り当て**: HEX直接指定を禁止し、Primary, On Primary, Primary Container, Surface, On Surface 等の役割ベースでカラーを割り当てること。
2. **Typography Scale**: Display, Headline, Title, Body, Label の5分類・スケールに従うこと。
3. **Shape Scale**: Extra Small (4px) 〜 Full (9999px) の角丸スケールを適用すること。
4. **デザインシステムの選択・拡張性**: 指定がない場合は `m3-expressive` を適用すること。将来別のデザインシステムが指定された場合は `references/01-design-system/` 配下の該当ディレクトリを参照すること。
5. **参照ドキュメント**: `references/01-design-system/m3-expressive/color-roles.md`, `expressive-shapes.md`, `component-specs.md` を読み込んで適用すること。

### Phase 2: 動的表現（M3 Expressive Motion）
静的スタイリング完了後、アニメーションと状態変化を定義すること。
1. **イージング・スプリング適用**: Emphasized Easing, Spring Physics を状態遷移・モーフィングに適用すること。
2. **参照ドキュメント**: `references/01-design-system/m3-expressive/expressive-motion.md` を読み込んで適用すること。

### Phase 3: 検証とフィードバック（Verification Protocol）
1. **Layer 1 (静的コード検証)**:
   - スクリプト実行環境が存在する場合、`scripts/verify-ui.js` を実行し、WCAG 2.2基準（対比比率 4.5:1以上、タップターゲットサイズ 48x48dp以上）の検証結果を取得すること。
   - 規約違反が検出された場合、違反箇所に対応するコード改修案を生成し、該当ファイルを更新すること。
2. **Layer 2 (描画視覚検証)**:
   - 実行環境に画面撮影および視覚認識（VLM）対応ツールが存在する場合、ローカル画面キャプチャを取得し、「要素の重なり（Overflow）」「グリッドアライメントのずれ」「カラーコントラスト違反」の有無を検証すること。
   - 違反が判定された場合、コード改修を行い、再キャプチャ・評価手順を実行すること。
3. **Layer 3 (人間実機確認の要請)**:
   - Layer 1（および利用可能な場合の Layer 2）の検証項目をすべてパスした後、変更点および確認要求項目を整理して人間に実機確認を依頼すること。
