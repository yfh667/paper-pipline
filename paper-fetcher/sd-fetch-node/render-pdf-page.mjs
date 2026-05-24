// Render page 1 of a PDF to PNG using headless Chrome's built-in PDF viewer.
import { addExtra } from 'puppeteer-extra';
import puppeteerCore from 'puppeteer-core';
import { resolve, basename } from 'node:path';
import { pathToFileURL } from 'node:url';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const pdf = process.argv[2];
if (!pdf) { console.error('usage: node render-pdf-page.mjs <pdf>'); process.exit(2); }
const url = pathToFileURL(resolve(pdf)).href;
const outPng = resolve(`out/${basename(pdf, '.pdf')}_p1.png`);

const puppeteer = addExtra(puppeteerCore);
const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: ['--no-sandbox'],
});
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1100, height: 1500 });
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60_000 });
  await new Promise((r) => setTimeout(r, 2500));
  await page.screenshot({ path: outPng });
  console.log('->', outPng);
} finally {
  await browser.close();
}
