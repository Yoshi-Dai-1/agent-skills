---
name: frontend-design-craft
description: W3C ARIA APGのセマンティック構造およびMaterial 3 / M3 Expressiveデザインシステムに準拠したWeb・アプリフロントエンドUIの構築・検証を行うガイドライン。
---

# Frontend Design Craft Skill

## 1. 概要
本スキルは、アクセシブルなHTML/DOM構造（W3C ARIA APG準拠）と、表現力の高いデザインシステム（Material 3 / M3 Expressive等）を適用してUIコンポーネントおよび画面レイアウトを構築・検証する標準手順を定義する。

## 2. 実行フェーズプロトコル

### Phase 0: 既存環境・設定の読み込み
1. **プロジェクト設定のスキャン**
   - リポジトリ直下の設定ファイル（`package.json`, `pubspec.yaml`, `tailwind.config.*`, `.eslintrc*`, `theme.*`, `tokens.json`, `.ui-rules.json` 等）を探索・確認すること。
   - 既存のカラー定義、余白スケール、コンポーネント構造、技術スタック（React, Vue, Flutter, Tailwind CSS等）を事前に特定すること。
2. **規約ファイルの優先適用ルール**
   - リポジトリ直下に `.ui-rules.json` が存在する場合は、最優先でそのトークン・例外ルールを適用すること。
   - 存在しない場合は本スキルのデフォルト規定（`references/` 配下）を適用すること。

### Phase 1: 構造定義（Structural Skeleton）
1. **セマンティックDOMの適用**
   - ページ全体およびコンポーネントの構造に W3C ARIA ランドマーク（`header`, `nav`, `main`, `aside`, `footer` 等）およびセマンティックタグを使用すること。
   - `references/00-foundation/semantic-skeleton.md` の仕様に従うこと。
2. **レイアウトグリッドの適用**
   - ブレイクポイント（Compact: <600dp, Medium: 600-839dp, Expanded: 840dp+）に応じたカラム数・マージン・ガターを適用すること。
   - `references/00-foundation/responsive-grid.md` の仕様に従うこと。

### Phase 2: デザインシステム適用（M3 Expressive等）
1. **デザインシステムの動的選択**
   - プロジェクト指定または `.ui-rules.json` に基づき、`references/01-design-system/` 配下の該当ディレクトリ（初期値: `m3-expressive`）から参照ファイルを読み込んで適用すること。
2. **カラーロールとトークンの適用**
   - Hex値の直書きを排除し、Color Roles（`Primary`, `On Primary`, `Surface`, `On Surface` 等）のCSS変数またはフレームワーク対応トークンを使用すること。
   - `references/01-design-system/m3-expressive/color-roles.md` の仕様に従うこと。
3. **形状スケール（Shape Scale）の適用**
   - M3 Corner Radii（`None: 0px`, `Small: 8px`, `Medium: 12px`, `Large: 16px`, `Extra Large: 28px`, `Full: 9999px`）およびMorphingルールを適用すること。
   - `references/01-design-system/m3-expressive/expressive-shapes.md` の仕様に従うこと。
4. **コンポーネント選定**
   - 目的（Navigation, Action, Input, Display）に合致する規格コンポーネントを選定・配置すること。
   - `references/01-design-system/m3-expressive/component-specs.md` の仕様に従うこと。

### Phase 3: 動的表現の付与（Expressive Motion）
1. **モーション物理と状態変化の適用**
   - スプリング物理パラメータおよび Emphasized Easing（`cubic-bezier(0.2, 0.0, 0.0, 1.0)`）を状態変化および画面遷移に適用すること。
   - `references/01-design-system/m3-expressive/expressive-motion.md` の仕様に従うこと。

### Phase 4: 検証およびフィードバックプロトコル

#### Layer 1: 静的コード検証（Static Verification）
1. **静的検証の実行**
   - `scripts/verify-ui.js` または同等の検証基準（WCAG 2.2 AA基準：コントラスト比 4.5:1 以上、タップターゲット 48x48dp 以上、ARIA属性の整合性）を実行すること。
2. **エラー修正手順**
   - 規約違反が検出された場合、違反箇所に対応するコード改修案を出力し、該当ファイルを上書き更新すること。

#### Layer 2: 視覚的評価（Visual Verification）
1. **対応ツールの有無の確認**
   - 実行環境において画面キャプチャ・ブラウザ表示取得機能（Playwright MCP, Playwright CLI, ツール内ブラウザ等）が利用可能か確認すること。
2. **視覚チェックの実行**
   - 利用可能な場合、ローカル描画スクリーショットを取得し、要素の重なり（Overflow）、グリッドからの逸脱、トークン不整合の有無を検証すること。
   - 不整合が検出された場合、修正案を生成して該当コードを更新すること。
   - 視覚ツールが利用不可能な環境の場合、Layer 1 の検証全項目クリアをもって人間への確認依頼ステップへ進むこと。

## 3. プロジェクト固有ルールの保持・書き込みプロトコル

1. **`.ui-rules.json` の作成・更新プロトコル**
   - プロジェクト固有のカスタムトークン（標準M3に含まれないブランド固有のカラーHex値、専用余白規約等）が確定した場合、リポジトリ直下の `.ui-rules.json` に追記・保存すること。
   - ファイルが存在しない場合は以下の標準スキーマに従って `.ui-rules.json` を新規作成すること：
   ```json
   {
     "$schema": "https://json-schema.org/draft/2020-12/schema",
     "version": "1.0",
     "designSystem": "m3-expressive",
     "tokens": {
       "color": {},
       "shape": {},
       "spacing": {}
     },
     "exceptions": []
   }
   ```
   - 既存の `.ui-rules.json` が存在する場合は、定義済みスキーマおよびフォーマットスタイル（インデント等）を厳格に維持した上で差分のみを追記すること。
2. **コアシステム設定ファイルの改修プロトコル**
   - `tailwind.config.js`, `package.json`, `tsconfig.json` 等のビルド・基盤設定ファイルの修正が必要な場合、ファイルを直接変更せず、提案する変更差分（Diff）を人間に提示し、承認を求めること。
