# -*- coding: utf-8 -*-
"""Render corrected key pages: TOC with ch5, ch5 start, refs."""
import os
import io

import fitz

ROOT = r"D:\Downloads\Documents\Satellite"
PDF = os.path.join(ROOT, "_build", "v9_preview.pdf")
OUT = os.path.join(ROOT, "_build", "v9_pdf_pages")
os.makedirs(OUT, exist_ok=True)

doc = fitz.open(PDF)
lines = []

toc_hit = []
for i in range(0, 16):
    t = doc[i].get_text()
    if "فصل پنجم" in t and "نتیجه" in t:
        toc_hit.append(i + 1)
lines.append("pages 1-16 containing 'فصل پنجم': %s" % toc_hit)

targets = toc_hit[-1:] + [125, 126, 127, 143]
for pno in targets:
    if not (1 <= pno <= doc.page_count):
        continue
    pix = doc[pno - 1].get_pixmap(dpi=110)
    fn = os.path.join(OUT, "q%03d.png" % pno)
    pix.save(fn)
    lines.append("rendered %s" % fn)

if toc_hit:
    lines.append("===== TOC PAGE %d =====" % toc_hit[-1])
    lines.append(doc[toc_hit[-1] - 1].get_text()[:2500])

lines.append("===== PAGE 125 =====")
lines.append(doc[124].get_text()[:2500])
lines.append("===== PAGE 143 =====")
lines.append(doc[142].get_text()[:600])

with io.open(os.path.join(ROOT, "_build", "v9_pdfinfo2.txt"), "w",
             encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ok")
