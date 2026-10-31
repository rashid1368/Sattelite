# -*- coding: utf-8 -*-
"""Final structural patch for v10 (run after build_all.sh):
 1. author-date citations: no comma between author and year (rule: (نام سال، صفحه));
 2. numbered reference list (Persian then English, one sequence);
 3. table of contents: entries for every new heading and for the English front matter,
    bookmarks on those headings, every entry wrapped in an internal hyperlink;
 4. Word is asked to update fields on opening (updateFields).
Reads and writes _build/thesis_v10_draft.docx."""
import os, sys, re, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx_util import W, ptext

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
d = docx.Document(PATH)
body = d.element.body
kids = list(body.iterchildren())

def style(el):
    ps = el.find(W + "pPr")
    if ps is None or ps.find(W + "pStyle") is None:
        return ""
    return ps.find(W + "pStyle").get(W + "val")

BODY0 = next(i for i, k in enumerate(kids) if ptext(k).strip().startswith("فصل اول") and len(ptext(k)) < 40 and i > 200)
REF_H = [i for i, k in enumerate(kids) if ptext(k).strip() == "منابع و مأخذ"][-1]
APP_H = next(i for i, k in enumerate(kids) if ptext(k).strip().startswith("پیوست الف:") )

# 1. citations: "(نام سال" -> "(نام سال" for author-date references in the chapters
pat = re.compile(r"\(([^()\d]{2,40}?)[،,]\s*(?=[۰-۹0-9]{4})")
n_cit = 0
for k in kids[BODY0:REF_H]:
    for t in k.iter(W + "t"):
        if t.text and "(" in t.text:
            new = pat.sub(lambda m: m.group(0) if m.group(1).strip().startswith("مأخذ") else "(" + m.group(1) + " ", t.text)
            if new != t.text:
                n_cit += 1
                t.text = new
print("citation nodes changed:", n_cit)

# 2. numbered references
def digits_fa(n):
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
num = 0
for k in kids[REF_H + 1:APP_H]:
    if style(k) in ("RefBodyFa", "RefEN"):
        num += 1
        r = OxmlElement("w:r")
        t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = digits_fa(num) + ". "
        r.append(t)
        ppr = k.find(qn("w:pPr"))
        idx = 1 if ppr is not None else 0
        k.insert(idx, r)
print("references numbered:", num)

# 3. bookmarks and TOC
def max_ref():
    m = 0
    for b in body.iter(W + "bookmarkStart"):
        nm = b.get(W + "name") or ""
        mm = re.match(r"_Ref(\d+)$", nm)
        if mm: m = max(m, int(mm.group(1)))
    return m
_next = [max_ref() + 1000]
bid = [max(int(b.get(W + "id") or 0) for b in body.iter(W + "bookmarkStart")) + 1]

def ensure_bookmark(p):
    for b in p.iter(W + "bookmarkStart"):
        return b.get(W + "name")
    name = "_Ref%d" % _next[0]; _next[0] += 1
    bs = OxmlElement("w:bookmarkStart"); bs.set(qn("w:id"), str(bid[0])); bs.set(qn("w:name"), name)
    be = OxmlElement("w:bookmarkEnd"); be.set(qn("w:id"), str(bid[0])); bid[0] += 1
    ppr = p.find(qn("w:pPr"))
    if ppr is not None: ppr.addnext(bs)
    else: p.insert(0, bs)
    p.append(be)
    return name

def norm(s):
    return re.sub(r"[^؀-ۿA-Za-z0-9]", "", s)

HEAD = {"Heading11": 0, "Heading21": 1, "Heading31": 2, "RefHeadingCenter": 0}
headings = [k for k in kids[BODY0:] if style(k) in HEAD and ptext(k).strip()]
# front matter / English items without heading style
eng_title = next(k for k in kids if ptext(k).strip().startswith("ISLAMIC AZAD"))
extra = [(eng_title, 0, "صفحه‌ی عنوان انگلیسی")]

toc = [k for k in kids[:BODY0] if style(k) == "TocEntry"]
def toc_key(p):
    t = ptext(p)
    t = re.sub(r"[0-9۰-۹]+\s*$", "", t)
    return norm(t)

# ensure toc entry template
TEMPLATE = toc[0]
def make_entry(text_title, level, bm):
    p = OxmlElement("w:p")
    ppr = copy.deepcopy(TEMPLATE.find(qn("w:pPr")))
    p.append(ppr)
    def run_text(txt):
        r = OxmlElement("w:r"); t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = txt; r.append(t); return r
    def fld(kind):
        r = OxmlElement("w:r"); f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), kind); r.append(f); return r
    indent = " " * (4 * level)
    p.append(run_text(indent + text_title))
    r = OxmlElement("w:r"); r.append(OxmlElement("w:tab")); p.append(r)
    p.append(fld("begin"))
    r = OxmlElement("w:r"); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGEREF %s \\h " % bm; r.append(it); p.append(r)
    p.append(fld("separate"))
    p.append(run_text("0"))
    p.append(fld("end"))
    return p

existing_keys = {toc_key(p): p for p in toc}
last = None
added = 0
for h in headings + [x[0] for x in extra]:
    if h in [x[0] for x in extra]:
        level, title = 0, "صفحه‌ی عنوان انگلیسی"
    else:
        level = HEAD[style(h)]
        title = ptext(h).strip()
    key = norm(title)
    match = None
    for tk, tp in existing_keys.items():
        if tk and key and (tk == key or key.startswith(tk) or tk.startswith(key)):
            match = tp; break
    if match is not None and match is not None:
        last = match
        continue
    bm = ensure_bookmark(h)
    entry = make_entry(title, level, bm)
    if last is None:
        raise SystemExit("no anchor for new entry: " + title[:30])
    last.addnext(entry)
    last = entry
    added += 1
print("toc entries added:", added)

# bookmarks for the entries that exist already: keep PAGEREF target; make the wrapper hyperlinks
def instr_bm(p):
    for it in p.iter(W + "instrText"):
        m = re.search(r"PAGEREF\s+(\S+)", it.text or "")
        if m: return m.group(1)
    return None

wrapped = 0
for p in [k for k in body.iterchildren() if k.tag == W + "p" and style(k) == "TocEntry"]:
    bm = instr_bm(p)
    if not bm or p.find(qn("w:hyperlink")) is not None:
        continue
    hl = OxmlElement("w:hyperlink"); hl.set(qn("w:anchor"), bm); hl.set(qn("w:history"), "1")
    for child in list(p):
        if child.tag == qn("w:pPr"): continue
        p.remove(child); hl.append(child)
    p.append(hl); wrapped += 1
print("toc entries wrapped:", wrapped)

# 4a. the section 4-7-1 heading was cloned from a level-2 heading; make it level 3
for k in body.iterchildren():
    if k.tag == W + "p" and ptext(k).strip().startswith("۴-۷-۱ تحلیل جاروب") and k.find(W+"pPr") is not None:
        ps = k.find(W+"pPr").find(W+"pStyle")
        if ps is not None: ps.set(W+"val", "Heading31")

# 4. ask Word to update fields on open
settings = d.settings.element
if settings.find(qn("w:updateFields")) is None:
    uf = OxmlElement("w:updateFields"); uf.set(qn("w:val"), "true")
    settings.insert(0, uf)

d.save(PATH)
print("saved", PATH)
