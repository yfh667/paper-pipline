// Diagnostic: reproduce fetch-one's NEW state (with overlay cleanup) and
// save a full top-of-page PNG so we can visually verify overlays are gone.
import puppeteer from 'puppeteer-core';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const url = process.argv[2] || 'https://www.sciencedirect.com/science/article/pii/S0952197626011747';

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: ['--no-sandbox', '--disable-blink-features=AutomationControlled'],
});
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1800, deviceScaleFactor: 1 });
  await page.setUserAgent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
  );
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120_000 });

  await page.evaluate(() => {
    Array.from(document.querySelectorAll('button')).forEach((b) => {
      const t = (b.textContent || '').trim().toLowerCase();
      if (/(accept all|i agree|got it|accept cookies)/i.test(t)) b.click();
    });
  });

  await page.waitForFunction(
    () => {
      const heads = Array.from(document.querySelectorAll('h2, h3'))
        .map((e) => (e.innerText || '').trim().toLowerCase());
      const markers = ['introduction', 'methods', 'results', 'conclusion'];
      return heads.some((h) => markers.some((m) => h === m || h.startsWith(m)));
    },
    { timeout: 90_000, polling: 1000 }
  ).then(() => true).catch(() => false);

  // Same selective expansion as fetch-one.mjs (no popover triggers).
  await page.evaluate(() => {
    const sel = [
      '.accordion__control[aria-expanded="false"]',
      'button[data-aa-name="show-section"]',
      'button[data-aa-button="show-section"]',
      'button.show-more-btn',
    ].join(',');
    document.querySelectorAll(sel).forEach((el) => { try { el.click(); } catch {} });
    const article = document.querySelector('article') || document.body;
    article.querySelectorAll('button, a').forEach((el) => {
      const t = (el.textContent || '').trim().toLowerCase();
      if (/^(show more|view all|expand|show full|show all \d)/.test(t)) {
        try { el.click(); } catch {}
      }
    });
  });
  await page.evaluate(async () => {
    await new Promise((done) => {
      let y = 0;
      const step = 500;
      const timer = setInterval(() => {
        window.scrollBy(0, step);
        y += step;
        if (y >= document.body.scrollHeight + 2000) {
          clearInterval(timer);
          window.scrollTo(0, 0);
          done();
        }
      }, 150);
    });
  });
  await new Promise((r) => setTimeout(r, 5000));

  // Apply the same cleanup as fetch-one.mjs before the screenshot.
  await page.addStyleTag({
    content: `
      .popover-content,
      [id^="popover-content-"],
      .accessbar-sticky,
      .sticky-table-of-contents,
      #gh-header,
      header[role="banner"],
      .recommendations,
      [data-aa-region="recommended-articles"],
      .feedback-button,
      [class*="FeedbackButton"],
      [class*="cookie"] {
        display: none !important;
      }
      .col-lg-18, .col-lg-9, [class*="MainContent"] {
        max-width: 100% !important;
        flex: 0 0 100% !important;
      }
    `,
  });
  await page.evaluate(() => {
    document.querySelectorAll('.popover-content, [id^="popover-content-"]').forEach((el) => el.remove());
    window.scrollTo(0, 0);
  });
  await new Promise((r) => setTimeout(r, 800));

  await page.screenshot({
    path: 'out/debug-top-after.png',
    clip: { x: 0, y: 0, width: 1280, height: 1800 },
  });
  console.log('screenshot -> out/debug-top-after.png');
} finally {
  await browser.close();
}
