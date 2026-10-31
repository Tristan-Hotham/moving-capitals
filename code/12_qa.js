// QA: serve the folder, open index.html at 1280 px and 390 px, collect console errors, take screenshots, exercise the controls.
// Run: node code/12_qa.js (needs playwright; Leaflet and topojson-client from a local npm folder, QA_NODE). Base tiles are blocked.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const NM = process.env.QA_NODE || '/tmp/claude-0/qa/node_modules';
const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.csv': 'text/csv', '.js': 'text/javascript' };
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0].split('#')[0])); fs.readFile(f.endsWith('/') ? f + 'index.html' : f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); }).listen(0);
(async () => {
  const b = await chromium.launch();
  for (const [w, h, tag, dark] of [[1280, 900, 'desktop', false], [390, 844, 'phone', false], [1280, 900, 'dark', true]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, colorScheme: dark ? 'dark' : 'light' });
    const errs = [];
    p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: NM + '/leaflet/dist/leaflet.js' }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: NM + '/leaflet/dist/leaflet.css' }));
    await p.route(/topojson-client.min.js/, r => r.fulfill({ path: NM + '/topojson-client/dist/topojson-client.min.js' }));
    await p.goto(`http://localhost:${srv.address().port}/index.html`, { waitUntil: 'load' });
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_top.png` });
    await p.evaluate(() => document.getElementById('atlas').scrollIntoView());
    await p.waitForTimeout(500);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_map_all.png` });
    if (dark) { await p.close(); console.log(tag, 'errors', errs.filter(e => !/ERR_|net::|Failed to load resource/.test(e))); continue; }
    await p.evaluate(() => { S.year = 1815; syncYear(); draw(); }); await p.waitForTimeout(500);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_map_1815.png` });
    await p.evaluate(() => { S.year = R.last_year; syncYear(); draw(); map.setView([50, 12], 5); }); await p.waitForTimeout(900);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_map_europe.png` });
    await p.evaluate(() => select('m083', true)); await p.waitForTimeout(1500);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_click.png` });
    await p.evaluate(() => document.getElementById('side').scrollIntoView({ block: 'center' })); await p.waitForTimeout(300);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_side.png` });
    await p.evaluate(() => document.getElementById('atlas').scrollIntoView());
    await p.fill('#q', 'Braz'); await p.waitForTimeout(300);
    const sug = await p.$eval('#sug', e => e.textContent);
    await p.keyboard.press('Enter'); await p.waitForTimeout(1500);
    await p.evaluate(() => document.getElementById('atlas').scrollIntoView());
    await p.screenshot({ path: `${ROOT}/qa/${tag}_search.png` });
    await p.click('#play'); await p.waitForTimeout(2500); await p.click('#play');
    const yr = await p.$eval('#yrlab', e => e.textContent);
    await p.evaluate(() => { const box = document.getElementById('map'); const b = box.querySelector('.lyrBtn'); b.click(); }); await p.waitForTimeout(300);
    await p.evaluate(() => document.getElementById('atlas').scrollIntoView());
    await p.screenshot({ path: `${ROOT}/qa/${tag}_layers.png` });
    for (const id of ['centChart', 'decChart', 'longChart', 'pbChart', 'seaChart', 'ctryChart', 'famTable', 'plannedNote']) {
      await p.evaluate(id => document.getElementById(id).scrollIntoView({ block: 'center' }), id); await p.waitForTimeout(250);
      await p.screenshot({ path: `${ROOT}/qa/${tag}_${id}.png` });
    }
    const fsb = await p.$$eval('.mfs-btn', e => e.length);
    const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    console.log(tag, 'fullscreen buttons', fsb, 'scrollWidth', sw, 'year after play', yr, 'search:', sug.slice(0, 90));
    console.log(tag, 'errors', errs.filter(e => !/ERR_|net::|Failed to load resource/.test(e)), 'network errors', errs.filter(e => /ERR_|net::|Failed to load resource/.test(e)).length);
    await p.close();
  }
  await b.close(); srv.close();
})();
