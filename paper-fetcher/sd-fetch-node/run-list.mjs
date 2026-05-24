// Driver: read C:\papers\needs_manual.txt, pick [elsevier_sciencedirect] lines,
// resolve each DOI via doi.org, run the same fetch logic as fetch-one.mjs,
// and write PDFs to C:\papers\sd-pdfs\ named by sanitized DOI.

import { spawn } from 'node:child_process';
import { readFileSync, mkdirSync, existsSync, statSync } from 'node:fs';
import { resolve } from 'node:path';

const LIST = 'C:\\papers\\needs_manual.txt';
const OUT_DIR = 'C:\\papers\\sd-pdfs';
const FETCH = resolve('fetch-one.mjs');

mkdirSync(OUT_DIR, { recursive: true });

const lines = readFileSync(LIST, 'utf8').split(/\r?\n/);
const jobs = [];
for (const raw of lines) {
  if (!raw.startsWith('[elsevier_sciencedirect]')) continue;
  const m = raw.match(/doi=([^)]+)\)/);
  if (!m) continue;
  const doi = m[1].trim();
  if (!doi) continue;
  const safe = doi.replace(/[\\/:*?"<>|]/g, '_');
  jobs.push({ doi, url: `https://doi.org/${doi}`, out: `${OUT_DIR}\\${safe}.pdf` });
}

console.log(`found ${jobs.length} SD entries`);

function runOne(job) {
  return new Promise((resolveP) => {
    const start = Date.now();
    console.log(`\n=== [${job.doi}] -> ${job.out}`);
    const child = spawn('node', [FETCH, job.url, job.out], { stdio: 'inherit' });
    child.on('close', (code) => {
      const sec = ((Date.now() - start) / 1000).toFixed(1);
      const size = existsSync(job.out) ? statSync(job.out).size : 0;
      console.log(`=== [${job.doi}] exit=${code}  ${sec}s  size=${size}B`);
      resolveP({ ...job, code, size, sec });
    });
  });
}

const GAP_SEC = 60;
const results = [];
for (let i = 0; i < jobs.length; i++) {
  const j = jobs[i];
  if (existsSync(j.out) && statSync(j.out).size > 200_000) {
    console.log(`-- skip (already have): ${j.out}`);
    results.push({ ...j, code: 0, size: statSync(j.out).size, sec: '0.0', skipped: true });
    continue;
  }
  results.push(await runOne(j));
  if (i < jobs.length - 1) {
    console.log(`-- sleep ${GAP_SEC}s before next --`);
    await new Promise((r) => setTimeout(r, GAP_SEC * 1000));
  }
}

console.log('\n========== SUMMARY ==========');
for (const r of results) {
  const ok = r.code === 0 && r.size > 200_000;
  console.log(`${ok ? 'OK ' : 'FAIL'}  ${r.doi}  ${r.size}B  ${r.sec}s${r.skipped ? '  (skipped)' : ''}`);
}
const okCount = results.filter((r) => r.code === 0 && r.size > 200_000).length;
console.log(`${okCount}/${results.length} ok`);
