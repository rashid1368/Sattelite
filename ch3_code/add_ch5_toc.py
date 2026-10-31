# -*- coding: utf-8 -*-
"""Add Chapter 5 entries to the manual TOC of v9."""
import copy
import json
import os

import docx
from docx.oxml.ns import qn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v9_ch1_ch5.docx")
DST = os.path.join(ROOT, "_build", "v9_toc.docx")

ORDER = [
    "فصل پنجم: نتیجه‌گیری و پیشنهادات",
    "۵-۱ مقدمه و خلاصه‌ی پژوهش",
    "۵-۲ بحث و تفسیر یافته‌ها",
    "۵-۲-۱ فرضیه‌ی اول: نایکنواختی عمر طبیعی و پیامد آن برای الزام دفع",
    "۵-۲-۲ فرضیه‌ی دوم: سهم اختلالات لونیسولار و فشار تابش خورشیدی",
    "۵-۲-۳ فرضیه‌ی سوم: مساحت بادبان، نایکنوایی و مرز بودجه‌ی جرم",
    "۵-۲-۴ فرضیه‌ی چهارم: سلسله‌مراتب عدم‌قطعیت و اولویت صحه‌گذاری",
    "۵-۳ نتیجه‌گیری کلی و پاسخ به پرسش‌های پژوهش",
    "۵-۴ محدودیت‌های پژوهش",
    "۵-۵ پیشنهادات",
    "۵-۵-۱ پیشنهادهای پژوهشی",
    "۵-۵-۲ پیشنهادهای کاربردی",
]


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
    result = runs[-2].find(qn("w:t"))
    if result is not None:
        result.text = "0"
    return el


def main():
    d = docx.Document(SRC)
    ps = d.paragraphs
    i_ref = None
    for i, p in enumerate(ps):
        if p.style.name == "TocEntry" and _text(p).startswith("منابع و مأخذ"):
            i_ref = i
            break
    if i_ref is None:
        raise SystemExit("TOC reference anchor not found")

    tpl = ps[174]._p
    anchor = ps[i_ref]._p
    book = json.load(open(os.path.join(ROOT, "_build", "ch5_bookmarks.json"),
                          encoding="utf-8"))
    for text in ORDER:
        if text not in book:
            raise SystemExit("bookmark missing: %s" % text)
        anchor.addprevious(make_entry(tpl, text, book[text]))

    d.save(DST)
    print("saved", DST, "toc entries added", len(ORDER))


if __name__ == "__main__":
    main()
