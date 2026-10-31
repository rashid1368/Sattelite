# -*- coding: utf-8 -*-
"""Tenth batch (chapter 5): interpretation of the eight-fold ratio, the 130 m2 case and
the definition, a closing summary, and one more application recommendation.
Reads and writes the v10 draft."""
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

body = find("پیامد طراحی این یافته")

def chain(anchor, texts):
    prev = anchor
    for t in texts:
        prev = clone_par_after(prev, body, t)
    return prev

chain(find("پیشنهادهای پژوهشی زیر"), [
    "این پیشنهادها به ترتیب اثر بر حکم انطباق مرتب شده‌اند. معیار پذیرش هر پیشنهاد آن است که پس از اجرای آزمون، حکم انطباق تغییر کند یا ثابت بماند؛ اگر تغییر کند، گزارش باید بر پایه‌ی حکم جدید باشد.",
])

chain(find("نکته‌ی تکمیلی: نسبت هشت‌برابری"), [
    "از نظر فیزیکی، نسبت هشت‌برابر را نباید مقدار ثابت مدار انتقال دانست. این نسبت به فاز اولیه و به تشدیدهای ماه و خورشید وابسته است، همان‌گونه که در بخش ۵-۲-۵ دیده شد. بنابراین می‌توان این عدد را به‌عنوان بزرگی اثر در هندسه‌ی مرجع گزارش کرد، اما نباید آن را ضریب تصحیح همه‌ی هندسه‌ها دانست.",
])

chain(find("محدودیت این تحلیل آن است که هر نتیجه‌ی آستانه‌ای"), [
    "نمونه‌ی ۱۳۰ متر مربع نشان می‌دهد که تعریف عمر و افق گزارش چه اثری دارند. با افق ۱۰۰ ساله، این حالت به ۱۲۰ کیلومتر نمی‌رسد، اما ۱۲۰ متر مربع در ۲۵٫۶ سال می‌رسد. اگر افق گزارش یا آستانه‌ی ورود تغییر کند، فهرست حالت‌های منطبق نیز تغییر می‌کند.",
])

chain(find("پاسخ‌های کمّی") if False else find("پرسش اصلی: انطباق تضمین‌شده"), [
    "این پاسخ‌ها برای حکم نهایی کافی نیستند. حکم نهایی منوط به تکمیل آزمون‌های بخش ۵-۶ است و تا آن زمان باید به‌عنوان «تأیید مشروط» خوانده شود.",
])

chain(find("پیام سوم برای پژوهشگران"), [
    "خلاصه‌ی بخش پنجم آن است که پاسخ این پژوهش برای استیج داخلی یک میدان است: هر هندسه، هر مساحت و هر مدل جو حکم متفاوتی می‌دهد. همین پیام، مهم‌ترین خروجی تصمیم‌گیری این پژوهش است.",
])

chain(find("توصیه‌ی هفتم، گزارش عمر"), [
    "توصیه‌ی یازدهم، برنامه‌ریزی برای گردآوری داده‌ی پروازی در مدار انتقال است. حتی یک داده‌ی پروازی از استیج جی‌تی‌او یا استیجی با مدار مشابه، می‌تواند جهت خطای مدل جو و مدل نیرو را در مرحله‌ی بلندمدت آزمون کند. این داده‌ها باید در طراحی مأموریت‌های آینده پیش‌بینی شوند.",
])

d.save(PATH)
print("saved", PATH)
