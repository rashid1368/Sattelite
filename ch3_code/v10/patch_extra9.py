# -*- coding: utf-8 -*-
"""Ninth batch (chapter 5): direction of the bias from each limitation. Reads and
writes the v10 draft."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx_util import W, ptext, clone_par_after

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
d = docx.Document(PATH)
kids = list(d.element.body.iterchildren())

def find(prefix):
    hits = [k for k in kids if ptext(k).strip().startswith(prefix)]
    assert hits, prefix
    return hits[0]

body = find("پیامد طراحی این یافته")
prev = find("دوازدهمین محدودیت، نبود داده")
for t in [
    "برای خواننده‌ی مقرراتی، جهت اثر هر محدودیت بر حکم انطباق مهم است. مدل جو جهت خطای ثابتی ندارد (بخش ۵-۲-۵). ساده‌سازی نگرش احتمالاً عملکرد بادبان را بیش‌برآورد می‌کند، زیرا بادبانی ایده‌آل فرض شده است. جدول NRLMSIS که تا ۶۰۰ کیلومتر محدود است، احتمالاً عمر را اندکی بلندتر نشان می‌دهد، زیرا پسا در ارتفاع‌های بالاتر صفر فرض شده است؛ این موضوع باید آزموده شود. ساده‌سازی‌های فشار تابش و سایه جهت خطای نامشخص دارند و باید با مدل کامل‌تر سنجیده شوند.",
    "بنابراین جهت خطای بیشتر محدودیت‌ها یا نامشخص است یا به حالت‌های مرزی وابسته است. این وضعیت دلیل آن است که حکم نهایی باید بعد از اجرای آزمون‌های بخش ۵-۶ صادر شود و نه پیش از آن.",
]:
    prev = clone_par_after(prev, body, t)

d.save(PATH)
print("saved", PATH)
