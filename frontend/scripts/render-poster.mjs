// 结题展板 HTML → PNG（A0 竖版 841×1189mm，deviceScaleFactor=6 → 约 152dpi）
// 用法：node render-poster.mjs <html路径> [png输出路径]
import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
import path from 'path';

const htmlPath = process.argv[2];
const pngPath = process.argv[3] || htmlPath.replace(/\.html$/i, '.png');
if (!htmlPath) {
  console.error('usage: node render-poster.mjs <html路径> [png输出路径]');
  process.exit(1);
}

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 841, height: 1189 }, // 1 CSS px = 1mm
  deviceScaleFactor: 6, // 841*6 = 5046px ≈ 152dpi
});
await page.goto(pathToFileURL(path.resolve(htmlPath)).href);
await page.waitForTimeout(600);
await page.screenshot({ path: pngPath, fullPage: true });
await browser.close();
console.log('PNG written:', pngPath);
