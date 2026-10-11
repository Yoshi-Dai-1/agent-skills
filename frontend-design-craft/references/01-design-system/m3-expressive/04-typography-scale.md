# Material 3 Typography Scale Specifications

## 0. 適用範囲と分担
- 本ファイルは M3 type scale の割当て正本とする。和文の行高・1行文字数・最小文字サイズは `00-foundation/content-accessibility.md` が優先し、ここで上書きしないこと。
- 色との組合せは `01-color-system.md` のペア規則、Button ラベルの文面規則は `00-foundation/content-accessibility.md` §3 に従うこと。

## 1. スケール構成（30 styles）
- 5 roles × 3 sizes：`Display Large / Medium / Small`、`Headline Large / Medium / Small`、`Title Large / Medium / Small`、`Body Large / Medium / Small`、`Label Large / Medium / Small`。
- 各 style に baseline と emphasized の2 variants があり、計 15 baseline + 15 emphasized = 30 styles。両者を併用して使うこと。
- Emphasized は baseline より高 weight＋微調整を加えたもので、selection・actions・headlines・editorial treatments 等の強調箇所専用である。本文全面に使わないこと。

## 2. Typeface と variable fonts
- 既定は Roboto（brand・plain とも）。brand typeface は Display / Headline 等の大型・表現用、plain typeface は Body / Label 等の小型・可読性用に使い分けること。
- 表現が必要な場合は Roboto Flex 等の variable font を使うこと。調整軸：weight / width / grade / slant / optical size（Roboto Flex の拡張軸：XOPQ / YOPQ / XTRA / YTUC / YTLC / YTAS / YTDE / YTFI）。
- Fallback 順序：variable font → Roboto → Noto Sans（日本語含む）。日本語で代替が崩れないことを確認すること。
- トークンは `md.sys.typescale.*` で参照し、size を恣意的に変えないこと（style の増減は§3に従う）。調整は line-height・tracking 中心とし、emphasized 系は相互に視覚的一貫性（例：いずれも幅広）を保つこと。

## 3. 運用規則
- 階層は size・weight・色・間隔で作り、emphasized・大型・装飾を同時多用しないこと（usability の hero moments は画面の要所に限定）。
- Major Second scale（key base 14、body 中心）に準拠し、デバイス別に style の増減が必要な場合のみ type scale を変更すること。Button ラベルの文面・同色規則は `06-component-specs.md` §1 に従うこと。
