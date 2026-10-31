# -*- coding: utf-8 -*-
"""Chapter 3 and Model B label: update the lifetime definition, the reproduction table
(Table 3-3), the T4 result, the environment note, the NRLMSIS paragraph, and the Model B
row of Table 4-1. Reads and writes the v10 draft. Failed substitutions are reported."""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx_util import W, ptext, set_par_text, clone_par_after, replace_in_text_nodes

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
d = docx.Document(PATH)
kids = list(d.element.body.iterchildren())
failed = []

def find(prefix, last=False):
    hits = [k for k in kids if ptext(k).strip().startswith(prefix)]
    assert hits, prefix
    return hits[-1] if last else hits[0]

def rep(p, old, new, label):
    if not replace_in_text_nodes(p, old, new):
        failed.append(label)

def append_text(p, text):
    r = OxmlElement("w:r"); t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
    r.append(t); p.append(r)

def clear_par(p, text):
    """Replace the whole content by one run (keeps paragraph properties and bookmarks)."""
    rpr = None
    first = p.find(W + "r")
    if first is not None and first.find(W + "rPr") is not None:
        rpr = copy.deepcopy(first.find(W + "rPr"))
    for child in list(p):
        if child.tag not in (W + "pPr", W + "bookmarkStart", W + "bookmarkEnd"):
            p.remove(child)
    r = OxmlElement("w:r")
    if rpr is not None: r.append(rpr)
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
    r.append(t); p.append(r)

# ---- section 3-6: definition of the lifetime ----
p = find("زمان عبور از حضیض و زمان نخستین رسیدن")
rep(p, "در اجراهای گزارش‌شده، فقط این آستانه‌ی ۱۲۰ کیلومتری پایان انتگرال‌گیری است.",
    "در اجراهای گزارش‌شده، آستانه‌ی ۱۲۰ کیلومتری پایان انتگرال‌گیری است و عمر با نخستین رخداد از دو رخداد زیر تعیین می‌شود: "
    "نخستین عبور حضیض زیر ۱۲۰ کیلومتر، یا رسیدن شعاعی به ۱۲۰ کیلومتر؛ هر کدام زودتر رخ دهد.", "def-1")
p = find("عمر مداری در این پژوهش برابر است")
rep(p, "این رسیدن، عبور رو به پایین از آستانه است.",
    "این رسیدن، عبور رو به پایین از آستانه است و زمان ورود برابر کمینه‌ی زمان رسیدن شعاعی و زمان نخستین عبور حضیض زیر ۱۲۰ کیلومتر است (بخش ۴-۲-۳).", "def-2")

# ---- section 3-7: environments ----
p = find("کد مرجع این پژوهش به زبان پایتون")
append_text(p, " محیط ب با تعریف قبلی عمر اجرا شده و برای تعریف جدید بازاجرا نشده است؛ بنابراین عددهای جدول ۳-۳ برای تعریف جدید از محیط الف گرفته شده‌اند.")

# ---- Table 3-3 (reproduction) ----
cap = find("جدول ۳-۳:")
tbl = kids[kids.index(cap) + 1]
assert tbl.tag == W + "tbl"
rows = list(tbl.iter(W + "tr"))
header = ["ردیف", "حالت", "مقدار مرجع (نمایی، سال)", "بازتولید، محیط الف (سال)", "اختلاف (درصد)",
          "NRLMSIS 2.0 (سال)", "اختلاف NRLMSIS نسبت به نمایی (درصد)"]
data = [
    ["۱", "کوتاه‌عمر، ω = ۲۷٫۴۹، Ω = ۱۷۵٫۶۲، بدون بادبان", "۰٫۲۹۱۲", "۰٫۲۹۱۱۸", "−۰٫۰۱", "۰٫۲۹۱۲۶", "+۰٫۰۳"],
    ["۲", "بدون بادبان، ω = Ω = ۰", "۷٫۴۹۲۵", "۷٫۴۹۲۴۷", "۰٫۰۰", "۵٫۵۵۰۲", "−۲۵٫۹"],
    ["۳", "بادبان ۱۴۰ متر مربع، ω = ۲۷۰، Ω = ۰", "۱۱٫۹۰۲", "۱۱٫۹۰۱۶۴", "۰٫۰۰", "۱۵٫۱۰۳", "+۲۶٫۹"],
    ["۴", "تلرانس نسبی ۱۰⁻⁹ تا ۱۰⁻۱۱ (ردیف ۱)", "۰٫۲۹۱۱۸", "۰٫۲۹۱۱۸ (هر سه)", "۰٫۰۰", "—", "—"],
]
for ci, c in enumerate(rows[0].findall(W + "tc")):
    clear_par(c.find(W + "p"), header[ci] if ci < len(header) else "")
for ri, vals in enumerate(data, start=1):
    cells = rows[ri].findall(W + "tc")
    for ci, c in enumerate(cells):
        clear_par(c.find(W + "p"), vals[ci])
for extra in rows[len(data) + 1:]:
    tbl.remove(extra)

p = find("جدول ۳-۳ نتیجه‌های بازتولید")
clear_par(p, ("جدول ۳-۳ بازتولید سه حالت مرجع و همگرایی تلرانس را با تعریف جدید رخداد نشان می‌دهد. در محیط الف، هر سه حالت "
              "با اختلافی کمتر از ۰٫۰۱ درصد نسبت به مقدار مرجع بازتولید شده‌اند. کاهش تلرانس نسبی از ۱۰⁻⁹ به ۱۰⁻۱۱ عمر حالت "
              "کوتاه‌عمر را تغییر نمی‌دهد (۰٫۲۹۱۱۸ سال در هر سه تلرانس؛ بخش ۴-۲-۱). ستون NRLMSIS همان حالت‌ها را با مدل چگالی "
              "NRLMSIS 2.0 نشان می‌دهد و اختلاف آن با مدل نمایی در بخش ۴-۷ بحث می‌شود. هدف این جدول بازتولیدپذیری و سنجش "
              "حساسیت به مدل جو است، نه مقایسه‌ی عددهای مرجع با یکدیگر، زیرا هر سه حالت هندسه‌های متفاوتی دارند."))

# ---- T4 row of Table 3-5 ----
done_t4 = False
for r in d.element.body.iter(W + "tr"):
    cells = r.findall(W + "tc")
    if cells and "T4" in ptext(cells[0]):
        for c in cells:
            if "۰٫۸ درصد" in ptext(c):
                clear_par(c.find(W + "p"), "اختلاف ۰٫۰ درصد (هر سه تلرانس ۰٫۲۹۱۱۸ سال)")
                done_t4 = True
        break
if not done_t4:
    failed.append("T4 cell")

# ---- chapter 3 global number updates (same as chapter 4) ----
GLOBAL = [("۸٫۰۵", "۸٫۰۶"), ("۴٫۶۷", "۴٫۶۶"), ("۷٫۵۰", "۷٫۴۹"), ("۸٫۱۰", "۸٫۱۱")]
start = max(i for i, k in enumerate(kids) if ptext(k).strip().startswith("فصل سوم") and len(ptext(k)) < 90)
stop = max(i for i, k in enumerate(kids) if ptext(k).strip().startswith("فصل چهارم") and len(ptext(k)) < 90)
for old, new in GLOBAL:
    for k in kids[start:stop]:
        for pp in k.iter(W + "p"):
            while old in ptext(pp):
                if not replace_in_text_nodes(pp, old, new):
                    break

# ---- section 3-9-3: consequence for lifetime ----
nxt = find("۳-۹-۴ مقایسه با داده‌های پروازی")
prev_p = kids[kids.index(nxt) - 1]
body_tpl = find("کد مرجع این پژوهش به زبان پایتون")
clone_par_after(prev_p, body_tpl, (
    "این بیش‌برآورد چگالی به عمر مداری یکنوا منتقل نمی‌شود. در حالت بدون بادبان، NRLMSIS عمر را ۲۵٫۹ درصد کوتاه‌تر و در "
    "حالت بادبان ۱۴۰ متر مربعی با ω = ۲۷۰، عمر را ۲۶٫۹ درصد بلندتر می‌کند (جدول ۳-۳ و بخش ۴-۷). پس مدل جو باید در "
    "گزارش انطباق به‌صورت جداگانه بررسی شود."))

# ---- Table 4-1: label of the Model B rows ----
for tbl4 in d.tables:
    hdr = [c.text for c in tbl4.rows[0].cells]
    if any("مقدارهای بررسی" in h for h in hdr):
        set_par_text(tbl4.rows[1].cells[1].paragraphs[0]._p, "تعداد نقاط در هر دور (بادبان ۱۴۰ متر مربع، ω = Ω = ۰)")
        set_par_text(tbl4.rows[2].cells[1].paragraphs[0]._p, "بیشینه‌ی گام (روز)، همان حالت")
        break
ex = find("تفسیر جدول ۴-۱:")
clone_par_after(ex, body_tpl, (
    "عدد ۵٫۱۴۹۹ سال مربوط به مدل B با بادبان ۱۴۰ متر مربع و ω = Ω = ۰ است و با فایل results/model_B_convergence.json "
    "بازتولید شد. مدل B بدون بادبان در همان حالت اولیه ۶۰٫۷۷ سال می‌دهد (جدول ۴-۳)."))

d.save(PATH)
print("saved", PATH)
print("failed substitutions:", failed)
