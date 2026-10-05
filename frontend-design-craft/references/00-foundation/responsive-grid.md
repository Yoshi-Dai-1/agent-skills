# Responsive Layout Grid Guidelines (Material 3 Foundations)

## 1. ブレイクポイントと画面スケール
画面幅（Width）に応じた3つの標準スケールを定義する。

- **Compact (< 600dp / px)**:
  - カラム数: 4
  - マージン: 16dp
  - ガター (Gutter): 16dp
  - 対象: スマートフォン縦画面

- **Medium (600dp - 839dp)**:
  - カラム数: 8
  - マージン: 24dp
  - ガター: 24dp
  - 対象: タブレット縦画面、折りたたみデバイス

- **Expanded (>= 840dp)**:
  - カラム数: 12
  - マージン: 24dp 〜 32dp (可変)
  - ガター: 24dp
  - 対象: デスクトップ、大型画面

## 2. カノニカル・レイアウトパターン (Canonical Layouts)
- **List-Detail**: 左側にリスト領域、右側に詳細領域を配置。Compact画面では画面遷移、Expanded画面では2カラム分割。
- **Feed**: カード型コンポーネントをグリッド状に並べる。画面幅に応じて1〜4列にスケール。
- **Supporting Pane**: メイン領域の隣に一時的または常駐型の補助パネルを配置。
