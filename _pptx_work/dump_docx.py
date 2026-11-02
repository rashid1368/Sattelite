# -*- coding: utf-8 -*-
import io, os, zipfile
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = r"D:\Downloads\Documents\Satellite\Haddadi_MSc_thesis_GTO_sail_deorbit_v10_ch1_ch5.docx"
out = io.open("thesis_dump.txt", "w", encoding="utf-8")
d = Document(SRC)


def iterblocks(parent):
    for child in parent.element.body.iterchildren():
        if child.tag.endswith('}p'):
            yield Paragraph(child, parent)
        elif child.tag.endswith('}tbl'):
            yield Table(child, parent)


i = 0
ti = 0
for b in iterblocks(d):
    if isinstance(b, Paragraph):
        i += 1
        txt = b.text.strip()
        blips = b._p.findall(
            './/{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        tag = "[IMG]" if blips else ""
        if not txt and not tag:
            continue
        out.write("P%d|%s|%s %s\n" % (i, b.style.name, tag, txt))
    else:
        ti += 1
        out.write("\n### TABLE %d rows=%d cols=%d\n" % (
            ti, len(b.rows), len(b.columns)))
        for r in b.rows[:60]:
            cells = [c.text.strip().replace("\n", " ") for c in r.cells]
            out.write("   | " + " ; ".join(cells) + "\n")
        out.write("\n")
out.close()
print("paras", i, "tables", ti)

z = zipfile.ZipFile(SRC)
os.makedirs("media", exist_ok=True)
names = [n for n in z.namelist() if n.startswith("word/media/")]
for n in names:
    open(os.path.join("media", os.path.basename(n)), "wb").write(z.read(n))
print("media count", len(names))
