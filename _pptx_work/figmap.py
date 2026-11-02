# -*- coding: utf-8 -*-
"""Map each [IMG] paragraph in the thesis to its media file and following caption."""
import io, os, re, zipfile
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = r"D:\Downloads\Documents\Satellite\Haddadi_MSc_thesis_GTO_sail_deorbit_v10_ch1_ch5.docx"
NS_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
NS_R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

d = Document(SRC)
rels = d.part.rels
out = io.open("fig_map.txt", "w", encoding="utf-8")

blocks = []
for child in d.element.body.iterchildren():
    if child.tag.endswith('}p'):
        blocks.append(Paragraph(child, d))
    elif child.tag.endswith('}tbl'):
        blocks.append(Table(child, d))

pending = None
for b in blocks:
    if isinstance(b, Table):
        continue
    blips = b._p.findall('.//' + NS_A + 'blip')
    if blips:
        ids = [bl.get(NS_R + 'embed') for bl in blips]
        files = []
        for rid in ids:
            try:
                files.append(os.path.basename(rels[rid].target_part.partname))
            except Exception:
                files.append('?')
        pending = ','.join(files)
        out.write("IMG %s  (para style=%s)\n" % (pending, b.style.name))
        continue
    if pending:
        t = b.text.strip()
        if t:
            out.write("    CAPTION: %s\n" % t)
            pending = None
out.close()
print("ok")
