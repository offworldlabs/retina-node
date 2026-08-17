# InstaCalc Presentation Mode — design handoff artifacts

NOTE: this content is unrelated to retina-node. It is parked on this session's
designated branch (claude/presentation-mode-blocks-hcxayp) purely so the design
session's artifacts survive container teardown. Safe to delete once mirrored to
kazad/instacalc-private issue #2931 (design coordination hub).

- presentation-mode-handoff.pdf — full handoff: approved rule, before/after
  evidence, complete renders of 3 calcs, implementation spec, backlog.
- stepper-gutter-spec.md — implementation spec (shipped as instacalc PR #2929).
- tracking-issue.md — drafted issue body (verification checklist + backlog);
  content largely mirrored into issue #2931 coordination.
- renders/ — pixel-faithful mock renders captured from the live product with a
  one-change DOM transform (scripts/fullcalc2.js applied via scripts/shot3.js).
- scripts/ — Playwright capture harness (proxied Node fetch for TLS via the
  session egress proxy) + PDF generator (handoff.py).
