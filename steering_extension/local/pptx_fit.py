"""Post-process a deck built by ~/bin/md2pptx so each markdown heading is one slide and its tables fit.

pandoc puts every table on its own "content with caption" slide and moves the bullets after it to another slide.
This pass merges those continuation slides back onto the heading slide, lays out title / intro text / table(s) /
bullets top to bottom (two tables go side by side), sizes columns to their content, and steps the body and table
fonts down (14/13 pt first, 9/8 pt last) until the estimated layout fits the slide. Slides without tables are
left as pandoc made them.

Usage (python-pptx is not in the project venv; run it ephemerally):
  ~/bin/md2pptx steering_extension/docs/week7_deck.md
  uv run --with python-pptx python3 steering_extension/local/pptx_fit.py steering_extension/docs/week7_deck.pptx steering_extension/docs/week7_deck.pptx
"""
import sys, copy
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import MSO_AUTO_SIZE

SRC, OUT = sys.argv[1], sys.argv[2]
P = Presentation(SRC)
W, H = P.slide_width, P.slide_height
IN = 914400

def is_title(sh):
    return sh.is_placeholder and sh.placeholder_format.type in (1, 3)  # TITLE, CENTER_TITLE

def set_font(tf, pt, bold=None):
    for p in tf.paragraphs:
        for r in p.runs:
            r.font.size = Pt(pt)
            if bold is not None: r.font.bold = bold
        p.space_after = Pt(2); p.space_before = Pt(0)

def fit_table(gf, left, top, width, pt):
    t = gf.table
    gf.left, gf.top = left, top
    ncol = len(t.columns)
    # column widths proportional to longest cell text, min share
    lens = []
    for ci in range(ncol):
        lens.append(max(len(t.cell(ri, ci).text) for ri in range(len(t.rows))))
    lens = [max(l, 14) for l in lens]
    tot = sum(lens)
    for ci, c in enumerate(t.columns):
        c.width = int(width * lens[ci] / tot)
    gf.width = width
    for row in t.rows:
        row.height = Inches(0.28)
        for c in row.cells:
            c.margin_left = c.margin_right = Inches(0.04); c.margin_top = c.margin_bottom = Inches(0.015)
            set_font(c.text_frame, pt)
    # estimated rendered height: rows * (lines * pt*1.25 + margins)
    est = 0
    for ri, row in enumerate(t.rows):
        maxlines = 1
        for ci in range(ncol):
            cw_in = t.columns[ci].width / IN - 0.08
            chars_per_line = max(1, int(cw_in * 72 / (pt * 0.52)))
            txt = t.cell(ri, ci).text
            maxlines = max(maxlines, -(-len(txt) // chars_per_line))
        est += max(maxlines * pt * 1.35 / 72 + 0.06, 0.25)
    return Inches(est)

def text_height(sh, width_in, pt):
    n = 0
    for p in sh.text_frame.paragraphs:
        chars = sum(len(r.text) for r in p.runs)
        cpl = max(1, int(width_in * 72 / (pt * 0.5)))
        n += max(1, -(-chars // cpl))
    return Inches(n * pt * 1.3 / 72 + 0.1)

# group slides: a slide with a non-empty title starts a group
slides = list(P.slides)
groups, cur = [], None
for s in slides:
    titles = [sh for sh in s.shapes if is_title(sh) and sh.has_text_frame and sh.text_frame.text.strip()]
    if titles or cur is None:
        cur = [s]; groups.append(cur)
    else:
        cur.append(s)

to_delete = []
for g in groups:
    base = g[0]
    if len(g) == 1 and not any(sh.has_table for sh in base.shapes):
        continue
    title = next((sh for sh in base.shapes if is_title(sh)), None)
    blocks = []  # (kind, shape) in document order
    for s in g:
        for sh in s.shapes:
            if sh is title or (is_title(sh)): continue
            if sh.has_table: blocks.append(('table', sh))
            elif sh.has_text_frame and sh.text_frame.text.strip(): blocks.append(('text', sh))
    # move shapes from continuation slides onto base
    spTree = base.shapes._spTree
    moved = []
    for kind, sh in blocks:
        if sh.part is base.part:
            moved.append((kind, sh))
        else:
            el = copy.deepcopy(sh._element)
            spTree.append(el)
            moved.append((kind, base.shapes[-1]))
    for s in g[1:]: to_delete.append(s)
    def layout(body_pt, tpt):
        margin = Inches(0.4); width = W - 2 * margin
        y = Inches(0.15)
        if title is not None:
            title.left, title.top, title.width, title.height = margin, y, width, Inches(0.65)
            set_font(title.text_frame, 26); title.text_frame.word_wrap = True
            y += Inches(0.72)
        tables = [b for b in moved if b[0] == 'table']
        first_table_idx = next((i for i, b in enumerate(moved) if b[0] == 'table'), len(moved))
        intro = [b[1] for b in moved[:first_table_idx]]
        after = [b[1] for b in moved[first_table_idx:] if b[0] == 'text']
        for sh in intro:
            sh.left, sh.top, sh.width = margin, y, width
            set_font(sh.text_frame, body_pt); sh.text_frame.word_wrap = True; sh.text_frame.auto_size = MSO_AUTO_SIZE.NONE
            h = text_height(sh, width / IN, body_pt); sh.height = h; y += h + Inches(0.05)
        if len(tables) == 2:
            gap = Inches(0.2); w1 = int((width - gap) * 0.5); w2 = width - gap - w1
            last_tab = max(i for i, b2 in enumerate(moved) if b2[0] == 'table')
            mid = [b[1] for i, b in enumerate(moved) if b[0] == 'text' and first_table_idx < i < last_tab]
            ytab = y
            if mid:
                m = mid[0]; m.left, m.top, m.width = margin + w1 + gap, y, w2
                set_font(m.text_frame, body_pt - 2); m.text_frame.word_wrap = True; m.height = Inches(0.4)
                after = [a for a in after if a is not m]; ytab2 = y + Inches(0.42)
            else: ytab2 = y
            h1 = fit_table(tables[0][1], margin, ytab, w1, tpt)
            h2 = fit_table(tables[1][1], margin + w1 + gap, ytab2, w2, tpt)
            y = max(ytab + h1, ytab2 + h2) + Inches(0.22)
        elif tables:
            h = fit_table(tables[0][1], margin, y, width, tpt); y += h + Inches(0.22)
        for sh in after:
            sh.left, sh.top, sh.width = margin, y, width
            set_font(sh.text_frame, body_pt); sh.text_frame.word_wrap = True; sh.text_frame.auto_size = MSO_AUTO_SIZE.NONE
            h = text_height(sh, width / IN, body_pt)
            sh.height = max(h, H - y - Inches(0.1)) if sh is after[-1] else h
            y += h + Inches(0.05)
        return y
    steps = [(14, 13), (14, 12), (13, 12), (13, 11), (13, 10), (12, 10), (12, 9), (11, 9), (11, 8), (10, 8), (9, 8)]
    for body_pt, tpt in steps:
        y = layout(body_pt, tpt)
        if y <= H - Inches(0.08): break
    print(f'{(title.text_frame.text[:36] if title else "?"):38s} body={body_pt} table={tpt} est_bottom={y / IN:.2f} in', file=sys.stderr)

# delete continuation slides
sldIdLst = P.slides._sldIdLst
for s in to_delete:
    for sldId in list(sldIdLst):
        if P.part.related_part(sldId.rId) is s.part:
            P.part.drop_rel(sldId.rId); sldIdLst.remove(sldId)
P.save(OUT)
print('slides', len(P.slides))
