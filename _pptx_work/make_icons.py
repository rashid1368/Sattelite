# -*- coding: utf-8 -*-
"""Generate flat geometric badge icons in the reference deck's icon style.

Each icon is a 256x256 RGBA PNG with a single-colour glyph on transparency,
so it can be tinted per-card by recolouring at generation time.
"""
import os
from PIL import Image, ImageDraw

OUT = "icons"
os.makedirs(OUT, exist_ok=True)

S = 256
W = 7  # stroke width


def blank():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def save(name, im):
    im.save(os.path.join(OUT, name + ".png"))
    print("  ", name)


# ---------------------------------------------------------------- glyph draw
def g_target(d, c):
    d.ellipse([c - 82, c - 82, c + 82, c + 82], outline=255, width=W)
    d.ellipse([c - 46, c - 46, c + 46, c + 46], outline=255, width=W)
    d.ellipse([c - 12, c - 12, c + 12, c + 12], fill=255)


def g_sail(d, c):
    # a deployed drag sail: mast + quad sail
    d.line([c - 74, c + 86, c + 62, c - 84], fill=255, width=W)
    d.line([c + 62, c - 84, c + 86, c + 60], fill=255, width=W)
    d.line([c + 86, c + 60, c - 74, c + 86], fill=255, width=W)
    d.line([c - 74, c + 86, c - 66, c - 40], fill=255, width=W)


def g_stage(d, c):
    # upper stage: cylinder body + nozzle
    d.rounded_rectangle([c - 46, c - 92, c + 46, c + 58], radius=10,
                        outline=255, width=W)
    d.polygon([(c - 46, c + 58), (c + 46, c + 58), (c + 26, c + 100),
               (c - 26, c + 100)], outline=255, width=W)
    d.line([c - 46, c - 20, c + 46, c - 20], fill=255, width=W)


def g_orbit(d, c):
    d.ellipse([c - 92, c - 40, c + 92, c + 40], outline=255, width=W)
    d.ellipse([c - 26, c - 26, c + 26, c + 26], fill=255)


def g_chart(d, c):
    d.line([c - 88, c + 82, c - 88, c - 76], fill=255, width=W)
    d.line([c - 88, c + 82, c + 88, c + 82], fill=255, width=W)
    d.rectangle([c - 66, c + 12, c - 34, c + 82], fill=255)
    d.rectangle([c - 14, c - 40, c + 18, c + 82], fill=255)
    d.rectangle([c + 38, c - 82, c + 70, c + 82], fill=255)


def g_wind(d, c):
    d.arc([c - 90, c - 78, c + 30, c + 12], 90, 270, fill=255, width=W)
    d.arc([c - 62, c - 34, c + 58, c + 56], 90, 270, fill=255, width=W)
    d.arc([c - 34, c + 10, c + 86, c + 100], 90, 270, fill=255, width=W)


def g_shield(d, c):
    d.polygon([(c, c - 92), (c + 76, c - 54), (c + 76, c + 18),
               (c, c + 92), (c - 76, c + 18), (c - 76, c - 54)],
              outline=255, width=W)


def g_warn(d, c):
    d.polygon([(c, c - 88), (c + 94, c + 76), (c - 94, c + 76)],
              outline=255, width=W)
    d.line([c, c - 26, c, c + 22], fill=255, width=W)
    d.ellipse([c - 9, c + 40, c + 9, c + 58], fill=255)


def g_gear(d, c):
    d.ellipse([c - 86, c - 86, c + 86, c + 86], outline=255, width=W)
    d.ellipse([c - 34, c - 34, c + 34, c + 34], outline=255, width=W)
    for k in range(8):
        import math
        a = math.radians(k * 45)
        x0 = c + math.cos(a) * 86
        y0 = c + math.sin(a) * 86
        x1 = c + math.cos(a) * 116
        y1 = c + math.sin(a) * 116
        d.line([x0, y0, x1, y1], fill=255, width=W + 2)


def g_calendar(d, c):
    d.rounded_rectangle([c - 84, c - 68, c + 84, c + 84], radius=10,
                        outline=255, width=W)
    d.line([c - 84, c - 20, c + 84, c - 20], fill=255, width=W)
    d.line([c - 46, c - 92, c - 46, c - 46], fill=255, width=W)
    d.line([c + 46, c - 92, c + 46, c - 46], fill=255, width=W)


def g_flask(d, c):
    d.line([c - 34, c - 92, c - 34, c - 34], fill=255, width=W)
    d.line([c + 34, c - 92, c + 34, c - 34], fill=255, width=W)
    d.line([c - 34, c - 92, c + 34, c - 92], fill=255, width=W)
    d.polygon([(c - 34, c - 34), (c + 34, c - 34), (c + 74, c + 84),
               (c - 74, c + 84)], outline=255, width=W)
    d.line([c - 60, c + 30, c + 60, c + 30], fill=255, width=W)


def g_doc(d, c):
    d.rounded_rectangle([c - 70, c - 92, c + 70, c + 92], radius=8,
                        outline=255, width=W)
    for i, y in enumerate((-50, -14, 22, 58)):
        d.line([c - 40, c + y, c + 40 - i * 12, c + y], fill=255, width=W)


def g_code(d, c):
    d.line([c - 40, c - 60, c - 92, c, c - 40, c + 60], fill=255,
           width=W + 2, joint="curve")
    d.line([c + 40, c - 60, c + 92, c, c + 40, c + 60], fill=255,
           width=W + 2, joint="curve")


def g_sun(d, c):
    d.ellipse([c - 40, c - 40, c + 40, c + 40], outline=255, width=W)
    import math
    for k in range(8):
        a = math.radians(k * 45)
        d.line([c + math.cos(a) * 58, c + math.sin(a) * 58,
                c + math.cos(a) * 94, c + math.sin(a) * 94],
               fill=255, width=W)


def g_moon(d, c):
    d.ellipse([c - 80, c - 80, c + 80, c + 80], outline=255, width=W)
    d.ellipse([c - 40, c - 92, c + 100, c + 72], fill=(0, 0, 0, 0))


def g_sat(d, c):
    d.rectangle([c - 30, c - 34, c + 30, c + 34], outline=255, width=W)
    d.rectangle([c - 96, c - 22, c - 40, c + 22], outline=255, width=W)
    d.rectangle([c + 40, c - 22, c + 96, c + 22], outline=255, width=W)
    d.line([c, c - 34, c, c - 76], fill=255, width=W)
    d.arc([c - 26, c - 108, c + 26, c - 44], 180, 360, fill=255, width=W)


def g_ruler(d, c):
    d.rounded_rectangle([c - 100, c - 40, c + 100, c + 40], radius=8,
                        outline=255, width=W)
    for x in (-60, -20, 20, 60):
        d.line([c + x, c - 40, c + x, c + 2], fill=255, width=W)


def g_search(d, c):
    d.ellipse([c - 84, c - 84, c + 40, c + 40], outline=255, width=W + 2)
    d.line([c + 28, c + 28, c + 92, c + 92], fill=255, width=W + 4)


def g_layers(d, c):
    d.polygon([(c, c - 86), (c + 88, c - 30), (c, c + 26), (c - 88, c - 30)],
              outline=255, width=W)
    d.line([c - 88, c + 8, c, c + 64, c + 88, c + 8], fill=255, width=W)
    d.line([c - 88, c + 46, c, c + 100, c + 88, c + 46], fill=255, width=W)


def g_balance(d, c):
    d.line([c, c - 92, c, c + 92], fill=255, width=W)
    d.line([c - 78, c - 56, c + 78, c - 56], fill=255, width=W)
    d.arc([c - 116, c - 40, c - 40, c + 36], 0, 180, fill=255, width=W)
    d.arc([c + 40, c - 40, c + 116, c + 36], 0, 180, fill=255, width=W)
    d.line([c - 40, c + 92, c + 40, c + 92], fill=255, width=W)


GLYPHS = {
    "target": g_target, "sail": g_sail, "stage": g_stage, "orbit": g_orbit,
    "chart": g_chart, "wind": g_wind, "shield": g_shield, "warn": g_warn,
    "gear": g_gear, "calendar": g_calendar, "flask": g_flask, "doc": g_doc,
    "code": g_code, "sun": g_sun, "moon": g_moon, "sat": g_sat,
    "ruler": g_ruler, "search": g_search, "layers": g_layers,
    "balance": g_balance,
}

print("generating icons...")
for name, fn in GLYPHS.items():
    im = blank()
    d = ImageDraw.Draw(im)
    fn(d, S // 2)
    save(name, im)
print("done")
