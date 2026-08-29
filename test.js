#!/usr/bin/env node
// Smoke test QR puzzle — load page, check no JS errors, board tiles render
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR: ' + e.message.slice(0, 120)));
  p.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text().slice(0, 120)); });
  await p.goto('file:///home/ubuntu/qr-puzzle/index.html', { waitUntil: 'load', timeout: 20000 }).catch(e => errs.push('NAV: ' + e.message.slice(0, 80)));
  await p.waitForTimeout(1500);
  const tiles = await p.locator('.tile').count();
  const progress = await p.locator('#progress').textContent();
  const moves = await p.locator('#moves').textContent();
  console.log('tiles:', tiles, '| progress:', progress, '| moves:', moves);
  // click scramble
  await p.click('#scrambleBtn');
  await p.waitForTimeout(800);
  const tiles2 = await p.locator('.tile').count();
  const winVisible = await p.locator('#win').evaluate(el => el.classList.contains('show'));
  console.log('after scramble tiles:', tiles2, '| win visible:', winVisible);
  console.log('errors:', errs.length ? errs.join('\n') : 'NONE ✅');
  await b.close();
})().catch(e => console.error('FATAL', e.message.slice(0, 200)));
