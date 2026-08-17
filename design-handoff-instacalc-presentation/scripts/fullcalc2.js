const { withPage } = require('./shot3.js');

const APPLY = () => {
  // only steppers that are actually visible count
  const pairs = [...document.querySelectorAll('row .stepper-pair')].filter(sp => sp.getBoundingClientRect().width > 0);
  if (!pairs.length) return 'no visible steppers';
  const w = Math.max(...pairs.map(sp => sp.getBoundingClientRect().width));
  pairs.forEach(sp => {
    const row = sp.closest('row');
    const rv = row.querySelector('.row-value');
    if (!rv) return;
    sp.style.marginLeft = '6px';
    rv.appendChild(sp);
    // keep an inline unit (e.g. %) glued to the digits: value, unit, then steppers.
    // The unit renders as a row-level span outside .row-value; pull it in before the steppers.
    const unitWrap = [...row.querySelectorAll('span[class*="text-xs"]')].find(el =>
      !rv.contains(el) && !el.closest('.row-label') && !el.closest('.stepper-pair'));
    if (unitWrap) { unitWrap.style.marginLeft = '2px'; rv.insertBefore(unitWrap, sp); }
  });
  const reserve = w + 6;
  document.querySelectorAll('[data-row-index]').forEach(rowEl => {
    const row = rowEl.querySelector('row');
    if (!row) return;
    const rv = row.querySelector('.row-value');
    if (!rv) return;
    const sp = rv.querySelector('.stepper-pair');
    const visible = sp && sp.getBoundingClientRect().width > 0;
    if (!visible) rv.style.paddingRight = reserve + 'px';
  });
  return 'applied, reserve=' + reserve;
};

(async () => {
  await withPage(async page => {
    for (const [name, url] of [
      ['exam2', 'https://instacalc.com/exam-algebra1/present'],
      ['sink2', 'https://instacalc.com/__kitchen-sink/present'],
    ]) {
      await page.setViewportSize({ width: 1280, height: 1000 });
      await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
      await page.waitForTimeout(3000);
      await page.addStyleTag({ content: '[class*="toast"], [role="status"], [aria-live] { display: none !important; }' });
      const h = await page.evaluate(() => {
        let max = document.documentElement.scrollHeight;
        for (const el of document.querySelectorAll('*')) if (el.scrollHeight > el.clientHeight + 50 && el.scrollHeight > max) max = el.scrollHeight;
        return max;
      });
      await page.setViewportSize({ width: 1280, height: Math.min(h + 100, 14000) });
      await page.waitForTimeout(1500);
      const res = await page.evaluate(APPLY);
      await page.waitForTimeout(400);
      await page.screenshot({ path: `${name}-after.png` });
      console.log(name, res);
    }
  });
})().catch(e => { console.error(e.message.split('\n')[0]); process.exit(1); });
