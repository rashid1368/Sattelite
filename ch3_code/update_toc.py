# -*- coding: utf-8 -*-
"""Add Chapter 4 (and Figure 3-7) entries to the manual TOC and figure list.

The TOC is built from TocEntry paragraphs whose page number is a PAGEREF field,
so the new entries reuse that structure and point at the bookmarks created while
Chapter 4 was inserted.  Word then refreshes every PAGEREF in one pass.

Usage:
    python update_toc.py in.docx out.docx
"""
import copy
import os
import sys

import docx
from docx.oxml.ns import qn

TOC_ITEMS = [
    ("فصل چهارم: تجزیه و تحلیل داده‌ها (یافته‌ها)", "_Ref07008"),
    ("۴-۱ مقدمه", "_Ref07009"),
    ("۴-۲ شرایط پایه و آزمون‌های مقدماتی", "_Ref07013"),
    ("۴-۲-۱ آزمون همگرایی و استقلال از گام زمانی", "_Ref07015"),
    ("۴-۲-۲ قاعده‌ی گزارش و طبقه‌بندی حالت‌ها", "_Ref07021"),
    ("۴-۳ آزمون فرضیه‌ی اول: نایکنواختی عمر طبیعی نسبت به هندسه‌ی ورود", "_Ref07024"),
    ("۴-۴ آزمون فرضیه‌ی دوم: سهم ماه، خورشید و فشار تابش خورشیدی", "_Ref07035"),
    ("۴-۵ آزمون فرضیه‌ی سوم: مساحت بادبان و انطباق با مهلت ۲۵ ساله", "_Ref07045"),
    ("۴-۶ آزمون فرضیه‌ی چهارم: حساسیت نتیجه به پارامترهای سناریویی و مدل", "_Ref07059"),
    ("۴-۷ اثر مدل چگالی جو بر نتیجه‌ها", "_Ref07070"),
    ("۴-۸ اعتبارسنجی با داده‌ی پروازی ALE-1", "_Ref07078"),
    ("۴-۹ جمع‌بندی فصل", "_Ref07086"),
]

FIG_ITEMS = ["_Ref07006", "_Ref07029", "_Ref07040", "_Ref07050", "_Ref07052",
             "_Ref07064"]


def _text(p):
    return " ".join(p.text.split())


def make_entry(tpl, text, bookmark):
    el = copy.deepcopy(tpl)
    runs = el.findall(qn("w:r"))
    runs[0].find(qn("w:t")).text = text
    for r in runs:
        instr = r.find(qn("w:instrText"))
        if instr is not None:
            instr.text = " PAGEREF %s \\h " % bookmark
    result = el.findall(qn("w:r"))[-2].find(qn("w:t"))
    if result is not None:
        result.text = "0"
    return el


def find_para(doc, pred, start=0):
    for i in range(start, len(doc.paragraphs)):
        if pred(doc.paragraphs[i]):
            return i
    return -1


def main(src, dst):
    d = docx.Document(src)
    ps = d.paragraphs

    i_ref = find_para(d, lambda p: p.style.name == "TocEntry"
                      and _text(p).startswith("منابع و مأخذ"))
    if i_ref < 0:
        raise SystemExit("TOC reference anchor not found")
    tpl = ps[i_ref - 1]._p  # a TocEntry paragraph with a PAGEREF field

    anchor = ps[i_ref]._p
    for text, bm in TOC_ITEMS:
        anchor.addprevious(make_entry(tpl, text, bm))

    i_symbols = find_para(d, lambda p: p.style.name == "FrontTitle"
                          and "نشانه" in p.text)
    if i_symbols < 0:
        raise SystemExit("symbols heading not found")
    last = ps[i_symbols - 1]
    while last.style.name != "TocEntry" and i_symbols - 1 > 0:
        i_symbols -= 1
        last = ps[i_symbols - 1]
    anchor = last._p.getnext()
    for bm in FIG_ITEMS:
        cap = None
        for p in d.paragraphs:
            bs = p._p.find(qn("w:bookmarkStart"))
            if bs is not None and bs.get(qn("w:name")) == bm:
                cap = p
                break
        if cap is None:
            raise SystemExit("caption bookmark not found: %s" % bm)
        anchor.addprevious(make_entry(tpl, _text(cap), bm))

    d.save(dst)
    print("saved", dst)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
