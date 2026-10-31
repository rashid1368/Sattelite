# -*- coding: utf-8 -*-
"""Insert Chapter 5 into v8 and save v9 (before the references heading)."""
import copy
import json
import os

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v8_ch1_ch4.docx")
DST = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v9_ch1_ch5.docx")

from ch5_text import C5

d = docx.Document(SRC)
P = d.paragraphs
TPL = dict(h1=P[800], h2=P[801], h3=P[807], fp=P[802], bt=P[803])

BM = [8100]
BOOK = {}


def first_rpr(p_el):
    r = p_el.find(qn("w:r"))
    if r is None:
        return None
    rp = r.find(qn("w:rPr"))
    return copy.deepcopy(rp) if rp is not None else None


def mk_run(text, rpr):
    r = OxmlElement("w:r")
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def strip(el):
    for tag in ("w:bookmarkStart", "w:bookmarkEnd", "w:r", "w:hyperlink"):
        for x in el.findall(qn(tag)):
            el.remove(x)


def next_bookmark():
    BM[0] += 1
    return "_Ref%05d" % BM[0]


def add_bookmark(el, name, at_start=True):
    bid = str(int(name[5:]))
    bs = OxmlElement("w:bookmarkStart")
    bs.set(qn("w:id"), bid)
    bs.set(qn("w:name"), name)
    if at_start:
        el.insert(1, bs)
    else:
        el.append(bs)
    be = OxmlElement("w:bookmarkEnd")
    be.set(qn("w:id"), bid)
    el.append(be)


def clone_par(kind, text):
    el = copy.deepcopy(TPL[kind]._p)
    rpr = first_rpr(el)
    strip(el)
    name = next_bookmark()
    bs = OxmlElement("w:bookmarkStart")
    bs.set(qn("w:id"), str(int(name[5:])))
    bs.set(qn("w:name"), name)
    el.append(bs)
    el.append(mk_run(text, rpr))
    be = OxmlElement("w:bookmarkEnd")
    be.set(qn("w:id"), str(int(name[5:])))
    el.append(be)
    return el, name


def set_text(run_el, s):
    t = run_el.find(qn("w:t"))
    if t is None:
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        run_el.append(t)
    t.text = s


def clone_h1(line1, line2):
    el = copy.deepcopy(TPL["h1"]._p)
    for tag in ("w:bookmarkStart", "w:bookmarkEnd"):
        for x in el.findall(qn(tag)):
            el.remove(x)
    runs = el.findall(qn("w:r"))
    for r in runs:
        for t in r.findall(qn("w:t")):
            r.remove(t)
    set_text(runs[0], line1)
    set_text(runs[2], line2)
    name = next_bookmark()
    bs = OxmlElement("w:bookmarkStart")
    bs.set(qn("w:id"), str(int(name[5:])))
    bs.set(qn("w:name"), name)
    el.insert(1, bs)
    be = OxmlElement("w:bookmarkEnd")
    be.set(qn("w:id"), str(int(name[5:])))
    el.append(be)
    return el, name


def build(blocks):
    out = []
    for b in blocks:
        k = b[0]
        if k == "h1":
            el, name = clone_h1(b[1], b[2])
            BOOK["%s: %s" % (b[1], b[2])] = name
        elif k in ("h2", "h3"):
            el, name = clone_par(k, b[1])
            BOOK[b[1]] = name
        elif k in ("p", "fp"):
            el, _ = clone_par("fp" if k == "fp" else "bt", b[1])
        else:
            raise ValueError("unknown block kind: %s" % k)
        out.append(el)
    return out


def main():
    # references heading: force a page start and drop the two empty spacers
    ref = None
    for p in d.paragraphs:
        if p.style.name == "RefHeadingCenter" and p.text.strip() == "منابع و مأخذ":
            ref = p
            break
    if ref is None:
        raise SystemExit("references heading not found")

    ppr = ref._p.find(qn("w:pPr"))
    if ppr.find(qn("w:pageBreakBefore")) is None:
        pb = OxmlElement("w:pageBreakBefore")
        ppr.insert(0, pb)

    prev = ref._p.getprevious()
    removed = 0
    while prev is not None and removed < 2:
        el = prev
        prev = prev.getprevious()
        if el.tag == qn("w:p") and not "".join(
                el.itertext()).strip():
            el.getparent().remove(el)
            removed += 1
        else:
            break

    for el in build(C5):
        ref._p.addprevious(el)

    d.save(DST)
    with open(os.path.join(ROOT, "_build", "ch5_bookmarks.json"), "w",
              encoding="utf-8") as f:
        json.dump(BOOK, f, ensure_ascii=False, indent=1)
    print("saved", DST)
    print("paragraphs", len(d.paragraphs), "bookmarks", len(BOOK),
          "removed empty", removed)


if __name__ == "__main__":
    main()
