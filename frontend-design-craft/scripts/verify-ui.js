/**
 * 静的自動検証スクリプト (Layer 1 Static Verification Script)
 * 実装済みチェック（大文字小文字・引用符種別・引用符なし属性・属性値内> に対応）：
 *  文書級（<html>/<head>/<!doctype> を含む文書のみ）：main（存在・重複）・header・nav・footer、lang、title、h1重複
 *  要素級（全ファイル）：無名ボタン（button・role=button）・無名リンク、alt欠落（img・画像ボタン）、
 *  リテラル色値（Hex・rgb()/hsl()・色名等。トークン定義は除外）、tabindex正値、id重複
 * 範囲外（Phase 3 Layer 2または手動判定）：対比比率実測（WCAG 1.4.3/1.4.11）、
 * ポインタターゲットサイズ実測、label関連付けの正誤、文言の妥当性。
 */
const fs = require('fs');

function stripComments(s) {
  return s.replace(/<!--[\s\S]*?-->|\{\/\*[\s\S]*?\*\/\}/g, '');
}

// 属性値の取得（引用符あり・なし・値なしに対応。data-* 等の接尾辞には一致しない）
function getAttr(tag, name) {
  const valued = tag.match(new RegExp('(?:\\s|^)' + name + '\\s*=\\s*(?:"([^"]*)"|\'([^\']*)\'|([^\\s>]+))', 'i'));
  if (valued) {
    if (valued[1] !== undefined) {
      return valued[1];
    }
    return valued[2] !== undefined ? valued[2] : valued[3];
  }
  if (new RegExp('(?:\\s|^)' + name + '(?=[\\s/>])', 'i').test(tag)) {
    return '';
  }
  return null;
}

// 引用符を考慮したタグ照合用パターン片（/ は含めず自己閉鎖と区別する）
const ATTRS = '((?:"[^"]*"|\'[^\']*\'|[^>"\'/])*)';

function countTags(src, names) {
  const re = new RegExp('<(?:' + names.join('|') + ')(?=[\\s>/])', 'gi');
  return (src.match(re) || []).length;
}

function hasTag(src, names) {
  return countTags(src, names) > 0;
}

function countRoles(src, values) {
  const re = new RegExp('<[a-zA-Z][\\w-]*' + ATTRS + '\\/?>', 'g');
  let m;
  let n = 0;
  while ((m = re.exec(src)) !== null) {
    const v = getAttr(m[0], 'role');
    if (v !== null && values.some((w) => w.toLowerCase() === v.trim().toLowerCase())) {
      n++;
    }
  }
  return n;
}

function hasRole(src, values) {
  return countRoles(src, values) > 0;
}

function verifyAccessibility(htmlContent) {
  const issues = [];
  const src = stripComments(htmlContent);
  const isDocument = /<!doctype|<html[\s>/]|<head[\s>/]/i.test(src);

  // 1. 文書構造チェック（文書ファイルのみ。断片コンポーネントは対象外）
  if (isDocument) {
    if (!hasTag(src, ['main']) && !hasRole(src, ['main'])) {
      issues.push('[Error] <main> または role="main" ランドマークが存在しません。');
    }
    if (countTags(src, ['main']) > 1 || countRoles(src, ['main']) > 1) {
      issues.push('[Warning] main ランドマークが複数存在します。プライマリコンテンツ領域は原則ひとつにすること。');
    }
    if (!hasTag(src, ['header']) && !hasRole(src, ['banner'])) {
      issues.push('[Warning] <header> または role="banner" ランドマークが推奨されます。');
    }
    if (!hasTag(src, ['nav']) && !hasRole(src, ['navigation'])) {
      issues.push('[Warning] <nav> または role="navigation" ランドマークが推奨されます。');
    }
    if (!hasTag(src, ['footer']) && !hasRole(src, ['contentinfo'])) {
      issues.push('[Warning] <footer> または role="contentinfo" ランドマークが推奨されます。');
    }
    const htmlTag = src.match(new RegExp('<html\\b' + ATTRS + '\\/?>', 'i'));
    const lang = htmlTag ? getAttr(htmlTag[0], 'lang') : null;
    if (lang === null || lang.trim() === '') {
      issues.push('[Warning] <html> に有効な lang 属性がありません。');
    }
    const h1Count = countTags(src, ['h1']);
    if (h1Count > 1) {
      issues.push(`[Warning] <h1> が ${h1Count} 件検出されました。ページ主題はひとつにすること。`);
    }
    const titleMatch = src.match(/<title\b[^>]*>([\s\S]*?)<\/title\s*>/i);
    if (!titleMatch || titleMatch[1].replace(/<[^>]*>/g, '').trim() === '') {
      issues.push('[Warning] 内容を特定できる <title> がありません。');
    }
  }

  // 2. ボタンのアクセシブルネームチェック（inner text または aria-label系の有無で判定）
  const btnRe = new RegExp('<button\\b' + ATTRS + '(?:/>|>([\\s\\S]*?)</button\\s*>)', 'gi');
  let m;
  let unnamedButtons = 0;
  while ((m = btnRe.exec(src)) !== null) {
    const attrs = ' ' + (m[1] || '');
    const innerText = (m[2] || '').replace(/<[^>]*>/g, '').replace(/&(nbsp|#160);/gi, '').trim();
    const label = getAttr(attrs, 'aria-label');
    const labelledby = getAttr(attrs, 'aria-labelledby');
    const named = (label !== null && label.trim() !== '') || (labelledby !== null && labelledby.trim() !== '');
    if (!named && innerText === '') {
      unnamedButtons++;
    }
  }
  if (unnamedButtons > 0) {
    issues.push(`[Error] アクセシブルネームのない <button> が ${unnamedButtons} 件検出されました。テキストまたは aria-label を付与してください。`);
  }

  // 2b. role=button および空リンクのアクセシブルネームチェック（button要素以外）
  const widgetRe = new RegExp('<([a-zA-Z][\\w-]*)' + ATTRS + '(?:/>|>([\\s\\S]*?)</\\1\\s*>)', 'gi');
  let w;
  let unnamedWidgets = 0;
  let unnamedLinks = 0;
  while ((w = widgetRe.exec(src)) !== null) {
    const tagName = w[1].toLowerCase();
    if (tagName === 'button' || tagName === 'input') {
      continue;
    }
    const attrs = ' ' + (w[2] || '');
    const role = getAttr(attrs, 'role');
    const innerText = (w[3] || '').replace(/<[^>]*>/g, '').replace(/&(nbsp|#160);/gi, '').trim();
    const label = getAttr(attrs, 'aria-label');
    const labelledby = getAttr(attrs, 'aria-labelledby');
    const named = (label !== null && label.trim() !== '') || (labelledby !== null && labelledby.trim() !== '');
    if (role !== null && role.trim().toLowerCase() === 'button') {
      if (!named && innerText === '') {
        unnamedWidgets++;
      }
      continue;
    }
    if (tagName === 'a' && getAttr(attrs, 'href') !== null) {
      if (!named && innerText === '') {
        unnamedLinks++;
      }
    }
  }
  if (unnamedWidgets > 0) {
    issues.push(`[Error] アクセシブルネームのない role="button" が ${unnamedWidgets} 件検出されました。テキストまたは aria-label を付与してください。`);
  }
  if (unnamedLinks > 0) {
    issues.push(`[Error] アクセシブルネームのないリンクが ${unnamedLinks} 件検出されました。テキストまたは aria-label を付与してください。`);
  }

  // 2c. tabindex正値およびid重複チェック
  const positiveTabindex = (src.match(/tabindex\s*=\s*["']?\+?[1-9][0-9]*/gi) || []).length;
  if (positiveTabindex > 0) {
    issues.push(`[Warning] tabindex正値が ${positiveTabindex} 件検出されました。フォーカス順序の混乱を避けるため0または-1にすること。`);
  }
  const idCounts = {};
  const idRe = /(?:\s|^)id\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/gi;
  let im2;
  while ((im2 = idRe.exec(src)) !== null) {
    const v = im2[1] !== undefined ? im2[1] : (im2[2] !== undefined ? im2[2] : im2[3]);
    idCounts[v] = (idCounts[v] || 0) + 1;
  }
  const dupIds = Object.keys(idCounts).filter((k) => idCounts[k] > 1);
  if (dupIds.length > 0) {
    issues.push(`[Warning] 重複idが ${dupIds.length} 件検出されました（${dupIds.slice(0, 5).join(', ')}）。label関連付けが破綻するため一意にすること。`);
  }

  // 3. 画像の alt チェック（値なしaltは装飾扱いで通過、空白のみは違反）
  const imgRe = new RegExp('<img\\b' + ATTRS + '\\/?>', 'gi');
  let noAlt = 0;
  let im;
  while ((im = imgRe.exec(src)) !== null) {
    const alt = getAttr(im[0], 'alt');
    if (alt === null || (alt !== '' && alt.trim() === '')) {
      noAlt++;
    }
  }
  const inputRe = new RegExp('<input\\b' + ATTRS + '\\/?>', 'gi');
  let noAltInputs = 0;
  let ii;
  while ((ii = inputRe.exec(src)) !== null) {
    const type = getAttr(ii[0], 'type');
    if (type === null || type.trim().toLowerCase() !== 'image') {
      continue;
    }
    const alt = getAttr(ii[0], 'alt');
    if (alt === null || (alt !== '' && alt.trim() === '')) {
      noAltInputs++;
    }
  }
  if (noAlt > 0) {
    issues.push(`[Error] alt 属性のない <img> が ${noAlt} 件検出されました。内容画像には目的の通る alt を、装飾画像には alt="" を付与してください。`);
  }
  if (noAltInputs > 0) {
    issues.push(`[Error] alt 属性のない画像ボタン（input[type=image]）が ${noAltInputs} 件検出されました。alt を付与してください。`);
  }

  // 4. リテラル色値の直書きチェック（トークン参照が正本。トークン定義自体は除外）
  const colorSrc = src.replace(/--[^\s"'=:;,{}()]+\s*['"]?\s*:[^;,}]+/g, '');
  const scanSrc = colorSrc.replace(/url\([^)]*\)/gi, '');
  const hexColors = scanSrc.match(/#[0-9a-fA-F]{3,8}\b/g) || [];
  const funcColors = scanSrc.match(/\b(?:rgb|rgba|hsl|hsla)\s*\(/gi) || [];
  const propRe = /(?:^|[;{"'])\s*(?:background|border|outline|text-decoration|column-rule|fill|stroke|box-shadow|text-shadow|[a-z-]*color)\s*:\s*(?:"([^"]*)"|'([^']*)'|([^;}{"']+))/gi;
  const nonColorToken = /^(?:\d*\.?\d+(?:px|em|rem|%|pt|pc|in|cm|mm|ex|ch|vw|vh|vmin|vmax|fr|s|ms|deg)?|solid|dashed|dotted|double|groove|ridge|inset|outset|hidden|thin|medium|thick|var\(.*|\)|calc\(.*)$/i;
  const splitTopLevel = (s) => {
    const out = [];
    let depth = 0;
    let cur = '';
    for (const ch of s) {
      if (ch === '(') {
        depth++;
      } else if (ch === ')') {
        depth = Math.max(0, depth - 1);
      }
      if (ch === ',' && depth === 0) {
        out.push(cur);
        cur = '';
      } else {
        cur += ch;
      }
    }
    out.push(cur);
    return out;
  };
  const normalizeValue = (raw) => {
    let v = raw.trim();
    if (/^["']/.test(v) && /["']$/.test(v)) {
      v = v.slice(1, -1).trim();
    } else {
      v = v.split(/["'<>]/)[0].trim();
    }
    return v.replace(/^[a-z-]+\s*:\s*/i, '');
  };
  const isTokenRef = (v) => /var\(|inherit|initial|unset|currentcolor|transparent|none|url\(|^auto$/i.test(v);
  let namedColors = 0;
  let pm;
  while ((pm = propRe.exec(colorSrc)) !== null) {
    const raw = pm[1] !== undefined ? pm[1] : (pm[2] !== undefined ? pm[2] : pm[3]);
    const chunks = splitTopLevel(raw || '');
    for (const chunk of chunks) {
      let v = normalizeValue(chunk).replace(/url\([^)]*\)/gi, '').trim();
      if (v === '' || isTokenRef(v)) {
        continue;
      }
      if (/#|rgba?\(|hsla?\(/i.test(v)) {
        continue;
      }
      const tokens = v.split(/[\s/]+/).filter((t) => t !== '');
      if (tokens.length > 0 && tokens.every((t) => nonColorToken.test(t))) {
        continue;
      }
      namedColors++;
    }
  }
  const attrRe = /(?:^|[\s"'`])(?:fill|stroke|stop-color|flood-color|lighting-color|color)\s*=\s*["']([^"']+)["']/gi;
  let am;
  while ((am = attrRe.exec(colorSrc)) !== null) {
    const v = am[1].trim();
    if (v === '' || isTokenRef(v)) {
      continue;
    }
    if (/#|rgba?\(|hsla?\(/i.test(v)) {
      continue;
    }
    namedColors++;
  }
  const colorTotal = hexColors.length + funcColors.length + namedColors;
  if (colorTotal > 0) {
    issues.push(`[Warning] リテラル色値の直書きが ${colorTotal} 件検出されました（Hex ${hexColors.length}／関数 ${funcColors.length}／色名等 ${namedColors}）。適用中のデザインシステムのカラーロール変数を使用してください。`);
  }

  return issues;
}

// CLI実行ロジック
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) {
    console.log('Usage: node scripts/verify-ui.js [対象ファイル] [--help]');
    console.log('対象マークアップファイル（HTML／JSX／TSX／Vue等）を検証する。検査項目：文書構造（main・header・nav・footer・lang・title・h1）、無名ボタン・無名リンク・無名role=button、alt欠落（img・画像ボタン）、リテラル色値、tabindex正値、id重複。');
    console.log('終了コード: 0=パスまたは警告のみ、1=[Error]検出、2=対象ファイルなし。');
    console.log('例: node scripts/verify-ui.js index.html');
    process.exit(0);
  }
  const targetFile = args.find((a) => !a.startsWith('-')) || 'index.html';
  if (fs.existsSync(targetFile)) {
    const content = fs.readFileSync(targetFile, 'utf8');
    const results = verifyAccessibility(content);
    console.log(`--- UI Verification Results for ${targetFile} ---`);
    if (results.length === 0) {
      console.log('✅ 検証パス: 違反項目は検出されませんでした。');
    } else {
      results.forEach((msg) => console.log(msg));
    }
    process.exitCode = results.some((msg) => msg.startsWith('[Error]')) ? 1 : 0;
  } else {
    console.log(`対象ファイル '${targetFile}' が見つかりませんでした。パスを確認し、対象リポジトリ内のマークアップファイルを指定してください。`);
    process.exitCode = 2;
  }
}

module.exports = { verifyAccessibility };
