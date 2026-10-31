# -*- coding: utf-8 -*-
"""Sixth batch: method notes for chapter 4 (one-at-a-time analysis, sampling size),
and budget and recommendation text for chapter 5. Reads and writes the v10 draft."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx_util import W, ptext, clone_par_after

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
d = docx.Document(PATH)
kids = list(d.element.body.iterchildren())

def find(prefix, last=False):
    hits = [k for k in kids if ptext(k).strip().startswith(prefix)]
    assert hits, prefix
    return hits[-1] if last else hits[0]

def chain(anchor, texts, tmpl=None):
    prev = anchor
    for t in texts:
        prev = clone_par_after(prev, tmpl, t)
    return prev

body4 = find("پیامد طراحی این یافته")   # body template (chapter 5 style)

chain(find("ترتیب کامل حساسیت چنین است"), [
    "روش تحلیل حساسیت یک‌به‌یک بود: هر پارامتر در مقدار بالا و پایین خود تغییر کرد و بقیه‌ی پارامترها ثابت ماندند. این روش ساده است و اثر هر پارامتر را در همان نقطه‌ی پایه نشان می‌دهد. محدودیت آن این است که اثرهای متقابل، مثلاً هم‌زمانی ضریب پسای بالا و تأخیر استقرار، دیده نمی‌شوند. برای همین، رتبه‌بندی این جدول برای تعمیم به کل فضای ورود کافی نیست و باید با نمونه‌برداری کامل تکمیل شود.",
], tmpl=body4)

chain(find("حکم فرضیه‌ی اول: تأیید. عمر طبیعی"), [
    "انتخاب شانزده هندسه با نمونه‌برداری لاتین ابرمکعبی انجام شد. این روش فضای دو بعدی ω و Ω را طوری پوشش می‌دهد که هر نقطه در یک بازه‌ی جداگانه باشد. این تعداد برای سنجش نایکنواختی کافی است، اما برای برآورد کسرهای انطباق با فاصله‌ی اطمینان کم است. بنابراین کسرهای ۳۱٫۳ و ۵۶٫۳ درصد را باید به‌عنوان مشاهده‌های نمونه خواند، نه به‌عنوان احتمال.",
], tmpl=body4)

chain(find("محدودیت جرمی، نتیجه را تعیین‌کننده‌تر"), [
    "در عمل، بودجه‌ی جرمی هر پروژه با سایر اجزای ماهواره رقابت دارد و هر کیلوگرم بادبان از ظرفیت محموله یا تجهیزات دیگر کم می‌کند. بنابراین بیشینه‌ی مساحت یک ثابت فنی نیست، بلکه نتیجه‌ی توافق میان طراح سامانه‌ی دفع و سایر بخش‌های ماهواره است. این توافق باید پیش از طراحی جزئی انجام شود، زیرا پس از آن تغییر جرم هزینه‌ی بیشتری دارد.",
], tmpl=body4)

anc = find("توصیه‌ی نهم، آزمون پایداری")
chain(anc, [
    "توصیه‌ی دهم، مشارکت زودهنگام تیم مقرراتی در طراحی است. اگر تعریف عمر، آستانه‌ی ورود و مدل جو مورد پذیرش نهاد مقرراتی پیش از اجرای شبیه‌سازی توافق شود، امکان تفسیر متفاوت از یک عدد کاهش می‌یابد.",
], tmpl=body4)

d.save(PATH)
print("saved", PATH)
