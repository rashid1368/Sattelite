# -*- coding: utf-8 -*-
"""Remove the MATLAB comparison from chapter 1 (paragraphs about verification) and
replace the footnotes that named MATLAB and Python. Reads and writes the v10 draft."""
import os, sys, re, zipfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx_util import W, ptext, set_par_text, replace_in_text_nodes

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
d = docx.Document(PATH)
kids = list(d.element.body.iterchildren())

def one_text(old):
    hits = [p for k in kids for p in ([k] if k.tag == W + "p" else k.iter(W + "p")) if old in ptext(p)]
    assert len(hits) == 1, (old[:40], len(hits))
    return hits[0]

def sub(old, new, para=None):
    p = para if para is not None else one_text(old)
    assert replace_in_text_nodes(p, old, new), ("node", old[:40])

# paragraph with the footnote marks 1-3
p400 = one_text("اعتبار عددی سه سطح دارد")
sub("مقایسه‌ی متلب", "بازتولیدپذیری نتیجه‌ها", para=p400)
sub(" و پایتون", " و اجرای پایتونی", para=p400)
sub(" نیز باید با ورودی یکسان و ", " با ورودی یکسان و ", para=p400)
sub("تلرانس مشخص انجام شود. اختلاف خروجی باید بر اساس", "تلرانس مشخص انجام شده است. اختلاف خروجی‌ها بر اساس", para=p400)
sub("بررسی شود.", "بررسی شده است.", para=p400)

# paragraph that compared MATLAB and Python
p401 = one_text("در مقایسه‌ی متلب و پایتون")
set_par_text(p401, (
    "در بازتولیدپذیری کد، یکسان‌بودن معادلات به‌تنهایی کافی نیست. قرارداد دستگاه مختصات، ترتیب مؤلفه‌های حالت، "
    "علامت سرعت زاویه‌ای زمین، واحد زاویه‌ها و تعریف ارتفاع باید یکسان باشد. خطا در تبدیل درجه و رادیان یا در تبدیل "
    "شعاع و ارتفاع می‌تواند خروجی ظاهراً معقول اما فیزیکی نادرست تولید کند. بنابراین، پیش از بررسی عمر مداری، باید یک "
    "حالت کوتاه‌مدت با خروجی بردار حالت در چند زمان مشترک بازبینی شود."))

d.save(PATH)

# footnotes 49 (MATLAB) and 50 (Python): rewrite their text in the package part
def fix(m):
    open_tag, fid, body = m.group(1), m.group(2), m.group(3)
    if fid == "49":
        body = re.sub(r"<w:t[^>]*>[^<]*MATLAB[^<]*</w:t>",
                      "<w:t>نسخه‌ی کد و کتابخانه‌های به‌کاررفته در بخش ۲-۶-۴ معرفی شده‌اند.</w:t>", body)
    if fid == "50":
        body = re.sub(r"<w:t[^>]*>[^<]*Python[^<]*</w:t>",
                      "<w:t>Python 3 with NumPy and SciPy libraries.</w:t>", body)
    return open_tag + body + "</w:footnote>"

tmp = PATH + ".tmp"
with zipfile.ZipFile(PATH) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/footnotes.xml":
            x = data.decode("utf8")
            x = re.sub(r'(<w:footnote [^>]*w:id="(\d+)"[^>]*>)(.*?)</w:footnote>', fix, x, flags=re.S)
            data = x.encode("utf8")
        zout.writestr(item, data)
shutil.move(tmp, PATH)
print("saved", PATH)
