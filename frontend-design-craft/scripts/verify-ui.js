/**
 * 静的自動検証スクリプト (Layer 1 Static Verification Script)
 * WCAG 2.2 アクセシビリティおよび M3 トークン適用を検証する。
 */
const fs = require('fs');

function verifyAccessibility(htmlContent) {
  const issues = [];
  
  // 1. ARIA ランドマークチェック
  if (!htmlContent.includes('<main') && !htmlContent.includes('role="main"')) {
    issues.push('[Error] <main> または role="main" ランドマークが存在しません。');
  }
  if (!htmlContent.includes('<header') && !htmlContent.includes('role="banner"')) {
    issues.push('[Warning] <header> または role="banner" ランドマークが推奨されます。');
  }

  // 2. ボタンのアクセシブルネームチェック
  const emptyButtons = htmlContent.match(/<button[^>]*>\s*<\/button>/g);
  if (emptyButtons) {
    issues.push(`[Error] テキストまたは aria-label のない空の <button> が ${emptyButtons.length} 件検出されました。`);
  }

  // 3. インライン HEX カラー直書きチェック (M3トークン非推奨の検出)
  const hexColors = htmlContent.match(/#[0-9a-fA-F]{3,6}/g);
  if (hexColors) {
    issues.push(`[Warning] カラーコード（Hex値）の直書きが ${hexColors.length} 件検出されました。M3 Color Roles変数を使用してください。`);
  }

  return issues;
}

// CLI実行ロジック
if (require.main === module) {
  const targetFile = process.argv[2] || 'index.html';
  if (fs.existsSync(targetFile)) {
    const content = fs.readFileSync(targetFile, 'utf8');
    const results = verifyAccessibility(content);
    console.log(`--- UI Verification Results for ${targetFile} ---`);
    if (results.length === 0) {
      console.log('✅ 検証パス: 違反項目は検出されませんでした。');
    } else {
      results.forEach(msg => console.log(msg));
    }
  } else {
    console.log(`対象ファイル '${targetFile}' が見つかりませんでした。`);
  }
}

module.exports = { verifyAccessibility };
