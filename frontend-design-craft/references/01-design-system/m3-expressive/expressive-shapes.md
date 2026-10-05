# Material 3 Expressive Shape Scale & Morphing

## 1. Shape Scale Values
- `None`: 0px
- `Extra Small`: 4px
- `Small`: 8px
- `Medium`: 12px
- `Large`: 16px
- `Extra Large`: 28px
- `Full`: 9999px (Pill Shape)

## 2. Component Shape Mapping
- **Buttons / Chips:** Full (9999px) または Extra Small (4px) / Small (8px)
- **Cards (Default):** Medium (12px) / Large (16px)
- **Dialogs / Sheets:** Extra Large (28px)
- **Floating Action Button (FAB):** Large (16px) または Full (9999px)

## 3. Shape Morphing Protocol
ホバー、アクティブ、選択状態における形状遷移（例: 角丸 16px ➔ 28px への変化）を行う際、連続的なアスペクト比を維持して変形させること。
