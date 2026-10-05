# Material 3 Expressive Motion Physics

## 1. Motion Tokens
- `Emphasized Easing`: `cubic-bezier(0.2, 0.0, 0.0, 1.0)` (標準のアニメーション遷移)
- `Emphasized Decelerate`: `cubic-bezier(0.05, 0.7, 0.1, 1.0)` (画面内への要素進入)
- `Emphasized Accelerate`: `cubic-bezier(0.3, 0.0, 0.8, 0.15)` (画面外への要素退場)

## 2. Duration Tokens
- `Short`: 100ms - 200ms (マイクロインタラクション、ホバー状態変化)
- `Medium`: 250ms - 400ms (小〜中規模のコンポーネント状態変更)
- `Long`: 450ms - 600ms (画面全体のレイアウト遷移・ダイアログ展開)
