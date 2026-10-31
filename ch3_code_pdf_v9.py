# -*- coding: utf-8 -*-
"""Render key pages of v9 preview PDF + dump TOC text."""
import os
import io

import fitz

ROOT = r"D:\Downloads\Documents\Satellite"
PDF = os.path.join(ROOT, "_build", "v9_preview.pdf")
OUT = os.path.join(ROOT, "_build", "v9_pdf_pages")
os.makedirs(OUT, exist_ok=True)

doc = fitz.open(PDF)
lines = ["pages=%d" % doc.page_count]
# find TOC pages: pages containing 'فهرست مطالب'
toc_pages = []
for i in range(8):
    t = doc[i].get_text()
    if "فهرست" in t:
        toc_pages.append(i + 1)
lines.append("toc pages: %s" % toc_pages)

for pno in (toc_pages[-1] if toc_pages else 8, 110, 111, 128):
    page = doc[pno - 1]
    pix = page.get_pixmap(dpi=110)
    fn = os.path.join(OUT, "p%03d.png" % pno)
    pix.save(fn)
    lines.append("rendered %s" % fn)

# text of last TOC page and page 110
for pno in ([toc_pages[-1]] if toc_pages else []) + [110, 128]:
    lines.append("===== PAGE %d =====" % pno)
    lines.append(doc[pno - 1].get_text()[:1800])

with io.open(os.path.join(ROOT, "_build", "v9_pdfinfo.txt"), "w",
             encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ok", doc.page_count)
