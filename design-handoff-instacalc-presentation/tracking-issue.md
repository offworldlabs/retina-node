# Presentation Mode: composable-block polish (post-#2929 tracking)

Tracking issue for the Presentation Mode polish effort. The stepper/gutter
system shipped in #2929; this tracks its verification and the remaining work.
Full handoff PDF (approved renders + spec) attached below.

**The shipped rule (#2929):** all digits share one right boundary; the gutter
to its right belongs to interaction. Input rows fill it with `value [unit] − +`
(6px off the number); computed rows leave it empty; calcs with no visible
steppers (all-slider calcs like mortgage-calculator) reserve nothing.

## Post-merge verification

- [ ] exam-algebra1/present — `a 2 − +` / `b 3 − +` / `c −5 − +` stack above `discriminant 49`; digits 2, 3, −5, 49 share one right edge
- [ ] __kitchen-sink/present — `8.25 % − +`, `95 % − +` (value, unit, steppers); long-suffix rows keep the phrase under the digits; grid/split sections 17–18 unaffected
- [ ] mortgage-calculator/present — pixel-identical to pre-#2929 (control case)
- [ ] Narrow/mobile widths (flex `justify-between` branch below the md breakpoint)
- [ ] Dark mode stepper contrast
- [ ] Hover visibility confirmed as an explicit decision (approved mocks: always visible)

## Remaining backlog

One delta at a time: before/after mock → owner approval → implement.

- [ ] Unit-suffix edge cases across the expanded 65-row __kitchen-sink fixture
- [ ] Two+ adjacent `@hero` rows render as competing centered cards (needs expanded fixture to reproduce)
- [ ] Explanation voice inversion — narrative renders bigger than its note (needs test-present fixture)
- [ ] Parser: adjacent `#` headings merge
- [ ] Parser: adjacent `>` LaTeX rows merge
- [ ] Parser: negative values drop `@prefix`/`@accent`
- [ ] Parser: interpolation loses formatting
- [ ] Parser: `@prefix($)` currency shows 3 decimals

## Working method (binding for this effort)

The live product is the design language — small corrections only. Every
proposal is a real screenshot beside identical content with exactly one thing
changed. One example, then stop for owner reaction. No invented palettes, no
monospace numbers, no boxes/chrome the product doesn't have.
