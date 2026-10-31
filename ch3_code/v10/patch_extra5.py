# -*- coding: utf-8 -*-
"""Fifth batch: NRLMSIS status for each hypothesis (chapter 4 summary), the 25-year
horizon rationale and methodological contribution (chapter 5), and one more
recommendation. Reads and writes _build/thesis_v10_draft.docx."""
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

T_BODY = find("پیامد طراحی این یافته")
T_H3_5 = find("۵-۲-۱ فرضیه‌ی اول", last=True)

def chain(anchor, texts, tmpl=T_BODY):
    prev = anchor
    for t in texts:
        prev = clone_par_after(prev, tmpl, t)
    return prev

chain(find("در مجموع، نتیجه‌ی اصلی این فصل"), [
    "بررسی با NRLMSIS وضعیت هر فرضیه را روشن‌تر می‌کند. حکم فرضیه‌ی اول با کسر انطباق ۲۵ درصد در مدل NRLMSIS همچنان تأیید است. حکم فرضیه‌ی دوم برای هندسه‌ی مرجع با NRLMSIS آزموده نشده و باید پیش از تعمیم تکمیل شود. حکم فرضیه‌ی سوم در جاروب ω = ۲۷۰ هم‌جهت است، اما وارونگی انطباق در ۸۰، ۱۳۰ و ۱۶۰ متر مربع دیده می‌شود. حکم فرضیه‌ی چهارم با NRLMSIS آزموده نشده است. بنابراین حکم دو فرضیه‌ی آخر باید «تأیید مشروط» بماند تا بررسی کامل انجام شود.",
])

chain(find("حکم مهلت ۲۵ ساله در عمل یک مرز"), [
    "مهلت ۲۵ ساله در رهنمودهای آی‌ای‌دی‌سی و استاندارد ایزو ۲۴۱۱۳ آمده است و هدف آن کاهش خطر برخورد با اجسام فعال و ماهواره‌هاست. این مهلت یک قرارداد است و نه یک ثابت فیزیکی. بنابراین عمرهای بیشتر از ۲۵ سال نیز از نظر فیزیکی معنادارند و نشان می‌دهند که استیج پس از این مدت همچنان در مدار باقی است.",
])

anc = find("پرسش اصلی: انطباق تضمین‌شده")
prev = clone_par_after(anc, T_H3_5, "۵-۳-۲ سهم روش‌شناختی پژوهش")
chain(prev, [
    "سهم روش‌شناختی این پژوهش در سه بخش خلاصه می‌شود. نخست، یک زنجیره‌ی انتشار مداری با دو مدل نیرو و دو مدل جو که هر دو در یک بسته‌ی کد پایتون بازتولیدپذیرند (بخش ۲-۶-۴). دوم، تعریف روشن عمر با رخداد حضیض و آستانه‌ی ۱۲۰ کیلومتر که حساسیت آن به تلرانس در بخش ۴-۲-۳ آزموده شد. سوم، نمونه‌برداری لاتین ابرمکعبی و جاروب مساحت که نشان می‌دهند حکم انطباق تابعی ناهموار از هندسه و مساحت است.",
    "این سه بخش، پیش از آن‌که یافته‌ی مهندسی باشند، یک چارچوب آزمون هستند. هر یافته را می‌توان با تکرار همان زنجیره بازبینی کرد و هر تغییر در مدل جو یا تعریف عمر، اثر آن بر حکم را نشان می‌دهد. این ویژگی در کاربرد مقرراتی ارزش دارد، زیرا تصمیم را از یک عدد گزارش‌شده به یک فرایند بازبینی‌پذیر منتقل می‌کند.",
    "محدودیت این سهم آن است که هنوز همه‌ی اجراهای لازم برای NRLMSIS تکمیل نشده‌اند. چارچوب آماده است، اما شمار اجراها برای حکم قطعی کافی نیست.",
])

chain(find("دهمین پیشنهاد، مدل نگرش"), [
    "یازدهمین پیشنهاد، انتشار عمومی کد و داده‌های خام همراه با نسخه‌ی دقیق کتابخانه‌ها است. این کار امکان بازتولید کامل نتیجه‌ها را فراهم می‌کند و برای داوری مقرراتی لازم است.",
])

d.save(PATH)
print("saved", PATH)
