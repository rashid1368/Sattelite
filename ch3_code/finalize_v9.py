# -*- coding: utf-8 -*-
"""Refresh PAGEREF fields in v9, report pagination, and export the PDF."""
import os
import sys

import win32com.client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_build", "v9_toc.docx")
DST = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v9_ch1_ch5.docx")
PDF = os.path.join(ROOT, "_build", "v9_preview.pdf")

word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(SRC, ReadOnly=False, AddToRecentFiles=False)
    doc.Fields.Update()
    doc.Repaginate()
    pages = doc.ComputeStatistics(2)
    notes = doc.Footnotes.Count
    zeros = 0
    errors = 0
    total_ref = 0
    for f in doc.Fields:
        if f.Type == 37:  # wdFieldPageRef
            total_ref += 1
            res = f.Result.Text.strip()
            if res in ("0", ""):
                zeros += 1
            if "Error" in res:
                errors += 1
    doc.SaveAs2(DST, FileFormat=16)
    doc.ExportAsFixedFormat(PDF, 17)
    print("pages", pages, "footnotes", notes, "pageref", total_ref,
          "zeros", zeros, "errors", errors)
    doc.Close(False)
finally:
    word.Quit()
