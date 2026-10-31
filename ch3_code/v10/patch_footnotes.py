# -*- coding: utf-8 -*-
"""Footnote layout: Persian footnotes right-aligned (number on the right), English
footnotes left-aligned (number on the left). Also reports footnotes whose text repeats
an earlier one (candidates for the 'each source once' rule). Edits the footnotes part of
_build/thesis_v10_draft.docx in place."""
import os, sys, shutil, zipfile, re
from lxml import etree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

zin = zipfile.ZipFile(PATH)
root = etree.fromstring(zin.read("word/footnotes.xml"))
seen, repeats, n_fa, n_en = {}, [], 0, 0
for fn in root.iter(W + "footnote"):
    fid = int(fn.get(W + "id"))
    if fid <= 0:
        continue
    text = "".join(t.text or "" for t in fn.iter(W + "t")).strip()
    persian = re.search(r"[\u0621-\u063A\u0641-\u064A\u0671-\u06D3]", text) is not None
    for p in fn.iter(W + "p"):
        ppr = p.find(W + "pPr")
        if ppr is None:
            ppr = etree.SubElement(p, W + "pPr"); p.insert(0, ppr)
        for tag in ("bidi", "jc"):
            for x in ppr.findall(W + tag):
                ppr.remove(x)
        b = etree.SubElement(ppr, W + "bidi"); b.set(W + "val", "1" if persian else "0")
        j = etree.SubElement(ppr, W + "jc"); j.set(W + "val", "right" if persian else "left")
        # schema order: bidi must come before jc; move jc to the end of pPr
        ppr.remove(j); ppr.append(j)
    if persian: n_fa += 1
    else: n_en += 1
    key = re.sub(r"\s+", " ", re.sub(r"[\u200e\u200f]", "", re.sub(r"^[0-9۰-۹]+\s*", "", text)))
    if key and key in seen:
        repeats.append((fid, seen[key], key[:60]))
    else:
        seen.setdefault(key, fid)

data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
tmp = PATH + ".tmp"
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        zout.writestr(item, data if item.filename == "word/footnotes.xml" else zin.read(item.filename))
zin.close()
shutil.move(tmp, PATH)
print("footnotes persian:", n_fa, "english:", n_en)
print("repeated footnote texts:", len(repeats))
for r in repeats[:20]:
    print("  ", r)
