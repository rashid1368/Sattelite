# -*- coding: utf-8 -*-
"""Insert the completed Chapter 3 sections and the new Chapter 4 into the thesis.

Chapter 3 patches: the two open validation sections (T7 density, T8 ALE-1) are
filled in, the sensitivity base point is aligned with the runs, and Table 3-5 is
updated.  Chapter 4 is built from the run logs under ch3_code/logs.
"""
import copy
import json
import os

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v5_ch1_ch3.docx")
FIGS = os.path.join(ROOT, "_build", "figs_ch4")

d = docx.Document(DOC)
P = d.paragraphs
TPL = dict(h1=P[655], h2=P[656], h3=P[665], fp=P[657], bt=P[658],
           cap=P[660], fig=P[669])


# ---------------------------------------------------------------- xml helpers
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


BM = [7000]


def clone_par(kind, text):
    tpl = TPL[kind]._p
    rpr = first_rpr(tpl)
    el = copy.deepcopy(tpl)
    strip(el)
    BM[0] += 1
    bs = OxmlElement("w:bookmarkStart")
    bs.set(qn("w:id"), str(BM[0]))
    bs.set(qn("w:name"), "_Ref%05d" % BM[0])
    el.append(bs)
    el.append(mk_run(text, rpr))
    be = OxmlElement("w:bookmarkEnd")
    be.set(qn("w:id"), str(BM[0]))
    el.append(be)
    return el


def clone_h1(line1, line2):
    tpl = TPL["h1"]._p
    el = copy.deepcopy(tpl)
    for tag in ("w:bookmarkStart", "w:bookmarkEnd"):
        for x in el.findall(qn(tag)):
            el.remove(x)
    runs = el.findall(qn("w:r"))
    for i, r in enumerate(runs):
        for t in r.findall(qn("w:t")):
            r.remove(t)
    # runs[0]: "فصل چهارم" (underlined), runs[1]: <w:br/>, runs[2]: title
    _set_text(runs[0], line1)
    _set_text(runs[2], line2)
    BM[0] += 1
    bs = OxmlElement("w:bookmarkStart")
    bs.set(qn("w:id"), str(BM[0]))
    bs.set(qn("w:name"), "_Ref%05d" % BM[0])
    el.insert(1, bs)
    be = OxmlElement("w:bookmarkEnd")
    be.set(qn("w:id"), str(BM[0]))
    el.append(be)
    return el


def _text(s):
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = s
    return t


def _set_text(run_el, s):
    t = run_el.find(qn("w:t"))
    if t is None:
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        run_el.append(t)
    t.text = s


def fig_par(path, width_cm):
    el = copy.deepcopy(TPL["fig"]._p)
    for tag in ("w:bookmarkStart", "w:bookmarkEnd"):
        for x in el.findall(qn(tag)):
            el.remove(x)
    rId, image = d.part.get_or_add_image(os.path.join(FIGS, path))
    blip = el.find(".//" + qn("a:blip"))
    blip.set(qn("r:embed"), rId)
    cx = int(Cm(width_cm))
    cy = int(cx * image.px_height / image.px_width)
    for e in el.iter(qn("wp:extent")):
        e.set("cx", str(cx))
        e.set("cy", str(cy))
    for xfrm in el.iter(qn("a:xfrm")):
        e = xfrm.find(qn("a:ext"))
        e.set("cx", str(cx))
        e.set("cy", str(cy))
    BM[0] += 1
    for dp in el.iter(qn("wp:docPr")):
        dp.set("id", str(BM[0]))
    return el


def tc(text, width, align, header):
    cell = OxmlElement("w:tc")
    pr = OxmlElement("w:tcPr")
    if header:
        bd = OxmlElement("w:tcBorders")
        b = OxmlElement("w:bottom")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "6")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        bd.append(b)
        pr.append(bd)
    va = OxmlElement("w:vAlign")
    va.set(qn("w:val"), "center")
    pr.append(va)
    tcw = OxmlElement("w:tcW")
    tcw.set(qn("w:w"), str(width))
    tcw.set(qn("w:type"), "dxa")
    pr.append(tcw)
    cell.append(pr)
    p = OxmlElement("w:p")
    ppr = OxmlElement("w:pPr")
    ps = OxmlElement("w:pStyle")
    ps.set(qn("w:val"), "Compact")
    ppr.append(ps)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "left" if (header or align == "l") else "center")
    ppr.append(jc)
    p.append(ppr)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rpr.append(OxmlElement("w:rtl"))
    r.append(rpr)
    r.append(_text(text))
    p.append(r)
    cell.append(p)
    return cell


def make_table(headers, rows, widths, aligns):
    tbl = OxmlElement("w:tbl")
    pr = OxmlElement("w:tblPr")
    st = OxmlElement("w:tblStyle")
    st.set(qn("w:val"), "Table")
    pr.append(st)
    pr.append(OxmlElement("w:bidiVisual"))
    w = OxmlElement("w:tblW")
    w.set(qn("w:w"), "5000")
    w.set(qn("w:type"), "pct")
    pr.append(w)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "start")
    pr.append(jc)
    bds = OxmlElement("w:tblBorders")
    for side, val in (("top", "single"), ("left", "nil"), ("bottom", "single"),
                      ("right", "nil"), ("insideH", "nil"), ("insideV", "nil")):
        b = OxmlElement("w:" + side)
        b.set(qn("w:val"), val)
        b.set(qn("w:sz"), "12")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        bds.append(b)
    pr.append(bds)
    look = OxmlElement("w:tblLook")
    for k, v in (("firstRow", "1"), ("lastRow", "0"), ("firstColumn", "0"),
                 ("lastColumn", "0"), ("noHBand", "0"), ("noVBand", "0")):
        look.set(qn("w:" + k), v)
    look.set(qn("w:val"), "0020")
    pr.append(look)
    tbl.append(pr)
    grid = OxmlElement("w:tblGrid")
    for wd in widths:
        g = OxmlElement("w:gridCol")
        g.set(qn("w:w"), str(wd))
        grid.append(g)
    tbl.append(grid)
    tr = OxmlElement("w:tr")
    trp = OxmlElement("w:trPr")
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trp.append(th)
    tr.append(trp)
    for h, wd in zip(headers, widths):
        tr.append(tc(h, wd, "c", True))
    tbl.append(tr)
    for row in rows:
        tr = OxmlElement("w:tr")
        for i, (v, wd) in enumerate(zip(row, widths)):
            tr.append(tc(v, wd, aligns[i], False))
        tbl.append(tr)
    return tbl


# bare figure without a caption paragraph is not used; caption is separate
def build(blocks):
    out = []
    for b in blocks:
        k = b[0]
        if k == "h1":
            out.append(clone_h1(b[1], b[2]))
        elif k in ("h2", "h3"):
            out.append(clone_par(k, b[1]))
        elif k in ("p", "fp"):
            out.append(clone_par("fp" if k == "fp" else "bt", b[1]))
        elif k == "cap":
            out.append(clone_par("cap", b[1]))
        elif k == "fig":
            out.append(fig_par(b[1], b[2]))
        elif k == "table":
            _, caption, headers, rows, widths, aligns = b
            out.append(clone_par("cap", caption))
            out.append(make_table(headers, rows, widths, aligns))
            # an empty spacer paragraph after the table keeps Word from merging
            out.append(clone_par("bt", ""))
    return out


# ---------------------------------------------------------------- ALE numbers
def ale():
    p = os.path.join(ROOT, "ch3_code", "logs", "t8_ale1.jsonl")
    rec = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf8"):
            if line.strip():
                r = json.loads(line)
                rec[r["tag"]] = r
    def g(tag, key, fmt="%.1f"):
        r = rec.get(tag)
        if not r or r.get(key) is None:
            return "—"
        return fmt % r[key]
    return g


G = ale()
NOM90 = G("ale1_nominal_f107_90", "t400_days")
NOM130 = G("ale1_nominal_f107_130", "t400_days")
FLY90 = G("ale1_asflown_f107_90", "t400_days")
FLY130 = G("ale1_asflown_f107_130", "t400_days")
print("ALE:", NOM90, NOM130, FLY90, FLY130)


# --------------------------------------------------------------------- patches
from ch4_text import (CH3_APPEND, CH3_REPLACE, CH3_TEXT, CH3_AFTER_765,
                      C4, TABLE35)


def set_text(p_el, text):
    rpr = first_rpr(p_el)
    for tag in ("w:r", "m:oMath", "m:oMathPara"):
        for x in p_el.findall(qn(tag)):
            p_el.remove(x)
    run = mk_run(text, rpr)
    be = p_el.find(qn("w:bookmarkEnd"))
    if be is not None:
        be.addprevious(run)
    else:
        p_el.append(run)


def append_text(p_el, text):
    rpr = first_rpr(p_el)
    run = mk_run(text, rpr)
    be = p_el.find(qn("w:bookmarkEnd"))
    if be is not None:
        be.addprevious(run)
    else:
        p_el.append(run)


def cell_text(cell, text):
    for p in cell.paragraphs:
        set_text(p._p, text)
        return
    p = cell.add_paragraph()
    set_text(p._p, text)


def main():
    # 1) chapter 3 paragraph patches
    for i, t in CH3_TEXT.items():
        append_text(P[i]._p, "")  # keep run order stable
        set_text(P[i]._p, P[i].text.replace(
            "توصیف شده است؛ نتیجه‌ی عددی آن هنوز گزارش نشده است.", t))
    for i, t in CH3_APPEND.items():
        append_text(P[i]._p, t)
    for i, t in CH3_REPLACE.items():
        set_text(P[i]._p, t)

    # 2) table 3-5
    t5 = d.tables[10]
    for row_idx, vals in TABLE35.items():
        for c, v in zip(range(1, 5), vals):
            cell_text(t5.rows[row_idx].cells[c], v)

    # 3) new section 3-9-3 material before the 3-9-4 heading
    anchor = P[766]._p
    for el in build(list(CH3_AFTER_765)):
        anchor.addprevious(el)

    # 4) chapter 4 before the references
    ref = None
    for p in d.paragraphs:
        if p.text.strip() == "منابع و مأخذ":
            ref = p._p
            break
    if ref is None:
        raise SystemExit("references anchor not found")
    for el in build(C4):
        ref.addprevious(el)

    out = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v6_ch1_ch4.docx")
    d.save(out)
    print("saved", out, "paragraphs", len(d.paragraphs), "tables", len(d.tables))


if __name__ == "__main__":
    main()
