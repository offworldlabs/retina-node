// Screenshot helper for instacalc presentation pages.
// Chrome in this container can't do TLS through the egress proxy itself
// (its trust store lacks the proxy CA), so we serve each request from
// Node via undici's ProxyAgent, which uses HTTPS_PROXY and verifies TLS
// against the proxy CA bundle per /root/.ccr/README.md guidance.
const { chromium } = require('playwright-core');
const { ProxyAgent, fetch: ufetch } = require('undici');
const fs = require('fs');
const ca = fs.readFileSync('/root/.ccr/ca-bundle.crt', 'utf8');
const dispatcher = new ProxyAgent({ uri: process.env.HTTPS_PROXY, requestTls: { ca } });

async function withPage(fn) {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 2 });
  await page.route('**/*', async route => {
    const req = route.request();
    try {
      const res = await ufetch(req.url(), { method: req.method(), headers: req.headers(), body: req.postDataBuffer() || undefined, dispatcher, redirect: 'manual' });
      const headers = {};
      res.headers.forEach((v, k) => { if (!['content-encoding', 'transfer-encoding', 'content-length'].includes(k)) headers[k] = v; });
      await route.fulfill({ status: res.status, headers, body: Buffer.from(await res.arrayBuffer()) });
    } catch (e) { await route.abort(); }
  });
  await fn(page);
  await browser.close();
}
module.exports = { withPage };

if (require.main === module) (async () => {
  await withPage(async page => {
    for (const [name, url] of [
      ['kitchen-sink', 'https://instacalc.com/__kitchen-sink/present'],
      ['exam-algebra1', 'https://instacalc.com/exam-algebra1/present'],
    ]) {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
      await page.waitForTimeout(3000);
      await page.screenshot({ path: `${name}-full.png`, fullPage: true });
      console.log(name, 'ok:', await page.title());
    }
  });
})().catch(e => { console.error(e.message.split('\n')[0]); process.exit(1); });
