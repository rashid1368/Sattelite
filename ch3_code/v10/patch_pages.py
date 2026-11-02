# -*- coding: utf-8 -*-
"""Fill PAGEREF results (table of contents and lists) with the printed page numbers
measured from a LibreOffice render of the draft. Word refreshes them again on opening
(updateFields is set). Usage: patch_pages.py <draft.docx> <render.pdf>"""
import os, sys, re, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx_util import W, ptext

DRAFT, PDF = sys.argv[1], sys.argv[2]
PHYSICAL = "--physical" in sys.argv  # continuous numbering from page 1 (IranDoc layout)
d = docx.Document(DRAFT)
body = d.element.body

def norm(s):
    return re.sub(r"[^؀-ۿA-Za-z0-9]", "", s)

n_pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout).group(1))
page_text, page_num = {}, {}
for p in range(1, n_pages + 1):
    t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", PDF, "-"], capture_output=True, text=True).stdout
    page_text[p] = norm(t)
    lines = [re.sub(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069]", "", l).strip() for l in t.replace("\f", "").split("\n")]
    lines = [l for l in lines if l]
    num = None
    for l in reversed(lines[-4:]):
        if re.fullmatch(r"[0-9۰-۹]+", l):
            num = int(l.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))); break
    page_num[p] = p if PHYSICAL else num

BODY_FIRST_PAGE = next((p for p in range(1, n_pages + 1) if (PHYSICAL or page_num.get(p) == 1) and page_text[p].startswith("فصلاول")), 15) if PHYSICAL else next((p for p in range(1, n_pages + 1) if page_num.get(p) == 1 and "فصلاول" in page_text[p]), 15)

bm_para = {}
for p in body.iter(W + "p"):
    for b in p.iter(W + "bookmarkStart"):
        bm_para.setdefault(b.get(W + "name"), p)

LAST = [BODY_FIRST_PAGE]
def find_page(bm):
    p_el = bm_para.get(bm)
    if p_el is None:
        return None
    key = norm(ptext(p_el))[:14]
    if len(key) < 3:
        return None
    # headings and captions occur in document order: search forward from the last match first
    if key == norm("چکیده")[:len(key)] and len(key) <= 6:
        for p in range(1, BODY_FIRST_PAGE + 1):
            if page_text[p].startswith(key):
                return page_num.get(p)
    for start in (LAST[0], BODY_FIRST_PAGE):
        for p in range(start, n_pages + 1):
            if key in page_text[p]:
                LAST[0] = p
                return page_num.get(p)
    return None

DIG = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
LASTPAGE = [BODY_FIRST_PAGE]
filled, missing = 0, []
for par in list(body.iter(W + "p")):
    instr = "".join(x.text or "" for x in par.iter(W + "instrText"))
    m = re.search(r"PAGEREF\s+(\S+)", instr)
    if not m:
        continue
    page = find_page(m.group(1))
    if page is None:
        missing.append(m.group(1))
        page = LASTPAGE[0]          # headings are in order: the previous known page is a lower bound
    else:
        LASTPAGE[0] = page
    state, done = 0, False
    for el in par.iter():
        if el.tag == W + "fldChar":
            typ = el.get(W + "fldCharType")
            if typ == "separate": state = 1
            elif typ == "end": state = 0
        elif state == 1 and el.tag == W + "t":
            el.text = str(page).translate(DIG)
            done = True
            break
    filled += done

d.save(DRAFT)
print("page numbers filled:", filled, "missing:", len(missing), missing[:5])
print("body starts at page", BODY_FIRST_PAGE)
