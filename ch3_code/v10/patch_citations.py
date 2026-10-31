# -*- coding: utf-8 -*-
"""Author-date citations with several authors (Turabian-style rule of the thesis guide):
two or three authors are listed (with 'و' before the last one); more than three authors
are written as 'و دیگران'. The author lists come from the reference list (checked by hand
against the entries; transliterations follow the names used in the text).
Reads and writes the v10 draft."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx_util import W, ptext, replace_in_text_nodes

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
d = docx.Document(PATH)
kids = list(d.element.body.iterchildren())
REF = [i for i, k in enumerate(kids) if ptext(k).strip() == "منابع و مأخذ"][-1]
MAP = {
    "هایرر": "هایرر، نورست و وانر",          # Hairer, Nørsett, Wanner (1993)
    "مک‌کی": "مک‌کی، بکمن و کانوِر",          # McKay, Beckman, Conover (2000)
    "معانی": "معانی، کوثری و فکور",           # 2014, three authors
    "ساداتی": "ساداتی، چگینی و سالاریه",       # 2017, three authors
    "علوی‌پور": "علوی‌پور، نیک‌خواه و روشنیان",  # 2017, three authors
    "اسکولیدو": "اسکولیدو و دیگران",          # four authors
    "ویرتانن": "ویرتانن و دیگران",
    "تالو": "تالو، آلسی و تومی",              # Talu, Alessi, Tommei (2021)
    "پروئیتی": "پروئیتی و دیگران",
    "امرت": "امرت و دیگران",
    "کاروالیو": "کاروالیو و دیگران",
    "تاکدا": "تاکدا و دیگران",
    "چن": "چن و دیگران",
    "سان‌خوان": "سان‌خوان، لتیزیا و لارا",      # San Juan, Letizia, Lara (2024)
    "ترسکو": "ترسکو و دیگران",
    "ترساکو": "ترسکو و دیگران",
    "پوتیش": "پوتیش و دیگران",
}
counts = {k: 0 for k in MAP}
for k in kids[240:REF]:
    for p in k.iter(W + "p"):
        for name, repl in MAP.items():
            while (name + " و همکاران") in ptext(p):
                if not replace_in_text_nodes(p, name + " و همکاران", repl):
                    break
                counts[name] += 1
print({k: v for k, v in counts.items() if v})
left = sum(ptext(k).count("و همکاران") for k in kids[240:REF])
print("remaining 'و همکاران' in chapters:", left)
d.save(PATH)
