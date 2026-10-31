# -*- coding: utf-8 -*-
"""Eighth batch (chapter 5): a section on perigee minimum versus entry time, and a
closing section with three messages. Reads and writes the v10 draft."""
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
H3 = find("۵-۲-۱ فرضیه‌ی اول", last=True)
H2 = find("۵-۶ ترتیب پیشنهادی")

def chain(anchor, texts, tmpl):
    prev = anchor
    for t in texts:
        prev = clone_par_after(prev, tmpl, t)
    return prev

anc = find("در نهایت، این پژوهش پیشنهاد می‌کند که گزارش طراحی")
prev = clone_par_after(anc, H3, "۵-۲-۱۰ کمینه‌ی حضیض یا زمان ورود؟")
chain(prev, [
    "یکی از پرسش‌هایی که در ارزیابی این پژوهش مطرح می‌شود آن است که چرا عمر به‌جای کمینه‌ی حضیض سنجیده شد. کمینه‌ی حضیض در ۲۵ سال کمیتی ساده و قابل مقایسه است، اما معیار مهلت نیست.",
    "شاهد آن در بخش ۴-۳ آمده است: هندسه‌ی شماره‌ی ۸ با کمینه‌ی حضیض ۲۵۰٫۱۷ کیلومتر هیچ‌گاه پایین‌تر نرفت، در حالی که هندسه‌ی شماره‌ی ۱۰ تا ۱۸۵٫۵۵ کیلومتر پایین آمد و باز هم به ۱۲۰ کیلومتر نرسید. هر دو غیرمنطبق‌اند، اما با دو کمیت متفاوت. اگر کمینه‌ی حضیض معیار بود، این تمایز پنهان می‌ماند.",
    "زمان ورود به ۱۲۰ کیلومتر نیز حساس به فاز است (بخش ۴-۲-۳)، پس به‌تنهایی کامل نیست. گزارش دوگانه‌ی «زمان ورود» و «کمینه‌ی حضیض» بهتر از یکی از این دو است: زمان ورود حکم را می‌دهد و کمینه‌ی حضیض نشان می‌دهد مدار تا چه اندازه به آستانه نزدیک شده است.",
], body)

anc = find("جمع‌بندی این بخش آن است که پیش از استناد عددی")
prev = clone_par_after(anc, H2, "۵-۷ سه پیام کلیدی برای سه گروه خواننده")
chain(prev, [
    "پیام نخست برای طراحان: هندسه‌ی ورود، مساحت و زمان استقرار باید هم‌زمان ارزیابی شوند. انطباق ویژگی هندسه‌ی مدار است، نه ویژگی مساحت به‌تنهایی. اگر مساحت تنها معیار باشد، تصمیم به ترکیب ω و Ω حساس می‌ماند.",
    "پیام دوم برای نهادهای مقرراتی: گزارش انطباق باید دامنه‌ای باشد و مدل جو، افق زمانی و تعریف عمر را صریح بیاورد. حکم یک‌عددی، حتی اگر درست باشد، در برابر تغییر کوچک فرضیات ناپایدار است.",
    "پیام سوم برای پژوهشگران: پیش از نتیجه‌گیری از یک جاروب، همگرایی عددی و اثر مدل جو باید بررسی شوند. این پژوهش نشان داد که حالت‌های مرزی با تغییر ۱۰ متر مربع در مساحت می‌توانند حکم خود را وارونه کنند. بنابراین آزمون‌های حساسیت باید بخش ثابت گزارش باشند، نه پیوست اختیاری.",
], body)

d.save(PATH)
print("saved", PATH)
