// Retry the 3 SD articles that hit anti-bot, with the stealth-enabled fetcher.
// Sequential with a delay between requests.

import { spawn } from 'node:child_process';
import { existsSync, statSync } from 'node:fs';
import { resolve } from 'node:path';

const OUT_DIR = 'C:\\papers\\sd-pdfs';
const FETCH = resolve('fetch-one.mjs');
const GAP_SEC = 20;

const dois = [
  '10.1016/j.ress.2026.112793',
  '10.1016/j.measurement.2025.118604',
  '10.1016/j.eswa.2025.129178',
];

function safeName(doi) {
  return doi.replace(/[\\/:*?"<>|]/g, '_');
}

function runOne(doi) {
  const out = `${OUT_DIR}\\${safeName(doi)}.pdf`;
  const url = `https://doi.org/${doi}`;
  console.log(`\n=== retry [${doi}] -> ${out}`);
  return new Promise((res) => {
    const start = Date.now();
    const child = spawn('node', [FETCH, url, out], { stdio: 'inherit' });
    child.on('close', (code) => {
      const sec = ((Date.now() - start) / 1000).toFixed(1);
      const size = existsSync(out) ? statSync(out).size : 0;
      console.log(`=== [${doi}] exit=${code}  ${sec}s  size=${size}B`);
      res({ doi, out, code, size, sec });
    });
  });
}

const results = [];
for (const doi of dois) {
  results.push(await runOne(doi));
  if (doi !== dois[dois.length - 1]) {
    console.log(`-- sleep ${GAP_SEC}s before next --`);
    await new Promise((r) => setTimeout(r, GAP_SEC * 1000));
  }
}

console.log('\n========== RETRY SUMMARY ==========');
for (const r of results) {
  const ok = r.code === 0 && r.size > 200_000;
  console.log(`${ok ? 'OK ' : 'FAIL'}  ${r.doi}  ${r.size}B  ${r.sec}s`);
}
const okCount = results.filter((r) => r.code === 0 && r.size > 200_000).length;
console.log(`${okCount}/${results.length} ok`);
console.log('ALL-DONE');
