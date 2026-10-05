# Material 3 Color Roles Specifications

## 1. Core Color Roles
すべてのカラー指定は以下のロール名で割り当て、Hex値の直接書き込みを排除すること。

- `Primary`: 画面上で最も強調すべきキーアクション（FAB, 主要ボタン）。
- `On Primary`: `Primary` コンテナ上のテキストおよびアイコン（高いコントラスト比確保）。
- `Primary Container`: 視覚的優先度の高いコンテナ領域。
- `On Primary Container`: `Primary Container` 上のテキストおよびアイコン。
- `Secondary` / `On Secondary`: 補助的なコントロールおよびチップ。
- `Surface`: カード、シート、ダイアログ等の背景領域。
- `On Surface`: `Surface` 上の標準テキスト。
- `Outline`: 境界線および分離線（不透明度含む）。

## 2. Contrast Requirements (WCAG 2.2 AA)
- 標準テキスト対背景: 最低 `4.5:1` 以上。
- 大型テキスト（24px以上または18px太字以上）: 最低 `3:1` 以上。
- UIコンポーネント境界・アクティブ状態表示: 最低 `3:1` 以上。
