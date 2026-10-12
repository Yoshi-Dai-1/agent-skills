/**
 * 静的自動検証スクリプト (Layer 1 Static Verification Script)
 * 実装済みチェック（大文字小文字・引用符種別・引用符なし属性・属性値内> に対応）：
 *  文書級（<html>/<head>/<!doctype> を含む文書のみ）：main（存在・重複）・header・nav・footer、lang、title、h1重複
 *  要素級（全ファイル）：無名ボタン（button・role=button）・無名リンク、alt欠落（img・画像ボタン）、
 *  リテラル色値（Hex・rgb()/hsl()・色名等。トークン定義・color-scheme宣言は除外。drop-shadow()内の色も検出。CSS宣言の走査はstyle要素内・style属性値・StyleSheet.create内に限定。font shorthand内・不正HTML内・JSデータ文字列内のCSS宣言は対象外）、tabindex正値、id重複
 * 範囲外（Phase 3 Layer 2またはLayer 3での確認）：対比比率実測（WCAG 1.4.3/1.4.11）、
 * ポインタターゲットサイズ実測、label関連付けの正誤、文言の妥当性。
 */
const fs = require('fs');

function stripComments(s) {
  return s.replace(/<!--[\s\S]*?-->|\{\/\*[\s\S]*?\*\/\}|\/\*[\s\S]*?\*\/|^[ \t]*\/\/.*$/gm, '');
}

// 属性値の取得（引用符あり・なし・値なしに対応。data-* 等の接尾辞には一致しない）
function getAttr(tag, name) {
  const valued = tag.match(new RegExp('(?:\\s|^)' + name + '\\s*=\\s*(?:"([^"]*)"|\'([^\']*)\'|([^\\s>]+))', 'i'));
  if (valued) {
    if (valued[1] !== undefined) {
      return valued[1];
    }
    if (valued[2] !== undefined) {
      return valued[2];
    }
    return (valued[3] || '').replace(/\/+$/, '');
  }
  if (new RegExp('(?:\\s|^)' + name + '(?=[\\s/>])', 'i').test(tag)) {
    return '';
  }
  return null;
}

// 引用符を考慮したタグ照合用パターン片（自己閉鎖は後続の explicit な \/?> で区別する）
const ATTRS = '((?:"[^"]*"|\'[^\']*\'|[^>"\'])*)';

function countTags(structSrc, names) {
  const re = new RegExp('<(?:' + names.join('|') + ')(?=[\\s>/])', 'gi');
  return (structSrc.match(re) || []).length;
}

function hasTag(structSrc, names) {
  return countTags(structSrc, names) > 0;
}

function countRoles(structSrc, values) {
  const re = new RegExp('<[a-zA-Z][\\w-]*' + ATTRS + '\\/?>', 'g');
  let m;
  let n = 0;
  while ((m = re.exec(structSrc)) !== null) {
    const v = getAttr(m[0], 'role');
    if (v !== null && values.some((w) => w.toLowerCase() === v.trim().toLowerCase())) {
      n++;
    }
  }
  return n;
}

function hasRole(structSrc, values) {
  return countRoles(structSrc, values) > 0;
}

// inner HTMLから accessible name の有無を判定する（aria-hidden配下は除外、img等のaltは名称に算入）
function accessibleInnerText(inner) {
  const visible = inner.replace(/<([a-zA-Z][\w-]*)[^>]*aria-hidden\s*=\s*(?:"true"|'true'|true)[^>]*>[\s\S]*?<\/\1\s*>/gi, '');
  const alts = [];
  const altTagRe = new RegExp('<(?:img|input)\\b' + ATTRS + '\\/?>', 'gi');
  let at;
  while ((at = altTagRe.exec(visible)) !== null) {
    if (/^<input\b/i.test(at[0])) {
      const tp = getAttr(at[0], 'type');
      if ((tp || '').trim().toLowerCase() !== 'image') {
        continue;
      }
    }
    const a = getAttr(at[0], 'alt');
    if (a !== null && a !== '' && a.replace(/&(nbsp|#160);/gi, '').trim() !== '') {
      alts.push(a.trim());
    }
  }
  const text = visible.replace(/<[^>]*>/g, '').replace(/&(nbsp|#160);/gi, '').trim();
  return (text + ' ' + alts.join(' ')).trim();
}

function verifyAccessibility(htmlContent) {
  const issues = [];
  const src = stripComments(htmlContent);
  // 構造検査用：script/style の内容物はタグ計数から除外する（style の CSS 自体は色検査で使う）
  const structSrc = src
    .replace(/<script\b[^>]*>[\s\S]*?(?:<\/script\s*>|$)/gi, '<script></script>')
    .replace(/<style\b[^>]*>[\s\S]*?(?:<\/style\s*>|$)/gi, '<style></style>');
  // <head> は小文字の素子のみ文書とみなす（JSXの Head コンポーネント等との混同を避けるため）
  const isDocument = /<!doctype|<html[\s>/]/i.test(structSrc) || /<head[\s>/]/.test(structSrc);

  // 1. 文書構造チェック（文書ファイルのみ。断片コンポーネントは対象外）
  if (isDocument) {
    if (!hasTag(structSrc, ['main']) && !hasRole(structSrc, ['main'])) {
      issues.push('[Error] <main> または role="main" ランドマークが存在しません。');
    }
    if (countTags(structSrc, ['main']) + countRoles(structSrc, ['main']) > 1) {
      issues.push('[Warning] main ランドマークが複数存在します。プライマリコンテンツ領域は原則ひとつにすること。');
    }
    // 文書級 header/footer は article/aside/main/nav/section 配下を除外して判定する（内包時は banner/contentinfo ではない）
    const topLevelSrc = structSrc.replace(/<(article|aside|main|nav|section)\b[^>]*>[\s\S]*?(?:<\/\1\s*>|$)/gi, '<$1></$1>');
    if (!hasTag(topLevelSrc, ['header']) && !hasRole(topLevelSrc, ['banner'])) {
      issues.push('[Warning] <header> または role="banner" ランドマークが推奨されます。');
    }
    if (!hasTag(structSrc, ['nav']) && !hasRole(structSrc, ['navigation'])) {
      issues.push('[Warning] <nav> または role="navigation" ランドマークが推奨されます。');
    }
    if (!hasTag(topLevelSrc, ['footer']) && !hasRole(topLevelSrc, ['contentinfo'])) {
      issues.push('[Warning] <footer> または role="contentinfo" ランドマークが推奨されます。');
    }
    const htmlTag = structSrc.match(new RegExp('<html\\b' + ATTRS + '\\/?>', 'i'));
    const lang = htmlTag ? getAttr(htmlTag[0], 'lang') : null;
    if (lang === null || lang.trim() === '') {
      issues.push('[Warning] <html> に有効な lang 属性がありません。');
    }
    const h1Count = countTags(structSrc, ['h1']);
    if (h1Count > 1) {
      issues.push(`[Warning] <h1> が ${h1Count} 件検出されました。ページ主題はひとつにすること。`);
    }
    const titleMatch = structSrc.match(/<title\b[^>]*>([\s\S]*?)<\/title\s*>/i);
    if (!titleMatch || titleMatch[1].replace(/<[^>]*>/g, '').trim() === '') {
      issues.push('[Warning] 内容を特定できる <title> がありません。');
    }
  }

  // 2. ボタンのアクセシブルネームチェック（inner text または aria-label系の有無で判定）
  const btnRe = new RegExp('<button\\b' + ATTRS + '(?:/>|>([\\s\\S]*?)</button\\s*>)', 'gi');
  let m;
  let unnamedButtons = 0;
  while ((m = btnRe.exec(structSrc)) !== null) {
    const attrs = ' ' + (m[1] || '');
    const innerText = accessibleInnerText(m[2] || '');
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

  // 2b. role=button および空リンクのアクセシブルネームチェック（button要素以外。外側要素に内包されても検出できるよう内側へ再帰走査）
  let unnamedWidgets = 0;
  let unnamedLinks = 0;
  function scanWidgets(part) {
    const widgetRe = new RegExp('<([a-zA-Z][\\w-]*)' + ATTRS + '(?:/>|>([\\s\\S]*?)</\\1\\s*>)', 'gi');
    let w;
    while ((w = widgetRe.exec(part)) !== null) {
      const tagName = w[1].toLowerCase();
      const inner = w[3] || '';
      if (tagName !== 'button' && tagName !== 'input') {
        const attrs = ' ' + (w[2] || '');
        const role = getAttr(attrs, 'role');
        const innerText = accessibleInnerText(inner);
        const label = getAttr(attrs, 'aria-label');
        const labelledby = getAttr(attrs, 'aria-labelledby');
        const named = (label !== null && label.trim() !== '') || (labelledby !== null && labelledby.trim() !== '');
        if (role !== null && role.trim().toLowerCase() === 'button') {
          if (!named && innerText === '') {
            unnamedWidgets++;
          }
        } else if (tagName === 'a' && getAttr(attrs, 'href') !== null) {
          if (!named && innerText === '') {
            unnamedLinks++;
          }
        }
      }
      if (inner.indexOf('<') !== -1) {
        scanWidgets(inner);
      }
    }
  }
  scanWidgets(structSrc);
  // input 要素（void のため上記走査に掛からない）の role=button を検査
  const inputWidgetRe = new RegExp('<input\\b' + ATTRS + '\\/?>', 'gi');
  let iw;
  while ((iw = inputWidgetRe.exec(structSrc)) !== null) {
    const role = getAttr(iw[0], 'role');
    if (role === null || role.trim().toLowerCase() !== 'button') {
      continue;
    }
    const label = getAttr(iw[0], 'aria-label');
    const labelledby = getAttr(iw[0], 'aria-labelledby');
    if ((label === null || label.trim() === '') && (labelledby === null || labelledby.trim() === '')) {
      unnamedWidgets++;
    }
  }
  if (unnamedWidgets > 0) {
    issues.push(`[Error] アクセシブルネームのない role="button" が ${unnamedWidgets} 件検出されました。テキストまたは aria-label を付与してください。`);
  }
  if (unnamedLinks > 0) {
    issues.push(`[Error] アクセシブルネームのないリンクが ${unnamedLinks} 件検出されました。テキストまたは aria-label を付与してください。`);
  }

  // 2c. tabindex正値チェック（引用符・中括弧・前後空白・+/-・前ゼロを許容し、数値が1以上の場合のみ警告。0/-1は対象外）
  const tabindexRe = /(?:^|[\s"'`])tabindex\s*=\s*(?:"([^"]*)"|'([^']*)'|\{([^}]*)\}|([^\s>]+))/gi;
  let tm;
  let positiveTabindex = 0;
  while ((tm = tabindexRe.exec(structSrc)) !== null) {
    const rawV = tm[1] !== undefined ? tm[1] : (tm[2] !== undefined ? tm[2] : (tm[3] !== undefined ? tm[3] : tm[4]));
    const v = (rawV || '').replace(/\/+$/, '').trim();
    if (/^\+?0*[1-9][0-9]*$/.test(v)) {
      positiveTabindex++;
    }
  }
  if (positiveTabindex > 0) {
    issues.push(`[Warning] tabindex正値が ${positiveTabindex} 件検出されました。フォーカス順序の混乱を避けるため0または-1にすること。`);
  }
  const idCounts = {};
  const idRe = /(?:\s|^)id\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/gi;
  let im2;
  while ((im2 = idRe.exec(structSrc)) !== null) {
    const rawId = im2[1] !== undefined ? im2[1] : (im2[2] !== undefined ? im2[2] : im2[3]);
    const v = (rawId || '').replace(/\/+$/, '');
    if (v === '') {
      continue;
    }
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
  while ((im = imgRe.exec(structSrc)) !== null) {
    const alt = getAttr(im[0], 'alt');
    if (alt === null || (alt !== '' && alt.replace(/&(nbsp|#160);/gi, '').trim() === '')) {
      noAlt++;
    }
  }
  const inputRe = new RegExp('<input\\b' + ATTRS + '\\/?>', 'gi');
  let noAltInputs = 0;
  let ii;
  while ((ii = inputRe.exec(structSrc)) !== null) {
    const type = getAttr(ii[0], 'type');
    if (type === null || type.trim().toLowerCase() !== 'image') {
      continue;
    }
    const alt = getAttr(ii[0], 'alt');
    if (alt === null || (alt !== '' && alt.replace(/&(nbsp|#160);/gi, '').trim() === '')) {
      noAltInputs++;
    }
  }
  if (noAlt > 0) {
    issues.push(`[Error] alt 属性のない <img> が ${noAlt} 件検出されました。内容画像には目的が伝わる alt を、装飾画像には alt="" を付与してください。`);
  }
  if (noAltInputs > 0) {
    issues.push(`[Error] alt 属性のない画像ボタン（input[type=image]）が ${noAltInputs} 件検出されました。alt を付与してください。`);
  }

  // 4. リテラル色値の直書きチェック（トークン参照が正本。トークン定義自体は除外）
  // 色走査は script 内容を除外する（構造走査の structSrc と同じ分離。style の CSS 自体は使う）
  const colorSrcBase = src.replace(/<script\b[^>]*>[\s\S]*?(?:<\/script\s*>|$)/gi, '<script></script>');
  const colorSrc = colorSrcBase.replace(/--[^\s"'=:;,{}()]+\s*['"]?\s*:[^;}]+/g, '');
  // 色宣言の走査対象は style 要素内と style 属性値に限定する（TSの型注釈・オブジェクトリテラルとの混同を避けるため。JSデータ文字列内のCSS宣言は対象外）
  const styleBlocks = [...src.matchAll(/<style\b[^>]*>([\s\S]*?)(?:<\/style\s*>|$)/gi)].map((m) => m[1]);
  // React Native の StyleSheet.create({...}) 内はCSS宣言として走査する（中括弧対応で抽出。型注釈とは文脈が異なるため混同しない）
  const styleSheetBlocks = [];
  const createRe = /(?:^|[^\w$])StyleSheet\s*\.\s*create\s*\(/g;
  let cm;
  while ((cm = createRe.exec(src)) !== null) {
    let j = cm.index + cm[0].length;
    while (j < src.length && /\s/.test(src[j])) {
      j++;
    }
    if (src[j] !== '{') {
      continue;
    }
    let depth = 0;
    const start = j;
    while (j < src.length) {
      if (src[j] === '{') {
        depth++;
      } else if (src[j] === '}') {
        depth--;
        if (depth === 0) {
          break;
        }
      }
      j++;
    }
    styleSheetBlocks.push(src.slice(start + 1, j));
  }
  const styleAttrVals = [];
  // style={{...}} 内はJS式のため、内包する引用符リテラルのみ別途評価する（識別子・三項式の残骸は対象外）
  const braceQuotedVals = [];
  for (const m of src.matchAll(/(?:^|[\s"'`{])style\s*=\s*(?:"([^"]*)"|'([^']*)'|\{\{([\s\S]*?)\}\})/gi)) {
    if (m[3] !== undefined) {
      const qs = m[3].match(/"([^"]*)"|'([^']*)'/g) || [];
      for (const q of qs) {
        braceQuotedVals.push(q.slice(1, -1));
      }
    } else {
      styleAttrVals.push(m[1] !== undefined ? m[1] : m[2]);
    }
  }
  let hexCount = 0;
  let funcCount = 0;
  const cssText = (styleBlocks.join('\n') + '\n' + styleSheetBlocks.join('\n') + '\n' + styleAttrVals.join('\n')).replace(/--[^\s"'=:;,{}()]+\s*['"]?\s*:[^;}]+/g, '').replace(/url\([^)]*\)/gi, '');
  const propRe = /(?:^|[;{"',])\s*(?:background(?:-image)?|border(?:-image)?|outline|text-decoration|column-rule|fill|stroke|box-shadow|text-shadow|(?!color-scheme\b)[a-z-]*color)\s*:\s*(?:"([^"]*)"|'([^']*)'|([^;}{"']+))/gi;
  const nonColorToken = /^(?:\.{3}[a-zA-Z_$][\w$.]*|[\[\]]|[a-zA-Z_$][\w$]*\.[\w$.]+|--[a-zA-Z0-9-_]+|\d*\.?\d+(?:px|em|rem|%|pt|pc|in|cm|mm|ex|ch|vw|vh|vmin|vmax|fr|s|ms|deg)?|solid|dashed|dotted|double|groove|ridge|inset|outset|hidden|thin|medium|thick|no-repeat|repeat-x|repeat-y|repeat|center|cover|contain|underline|overline|line-through|stretch|scroll|fixed|local|left|right|top|bottom|space|round|to|at|circle|ellipse|closest-side|closest-corner|farthest-side|farthest-corner|from|[-+*/]|border-box|padding-box|content-box|var\(.*|\)|calc\(.*)$/i;
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
    // 値部に混入した後続宣言（prop: 形式。カンマ・改行区切りの跨ぎ捕獲）を除去する
    return v.replace(/^[a-z-]+\s*:\s*/i, '');
  };
  // var() はfallback抽出後に評価する（fallback内リテラルの取り漏れ防止）。該当手段なし・解決不能な参照は除去する
  const expandVarFallback = (v) => v.replace(/var\([^()]*\)/gi, (m) => {
    const inner = m.slice(4, -1);
    let depth = 0;
    for (let i = 0; i < inner.length; i++) {
      const ch = inner[i];
      if (ch === '(') {
        depth++;
      } else if (ch === ')') {
        depth--;
      } else if (ch === ',' && depth === 0) {
        return inner.slice(i + 1);
      }
    }
    return '';
  });
  // トークン参照部を除去して残部を評価する（キーワード混在時の取り漏れ防止）
  const stripValueTokens = (v) => expandVarFallback(v).replace(/url\([^)]*\)/gi, '').replace(/\b(?:inherit|initial|unset|currentcolor|transparent|none|auto)\b/gi, ' ').trim();
  const countColorLiterals = (v) => {
    const hh = v.match(/#[0-9a-fA-F]{3,8}\b/g) || [];
    const ff = v.match(/\b(?:rgb|rgba|hsl|hsla)\s*\(/gi) || [];
    return { h: hh.length, f: ff.length };
  };
  // 関数スケルトン（gradient名・括弧）を除去して残部トークンを評価する
  const flattenFunctions = (v) => v.replace(/[a-zA-Z-]+\(/g, '').replace(/[()]/g, ' ');
  let namedColors = 0;
  let pm;
  while ((pm = propRe.exec(cssText)) !== null) {
    const raw = pm[1] !== undefined ? pm[1] : (pm[2] !== undefined ? pm[2] : pm[3]);
    const chunks = splitTopLevel(raw || '');
    for (const chunk of chunks) {
      const v = stripValueTokens(normalizeValue(chunk));
      if (v === '') {
        continue;
      }
      const c = countColorLiterals(v);
      if (c.h > 0 || c.f > 0) {
        hexCount += c.h;
        funcCount += c.f;
        continue;
      }
      const tokens = flattenFunctions(v).split(/[\s/,]+/).filter((t) => t !== '');
      if (tokens.length === 0 || tokens.every((t) => nonColorToken.test(t))) {
        continue;
      }
      namedColors++;
    }
  }
  // drop-shadow() 内のリテラル色（filter自体は対象外とし、色関数のみ検査。blur()等の非色関数は除外）
  const dropShadowRe = /drop-shadow\s*\(([^)]*)\)/gi;
  let dm;
  while ((dm = dropShadowRe.exec(cssText)) !== null) {
    const args = stripValueTokens(dm[1].replace(/url\([^)]*\)/gi, '').trim());
    if (args === '') {
      continue;
    }
    const c = countColorLiterals(args);
    if (c.h > 0 || c.f > 0) {
      hexCount += c.h;
      funcCount += c.f;
      continue;
    }
    const shadowTokens = flattenFunctions(args).split(/[\s/,]+/).filter((t) => t !== '');
    if (shadowTokens.length > 0 && !shadowTokens.every((t) => nonColorToken.test(t))) {
      namedColors++;
    }
  }
  const attrRe = /(?:^|[\s"'`])(?:fill|stroke|stop-color|flood-color|lighting-color|bgcolor|color)\s*=\s*(?:"([^"]*)"|'([^']*)'|(\{[^{}]*\})|([^\s>]+))/gi;
  let am;
  while ((am = attrRe.exec(colorSrc)) !== null) {
    const rawAttr = am[1] !== undefined ? am[1] : (am[2] !== undefined ? am[2] : (am[3] !== undefined ? am[3] : (am[4] || '').replace(/\/+$/, '')));
    const trimmedAttr = (rawAttr || '').trim();
    // JSX動的束縛（{...}）は識別子を除外し、内包する引用符リテラルのみ評価する
    const attrValues = /^\{[\s\S]*\}$/.test(trimmedAttr)
      ? ((trimmedAttr.match(/"([^"]*)"|'([^']*)'/g) || []).map((q) => q.slice(1, -1)))
      : [trimmedAttr];
    for (const attrValue of attrValues) {
      const v = stripValueTokens((attrValue || '').trim());
      if (v === '') {
        continue;
      }
      const c = countColorLiterals(v);
      if (c.h > 0 || c.f > 0) {
        hexCount += c.h;
        funcCount += c.f;
        continue;
      }
      const attrTokens = flattenFunctions(v).split(/[\s/,]+/).filter((t) => t !== '');
      if (attrTokens.length === 0 || attrTokens.every((t) => nonColorToken.test(t))) {
        continue;
      }
      namedColors++;
    }
  }
  for (const q of braceQuotedVals) {
    const v = stripValueTokens((q || '').trim());
    if (v === '') {
      continue;
    }
    const c = countColorLiterals(v);
    if (c.h > 0 || c.f > 0) {
      hexCount += c.h;
      funcCount += c.f;
      continue;
    }
    const tokens = flattenFunctions(v).split(/[\s/,]+/).filter((t) => t !== '');
    if (tokens.length === 0 || tokens.every((t) => nonColorToken.test(t))) {
      continue;
    }
    namedColors++;
  }
  const colorTotal = hexCount + funcCount + namedColors;
  if (colorTotal > 0) {
    issues.push(`[Warning] リテラル色値の直書きが ${colorTotal} 件検出されました（Hex ${hexCount}／関数 ${funcCount}／色名等 ${namedColors}）。適用中のデザインシステムのカラーロール変数を使用してください。`);
  }

  return issues;
}

// CLI実行ロジック
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) {
    console.log('Usage: node scripts/verify-ui.js [対象ファイル] [--help]');
    console.log('対象マークアップファイル（HTML／JSX／TSX／Vue等）を検証する。検査項目：文書構造（main・header・nav・footer・lang・title・h1）、無名ボタン・無名リンク・無名role=button、alt欠落（img・画像ボタン）、リテラル色値（CSS宣言の走査はstyle要素内・style属性値・StyleSheet.create内に限定。font shorthand内・不正HTML内・JSデータ文字列内のCSS宣言は対象外）、tabindex正値、id重複。');
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
