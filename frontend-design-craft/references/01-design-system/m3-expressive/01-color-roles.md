# Material 3 Color Roles Specifications

## 1. ダイナミックカラーロール（Color Roles）
カラーコード（Hex値）の直書きを禁止し、以下のセマンティックロールを割り当てる。

### アクセントロール (Accent Roles)
- **`Primary` / `On Primary`**: ページ内で最も重要なアクション・要素（FAB、Primary Buttonなど）。
- **`Primary Container` / `On Primary Container`**: Primaryより主張を抑えた強調領域。
- **`Secondary` / `On Secondary`**: 補助的なアクション・フィルタチップ等。
- **`Secondary Container` / `On Secondary Container`**: 選択状態のアイテム背景など。
- **`Tertiary` / `On Tertiary`**: 代替のアクセント・対比要素。

### サーフェスロール (Surface Roles)
- **`Surface` / `On Surface`**: 背景および標準テキスト。
- **`Surface Variant` / `On Surface Variant`**: カード境界線や二次テキスト。
- **`Outline` / `Outline Variant`**: コンポーネントのボーダー、境界線。

## 2. コントラスト要件 (WCAG 2.2 Level AA)
- 通常テキスト (18pt未満または太字14pt未満): **4.5:1** 以上の対比比率を担保すること。
- 大型テキスト (18pt以上または太字14pt以上) およびUIコンポーネント: **3:1** 以上の対比比率を担保すること。
