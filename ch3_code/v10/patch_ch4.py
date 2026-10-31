# -*- coding: utf-8 -*-
"""Chapter 4 patch: v9 -> _build/thesis_v10_ch4.docx.

Replaces numbers that were recalculated (tolerance convergence, Model B ratios,
NRLMSIS reference cases and the omega=270 sweep) and rewrites the paragraphs whose
conclusions no longer hold (one-way atmospheric bias, 'upper bound' claims).
"""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx_util import W, ptext, set_par_text, clone_par_after, replace_in_text_nodes

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "Haddadi_MSc_thesis_GTO_sail_deorbit_v9_ch1_ch5.docx")
DST = os.path.join(ROOT, "_build", "thesis_v10_ch4.docx")

d = docx.Document(SRC)
body = d.element.body
kids = list(body.iterchildren())
CH4_START, CH4_END = 825, 918     # Heading 'فصل چهارم' .. heading 'فصل پنجم'
log = []

def region(a, b):
    return kids[a:b]

def all_pars(a, b):
    out = []
    for el in region(a, b):
        out.extend(el.iter(W + "p"))
    return out

def rewrite_par(prefix, new_text, a=CH4_START, b=CH4_END):
    hits = [p for p in all_pars(a, b) if ptext(p).strip().startswith(prefix)]
    assert len(hits) == 1, (prefix, len(hits))
    set_par_text(hits[0], new_text)
    log.append("rewrite: " + prefix[:40])
    return hits[0]

def replace_sentence(prefix, old_sub, new_sub, a=CH4_START, b=CH4_END):
    hits = [p for p in all_pars(a, b) if old_sub in ptext(p)]
    assert len(hits) == 1, (old_sub[:40], len(hits))
    p = hits[0]
    if not replace_in_text_nodes(p, old_sub, new_sub):
        set_par_text(p, ptext(p).replace(old_sub, new_sub))
    log.append("sentence: " + old_sub[:40])
    return p

# ---- 1. global numeric updates inside chapter 4 (single-text-node replacements) ----
GLOBAL = [
    ("۸٫۰۵", "۸٫۰۶"),   # J2+drag / full ratio (60.36/7.4925)
    ("۴٫۶۷", "۴٫۶۶"),   # 60.36/12.94
    ("۷٫۵۰", "۷٫۴۹"),   # full model, natural, omega=0 (7.4925)
    ("۸٫۱۰", "۸٫۱۱"),   # Model B / full (60.77/7.4925)
]
n_global = 0
for old, new in GLOBAL:
    for p in all_pars(CH4_START, CH4_END):
        while old in ptext(p):
            if replace_in_text_nodes(p, old, new):
                n_global += 1
            else:
                set_par_text(p, ptext(p).replace(old, new)); n_global += 1
                break
log.append("global replacements: %d" % n_global)

# ---- 2. Table 4-1 tolerance row: new converged values ----
tables = d.tables
t41 = tables[13]
assert "۰٫۲۹۳۵" in t41.rows[3].cells[3].text, t41.rows[3].cells[3].text
set_par_text(t41.rows[3].cells[3].paragraphs[0]._p, "۰٫۲۹۱۱۸، ۰٫۲۹۱۱۸، ۰٫۲۹۱۱۸")
log.append("table 4-1 tolerance row")

# ---- 3. Paragraph on tolerance (4-2-1) ----
rewrite_par("در مدل A، کاهش تلرانس نسبی", (
    "در مدل A، با کاهش تلرانس نسبی از ۱۰⁻⁹ به ۱۰⁻¹⁰ و سپس به ۱۰⁻¹¹، زمان رسیدن به ۱۲۰ کیلومتر "
    "در هر سه حالت ۰٫۲۹۱۱۸ سال می‌ماند و تغییر نسبی آن صفر است. این پایداری نتیجه‌ی اصلاح تعریف "
    "رخداد است. در نسخه‌ی پیشین، رخداد شعاعی شیب‌های کم‌عمق نزدیک حضیض را از دست می‌داد و زمان ورود "
    "با تغییر تلرانس جابه‌جا می‌شد (۰٫۸ و ۱۰٫۵ درصد). با تعریف مبتنی بر حضیض، این ناپایداری دیگر دیده "
    "نمی‌شود. بنابراین عمر حالت‌های کوتاه‌عمر و بلندعمر هر دو با دقت عددی مدل نمایی گزارش می‌شوند."))

# ---- 4. Table 4-6 (atmosphere): rebuild rows ----
t46 = tables[18]
header = [c.text for c in t46.rows[0].cells]
assert header[1].startswith("مدل نمایی"), header
rows_new = [
    ["کوتاه‌عمر، ω = ۲۷٫۵", "۰٫۲۹۱۲", "۰٫۲۹۱۳", "+۰٫۰", "توافق دو مدل در ارتفاع پایین"],
    ["بدون بادبان، ω = Ω = ۰", "۷٫۴۹", "۵٫۵۵", "−۲۵٫۹", "عمر NRLMSIS کوتاه‌تر است"],
    ["بادبان ۱۴۰ متر مربع، ω = ۲۷۰", "۱۱٫۹۰", "۱۵٫۱۰", "+۲۶٫۹", "عمر NRLMSIS بلندتر است؛ کمینه‌ی حضیض ۱۴۲٫۴ کیلومتر"],
    ["بادبان ۸۰ متر مربع، ω = ۲۷۰", "۱۸٫۰۵", "بیش از ۲۵", "—", "حکم انطباق وارونه می‌شود"],
    ["بادبان ۱۲۵ متر مربع، ω = ۲۷۰", "۱۵٫۱۵", "۱۴٫۱۴", "−۶٫۷", "هر دو مدل منطبق"],
    ["بادبان ۱۳۰ متر مربع، ω = ۲۷۰", "بیش از ۲۵", "۱۳٫۹۲", "—", "حکم انطباق وارونه می‌شود"],
    ["بادبان ۲۵۰ متر مربع، ω = ۲۷۰", "۷٫۲۶", "۲۴٫۴۶", "+۲۳۷", "هر دو مدل منطبق"],
    ["بادبان ۳۰۰ متر مربع، ω = ۲۷۰", "۱۰٫۰۵", "۱۶٫۹۹", "+۶۹", "هر دو مدل منطبق"],
    ["بادبان ۴۰۰ متر مربع، ω = ۲۷۰", "۱۸٫۱۴", "۹٫۱۴", "−۴۹٫۶", "هر دو مدل منطبق"],
]
tmpl = t46.rows[1]._tr
for _ in range(len(rows_new) - (len(t46.rows) - 1)):
    t46._tbl.append(copy.deepcopy(tmpl))
for r_i, vals in enumerate(rows_new, start=1):
    row = t46.rows[r_i]
    for c_i, v in enumerate(vals):
        set_par_text(row.cells[c_i].paragraphs[0]._p, v)
log.append("table 4-6 rebuilt: %d rows" % len(rows_new))

# caption of table 4-6
cap = [p for p in all_pars(CH4_START, CH4_END) if ptext(p).startswith("جدول ۴-۶:")]
assert len(cap) == 1
set_par_text(cap[0], "جدول ۴-۶: اثر مدل جو بر زمان رسیدن به ۱۲۰ کیلومتر در حالت‌های مرجع و در جاروب ω = ۲۷۰ (F10.7 = ۱۳۰، Ap = ۱۰)")

# intro of 4-7
replace_sentence("مدل جو", "سه حالت مرجع با مدل NRLMSIS 2.0 دوباره اجرا شدند",
                 "سه حالت مرجع و جاروب ۸ مساحتی ω = ۲۷۰ با مدل NRLMSIS 2.0 دوباره اجرا شدند")

# ---- 5. interpretation paragraphs of 4-7 ----
rewrite_par("تفسیر جدول ۴-۶:", (
    "تفسیر جدول ۴-۶: در حالت کوتاه‌عمر، دو مدل تقریباً یک نتیجه می‌دهند (۰٫۲۹۱۲ در برابر ۰٫۲۹۱۳ سال). "
    "در حالت بدون بادبان، NRLMSIS عمر را از ۷٫۴۹ به ۵٫۵۵ سال کاهش می‌دهد (۲۵٫۹ درصد کوتاه‌تر)، اما در "
    "حالت بادبان ۱۴۰ متر مربع با ω = ۲۷۰، عمر از ۱۱٫۹۰ به ۱۵٫۱۰ سال افزایش می‌یابد (۲۶٫۹ درصد بلندتر). "
    "جهت تغییر در این دو حالت یکی نیست. این جهت با نسبت چگالی بخش ۳-۹-۳ هم یکی نیست: نمایی در ارتفاع‌های "
    "۲۰۰ تا ۳۰۰ کیلومتر حدود ۱٫۴ تا ۱٫۶ برابر چگالی NRLMSIS است و انتظار می‌رفت عمر نمایی همه‌جا کوتاه‌تر باشد."))

rewrite_par("این نتیجه دو پیامد دارد.", (
    "این نتیجه سه پیامد دارد. نخست، جهت خطای مدل جو در عمر یکنواخت نیست. جاروب ω = ۲۷۰ این موضوع را روشن "
    "می‌کند: مدل نمایی برای ۸۰ متر مربع عمر ۱۸٫۰۵ سال و برای ۱۳۰ متر مربع بیش از ۲۵ سال می‌دهد، در حالی "
    "که NRLMSIS برای ۸۰ متر مربع به ۱۲۰ کیلومتر نمی‌رسد و برای ۱۳۰ متر مربع عمر ۱۳٫۹۲ سال می‌دهد. یعنی "
    "حکم انطباق در هر دو مورد با تغییر مدل جو وارونه می‌شود. دوم، نسبت عمر دو مدل در حالت‌های جاروب از "
    "۰٫۵۰ تا ۳٫۳۷ تغییر می‌کند (جدول ۴-۶). سوم، این نوسان در مرحله‌ی اولیه‌ی مسیر دیده نمی‌شود. در حالت "
    "بدون بادبان، مسیر حضیض در یک سال نخست در هر دو مدل تا حدود دو کیلومتر به هم نزدیک است و تنها لحظه‌ی "
    "عبور حضیض از ۱۲۰ کیلومتر جابه‌جا می‌شود. پس عمر یک رخداد آستانه‌ای و حساس به فاز است و نسبت آن به "
    "نسبت چگالی ساده نیست."))

replace_sentence("در عین حال", "و تغییر مدل جو آن‌ها را از بین نمی‌برد؛ فقط مقدار عددی و کسر انطباق را جابه‌جا می‌کند.",
                 "و تغییر مدل جو آن‌ها را از بین نمی‌برد. جاروب NRLMSIS هم عمر را نسبت به مساحت غیریکنوا نشان "
                 "می‌دهد: ۱۴۰ و ۲۵۰ متر مربع منطبق‌اند، اما ۱۶۰ متر مربع منطبق نیست. مدل جو فقط مقدار عددی و کسر "
                 "انطباق را جابه‌جا می‌کند.")

rewrite_par("حکم این بخش: کسرهای انطباق", (
    "حکم این بخش: کسرهای انطباق گزارش‌شده در بخش ۴-۵ با مدل نمایی به‌دست آمده‌اند و جهت خطای آن‌ها ثابت "
    "نیست. در جاروب ω = ۲۷۰ دو حالت (۸۰ و ۱۳۰ متر مربع) با تغییر مدل جو حکم خود را عوض می‌کنند. بنابراین "
    "کسر انطباق بخش ۴-۵ را نمی‌توان کران بالای انطباق دانست. برای حکم مقرراتی نهایی، کل شبکه‌ی ۱۶ هندسه "
    "باید با NRLMSIS 2.0 و با افق‌های ۲۵ و ۱۰۰ سال اجرا شود؛ جاروب ω = ۲۷۰ نخستین گام این کار است."))

# ---- 6. ALE-1 conclusion ----
replace_sentence("حکم این بخش: مدل این پژوهش", "بنابراین، عمرهای گزارش‌شده در این فصل کران پایین عمر واقعی‌اند.",
                 "بنابراین، برای مسیر فرود ALE-1 مدل نمایی عمر را کوتاه‌تر از واقعیت برآورد می‌کند. این جهت خطا "
                 "برای این مسیر معتبر است و به همه‌ی هندسه‌ها تعمیم داده نمی‌شود (بخش ۴-۷).")

# ---- 7. chapter-4 summary limitation ----
replace_sentence("سه محدودیت، دامنه", "نخست، همه‌ی اجراها با مدل نمایی جو انجام شده‌اند و همان‌گونه که در بخش ۴-۷ نشان داده شد، این مدل عمر را کوتاه‌تر و انطباق را آسان‌تر از واقعیت نشان می‌دهد؛ پس کسرهای انطباق کران بالا هستند.",
                 "نخست، بیشتر اجراها با مدل نمایی جو انجام شده‌اند. بخش ۴-۷ نشان داد که جهت سوگیری عمر در مدل جو یکنواخت "
                 "نیست؛ بنابراین کسرهای انطباق این فصل را نمی‌توان کران بالا یا پایین دانست و باید با NRLMSIS کامل شوند.")

d.save(DST)
print("saved", DST)
print("\n".join(log))
