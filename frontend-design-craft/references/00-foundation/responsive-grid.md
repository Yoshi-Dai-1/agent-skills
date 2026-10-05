# Responsive Grid & Breakpoint Specifications

## 1. M3 レスポンシブブレイクポイント
- **Compact (Window width < 600dp)**:
  - ターゲット: モバイル端末（縦持ち）
  - カラム数: **4**
  - マージン: **16dp**
  - ガター (Gutter): **16dp**
- **Medium (Window width 600dp - 839dp)**:
  - ターゲット: タブレット（縦持ち）、折りたたみ端末
  - カラム数: **8**
  - マージン: **24dp**
  - ガター (Gutter): **24dp**
- **Expanded (Window width >= 840dp)**:
  - ターゲット: デスクトップ、タブレット（横持ち）
  - カラム数: **12**
  - マージン: **24dp** または **auto**
  - ガター (Gutter): **24dp**

## 2. レイアウトパターン (Canonical Layouts)
- **Supporting Pane**: メイン領域とサイド補助領域の2カラム構成。
- **List-Detail**: 一覧と詳細の2分割表示。
- **Feed**: カード型カードがグリッド状に並ぶフィード表示。
