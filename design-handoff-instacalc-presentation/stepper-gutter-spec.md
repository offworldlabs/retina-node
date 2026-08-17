# Presentation Mode — stepper/gutter alignment spec

Approved 2026-08-15 from live-render mocks (exam-algebra1, __kitchen-sink,
mortgage-calculator). One rule, no new chrome:

## The rule

**All digits share one right boundary; the gutter to its right belongs to
interaction.**

- Every standard row's value column right-aligns digits on a single shared
  boundary (the current value-column edge).
- A fixed-width gutter (stepper-pair width + 6px ≈ 64px) sits to the right of
  that boundary.
- **Input rows** (visible stepper): the `− +` pair sits in the gutter, 6px off
  the number. Order with inline units: `8.25 % − +` — unit stays glued to the
  digits, steppers last.
- **Computed rows** (no stepper): gutter stays empty. The absence of `− +`
  plus the existing ink color (vs. accent + dashed underline on inputs) is
  what marks "this is a result."
- **Calcs with no visible steppers anywhere** (e.g. mortgage-calculator, all
  sliders): no gutter is reserved; the page renders exactly as today.

## Current defect being fixed

The `.stepper-pair` renders as its own far-right slot *outside* the content
column (card text column ends at x=1012; steppers at x=1023–1081 at 1280px
viewport), ~90px of dead space from the value it edits.

## Implementation notes (renderer, Svelte row component ~ svelte-1459lf9)

- Real fix is the row grid template, not DOM reparenting: the value column
  ends at the shared boundary; a fixed `auto` stepper column follows it
  (width = stepper-pair width + 6px), present whenever the calc has any
  stepper rows so the boundary stays consistent.
- Slider rows already carry hidden zero-width `.stepper-pair` nodes — only
  *visible* steppers count when deciding whether a calc reserves the gutter.
- Inline unit spans currently render as row-level siblings after
  `.row-value`; they must order before the steppers (value, unit, steppers).
- Unit-below-value rows (`180` over `lbs`) need no change.
- Check hover behavior: if steppers were meant to be hover-revealed, this
  placement works either way, but decide explicitly.

## Reference: mock transform used for the approved screenshots

The in-page JS that produced the approved renders (reparenting version —
use as a visual oracle, not as the implementation):

```js
const pairs = [...document.querySelectorAll('row .stepper-pair')]
  .filter(sp => sp.getBoundingClientRect().width > 0);
if (pairs.length) {
  const w = Math.max(...pairs.map(sp => sp.getBoundingClientRect().width));
  pairs.forEach(sp => {
    const row = sp.closest('row');
    const rv = row.querySelector('.row-value');
    if (!rv) return;
    sp.style.marginLeft = '6px';
    rv.appendChild(sp);
    const unitWrap = [...row.querySelectorAll('span[class*="text-xs"]')].find(el =>
      !rv.contains(el) && !el.closest('.row-label') && !el.closest('.stepper-pair'));
    if (unitWrap) { unitWrap.style.marginLeft = '2px'; rv.insertBefore(unitWrap, sp); }
  });
  const reserve = w + 6;
  document.querySelectorAll('[data-row-index]').forEach(rowEl => {
    const rv = rowEl.querySelector('row .row-value');
    if (!rv) return;
    const sp = rv.querySelector('.stepper-pair');
    if (!(sp && sp.getBoundingClientRect().width > 0)) rv.style.paddingRight = reserve + 'px';
  });
}
```

## Acceptance checks (screenshot these three calcs)

1. exam-algebra1: `a 2 − +` / `b 3 − +` / `c −5 − +` stack above
   `discriminant 49`; digits 2, 3, −5, 49 share one right edge.
2. __kitchen-sink: `8.25 % − +`, `95 % − +`; long-suffix rows
   (`150` over `dollars per hour`) keep suffix under the digits with `− +`
   beside the number; grid/split layouts (sections 17–18) unaffected.
3. mortgage-calculator: pixel-identical to production (sliders only).
