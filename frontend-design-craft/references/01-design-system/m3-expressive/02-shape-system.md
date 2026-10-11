# Material 3 Shape System Specifications

## 0. 適用範囲
- 本ファイルは角丸スケールと形状変化（morph）の正本とする。アニメーションの駆動方式は `03-motion-system.md`、コンポーネント別の最終サイズは `06-component-specs.md` に従うこと。

## 1. コーナー半径スケール（`md.sys.shape.*`）
- `None`: 0（正方形・全幅コンテナ。`RectangleShape`）
- `Extra Small`: 4dp（TextField、Tooltip）
- `Small`: 8dp（Chip、Buttonの一部）
- `Medium`: 12dp（Card、Dialogの一部）
- `Large`: 16dp（Navigation Drawer、FAB）
- `Extra Large`: 28dp（Large Card、Modal Bottom Sheet）
- M3 Expressive 追加トークン：`Large increased 20dp` / `Extra large increased 32dp` / `Extra extra large 48dp`
- `Full`: pill・Avatar 用の完全円形。旧 `50%` 表記は使わず `Full` に統一すること。

## 2. 形状ライブラリ（35 shapes）
- `cookie4Sided / cookie6Sided / sunny / burst / heart / fan / gem / pill` 等の全35形状は、画像切抜き・Avatar・装飾・Loading Indicator 等の表現用である。コンポーネントの角丸の代わりに無秩序に使わないこと。
- ライブラリ内の全形状は相互にシームレスに morph 可能である。

## 3. Shape morph（形状変化の規則）
- morph は既定で expressive motion scheme で駆動する。linear や easing 単体で morph させないこと（詳細は `03-motion-system.md` の spatial トークン）。
- 用途：pressed / selected 等の interaction states、進行中アクション（typing・loading）、Card 展開・FAB 拡張、環境変化の伝達。装飾のための常時変形は禁止。
- Button の実測値（`https://m3.material.io/components/buttons/specs` 正本）：
  - Round resting: XS / S / M / L / XL = すべて `Full`
  - Square resting: XS 12dp / S 12dp / M 16dp / L 28dp / XL 28dp
  - Pressed（round・square とも同一）：XS 8dp / S 8dp / M 12dp / L 16dp / XL 16dp
  - Toggle は resting で round（未選択）⇔ square（選択）を反転させる。未選択が square なら選択は round。
- 矩形は既定で全角を均等に丸める。非対称が必要な場合のみ個別角を調整すること。
- Round と square を混在させて緊張感・階層を作る場合は意図を明確にし、画面全体で濫用しないこと。
