# -*- coding: utf-8 -*-
import io, sys
from pptx import Presentation
from pptx.util import Emu
out = io.open("ref_dump.txt","w",encoding="utf-8")
def w(*a): out.write(" ".join(str(x) for x in a)+"\n")
p = Presentation(r"D:\Downloads\Documents\Satellite\ارائه_دفاع_پریسا_باقری.pptx")
w("SLIDE SIZE:", p.slide_width, p.slide_height, p.slide_width/914400, "x", p.slide_height/914400, "in")
w("N SLIDES:", len(p.slides))
for i, s in enumerate(p.slides, 1):
    w("="*70)
    w(f"SLIDE {i}  layout={s.slide_layout.name}")
    try:
        bg = s.background.fill
        w("  BG type:", bg.type, getattr(bg.fore_color,'rgb',None) if bg.type==1 else "")
    except Exception as e:
        w("  BG err", e)
    for sh in s.shapes:
        w(f"  [{sh.shape_type}] name={sh.name!r} pos=({Emu(sh.left).inches:.2f},{Emu(sh.top).inches:.2f}) size=({Emu(sh.width).inches:.2f}x{Emu(sh.height).inches:.2f})")
        try:
            f = sh.fill
            if f.type == 1:
                w(f"      fill=solid rgb={f.fore_color.rgb}")
            else:
                w(f"      fill=type{f.type}")
        except Exception as e:
            w("      fill n/a")
        if sh.has_text_frame:
            for para in sh.text_frame.paragraphs:
                runs=[]
                for r in para.runs:
                    f=r.font; col=None
                    try:
                        if f.color and f.color.type is not None: col=str(f.color.rgb)
                    except: pass
                    runs.append((r.text, f.name, f.size.pt if f.size else None, f.bold, col))
                if runs:
                    w(f"      L{para.level} align={para.alignment} :: {runs}")
out.close()
print("done")
