// 结题报告 HTML → PDF（A4，使用本工程 node_modules 中的 playwright + chromium）
// 用法：node render-report-pdf.mjs <html路径> [pdf输出路径]
import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
import path from 'path';

const htmlPath = process.argv[2];
const pdfPath = process.argv[3] || htmlPath.replace(/\.html$/i, '.pdf');
if (!htmlPath) {
  console.error('usage: node render-report-pdf.mjs <html路径> [pdf输出路径]');
  process.exit(1);
}

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(pathToFileURL(path.resolve(htmlPath)).href);
await page.waitForTimeout(500); // 等待字体加载
await page.pdf({
  path: pdfPath,
  format: 'A4',
  printBackground: true,
  preferCSSPageSize: true,
  displayHeaderFooter: false,
});
await browser.close();
console.log('PDF written:', pdfPath);
