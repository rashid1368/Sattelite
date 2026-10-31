# -*- coding: utf-8 -*-
"""Small helpers for editing the v9 thesis body in place (python-docx + lxml)."""
import copy
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def ptext(el):
    return "".join(t.text or "" for t in el.iter(W + "t"))


def runs_rpr_signatures(p_el):
    """Distinct run-property XML strings among the direct runs of a paragraph."""
    sigs = set()
    for r in p_el.findall(W + "r"):
        rp = r.find(W + "rPr")
        from lxml import etree
        sigs.add(etree.tostring(rp) if rp is not None else b"")
    return sigs


def replace_in_text_nodes(p_el, old, new):
    """Replace inside a single w:t node. Returns True when the text was found."""
    done = False
    for t in p_el.iter(W + "t"):
        if t.text and old in t.text:
            t.text = t.text.replace(old, new)
            done = True
    return done


def set_par_text(p_el, new, keep_first_rpr=True):
    """Replace all runs of a paragraph by one run carrying the first run's formatting.
    Bookmarks and paragraph properties are kept. Refuses paragraphs with footnotes."""
    assert next(p_el.iter(W + "footnoteReference"), None) is None, "paragraph has footnotes"
    rpr = None
    first = p_el.find(W + "r")
    if keep_first_rpr and first is not None and first.find(W + "rPr") is not None:
        rpr = copy.deepcopy(first.find(W + "rPr"))
    for child in list(p_el):
        if child.tag in (W + "r", W + "hyperlink"):
            p_el.remove(child)
    r = OxmlElement("w:r")
    if rpr is not None:
        r.append(rpr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = new
    r.append(t)
    p_el.append(r)


def clone_par_after(anchor_el, template_el, text):
    """Insert a copy of template_el (paragraph) after anchor_el with new text."""
    new = copy.deepcopy(template_el)
    # strip bookmarks so that ids stay unique
    for tag in ("w:bookmarkStart", "w:bookmarkEnd"):
        for x in new.findall(qn(tag)):
            new.remove(x)
    set_par_text(new, text)
    anchor_el.addnext(new)
    return new


def find_pars(root_el, prefix=None, contains=None):
    out = []
    for p in root_el.iter(W + "p"):
        t = ptext(p)
        if prefix is not None and not t.strip().startswith(prefix):
            continue
        if contains is not None and contains not in t:
            continue
        out.append(p)
    return out
