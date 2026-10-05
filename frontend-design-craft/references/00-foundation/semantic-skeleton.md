# Semantic Skeleton & Accessibility Guidelines (W3C ARIA APG)

## 1. 必須 ARIA ランドマーク（Landmark Roles）
すべてのページ構造は、以下の標準ランドマーク要素で構成すること。

- **`header` / `role="banner"`**: ページの主要ヘッダーおよびブランディング。全ページに1つ。
- **`nav` / `role="navigation"`**: 主要ナビゲーションリンク群。複数存在する場合は `aria-label` で明確に区別すること。
- **`main` / `role="main"`**: ページのプライマリコンテンツ領域。全ページに原則1つ。
- **`aside` / `role="complementary"`**: メインコンテンツをサポートするサイドパネル・補助領域。
- **`footer` / `role="contentinfo"`**: 著作権情報、補足リンク、ページフッター。

## 2. インタラクティブ要素とアクセシブルネーム
- **`<button>`**: 視覚的テキストが存在しないアイコンボタンには、必ず `aria-label` 属性を指定すること。
- **フォーム入力**: すべての `<input>`, `<select>`, `<textarea>` は `<label>` 要素と `id` / `for` 結合、または `aria-labelledby` で関連付けること。
- **キーボード操作**: インタラクティブな全要素は `Tab` キーでフォーカス可能であり、`Enter` / `Space` キーで実行可能であること。
