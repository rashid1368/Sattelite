# -*- coding: utf-8 -*-
"""Dump TOC pages and search for ch5 entries."""
import os
import io

import fitz

ROOT = r"D:\Downloads\Documents\Satellite"
PDF = os.path.join(ROOT, "_build", "v9_preview.pdf")
doc = fitz.open(PDF)
lines = []
hits = []
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "پنجم" in t:
        hits.append((i + 1, t.count("پنجم")))
lines.append("pages with 'پنجم': %s" % hits)

for pno in range(7, 13):
    lines.append("===== PAGE %d =====" % pno)
    lines.append(doc[pno - 1].get_text()[-1500:])

with io.open(os.path.join(ROOT, "_build", "v9_toc_dump.txt"), "w",
             encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ok")
