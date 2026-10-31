# -*- coding: utf-8 -*-
"""Seventh batch (chapter 4): Model B initial state and the ALE-1 descent definition.
Reads and writes the v10 draft."""
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

def chain(anchor, texts):
    prev = anchor
    for t in texts:
        prev = clone_par_after(prev, body, t)
    return prev

chain(find("تفسیر جدول ۴-۳:"), [
    "مدل B دو مقدار اولیه‌ی متفاوت دارد. با حالت اولیه‌ی استخراج‌شده از حالت osculating، عمر ۶۰٫۷۷ سال و با عناصر میانگین ۶۴٫۳۷ سال است. این تفاوت حدود ۶ درصد است و نشان می‌دهد انتخاب حالت اولیه در نتیجه اثر دارد. در این پژوهش حالت osculating به‌عنوان مبنا انتخاب شد تا با حالت اولیه‌ی مدل A سازگار باشد، و عناصر میانگین به‌عنوان حساسیت گزارش شده‌اند.",
])

chain(find("تفسیر جدول ۴-۷:"), [
    "روش محاسبه‌ی زمان فرود ALE-1 ساده است: مدار از ارتفاع ۵۰۰ کیلومتر با مدل جو و نیروهای این پژوهش منتشر می‌شود تا وقتی ارتفاع به زیر ۴۰۰ کیلومتر برسد. این تعریف با تعریف عمر در بقیه‌ی فصل متفاوت است، زیرا هدف آن یک فرود مشخص است و نه رسیدن به ۱۲۰ کیلومتر. بنابراین عددهای جدول ۴-۷ باید به‌عنوان نسبت‌های زمانی خوانده شوند، نه به‌عنوان عمر مطلق.",
])

d.save(PATH)
print("saved", PATH)
