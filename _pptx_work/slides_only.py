# -*- coding: utf-8 -*-
import io
from pptx import Presentation
out=io.open("ref_text.txt","w",encoding="utf-8")
p=Presentation(r"D:\Downloads\Documents\Satellite\ارائه_دفاع_پریسا_باقری.pptx")
for i,s in enumerate(p.slides,1):
    out.write(f"\n===== SLIDE {i} =====\n")
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            t=sh.text_frame.text.replace("\n"," | ").replace("\x0b"," / ")
            out.write(f"  - {t}\n")
        elif sh.shape_type==13:
            out.write(f"  [IMG {sh.name}]\n")
out.close()
print("ok")
