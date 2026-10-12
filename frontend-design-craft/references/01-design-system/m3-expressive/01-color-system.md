# Material 3 Color System Specifications

## 0. 適用範囲と優先順位（必読）
- リテラル色値（Hex・rgb()/hsl()・色名等）の直書きを禁止し、`md.sys.color.*` トークン経由でセマンティックロールを参照すること。
- 本ファイルは色ロールの割当てとペア規則を正本とする。比率の数値は `references/00-foundation/content-accessibility.md` §4 に従い、ここで再定義しないこと。行高・文字数・最小文字サイズも同ファイルに従うこと。
- デザインSSoTが存在する場合、SSoT側のトークン定義を本ファイルの `md.sys.color.*` ロールへの割当て源として使い、SSoTにないロールは§1の生成順序に従うこと。
- Elevationの見せ方・State layerの不透明度は `06-component-specs.md` に従い、ここでは色の定義のみ行うこと。

## 1. ダイナミックカラーの生成順序
1. 5 Key Colors（Primary / Secondary / Tertiary / Neutral / Neutral Variant）から tonal palette を生成する。
2. palette の tone をロールに割当てる（例：lightで `primary40 → Primary`、`primary100 → On Primary`）。
3. 同一ロール群で light / dark の両テーマを生成すること。片方のみの生成を禁止する。

## 2. ロール全量（26+ 標準＋Fixed。`Surface Variant` は廃止）
### アクセント
- `Primary` / `On Primary` / `Primary Container` / `On Primary Container`
- `Secondary` / `On Secondary` / `Secondary Container` / `On Secondary Container`
- `Tertiary` / `On Tertiary` / `Tertiary Container` / `On Tertiary Container`
- `Error` / `On Error` / `Error Container` / `On Error Container`

### Fixed（light / dark で値を変えない）
- `Primary Fixed` / `Primary Fixed Dim` / `On Primary Fixed` / `On Primary Fixed Variant`
- `Secondary Fixed` / `Secondary Fixed Dim` / `On Secondary Fixed` / `On Secondary Fixed Variant`
- `Tertiary Fixed` / `Tertiary Fixed Dim` / `On Tertiary Fixed` / `On Tertiary Fixed Variant`
- `On Fixed` 系は対応する Fixed 色上のテキスト・アイコン用である。`Fixed Dim` は同系 Fixed より強い強調 tone であり、light / dark で同一値を保つ必要がある場合に container の代わりに使うこと。

### サーフェス（Tone-based。elevation透かしは使わない）
- `Surface Dim` / `Surface` / `Surface Bright`
- `Surface Container Lowest` / `Surface Container Low` / `Surface Container` / `Surface Container High` / `Surface Container Highest`
- `On Surface` / `On Surface Variant`
- 旧→新対応：`Elevation +1 → Low`、`+2 → Container（カード等の標準）`、`+3 → High`、`+4/+5 → Highestで代替`、`Surface Variant → Surface Container Highestに統合`、`Container Lowest は新設`。
- 2023更新値：lightの `Surface` は tone 99→98、neutral palette の chroma は 4→6、dark の surface 群は全体に暗くする。

### 境界・反転・その他
- `Outline` / `Outline Variant`
- `Inverse Surface` / `Inverse On Surface` / `Inverse Primary`
- `Scrim` / `Shadow`
- 廃止・移行：`Background`→`Surface`、`On Background`→`On Surface`、`Surface Variant`→`Surface Container Highest`。旧名での指定を禁止する。
- `Container` 系はボタン等の fill 専用であり、テキスト・アイコン色に使わないこと。テキスト・アイコンは対応する `On *` を使うこと。
- `Surface` は背景の既定、`Surface Container` は contained 領域の既定。`On Surface` / `On Surface Variant` はすべての surface・container 上のテキスト・アイコンに使うこと。

## 3. 対比とコントラストレベル
- 比率の最低線は `references/00-foundation/content-accessibility.md` §4 に従うこと。
- `On *` は対応する container / surface との accessible な組合せが動的カラーで保証される。`Primary Container` 上は `On Primary Container` を使う等、ペアを崩さないこと（例：`Tertiary Container` 上に `Primary Container` の文字色は不可）。
- User-controlled contrast の Standard / Medium / High を切り替えてもペアを維持できる割当てにすること。
- 色だけに頼らず、エラー等はアイコン＋`aria-invalid`＋`aria-describedby` を併用すること（詳細は `references/00-foundation/content-accessibility.md` §2）。
