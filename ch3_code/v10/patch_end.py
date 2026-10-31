# -*- coding: utf-8 -*-
"""End matter for v10: Appendix A (Python code with syntax colours), the English
abstract, and the English title page. Reads and writes the v10 draft."""
import os, sys, io, keyword, builtins, tokenize, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx_util import W, ptext, set_par_text

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
CODE_DIR = os.path.join(ROOT, "ch3_code")
d = docx.Document(PATH)
body = d.element.body
kids = list(body.iterchildren())
sect = body.find(qn("w:sectPr"))

def find(prefix, last=False):
    hits = [k for k in kids if ptext(k).strip().startswith(prefix)]
    assert hits, prefix
    return hits[-1] if last else hits[0]

H1 = find("فصل سوم", last=True)
H2 = find("۵-۲-۱ فرضیه‌ی اول", last=True)
BODY = find("پیامد طراحی این یافته")

def append(el):
    sect.addprevious(el)
    return el

def ppr_set(p, bidi=None, jc=None, shd=None, space_after=None, space_before=None, line=None, page_break=False, keep=False):
    pPr = p.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr"); p.insert(0, pPr)
    for tag in ("w:pageBreakBefore", "w:keepNext", "w:shd", "w:spacing", "w:bidi", "w:jc"):
        for x in pPr.findall(qn(tag)):
            pPr.remove(x)
    if page_break:
        pPr.append(OxmlElement("w:pageBreakBefore"))
    if keep:
        pPr.append(OxmlElement("w:keepNext"))
    if shd:
        e = OxmlElement("w:shd"); e.set(qn("w:val"), "clear"); e.set(qn("w:color"), "auto"); e.set(qn("w:fill"), shd); pPr.append(e)
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:before"), str(space_before if space_before is not None else 0))
    sp.set(qn("w:after"), str(space_after if space_after is not None else 0))
    sp.set(qn("w:line"), str(line if line is not None else 240)); sp.set(qn("w:lineRule"), "auto")
    pPr.append(sp)
    if bidi is not None:
        b = OxmlElement("w:bidi"); b.set(qn("w:val"), "1" if bidi else "0"); pPr.append(b)
    if jc:
        j = OxmlElement("w:jc"); j.set(qn("w:val"), jc); pPr.append(j)
    return p

def run(text, color=None, bold=False, italic=False, font=None, size=None):
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    if font:
        rf = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            rf.set(qn(a), font)
        rPr.append(rf)
    if bold:
        rPr.append(OxmlElement("w:b"))
    if italic:
        rPr.append(OxmlElement("w:i"))
    if color:
        c = OxmlElement("w:color"); c.set(qn("w:val"), color); rPr.append(c)
    if size:
        s = OxmlElement("w:sz"); s.set(qn("w:val"), str(size)); rPr.append(s)
        s2 = OxmlElement("w:szCs"); s2.set(qn("w:val"), str(size)); rPr.append(s2)
    r.append(rPr)
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
    r.append(t)
    return r

def new_par(runs, **kw):
    p = OxmlElement("w:p")
    ppr_set(p, **kw)
    for r in runs:
        p.append(r)
    return p

# ---------- colouring of Python source (IDLE/VS Code-like palette) ----------
COL = {"kw": "0000FF", "builtin": "267F99", "str": "A31515", "com": "008000",
       "num": "098658", "def": "795E26", "op": "000000", "plain": "000000"}
BUILTINS = set(dir(builtins))

def colorize(src):
    lines = src.split("\n")
    segs = {i: [] for i in range(len(lines))}     # list of (col_start, col_end, kind)
    prev = None
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    for tok in toks:
        if tok.type in (tokenize.ENCODING, tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER,
                        tokenize.INDENT, tokenize.DEDENT):
            continue
        (sr, sc), (er, ec) = tok.start, tok.end
        if tok.type == tokenize.COMMENT: kind = "com"
        elif tok.type == tokenize.STRING: kind = "str"
        elif tok.type == tokenize.NUMBER: kind = "num"
        elif tok.type == tokenize.NAME:
            if keyword.iskeyword(tok.string): kind = "kw"
            elif prev in ("def", "class"): kind = "def"
            elif tok.string in BUILTINS: kind = "builtin"
            else: kind = "plain"
        elif tok.type == tokenize.OP: kind = "op"
        else: kind = "plain"
        if tok.type != tokenize.COMMENT:
            prev = tok.string
        for r in range(sr, er + 1):
            a = sc if r == sr else 0
            b = ec if r == er else len(lines[r - 1]) + 0
            if r - 1 < len(lines) and b > a:
                segs[r - 1].append((a, b, kind))
    out = []
    for i, line in enumerate(lines):
        pieces, pos = [], 0
        for a, b, kind in sorted(segs[i]):
            if a > pos:
                pieces.append((line[pos:a], "plain"))
            if b > a and a >= pos:
                pieces.append((line[a:b], kind)); pos = b
        if pos < len(line):
            pieces.append((line[pos:], "plain"))
        out.append(pieces or [("", "plain")])
    return out

def code_paragraphs(path):
    src = open(path, encoding="utf8").read()
    res = []
    for pieces in colorize(src):
        runs = []
        for text, kind in pieces:
            if text == "":
                continue
            runs.append(run(text, color=COL[kind], bold=(kind in ("kw", "def")), italic=(kind == "com"),
                            font="Consolas", size=16))
        if not runs:
            runs.append(run(" ", font="Consolas", size=16))
        res.append(new_par(runs, bidi=False, jc="left", shd="F4F4F4", line=228))
    return res

# ---------- Appendix A ----------
app_h = copy.deepcopy(H1._p if hasattr(H1, "_p") else H1)
for x in list(app_h):
    if x.tag != qn("w:pPr"):
        app_h.remove(x)
set_par_text(app_h, "پیوست الف: کد پایتون شبیه‌سازی")
ppr_set(app_h, bidi=True, jc="center", page_break=True, keep=True)
append(app_h)
intro = clone_body = copy.deepcopy(BODY)
for x in list(intro):
    if x.tag == qn("w:r") or x.tag == qn("w:bookmarkStart") or x.tag == qn("w:bookmarkEnd"):
        intro.remove(x)
set_par_text(intro, ("کد زیر تمام معادله‌های حرکت، مدل جو، مدل پسا و رخداد عمر را پیاده‌سازی می‌کند. همه‌ی محاسبه‌های این "
                     "پایان‌نامه با پایتون انجام شده‌اند؛ اجراهای فصل سوم و چهارم با همین فایل‌ها و کتابخانه‌های NumPy و SciPy "
                     "تولید شده‌اند. نسخه‌ی کد در مخزن پژوهش نگه‌داری می‌شود."))
append(intro)

FILES = [("full_prop.py", "الف-۱: full_prop.py (انتشار عددی کامل: مدل A)"),
         ("decay_sim.py", "الف-۲: decay_sim.py (ثابت‌ها، مدل B، تعریف عمر)"),
         ("nrlmsis_atm.py", "الف-۳: nrlmsis_atm.py (جدول چگالی NRLMSIS 2.0)"),
         ("run_cases.py", "الف-۴: run_cases.py (اجرای حالت‌های مرجع)")]
for fname, title in FILES:
    h = copy.deepcopy(H2)
    for x in list(h):
        if x.tag != qn("w:pPr"):
            h.remove(x)
    set_par_text(h, title)
    append(h)
    for cp in code_paragraphs(os.path.join(CODE_DIR, fname)):
        append(cp)
    append(new_par([run(" ")], bidi=False))

# ---------- English abstract (new page) ----------
ABSTRACT_EN = (
    "Upper stages left in geostationary transfer orbit (GTO) after satellite separation can remain in orbit for "
    "decades, because their perigee is close to 250 km. This study evaluates whether such a stage can be disposed of "
    "passively with a small-satellite drag sail. The work is a numerical simulation. Model A integrates the full "
    "equations of motion with Earth oblateness (J2), atmospheric drag, lunar and solar third-body perturbations and "
    "solar radiation pressure; Model B is an orbit-averaged model with drag only. Entry geometries are sampled with a "
    "sixteen-point Latin hypercube in argument of perigee and right ascension of the ascending node, and the sail area "
    "is varied from 40 to 400 m². Lifetime is the time of first perigee passage below 120 km, found with a perigee-based "
    "event function. The atmosphere is an exponential profile, compared with NRLMSIS 2.0 through pymsis (F10.7 = 130, "
    "Ap = 10). The code is written in Python with NumPy and SciPy and uses the DOP853 integrator with relative tolerance "
    "1e-9. Without a sail, 5 of the 16 geometries reach 120 km within 25 years, and a drag-only model overestimates the "
    "reference lifetime about eight times. With a 140 m² sail, 15 geometries comply with the exponential model and 14 "
    "with NRLMSIS. Lifetime is not a monotonic function of sail area, and the atmosphere model reverses the compliance "
    "verdict for some areas. The results should therefore be reported as a distribution over entry geometry and "
    "atmosphere model, which is relevant to domestic upper-stage design and to the 25-year disposal rule."
)
KEYWORDS_EN = "Keywords: passive deorbit; drag sail; geostationary transfer orbit; upper stage; orbital lifetime; NRLMSIS 2.0"

hab = copy.deepcopy(H1)
for x in list(hab):
    if x.tag != qn("w:pPr"):
        hab.remove(x)
set_par_text(hab, "Abstract")
ppr_set(hab, bidi=False, jc="center", page_break=True, keep=True)
append(hab)
append(new_par([run(ABSTRACT_EN, font="Times New Roman", size=24)], bidi=False, jc="both", line=276, space_after=160))
append(new_par([run(KEYWORDS_EN, font="Times New Roman", size=24, italic=True)], bidi=False, jc="left", line=276))

# ---------- English title page (new page) ----------
TITLE_LINES = [
    ("ISLAMIC AZAD UNIVERSITY", True, 28), ("SCIENCE AND RESEARCH BRANCH", True, 24),
    ("Faculty of ......... - Department of .........", False, 24),
    ("Thesis for receiving «M.Sc» degree on .........", False, 24),
    ("Subject:", False, 24),
    ("Computational Design and Implementation of a Small-Satellite Drag-Sail Method for Passive Disposal of "
     "Spacecraft Separation Stages in a Geostationary Transfer Orbit", True, 26),
    ("Thesis Advisor:", False, 24), ("A. Mahmoudi Ph.D.", False, 24),
    ("Consulting Advisor:", False, 24), ("A. H. Hashemian Ph.D.", False, 24),
    ("By:", False, 24), ("Mohammad Haddadi", False, 24),
    ("Autumn 2026", False, 24),
]
first = True
for text, bold, size in TITLE_LINES:
    append(new_par([run(text, font="Times New Roman", bold=bold, size=size)], bidi=False, jc="center",
                   page_break=first, space_before=120, line=276))
    first = False

d.save(PATH)
print("saved", PATH)
