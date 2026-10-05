# Material 3 Expressive Motion Physics Specifications

## 1. イージング曲線 (Easing)
- **Emphasized Easing (標準強調)**: `cubic-bezier(0.2, 0.0, 0.0, 1.0)` - 画面上の主要な動き。
- **Emphasized Decelerate**: `cubic-bezier(0.05, 0.7, 0.1, 1.0)` - 要素の画面内参入。
- **Emphasized Accelerate**: `cubic-bezier(0.3, 0.0, 0.8, 0.15)` - 要素の画面外退場。

## 2. スプリング物理 (Spring Physics)
- M3 Expressiveにおけるフィードバックアニメーションには、Stiffness（剛性）と Damping（減衰比）で定義されるスプリングモーションを優先適用すること。
- トランジション時間: 標準アニメーションは 200ms 〜 500ms の範囲内に設定すること。
