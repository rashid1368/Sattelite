# -*- coding: utf-8 -*-
"""Diagnose v9 bookmarks: structural checks + Word COM control on v8."""
import os
import io
import zipfile
from collections import Counter

import docx
from docx.oxml.ns import qn

ROOT = r"D:\Downloads\Documents\Satellite"
V8 = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v8_ch1_ch4.docx")
V9 = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v9_ch1_ch5.docx")
OUT = os.path.join(ROOT, "_build", "bm_diag2.txt")

lines = []


def structural(path, tag):
    d = docx.Document(path)
    body = d.element.body
    starts = body.findall(".//" + qn("w:bookmarkStart"))
    ends = body.findall(".//" + qn("w:bookmarkEnd"))
    names = [s.get(qn("w:name")) for s in starts]
    ids = [s.get(qn("w:id")) for s in starts]
    cn = Counter(names)
    ci = Counter(ids)
    lines.append("%s: bookmarkStart=%d bookmarkEnd=%d" % (tag, len(starts), len(ends)))
    lines.append("  dup names: %s" % {k: v for k, v in cn.items() if v > 1})
    lines.append("  dup ids: %s" % {k: v for k, v in ci.items() if v > 1})
    # zero-length bookmarks: find start index and check next sibling is end with same id
    zero = 0
    for s in starts:
        nxt = s.getnext()
        if nxt is not None and nxt.tag == qn("w:bookmarkEnd") and nxt.get(qn("w:id")) == s.get(qn("w:id")):
            zero += 1
    lines.append("  zero-length bookmarks: %d" % zero)
    # duplicate w14:paraId
    W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
    pids = [p.get("{%s}paraId" % W14) for p in body.findall(".//" + qn("w:p"))]
    pids = [p for p in pids if p]
    cp = Counter(pids)
    lines.append("  paragraphs with paraId: %d  dup paraId: %d"
                 % (len(pids), sum(1 for v in cp.values() if v > 1)))
    # list bookmarks on ch5 headings
    for name in ("_Ref08101", "_Ref08102", "_Ref07008", "_Ref00167"):
        lines.append("  exists %s: %s" % (name, name in names))
    return d


structural(V8, "v8")
structural(V9, "v9")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

import win32com.client as w

word = w.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    for tag, path in (("v8", V8), ("v9", V9)):
        doc = word.Documents.Open(path, ReadOnly=True, AddToRecentFiles=False)
        try:
            names = []
            for i in range(1, doc.Bookmarks.Count + 1):
                try:
                    names.append(doc.Bookmarks(i).Name)
                except Exception as e:
                    names.append("ERR:%s" % e)
            out = ["COM %s: Bookmark count=%d" % (tag, doc.Bookmarks.Count)]
            out.append("  first 20: %s" % names[:20])
            for nm in ("_Ref08101", "_Ref08102", "_Ref07008", "_Ref00167"):
                out.append("  Exists %s: %s" % (nm, doc.Bookmarks.Exists(nm)))
            doc.Repaginate()
            for nm in ("_Ref08101", "_Ref08102", "_Ref07008", "_Ref00167"):
                if doc.Bookmarks.Exists(nm):
                    r = doc.Bookmarks(nm).Range
                    out.append("  %s page=%s text=%r" % (
                        nm, r.Information(3), r.Text[:40]))
            with io.open(OUT, "a", encoding="utf-8") as f:
                f.write("\n".join(out) + "\n")
        finally:
            doc.Close(False)
finally:
    word.Quit()

print("done")
