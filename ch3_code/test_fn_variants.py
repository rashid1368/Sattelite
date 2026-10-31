# -*- coding: utf-8 -*-
"""Build footnote-repair variants of the thesis and measure Word's page count.

Each variant rewrites only word/footnotes.xml (and settings/document where the
variant requires it), then opens the result through Word COM and reports
ComputeStatistics(2).
"""
import os
import shutil
import sys
import zipfile

from lxml import etree
import win32com.client as win32

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Haddadi_MSc_thesis_GTO_sail_deorbit_v6_ch1_ch4.docx")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_build", "fn_variants")
os.makedirs(OUT, exist_ok=True)


def rewrite(src, dst, notes_mut=None, doc_mut=None, settings_mut=None):
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/footnotes.xml" and notes_mut:
            data = notes_mut(etree.fromstring(data))
        elif item.filename == "word/document.xml" and doc_mut:
            data = doc_mut(etree.fromstring(data))
        elif item.filename == "word/settings.xml" and settings_mut:
            data = settings_mut(etree.fromstring(data))
        zout.writestr(item, data)
    zout.close()
    zin.close()


def notes_variant(reorder=False, add_ref=False, drop_orphans=False, contiguous=False):
    def mut(root):
        notes = root.findall(W + "footnote")
        if drop_orphans:
            keep = []
            for n in notes:
                if n.get(W + "type") is not None or n.get(W + "id") not in ("329", "357"):
                    keep.append(n)
            for n in notes:
                if n not in keep:
                    root.remove(n)
            notes = keep
        if contiguous:
            real = [n for n in notes if n.get(W + "type") is None]
            for i, n in enumerate(real, start=1):
                n.set(W + "id", str(i))
        if add_ref:
            for n in notes:
                if n.get(W + "type") is not None:
                    continue
                p = n.find(W + "p")
                runs = p.findall(W + "r")
                first = runs[0]
                tr = first.find(W + "t")
                if tr is not None and tr.text and tr.text.strip() in "۰۱۲۳۴۵۶۷۸۹":
                    first.remove(tr)
                r = etree.SubElement(p, W + "r")
                rpr = etree.SubElement(r, W + "rPr")
                rs = etree.SubElement(rpr, W + "rStyle")
                rs.set(W + "val", "FootnoteReference")
                etree.SubElement(r, W + "footnoteRef")
                p.insert(0, r)
        if reorder:
            seps = [n for n in notes if n.get(W + "type") is not None]
            for n in seps:
                root.remove(n)
            for i, n in enumerate(seps):
                root.insert(i, n)
            seps.sort(key=lambda n: int(n.get(W + "id")))
            for i, n in enumerate(seps):
                root.insert(i, n)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return mut


def doc_strip_custom(root):
    for ref in root.iter(W + "footnoteReference"):
        if ref.get(W + "customMarkFollows"):
            del ref.attrib[W + "customMarkFollows"]
            run = ref.getparent()
            nxt = run.getnext()
            if nxt is not None:
                t = nxt.find(W + "t")
                if (t is not None and t.text is not None
                        and t.text.strip() and all(ch in "۰۱۲۳۴۵۶۷۸۹" for ch in t.text.strip())):
                    nxt.getparent().remove(nxt)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def settings_drop_restart(root):
    fp = root.find(W + "footnotePr")
    if fp is not None:
        for el in list(fp):
            fp.remove(el)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def doc_drop_restart(root):
    for sp in root.iter(W + "sectPr"):
        fp = sp.find(W + "footnotePr")
        if fp is not None:
            sp.remove(fp)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def page_count(path):
    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        d = word.Documents.Open(path, ReadOnly=True, AddToRecentFiles=False)
        try:
            n = d.ComputeStatistics(2)
            pages = d.Range().Information(3)
        finally:
            d.Close(False)
        return n, pages
    finally:
        word.Quit()


if __name__ == "__main__":
    variants = {
        "base": {},
        "no_restart": {"doc_mut": doc_drop_restart},
        "sep_order": {"notes_mut": notes_variant(reorder=True)},
        "add_ref": {"notes_mut": notes_variant(add_ref=True), "doc_mut": doc_strip_custom},
        "drop_orphans": {"notes_mut": notes_variant(drop_orphans=True),
                         "doc_mut": doc_strip_custom},
        "clean_all": {"notes_mut": notes_variant(reorder=True, add_ref=True,
                                                 drop_orphans=True, contiguous=True),
                      "doc_mut": doc_strip_custom, "settings_mut": settings_drop_restart},
    }
    want = sys.argv[1:] or list(variants)
    for name in want:
        cfg = variants[name]
        dst = os.path.join(OUT, "v_%s.docx" % name)
        rewrite(SRC, dst, **cfg)
        try:
            n, pages = page_count(dst)
            print("%-14s pages=%-5s lastpage=%s" % (name, n, pages), flush=True)
        except Exception as e:
            print("%-14s ERROR %s" % (name, e), flush=True)
