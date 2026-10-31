# -*- coding: utf-8 -*-
"""Check current PAGEREF results in v9, add missing _Ref00167, update, save."""
import os
import io

import win32com.client as w

ROOT = r"D:\Downloads\Documents\Satellite"
V9 = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v9_ch1_ch5.docx")
FIX = os.path.join(ROOT, "_build", "v9_fixed.docx")
PDF = os.path.join(ROOT, "_build", "v9_preview.pdf")
OUT = os.path.join(ROOT, "_build", "v9_fields.txt")

lines = []


def dump_fields(doc, tag):
    lines.append("== %s ==" % tag)
    n = 0
    zeros = 0
    errs = 0
    shown = 0
    for f in doc.Fields:
        if f.Type != 37:  # wdFieldPageRef
            continue
        n += 1
        try:
            code = f.Code.Text
        except Exception:
            code = "?"
        res = f.Result.Text.strip()
        if res in ("0", ""):
            zeros += 1
        if "Error" in res or "خطا" in res:
            errs += 1
        if ("_Ref081" in code or "_Ref070" in code or "_Ref00167" in code) and shown < 40:
            lines.append("  %s -> %r" % (code.strip(), res))
            shown += 1
    lines.append("  pageref total=%d zeros=%d errors=%d" % (n, zeros, errs))


word = w.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(V9, ReadOnly=False, AddToRecentFiles=False)
    try:
        doc.Repaginate()
        dump_fields(doc, "before")

        if not doc.Bookmarks.Exists("_Ref00167"):
            target = None
            for p in doc.Paragraphs:
                if p.Range.Text.strip() == "منابع و مأخذ" and p.Style.NameLocal in (
                        "RefHeadingCenter", "Ref Heading Center"):
                    target = p
                    break
            if target is None:
                for p in doc.Paragraphs:
                    if p.Range.Text.strip() == "منابع و مأخذ":
                        target = p
                        break
            if target is None:
                raise SystemExit("references heading not found in COM")
            doc.Bookmarks.Add("_Ref00167", target.Range)
            lines.append("added _Ref00167 on: %r" % target.Range.Text.strip()[:60])

        doc.Fields.Update()
        doc.Repaginate()
        dump_fields(doc, "after")

        lines.append("pages=%d footnotes=%d" % (
            doc.ComputeStatistics(2), doc.Footnotes.Count))
        doc.SaveAs2(FIX, FileFormat=16)
        doc.ExportAsFixedFormat(PDF, 17)
        lines.append("saved %s" % FIX)
    finally:
        doc.Close(False)
finally:
    word.Quit()

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("done")
