# -*- coding: utf-8 -*-
"""Repair the thesis footnotes so Word 2021 paginates the whole document.

The source file marks footnotes with `<w:footnoteReference w:customMarkFollows="1"/>`
followed by a hand-typed Persian digit.  Word 2021 stops laying the document out at
the first pages when it meets that construct (17 pages instead of ~125), while other
viewers tolerate it.  The repair:

  1. drops `customMarkFollows` and adds a hidden real `<w:footnoteReference>`, so the
     mark Word generates is present but invisible;
  2. inserts a hidden `<w:footnoteRef/>` at the start of each footnote, keeping the
     hand-typed Persian digit as the visible mark (Word's automatic numbering cannot
     emit Persian digits);
  3. renumbers the visible Persian digits per page, using Word's own layout, so the
     per-page sequence stays correct after the Chapter 3/4 edits.

Usage:
    python fix_footnotes.py in.docx out.docx
"""
import io
import os
import shutil
import sys
import tempfile
import zipfile
from collections import defaultdict

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def fa_num(n):
    return "".join(FA_DIGITS[int(c)] for c in str(n))


def _serialize(root):
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _rewrite_zip(src, dst, document=None, footnotes=None):
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/document.xml" and document is not None:
            data = document
        elif item.filename == "word/footnotes.xml" and footnotes is not None:
            data = footnotes
        zout.writestr(item, data)
    zout.close()
    zin.close()


def _digit_run_after(ref):
    run = ref.getparent()
    nxt = run.getnext()
    if nxt is None or nxt.tag != W + "r":
        return None
    t = nxt.find(W + "t")
    if t is None or t.text is None:
        return None
    txt = t.text.strip()
    if not txt or any(ch not in FA_DIGITS for ch in txt):
        return None
    return nxt


def structure_repair(src, dst):
    zin = zipfile.ZipFile(src)
    doc = etree.fromstring(zin.read("word/document.xml"))
    notes = etree.fromstring(zin.read("word/footnotes.xml"))
    zin.close()

    refs = list(doc.iter(W + "footnoteReference"))
    ref_ids = {int(r.get(W + "id")) for r in refs}

    for ref in refs:
        if ref.get(W + "customMarkFollows") is not None:
            del ref.attrib[W + "customMarkFollows"]
        run = ref.getparent()
        rpr = run.find(W + "rPr")
        if rpr is None:
            rpr = etree.Element(W + "rPr")
            run.insert(0, rpr)
        if rpr.find(W + "vanish") is None:
            etree.SubElement(rpr, W + "vanish")

    for note in list(notes.findall(W + "footnote")):
        if note.get(W + "type") is not None:
            continue
        nid = int(note.get(W + "id"))
        if nid not in ref_ids:
            notes.remove(note)
            continue
        p = note.find(W + "p")
        for old in p.findall(W + "r"):
            if old.find(W + "footnoteRef") is not None:
                p.remove(old)
                break
        r = etree.Element(W + "r")
        rpr = etree.SubElement(r, W + "rPr")
        rs = etree.SubElement(rpr, W + "rStyle")
        rs.set(W + "val", "FootnoteReference")
        etree.SubElement(rpr, W + "vanish")
        etree.SubElement(r, W + "footnoteRef")
        p.insert(0, r)

    _rewrite_zip(src, dst, document=_serialize(doc), footnotes=_serialize(notes))


def footnote_ids(path):
    with zipfile.ZipFile(path) as z:
        doc = etree.fromstring(z.read("word/document.xml"))
    return [int(r.get(W + "id")) for r in doc.iter(W + "footnoteReference")]


def apply_marks(src, dst, marks):
    """marks: list of Persian strings in document order."""
    zin = zipfile.ZipFile(src)
    doc = etree.fromstring(zin.read("word/document.xml"))
    notes = etree.fromstring(zin.read("word/footnotes.xml"))
    zin.close()

    by_id = {}
    for note in notes.findall(W + "footnote"):
        if note.get(W + "type") is not None:
            continue
        by_id[int(note.get(W + "id"))] = note

    for ref, mark in zip(doc.iter(W + "footnoteReference"), marks):
        nid = int(ref.get(W + "id"))
        br = _digit_run_after(ref)
        if br is not None:
            br.find(W + "t").text = mark
        note = by_id.get(nid)
        if note is not None:
            for run in note.find(W + "p").findall(W + "r"):
                t = run.find(W + "t")
                if t is None or t.text is None:
                    continue
                txt = t.text.strip()
                if txt and all(ch in FA_DIGITS for ch in txt):
                    t.text = mark
                    break

    _rewrite_zip(src, dst, document=_serialize(doc), footnotes=_serialize(notes))


def word_pages(path):
    import win32com.client as win32

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        d = word.Documents.Open(os.path.abspath(path), ReadOnly=True,
                                AddToRecentFiles=False)
        try:
            pages = []
            for i in range(1, d.Footnotes.Count + 1):
                pages.append(int(d.Footnotes(i).Reference.Information(3)))
            total = int(d.ComputeStatistics(2))
        finally:
            d.Close(False)
        return pages, total
    finally:
        word.Quit()


def marks_for_pages(pages):
    cnt = defaultdict(int)
    out = []
    for p in pages:
        cnt[p] += 1
        out.append(fa_num(cnt[p]))
    return out


def read_marks(path):
    with zipfile.ZipFile(path) as z:
        doc = etree.fromstring(z.read("word/document.xml"))
    out = []
    for ref in doc.iter(W + "footnoteReference"):
        run = _digit_run_after(ref)
        out.append(run.find(W + "t").text.strip() if run is not None else "")
    return out


def repair(src, dst, max_iter=3):
    tmpdir = tempfile.mkdtemp(prefix="fnfix_")
    step1 = os.path.join(tmpdir, "step1.docx")
    structure_repair(src, step1)
    pages, total = word_pages(step1)
    print("pages=%d footnotes=%d" % (total, len(pages)), flush=True)

    cur = step1
    for it in range(max_iter):
        marks = marks_for_pages(pages)
        nxt = os.path.join(tmpdir, "iter%d.docx" % it)
        apply_marks(cur, nxt, marks)
        pages2, total2 = word_pages(nxt)
        marks2 = marks_for_pages(pages2)
        stable = marks == marks2
        print("iter %d: pages=%d stable_marks=%s" % (it, total2, stable), flush=True)
        cur, pages = nxt, pages2
        if stable:
            break
    else:
        final = os.path.join(tmpdir, "iter_final.docx")
        apply_marks(cur, final, marks2)
        cur = final
        _, total2 = word_pages(cur)
        print("final pages=%d" % total2, flush=True)

    shutil.copyfile(cur, dst)
    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    repair(src, dst)
    print("wrote", dst)
