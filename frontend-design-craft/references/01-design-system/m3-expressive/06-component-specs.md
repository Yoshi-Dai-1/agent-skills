# Material 3 Component Specifications

## 0. 適用範囲と参照
- 色は `01-color-system.md`、形状は `02-shape-system.md`、動きは `03-motion-system.md`、書体は `04-typography-scale.md`、M3サイズは `05-layout-system.md`、画面幅の原則は `references/00-foundation/responsive-grid.md`、ランドマーク・命名・ターゲット最低線は `references/00-foundation/semantic-skeleton.md` に従うこと。本ファイルでトークンを再定義しないこと。

## 1. Buttons（`https://m3.material.io/components/buttons` 正本）
- Variants：`default` / `toggle(selection)`。Toggle 以外で選択状態を形状変化で表さないこと。
- Colors（5 configurations。階層名ではない）：`elevated` / `filled（既定）` / `tonal` / `outlined` / `text`。旧記述の `Outlined (Tertiary)` は誤りであり使わないこと。icons と labels は同色にし、dynamic color 対応を崩さないこと。Neutral text button は非推奨。
- Sizes：`XS / S（既定・M3 baseline）/ M / L / XL` の5サイズ。`XS / M / L / XL` は Expressive 追加、`S` は従来の既定サイズである。
- Shapes：`round（既定・Full）` / `square`。各サイズの実測値は `02-shape-system.md` §3 を正本とし、ここで再定義しないこと。
- Small padding は `16dp` を推奨、`24dp` は非推奨。leading / trailing icon は標準 20dp。既定高さ 40dp（M2 の 36dp ではない）。ラベルは sentence case・簡潔文言。
- 駆動は `03-motion-system.md` の fast spatial（小要素）/ fast effects（色変化）を使うこと。

## 2. FAB（`https://m3.material.io/components/floating-action-button` 正本）
- Variants（size 基準。色基準ではない）：`FAB` / `Medium FAB` / `Large FAB`。`Small FAB` は非推奨で使わないこと。`Medium` が大半の場面の推奨、無印 `FAB` が最小、`Large` は Expanded 以上の明確な主行動用である。
- サイズの目安（baseline 値であり単独指定は禁止）：無印 FAB 56dp / Small 40dp（非推奨）/ Large 96dp。Medium は Expressive 追加。breakpoint に応じてスケールさせ、surface と十分なコントラストを確保すること。
- 配置：Compact・Medium では既定で右下（到達容易・内容被覆回避）。Expanded では左上・navigation rail 内も検討し、最初に目に入る主行動として扱うこと。navigation bar の上方または内部に配置でき、badge 等で被覆しないこと。container は square 系とし、hover で elevation を 1 level 上げる（例：level 3→4）。
- Extended FAB：`Small / Medium / Large` を使うこと。サイズは Small 56dp / Medium 80dp / Large 96dp。baseline extended FAB は非推奨であり、代替は small extended（type が label large→title medium、inner padding 縮小）である。参考 baseline 実測：高さ 56dp・最小幅 80dp・角丸 16dp・icon 24dp・padding 16dp・margin 16dp。
- Surface FAB 色は残存するが非推奨。branded 色（primary / secondary / tertiary 系）を使うこと。

## 3. Navigation（`https://m3.material.io/components/navigation-bar` 正本。`references/00-foundation/responsive-grid.md` の原則と `05-layout-system.md` の幅区分を併用）
- `Flexible navigation bar` を使うこと。baseline navigation bar は非推奨である。flexible は短尺化され、Medium window で水平アイテムに対応する。
- Compact では vertical items、Medium では horizontal items（幅区分の数値は `05-layout-system.md` §1）。3〜5 destinations、同等重要度、画面間で destinations を変えないこと。
- Elevation shadow は付けない。active destination は contrasting color の pill で示すこと。
- `Navigation Rail` は Medium / Expanded 用サイドナビゲーションである。Compact の bottom は bar、side は rail と混同しないこと。

## 4. App bars・Toolbar・Search（`https://m3.material.io/components/app-bars` 正本）
- 名称は `Top App Bar` ではなく `App Bar` を使うこと。4 variants：`Search` / `Small` / `Medium flexible` / `Large flexible` を使うこと。
- baseline の `Medium` / `Large` は非推奨であり、代替は `Medium flexible` / `Large flexible`（短尺化・subtitle・折り返し・画像や filled button の収容、leading/center テキスト）である。`Center-aligned` は独立 variant ではなく small の centered-text configuration として扱うこと。
- 用途：Search は検索が要の home 面の強調 entry-point、`Small` は dense・scrolled 面、`Medium flexible` は大見出し表示（scroll で small へ collapse）、`Large flexible` は見出し強調。scroll 時は body と分離する fill を適用すること。headline は省略せず、flexible では2行折り返し可。
- `Toolbar` は頻用アクションを並べる flexible なコンポーネントであり、FAB と組合わせできる。page actions の表示は app bar ではなく toolbar を使うこと。
- `Search` は search bar＋search view の総称である。contained style（推奨）を使い、bar は focus 時に幅を広げること。入力中の suggested keywords を list 表示できる。

## 5. その他の Expressive 差分（代表以外）
- **Button groups**：`standard`（分離型。選択・押下で隣接ボタンの幅・形状・padding が連動）/ `connected`（連結型。選択ボタンのみ morph、padding 一律 2dp）を使い分けること。旧 segmented button は非推奨であり代替は button groups である。XS〜XL の全ボタンサイズ対応、single / multi / selection-required 対応。group 自体に色はなく button の色 style（filled / tonal / outlined 等）を使うこと。text button・標準 icon button を内部に使わないこと。XS・S group は target 48dp・最小幅 48dp を確保すること。
- **Split button**：共通 button＋menu icon button の構成であり、同一サイズの button と並べて使うこと。menu 側は起動時に spin＋形状変化すること。5サイズ対応。
- **FAB menu**：FAB の選択時に container transform で遷移し、関連アクション群へ展開するメニューである。FAB に関連する action が多数ある場合に使うこと。展開時は menu item 群を stagger 表示し、`ToggleFloatingActionButton` と組み合わせること。FAB §2 の配置・コントラスト規則に従うこと。
- **Progress indicators**：`linear` / `circular` の2 variants であり、一連の process 内では同一 configuration に統一すること。active track への wave 付与と track height 可変化は表現が必要な場合のみ使うこと。

## 6. Elevation と State layers（色の使い方の正本は `01-color-system.md`）
- 全 surface・component は既定 resting elevation を持ち、既定値を恣意に変えないこと。elevation の表現は tonal surface colors が主であり、shadow は背景保護・interaction 促進が必要な場合に足すものである（M2 の常時 shadow ではない）。
- hover 等ではすべての同種要素で一貫して 1 level 上げること（例：全 Material buttons）。
- State layer は content 色（通常 on color）の overlay で、hover 8% / focus 10% / press 10% / drag 16% の固定 opacity を使うこと。一度に1 layer のみ。例：`Secondary Container`＋`On Secondary Container` の enabled には `On Secondary Container` 色の layer を載せる。

## 7. タップターゲット（M3上乗せ分のみ。最低線は `references/00-foundation/semantic-skeleton.md` §4）
- WCAG最低線（24×24 CSS px）・AAA目安（44×44）・例外規定は `references/00-foundation/semantic-skeleton.md` §4 に従うこと。WCAG と M3 の帰属を一括りにしないこと。
- Material Design 3 の要求：**48×48dp** 以上（`1dp ≈ 1px @160dpi`、Web では CSS px 換算。`48px 固定` と短絡しないこと）。XS・S icon buttons も target 48×48dp 以上を必須とすること。
- Inline テキスト内リンクは一律 48 対象にしないこと（例外は `references/00-foundation/semantic-skeleton.md` §4）。
