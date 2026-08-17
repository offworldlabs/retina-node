from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, HRFlowable, PageBreak, Preformatted)
from reportlab.lib.styles import ParagraphStyle
from PIL import Image as PILImage

CREAM = HexColor('#FAF7ED'); INK = HexColor('#3B3A33'); DIM = HexColor('#787469')

def bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(CREAM); canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas.setFillColor(DIM); canvas.setFont('Helvetica', 8)
    canvas.drawRightString(letter[0]-0.7*inch, 0.45*inch, f"instacalc presentation mode — handoff — page {doc.page}")
    canvas.restoreState()

st = {
 'title': ParagraphStyle('t', fontName='Times-Roman', fontSize=27, leading=32, textColor=INK, spaceAfter=4),
 'sub': ParagraphStyle('s', fontName='Helvetica', fontSize=10.5, leading=15, textColor=DIM, spaceAfter=12),
 'h1': ParagraphStyle('h1', fontName='Times-Roman', fontSize=19, leading=23, textColor=INK, spaceBefore=14, spaceAfter=7),
 'h2': ParagraphStyle('h2', fontName='Times-Roman', fontSize=14.5, leading=18, textColor=INK, spaceBefore=12, spaceAfter=5),
 'body': ParagraphStyle('b', fontName='Helvetica', fontSize=10, leading=15, textColor=INK, spaceAfter=8),
 'cap': ParagraphStyle('c', fontName='Helvetica-Oblique', fontSize=9, leading=13, textColor=DIM, spaceBefore=3, spaceAfter=10),
 'label': ParagraphStyle('l', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=DIM, spaceBefore=8, spaceAfter=3),
 'code': ParagraphStyle('code', fontName='Courier', fontSize=7.5, leading=9.5, textColor=INK),
}

def img(path, max_w, max_h=None):
    w, h = PILImage.open(path).size
    scale = max_w / w
    if max_h and h*scale > max_h: scale = max_h / h
    return Image(path, width=w*scale, height=h*scale)

doc = SimpleDocTemplate('presentation-mode-handoff.pdf', pagesize=letter,
                        leftMargin=0.8*inch, rightMargin=0.8*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
W = letter[0] - 1.6*inch
H = letter[1] - 1.5*inch
S = []

# ---- Cover / summary
S.append(Paragraph('Presentation Mode — Stepper &amp; Gutter System', st['title']))
S.append(Paragraph('Handoff document · approved design, full-page renders, implementation spec · August 15, 2026', st['sub']))
S.append(HRFlowable(width='100%', thickness=0.75, color=DIM))
S.append(Paragraph('Summary', st['h1']))
S.append(Paragraph(
 'Presentation mode’s biggest repeated visual flaw was fixed as a system, approved by the owner from pixel-faithful '
 'live-render mocks. The − + stepper pair — previously orphaned in the right margin, outside the content column — '
 'now attaches to the value it edits, while computed rows keep their digits on the same shared boundary with an '
 'empty gutter. The rule strengthens the product’s goal: steppers invite readers to play with the inputs; the '
 'quiet gutter next to a result says “this one answers back.”', st['body']))
S.append(Paragraph('The rule (approved)', st['h1']))
S.append(Paragraph(
 '<b>All digits share one right boundary; the gutter to its right belongs to interaction.</b><br/><br/>'
 '1.&nbsp;&nbsp;Every standard row right-aligns its number on a single shared boundary.<br/>'
 '2.&nbsp;&nbsp;A fixed gutter (stepper width + 6 px ≈ 64 px) sits right of that boundary.<br/>'
 '3.&nbsp;&nbsp;Input rows fill the gutter with − + , 6 px off the number. With inline units the order is '
 '“8.25&nbsp;%&nbsp;−&nbsp;+” — unit glued to digits, steppers last.<br/>'
 '4.&nbsp;&nbsp;Computed rows leave the gutter empty; no − + plus ink color (vs. accent + dashed underline) marks a result.<br/>'
 '5.&nbsp;&nbsp;Calcs with no steppers anywhere (all-slider calcs like mortgage-calculator) reserve nothing and render unchanged.', st['body']))
S.append(Paragraph('Design-language precedent', st['h2']))
S.append(Paragraph(
 'Airbnb’s guest picker and Stripe’s quantity control treat count + buttons as one object; native number fields and '
 'macOS steppers put spinners at the field’s right edge; iOS HIG says place a stepper adjacent to the value it '
 'modifies. Nobody floats controls at the page margin. The trailing “value − +” order (rather than “− value +”) is '
 'the adaptation that preserves the worked-document’s right-aligned digit column. Financial-calculator sites dodge '
 'the input/result question with separate panels; instacalc interleaves them, so the within-column cues carry the meaning.', st['body']))
S.append(PageBreak())

# ---- Finding
S.append(Paragraph('The defect', st['h1']))
S.append(Paragraph(
 'On every editable numeric row of every stepper calc, .stepper-pair rendered as its own far-right slot outside '
 'the content column: at a 1280 px viewport the card’s text column ends at x = 1012 while the steppers sat at '
 'x = 1023–1081 — ~90 px of empty paper between the number and its controls. It appeared on the exam’s a/b/c rows '
 'and throughout the kitchen sink (sections 4–7, 10, 15, 19–20).', st['body']))
S.append(Paragraph('BEFORE — production render (Algebra I exam, Problem 6 coefficients)', st['label']))
S.append(img('crop-before.png', W))
S.append(Paragraph('AFTER — approved: steppers attach to the value; digits keep one boundary', st['label']))
S.append(img('crop-after.png', W))
S.append(Paragraph(
 'Both images are the real product render; the “after” relocates only the stepper node. Fonts, colors, underline, '
 'spacing: untouched.', st['cap']))
S.append(Paragraph('Detail: inline units stay glued to the digits', st['h2']))
S.append(img('detail-taxrate.png', W*0.85, 1.0*inch))
S.append(img('detail-tooltip.png', W*0.85, 1.0*inch))
S.append(Paragraph('“8.25 % − +” and “95 % − +” — value, unit, steppers. Unit-below-value rows (“180” over “lbs”) are unchanged.', st['cap']))
S.append(PageBreak())

# ---- Full renders: exam
S.append(Paragraph('Full-calc render — Algebra I exam (flagship content)', st['h1']))
S.append(Paragraph(
 'Complete /present page with the system applied. Note Problem 6: inputs “a 2 − +”, “b 3 − +”, “c −5 − +” stack '
 'directly above computed “discriminant 49”, all digits on one right edge.', st['body']))
for i in range(1, 4):
    S.append(img(f'exam-stepper-system-{i}of3.png', W, H - (1.6*inch if i == 1 else 0.4*inch)))
    S.append(Paragraph(f'exam-algebra1/present — part {i} of 3', st['cap']))
    if i < 3: S.append(PageBreak())
S.append(PageBreak())

# ---- Full renders: kitchen sink
S.append(Paragraph('Full-calc render — Kitchen Sink (all 27 sections)', st['h1']))
S.append(Paragraph(
 'The canonical coverage fixture under the same rule: long-suffix rows keep the phrase under the digits with − + '
 'beside the number; hint/note/tooltip rows, sections, grid and split layouts, heroes, and readonly rows are unaffected.', st['body']))
for i in range(1, 5):
    S.append(img(f'sink-stepper-system-{i}of4.png', W, H - (1.3*inch if i == 1 else 0.4*inch)))
    S.append(Paragraph(f'__kitchen-sink/present — part {i} of 4', st['cap']))
    if i < 4: S.append(PageBreak())
S.append(PageBreak())

# ---- Mortgage control
S.append(Paragraph('Control case — Mortgage Calculator (unchanged by design)', st['h1']))
S.append(Paragraph(
 'This calc uses sliders only — no visible steppers — so rule 5 reserves no gutter and the page renders exactly '
 'as production. A rule that leaves already-good pages alone is the test that it is a rule, not a patch.', st['body']))
S.append(img('mortgage-full-before-p00.png', W, H - 1.9*inch))
S.append(Paragraph('mortgage-calculator/present — production render, no change required', st['cap']))
S.append(PageBreak())

# ---- Implementation spec
S.append(Paragraph('Implementation spec', st['h1']))
S.append(Paragraph('Target: the presentation row component in kazad/instacalc-private (rendered class hash svelte-1459lf9 on the live site).', st['body']))
S.append(Paragraph(
 '• The real fix is the row grid template, not DOM reparenting: the value column ends at the shared boundary and a '
 'fixed stepper column (stepper width + 6 px) follows, present whenever the calc has any visible stepper rows.<br/>'
 '• Slider rows carry hidden zero-width .stepper-pair nodes — only <b>visible</b> steppers count when deciding '
 'whether a calc reserves the gutter.<br/>'
 '• Inline unit spans currently render as row-level siblings after .row-value; the order must become value, unit, steppers.<br/>'
 '• Unit-below-value rows need no change.<br/>'
 '• Decide hover behavior explicitly: the approved mocks show steppers always visible.', st['body']))
S.append(Paragraph('Reference transform (visual oracle used for the approved renders — not the implementation)', st['h2']))
S.append(Preformatted('''const pairs = [...document.querySelectorAll('row .stepper-pair')]
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
}''', st['code']))
S.append(Paragraph('Acceptance checks', st['h2']))
S.append(Paragraph(
 '1.&nbsp;&nbsp;exam-algebra1/present: a/b/c read “2 − +” etc. above “discriminant 49”; digits 2, 3, −5, 49 share one right edge.<br/>'
 '2.&nbsp;&nbsp;__kitchen-sink/present: “8.25 % − +”, “95 % − +”; long-suffix rows keep the phrase under the digits; '
 'grid/split sections 17–18 unaffected.<br/>'
 '3.&nbsp;&nbsp;mortgage-calculator/present: pixel-identical to production.', st['body']))

# ---- Status & backlog
S.append(Paragraph('Status and backlog', st['h1']))
rows = [
 ['Stepper/gutter system', 'APPROVED. Implementation session spawned from kazad/instacalc-private:\n“Presentation Mode: stepper/gutter alignment”\n(session_019nXynad6eMijn6rs9y3QzF), branch presentation-stepper-gutter.'],
 ['Unit suffix edge cases', 'Next mock candidate — needs the expanded 65-row __kitchen-sink fixture.'],
 ['Adjacent @hero rows compete', 'Not reproducible on live fixtures (single heroes only); needs expanded fixture.'],
 ['Narrative/note voice inversion', 'Needs test-present fixture content.'],
 ['Parser bugs (heading/LaTeX merges,\n@prefix on negatives, currency decimals)', 'Code fixes, not visual; do in the instacalc-sourced session.'],
]
t = Table(rows, colWidths=[W*0.34, W*0.66])
t.setStyle(TableStyle([
 ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
 ('FONTSIZE', (0,0), (-1,-1), 8.5), ('TEXTCOLOR', (0,0), (-1,-1), INK),
 ('LINEBELOW', (0,0), (-1,-2), 0.25, HexColor('#DDD8C8')),
 ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
 ('LEFTPADDING', (0,0), (-1,-1), 0), ('VALIGN', (0,0), (-1,-1), 'TOP'),
]))
S.append(t)
S.append(Paragraph('Working method (carry forward)', st['h2']))
S.append(Paragraph(
 'The live product is the design language — make small corrections to it, never a new identity. One change at a '
 'time; every proposal is a real screenshot beside the identical content with exactly one thing changed; show one '
 'example and stop for the owner’s reaction. No invented palettes, no monospace numbers, no boxes or chrome the '
 'product doesn’t have.', st['body']))

doc.build(S, onFirstPage=bg, onLaterPages=bg)
print('done')
