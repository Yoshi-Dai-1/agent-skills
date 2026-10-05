# W3C ARIA APG Semantic Skeleton Guide

## 1. Standard Landmark Regions
すべての画面において、以下のW3C ARIA標準ランドマーク構造を必ず維持すること。

- `<header role="banner">`: アプリケーションヘッダーおよび最上位タイトルの配置。
- `<nav role="navigation">`: メインナビゲーション（Navigation Rail, Drawer, Bottom Navigation）の配置。
- `<main role="main">`: ページの主要コンテンツ領域。1画面につき1つのみ配置。
- `<aside role="complementary">`: 補助パネル、サポーティングペイン、コンテキスト情報の配置。
- `<footer role="contentinfo">`: ページフッター、著作権、補足リンクの配置。

## 2. Interactive Element Semantics
- クリック可能な要素には `<button>` を使用し、`<div onClick>` を禁止すること。
- テキスト入力には `<input>`, `<textarea>` を使用し、明確に対応する `<label>` または `aria-label` を付与すること。
- 画像要素には具体的な説明を含む `alt` 属性を付与し、装飾目的の画像には `alt=""` および `aria-hidden="true"` を設定すること。
