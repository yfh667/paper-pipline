// Usage: node fetch-one.mjs <url> [out.pdf]
// Opens a ScienceDirect article, waits long enough for the lazy-loaded body
// (Introduction / Methods / etc.) to actually appear, expands collapsibles,
// scrolls to force-render figures, then prints to PDF.

import { addExtra } from 'puppeteer-extra';
import puppeteerCore from 'puppeteer-core';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const puppeteer = addExtra(puppeteerCore);
puppeteer.use(StealthPlugin());

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const NAV_TIMEOUT_MS = 120_000;
const BODY_WAIT_MS = 90_000;   // how long we'll wait for full-text sections
const POST_BODY_SETTLE_MS = 6_000;

const [, , urlArg, outArg] = process.argv;
if (!urlArg) {
  console.error('usage: node fetch-one.mjs <url> [out.pdf]');
  process.exit(2);
}

function deriveName(url) {
  const m = url.match(/\/pii\/([A-Z0-9]+)/i);
  return m ? `${m[1]}.pdf` : `article-${Date.now()}.pdf`;
}

const outPath = resolve(outArg || `out/${deriveName(urlArg)}`);
mkdirSync(dirname(outPath), { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
  ],
});

const t0 = Date.now();
const log = (...a) => console.log(`[+${((Date.now() - t0) / 1000).toFixed(1)}s]`, ...a);

try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1800, deviceScaleFactor: 1 });
  await page.setUserAgent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
  );

  log('nav', urlArg);
  await page.goto(urlArg, { waitUntil: 'domcontentloaded', timeout: NAV_TIMEOUT_MS });

  // Dismiss cookie/consent banners early.
  await page.evaluate(() => {
    Array.from(document.querySelectorAll('button')).forEach((b) => {
      const t = (b.textContent || '').trim().toLowerCase();
      if (/(accept all|i agree|got it|accept cookies)/i.test(t)) b.click();
    });
  });

  // Poll until full-text sections (not just abstract) are in the DOM.
  log('waiting for full-text sections to render...');
  const bodyReady = await page.waitForFunction(
    () => {
      const heads = Array.from(document.querySelectorAll('h2, h3'))
        .map((e) => (e.innerText || '').trim().toLowerCase());
      // Heuristic: any one of these section labels showing up means the body
      // (not just the abstract) is mounted.
      const markers = [
        'introduction', '1. introduction',
        'methods', 'methodology', 'materials and methods',
        'results', 'discussion', 'conclusion', 'conclusions',
        'references', 'related work', 'experiments',
      ];
      return heads.some((h) => markers.some((m) => h === m || h.startsWith(m)));
    },
    { timeout: BODY_WAIT_MS, polling: 1000 }
  ).then(() => true).catch(() => false);

  if (!bodyReady) {
    log('WARN: full-text sections did not appear within', BODY_WAIT_MS, 'ms');
  } else {
    log('full-text sections detected');
  }

  // Anti-bot / paywall detection. If SD threw up the sign-in / "access through
  // your institution" interstitial, the body never has real sections and we
  // should hard-fail so the caller can retry instead of saving a junk PDF.
  const block = await page.evaluate(() => {
    const text = (document.body.innerText || '').toLowerCase();
    const markers = [
      'access through your institution',
      'sign in to view full text',
      'sign in to access',
      'register to access',
      'purchase pdf',
      'unusual activity from your network',
      'are you a robot',
      'access denied',
      'just a moment',          // cloudflare interstitial
      'checking your browser',  // cloudflare interstitial
    ];
    const hit = markers.find((m) => text.includes(m));
    return { hit: hit || null, chars: text.length };
  });
  if (block.hit || !bodyReady) {
    log('BLOCKED by anti-bot / paywall:', block.hit || '(no body sections)',
        '  bodyChars=', block.chars);
    throw new Error(`anti-bot blocked: ${block.hit || 'no full-text DOM'}`);
  }

  // Expand collapsed CONTENT sections only — NOT popover triggers
  // (clicking every [aria-expanded=false] pops open Share / Export-citation /
  // Institution / Support overlays that end up covering the Abstract).
  await page.evaluate(() => {
    const contentToggleSelectors = [
      '.accordion__control[aria-expanded="false"]',
      'button[data-aa-name="show-section"]',
      'button[data-aa-button="show-section"]',
      'button.show-more-btn',
    ];
    document.querySelectorAll(contentToggleSelectors.join(',')).forEach((el) => {
      try { el.click(); } catch {}
    });
    // Inline "Show more references" / "View all figures" buttons inside the article.
    const article = document.querySelector('article') || document.body;
    article.querySelectorAll('button, a').forEach((el) => {
      const t = (el.textContent || '').trim().toLowerCase();
      if (/^(show more|view all|expand|show full|show all \d)/.test(t)) {
        try { el.click(); } catch {}
      }
    });
  });

  // Scroll through the whole page so lazy figures/refs load.
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

  // Let any final XHR / image load settle.
  await new Promise((r) => setTimeout(r, POST_BODY_SETTLE_MS));

  // Diagnostics so we can tell if it worked without opening the PDF.
  const diag = await page.evaluate(() => {
    const text = document.body.innerText || '';
    const heads = Array.from(document.querySelectorAll('h2, h3'))
      .map((e) => (e.innerText || '').trim())
      .filter(Boolean);
    return {
      title: document.title,
      bodyChars: text.length,
      sectionHeadings: heads.slice(0, 30),
    };
  });
  log('title:', diag.title);
  log('body chars:', diag.bodyChars);
  log('section headings:', diag.sectionHeadings);

  // Strip overlays / chrome that would cover the article in the printed PDF:
  // popover bubbles, sticky access bar, side TOC, header, ads, recommendations.
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
      [class*="cookie"],
      [data-aa-name="article-actions"] [aria-expanded="true"] + .popover-content,
      [class*="reading-assistant"i],
      [class*="ReadingAssistant"],
      [id*="reading-assistant"i],
      [data-aa-name*="reading-assistant"i],
      [aria-label*="Reading Assistant"i] {
        display: none !important;
      }
      /* Article goes full width once side TOC is gone */
      .col-lg-18, .col-lg-9, [class*="MainContent"] {
        max-width: 100% !important;
        flex: 0 0 100% !important;
      }
    `,
  });
  // Force-close any popovers still flagged open (defensive).
  await page.evaluate(() => {
    document.querySelectorAll('[aria-expanded="true"]').forEach((el) => {
      const ctrl = el.getAttribute('aria-controls') || '';
      if (/popover|share|export|cite|institution|support/i.test(ctrl)) {
        try { el.click(); } catch {}
      }
    });
    document.querySelectorAll('.popover-content, [id^="popover-content-"]').forEach((el) => {
      el.remove();
    });

    // Kill the "Reading Assistant" AI widget that SD injects inline above the
    // article body. It steals the entire first viewport-height of the article
    // and shows "Sign in to unlock" CTAs repeatedly in the printed PDF.
    const matchAttrs = (el) => {
      const id = el.id || '';
      const cls = (el.className && el.className.toString && el.className.toString()) || '';
      const aria = el.getAttribute('aria-label') || '';
      const aaname = el.getAttribute('data-aa-name') || '';
      return `${id} ${cls} ${aria} ${aaname}`;
    };
    document.querySelectorAll('*').forEach((el) => {
      if (/reading[\s\-_]?assistant/i.test(matchAttrs(el))) {
        try { el.remove(); } catch {}
      }
    });
    // Fallback: any element whose direct text starts with "Reading Assistant"
    // or contains the "Sign in to unlock" CTA — walk up to the obvious panel
    // ancestor (max 6 levels) and delete it.
    const textHits = [];
    document.querySelectorAll('body *').forEach((el) => {
      const t = (el.textContent || '').trim();
      if (!t) return;
      if (/^Reading Assistant\b/i.test(t) || /Sign in to unlock/i.test(t)) {
        textHits.push(el);
      }
    });
    for (const start of textHits) {
      let cur = start;
      for (let i = 0; i < 6 && cur && cur !== document.body; i++) {
        const rect = cur.getBoundingClientRect && cur.getBoundingClientRect();
        if (rect && rect.height > 300 && rect.width > 400) break;
        cur = cur.parentElement;
      }
      try { cur && cur !== document.body && cur.remove(); } catch {}
    }
  });

  // Do NOT emulate print media — SD's print stylesheet strips the body.
  await page.pdf({
    path: outPath,
    format: 'A4',
    printBackground: true,
    margin: { top: '14mm', bottom: '14mm', left: '12mm', right: '12mm' },
  });
  log('saved ->', outPath);
} finally {
  await browser.close();
}
