# -*- coding: utf-8 -*-
"""Front matter patch: rewrites the Persian abstract with the recalculated numbers and
without the MATLAB sentence. Reads and writes _build/thesis_v10_draft.docx."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx_util import W, ptext, set_par_text

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
d = docx.Document(PATH)
kids = list(d.element.body.iterchildren())
hits = [k for k in kids[:400] if ptext(k).strip().startswith("استیج‌های بالایی موشک")]
assert len(hits) == 1, len(hits)
ABSTRACT = (
    "استیج‌های بالایی موشک‌های پرتاب که پس از جدایش ماهواره‌ها در مدار انتقال زمین‌ثابت باقی می‌مانند، با حضیض "
    "نزدیک به ۲۵۰ کیلومتر، ممکن است بیش از ۲۵ سال در فضا بمانند. هدف این پژوهش ارزیابی امکان دفع غیرفعال چنین "
    "استیجی با یک بادبان پسای ایده‌آل است. این پژوهش از نظر هدف کاربردی و از نظر روش، شبیه‌سازی عددی است. مدل A "
    "انتگرال‌گیری عددی کامل معادلات حرکت با ناکرویی زمین، پسای جوی، اختلالات ماه و خورشید و فشار تابش است؛ مدل B "
    "میانگین‌گیری مداری فقط با پسای جوی است. فضای ورود با نمونه‌برداری لاتین ابرمکعبی شانزده‌نقطه‌ای از آرگومان "
    "حضیض و طول گره‌ی صعودی ساخته شد. الگوریتم با پایتون (نامپای و اسسایپای) و انتگرال‌گیر DOP853 پیاده‌سازی شد. "
    "بدون بادبان، ۵ هندسه از ۱۶ هندسه در ۲۵ سال به ارتفاع ۱۲۰ کیلومتر می‌رسند (کسر انطباق ۳۱٫۳ درصد) و مدل فقط‌پسا "
    "عمر را حدود ۸ برابر بیش‌برآورد می‌کند. با بادبان ۱۴۰ متر مربعی، ۱۵ هندسه از ۱۶ هندسه با مدل نمایی و ۱۴ هندسه "
    "با مدل NRLMSIS 2.0 منطبق می‌شوند. عمر به مساحت بادبان یکنواخت نیست و مدل جو در برخی مساحت‌ها جهت حکم انطباق "
    "را وارونه می‌کند. بنابراین نتیجه‌ها به هندسه‌ی ورود و مدل جو وابسته‌اند و باید به‌صورت توزیع گزارش شوند؛ این "
    "نتیجه‌ها در طراحی استیج‌های داخلی و ارزیابی انطباق با قاعده‌ی ۲۵ ساله کاربرد دارند. نتایج با پیاده‌سازی پایتونی "
    "به‌دست آمده‌اند و کد آن در ضمیمه‌ها آمده است."
)
set_par_text(hits[0], ABSTRACT)
d.save(PATH)
print("abstract words:", len(ABSTRACT.split()))
