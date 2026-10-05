---
name: frontend-design-craft
description: W3C ARIA APG、WCAG 2.2、および Material 3 / Material 3 Expressive ガイドラインに完全に準拠したフロントエンドUIデザイン・コンポーネントを設計・構築・監査・改修するスキル。
---

# Frontend Design Craft

W3C ARIAセマンティクスおよびMaterial 3 (M3) Expressiveデザインシステムに基づき、アクセシブルで美しいフロントエンドUIを段階的に構築・監査すること。

---

## 💡 基本原則（Core Principles）

1. **基礎と装飾の分離（Foundation First）**
   - 見た目（M3 Expressive）の前に、W3C ARIAに準拠した意味的構造（DOM/セマンティクス）およびレスポンシブグリッドを確定させること。
2. **技術スタック非依存（Generic Tech Stack）**
   - プロジェクトのファイル構成やパッケージ設定（package.json, pubspec.yaml等）を分析し、既存の技術スタック（React, Vue, Flutter, Tailwind CSS等）を特定した上で適用すること。「自動」という抽象表現に頼らず、ソースコードの文脈に沿ってトークンを翻訳・適用すること。
3. **プロジェクト固有ルールの優先適用**
   - リポジトリ直下に `.ui-rules.json` が存在する場合は、その設定を最優先で適用すること。存在しない場合は本スキルのデフォルト規約を適用し、プロジェクト固有ルールを永続化する必要が生じた場合のみ `.ui-rules.json` を新規作成・更新すること。

---

## 🛠️ 実行プロセス（Execution Phases）

### Phase 0: 画面骨格・セマンティクス定義
- **参照ファイル:** `references/00-foundation/semantic-skeleton.md`, `references/00-foundation/responsive-grid.md`
- **作業内容:**
  1. `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>` などのW3C ARIA ランドマーク属性を定義すること。
  2. 画面サイズ（Compact / Medium / Expanded）に応じたブレイクポイントとレイアウトグリッド（4 / 8 / 12 カラム）を決定すること。

### Phase 1: M3 Expressive 静的スタイリング
- **参照ファイル:** `references/01-design-system/m3-expressive/color-roles.md`, `references/01-design-system/m3-expressive/expressive-shapes.md`, `references/01-design-system/m3-expressive/component-specs.md`
- **作業内容:**
  1. Hex値の直書きを禁止し、`Primary`, `Surface`, `On Surface` などの M3 Color Roles を割り当てること。
  2. M3 Shape Scale（None, Extra Small 〜 Extra Large）に基づき、コンテナやカードの角丸（Corner Radius）を適用すること。
  3. UI部品（Top App Bar, Card, Button等）の選定・配置基準を遵守すること。

### Phase 2: M3 Expressive 動的表現（Motion）
- **参照ファイル:** `references/01-design-system/m3-expressive/expressive-motion.md`
- **作業内容:**
  1. 静的構造が確立した後に、Spring Physics や Emphasized Easing などのモーショントークンを付加すること。
  2. 状態変化（State Changes）やコンポーネント間の形状変化（Morphing）のアニメーションを定義すること。

### Phase 3: 多層自動検証（Multi-Layer Verification Protocol）
- **作業内容:**
  1. **Layer 1 (静的検証):** スクリプト `scripts/verify-ui.js` またはルール照合を実行し、コントラスト比（AA基準: 4.5:1 / 3:1）および必須ARIA属性の不備を検出すること。規約違反が検出された場合、該当箇所のコード改修案を生成しファイルを上書き更新すること。
  2. **Layer 2 (視覚的検証):** 実行環境内でローカルサーバーの画面撮影・視覚認識が可能なツールが存在する場合、描画結果を取得し「要素の重なり（Overflow）」「グリッド逸脱」の有無を検証すること。欠陥が判定された場合はコード改修案を生成し上書き更新すること。
  3. **Layer 3 (人間実機確認):** Layer 1 および Layer 2（利用可能な場合）の検証を通過した成果物のみを人間に提示し、実機確認を依頼すること。
