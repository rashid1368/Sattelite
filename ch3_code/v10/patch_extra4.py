# -*- coding: utf-8 -*-
"""Fourth batch of text: computational cost (chapter 4), a twelfth limitation and a
design-guidance section (chapter 5), and a lead-in paragraph for chapter 5.
Reads and writes _build/thesis_v10_draft.docx."""
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

# chapter 4: computational cost, after the 100-year paragraph
chain(find("در بخش ۴-۷-۱ افق ۱۰۰ ساله"), [
    "زمان محاسبه‌ی هر اجرا به مدل جو و افق زمانی وابسته است. اجرای ۱۰۰ ساله با مدل نمایی برای مساحت ۱۳۰ متر مربع حدود ۲۴ دقیقه (۱۴۶۰ ثانیه) در یک هسته‌ی پردازشی طول کشید، در حالی که اجرای ۲۵ ساله‌ی NRLMSIS بین ۳۶۰ تا ۸۶۰ ثانیه بود. هزینه‌ی NRLMSIS بیشتر از ساختن جدول چگالی ناشی می‌شود که در بازه‌های ۳۰ روزه به‌روز می‌شود. این زمان‌ها نشان می‌دهند که اجرای کامل شبکه‌ی ۱۶ هندسه با افق ۱۰۰ ساله و هر دو مدل از نظر محاسباتی قابل انجام است، اما باید به‌صورت دسته‌ای و موازی اجرا شود.",
])

# chapter 4: methodological note after the sweep discussion
chain(find("این یافته‌ها نشان می‌دهند که عمر در جاروب"), [
    "نکته‌ی روش‌شناختی آن است که جاروب مساحت برای یک هندسه‌ی ورود انجام شده و تعمیم آن به همه‌ی ۱۶ هندسه نیاز به اجرای جداگانه دارد. بنابراین ناهمواری عمر در جاروب ω = ۲۷۰ یک شاهد جزئی است و نه یک برآورد آماری از کل فضای ورود.",
])

# chapter 5: lead-in paragraph after the main message paragraph
chain(find("پیام مرکزی این فصل"), [
    "ساختار بحث در ادامه چنین است: نخست نتیجه‌های هر فرضیه تفسیر می‌شوند (بخش‌های ۵-۲-۱ تا ۵-۲-۴)، سپس تفسیر نوسان عمر با مدل جو و تعریف رخداد آورده می‌شود (بخش‌های ۵-۲-۵ تا ۵-۲-۸)، و پس از آن پاسخ به پرسش‌ها، محدودیت‌ها، پیشنهادها و ترتیب آزمون‌های باقی‌مانده می‌آید.",
])

# chapter 5: twelfth limitation after the eleventh
chain(find("یازدهمین محدودیت، فرض مدل نگرش ثابت"), [
    "دوازدهمین محدودیت، نبود داده‌ی پروازی برای مدار انتقال زمین‌ثابت است. آزمون مدل با داده‌ی پروازی تنها برای ALE-1 امکان‌پذیر بود و آن نیز برای مسیر فرود است. بنابراین هیچ شاهد پروازی مستقیمی برای مرحله‌ی بلندمدت عمر در مدار انتقال وجود ندارد و اعتبار نتیجه‌ها بر پایه‌ی صحت فیزیکی مدل و همگرایی عددی است.",
])

# chapter 5: design guidance section after 5-2-8
anc = find("در هر حال، این پژوهش داده‌ی پروازی کاملی")
prev = clone_par_after(anc, T_H3_5, "۵-۲-۹ پیام برای طراحی استیج‌های داخلی")
chain(prev, [
    "استیج‌های داخلی، یعنی استیج‌هایی که در صنعت فضایی کشور ساخته یا به کار گرفته می‌شوند، معمولاً جرم، ارتفاع حضیض و زمان جدایش مشخصی دارند که با این پژوهش تطبیق‌پذیرند. پیام طراحی برای چنین استیج‌هایی دو بخش دارد. بخش نخست، ارزیابی هندسه‌ی ورود است؛ یعنی پیش از تعیین مساحت، ω و Ω را در لحظه‌ی جدایش برآورد کرد و نسبت به خطای آن‌ها حساسیت را سنجید.",
    "بخش دوم، انتخاب مساحت با حاشیه است. با توجه به بخش ۵-۲-۶، مساحتی که در هر دو مدل جو منطبق باشد باید پایه‌ی طراحی قرار گیرد. افزودن جرم بادبان، همراه با حاشیه‌ی جرم، باید بر پایه‌ی بودجه‌ی واقعی استیج ارزیابی شود و نه بر پایه‌ی بیشینه‌ی تئوریک.",
    "در نهایت، این پژوهش پیشنهاد می‌کند که گزارش طراحی بادبان برای استیج داخلی پیش از تصویب، هر سه مؤلفه‌ی هندسه، مساحت و مدل جو را به‌صورت جدولی ارائه کند. این روش امکان می‌دهد که نهادهای مقرراتی و تیم طراحی روی همان عدد توافق کنند، بی‌آنکه حکم انطباق به یک عدد خوش‌بینانه تقلیل یابد.",
])

d.save(PATH)
print("saved", PATH)
