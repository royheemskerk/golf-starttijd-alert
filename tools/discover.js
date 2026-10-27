// Eenmalige verkenning: opent de reserveringspagina en logt alle netwerkverzoeken,
// iframes en JSON-antwoorden, zodat we de echte bron van de starttijden kunnen vinden.
const { chromium } = require('playwright');
const fs = require('fs');

const URL = process.env.TARGET_URL;
const out = [];
const log = (...a) => { const s = a.join(' '); console.log(s); out.push(s); };

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ locale: 'nl-NL' });
  page.on('request', r => {
    if (['xhr', 'fetch', 'document', 'script'].includes(r.resourceType()))
      log('REQ', r.resourceType(), r.method(), r.url(), r.postData() ? 'BODY=' + r.postData().slice(0, 500) : '');
  });
  page.on('response', async r => {
    const ct = r.headers()['content-type'] || '';
    if (ct.includes('json') || r.request().resourceType() === 'xhr' || r.request().resourceType() === 'fetch') {
      let body = '';
      try { body = (await r.text()).slice(0, 3000); } catch {}
      log('RES', r.status(), r.url(), ct, '\n', body, '\n----');
    }
  });

  await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(5000);
  log('\n=== FRAMES ===');
  for (const f of page.frames()) log('FRAME', f.url());
  log('\n=== IFRAME/SCRIPT/LINKS ===');
  const info = await page.evaluate(() => ({
    iframes: [...document.querySelectorAll('iframe')].map(i => i.src),
    scripts: [...document.querySelectorAll('script[src]')].map(s => s.src),
    links: [...document.querySelectorAll('a[href]')].map(a => a.href).filter(h => /reserv|book|start|tee|golf/i.test(h)),
  }));
  log(JSON.stringify(info, null, 2));
  for (const f of page.frames()) {
    log('\n=== TEXT van frame', f.url(), '===');
    try { log((await f.evaluate(() => document.body.innerText)).slice(0, 4000)); } catch (e) { log('ERR', e.message); }
  }
  fs.writeFileSync('discover.log', out.join('\n'));
  fs.writeFileSync('page.html', await page.content());
  for (const [i, f] of page.frames().entries()) { try { fs.writeFileSync(`frame${i}.html`, await f.content()); } catch {} }
  await page.screenshot({ path: 'page.png', fullPage: true });
  await browser.close();
})();
