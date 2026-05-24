// Render page 1 of every SD PDF under C:\papers\sd-pdfs and save PNGs side by
// side so we can eyeball which ones still have Reading Assistant overlay.
import { addExtra } from 'puppeteer-extra';
import puppeteerCore from 'puppeteer-core';
import { readdirSync, mkdirSync } from 'node:fs';
import { resolve, join, basename } from 'node:path';
import { pathToFileURL } from 'node:url';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SRC = 'C:\\papers\\sd-pdfs';
const OUT = resolve('out/audit');
mkdirSync(OUT, { recursive: true });

const pdfs = readdirSync(SRC).filter((f) => f.toLowerCase().endsWith('.pdf'));
const puppeteer = addExtra(puppeteerCore);
const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1000, height: 1300 });
  for (const f of pdfs) {
    const url = pathToFileURL(join(SRC, f)).href;
    const out = join(OUT, basename(f, '.pdf') + '_p1.png');
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60_000 });
    await new Promise((r) => setTimeout(r, 1500));
    await page.screenshot({ path: out });
    console.log(out);
  }
} finally {
  await browser.close();
}
