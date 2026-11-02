# -*- coding: utf-8 -*-
"""Reusable layout helpers that reproduce the reference defense deck's design system.

Design tokens and geometry were taken from
"ارائه_دفاع_پریسا_باقری.pptx" (16:9, Tahoma, RTL, teal/purple/orange palette).
"""
import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.ns import qn

# ----------------------------------------------------------------- palette
TEAL = RGBColor(0x0F, 0x52, 0x57)      # primary deep teal
PURPLE = RGBColor(0x6D, 0x59, 0x7A)    # secondary
ORANGE = RGBColor(0xD9, 0x67, 0x4A)    # accent warm
YELLOW = RGBColor(0xE9, 0xB4, 0x4C)    # accent gold
GREEN = RGBColor(0x2A, 0x9D, 0x8F)     # accent teal-green
INK = RGBColor(0x26, 0x32, 0x38)       # body text
MUTED = RGBColor(0x6B, 0x7B, 0x83)     # secondary text
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

T_ORANGE = RGBColor(0xFB, 0xEC, 0xE7)  # card tints
T_GREEN = RGBColor(0xE6, 0xF2, 0xF1)
T_PURPLE = RGBColor(0xEF, 0xEA, 0xF3)
T_YELLOW = RGBColor(0xFB, 0xF3, 0xE1)
T_GREY = RGBColor(0xF4, 0xF6, 0xF7)
T_TEAL = RGBColor(0xCD, 0xE7, 0xE4)

FONT = "Tahoma"

SW, SH = 13.3333, 7.5   # slide size, inches


# ----------------------------------------------------------------- utils
def new_deck():
    prs = Presentation()
    prs.slide_width = Inches(SW)
    prs.slide_height = Inches(SH)
    return prs


def blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _set_rtl(p):
    pPr = p._p.get_or_add_pPr()
    pPr.set('rtl', '1')


def _set_fonts(run, size, bold, color, font=FONT, italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = font
    f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ('a:latin', 'a:ea', 'a:cs'):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)
    for tag in ('a:latin', 'a:ea', 'a:cs'):
        el = rPr.makeelement(qn(tag), {'typeface': font})
        rPr.append(el)


def txbox(slide, x, y, w, h, lines, align='r', anchor='t', rtl=True,
          margin=0.0, line_spacing=None, space_after=0):
    """lines: list of dicts {t, sz, b, c, align, sp(space_after pt), ls(line spacing)}"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0)
    tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE,
                          'b': MSO_ANCHOR.BOTTOM}[anchor]
    amap = {'r': PP_ALIGN.RIGHT, 'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER,
            'j': PP_ALIGN.JUSTIFY}
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = amap.get(ln.get('align', align), PP_ALIGN.RIGHT)
        if rtl:
            _set_rtl(p)
        if ln.get('sp'):
            p.space_after = Pt(ln['sp'])
        if ln.get('spb'):
            p.space_before = Pt(ln['spb'])
        ls = ln.get('ls', line_spacing)
        if ls:
            p.line_spacing = ls
        r = p.add_run()
        r.text = ln['t']
        _set_fonts(r, ln.get('sz', 14), ln.get('b', False), ln.get('c', INK))
    return tb


def shape(slide, kind, x, y, w, h, fill=None, line=None, line_w=1.0,
          adj=None, rot=None, shadow=False):
    sp = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w)
    if adj is not None:
        try:
            sp.adjustments[0] = adj
        except Exception:
            pass
    if rot is not None:
        sp.rotation = rot
    if not shadow:
        sp.shadow.inherit = False
    sp.text_frame.word_wrap = True
    return sp


def rrect(slide, x, y, w, h, fill=None, line=None, line_w=1.0, adj=0.12):
    return shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, line,
                 line_w, adj=adj)


def rect(slide, x, y, w, h, fill=None, line=None, line_w=1.0):
    return shape(slide, MSO_SHAPE.RECTANGLE, x, y, w, h, fill, line, line_w)


def ellipse(slide, x, y, w, h, fill=None, line=None, line_w=1.0):
    return shape(slide, MSO_SHAPE.OVAL, x, y, w, h, fill, line, line_w)


def hline(slide, x, y, w, color=MUTED, weight=1.0):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                Inches(w), Pt(weight))
    sp.fill.solid()
    sp.fill.fore_color.rgb = color
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def vline(slide, x, y, h, color=MUTED, weight=1.0):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                Pt(weight), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = color
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


# ----------------------------------------------------------------- icons
def icon(slide, name, x, y, size, color):
    """Draw a flat glyph icon tinted to `color`."""
    from PIL import Image as _I
    import io
    src = os.path.join("icons", name + ".png")
    im = _I.open(src).convert("RGBA")
    px = im.getdata()
    im.putdata([(r, g, b, a) if a > 0 else (r, g, b, 0) for (r, g, b, a) in px])
    # recolour: keep alpha, take colour from `color`
    r0, g0, b0 = color[0], color[1], color[2]
    out = _I.new("RGBA", im.size, (r0, g0, b0, 0))
    out.putdata([(r0, g0, b0, a) for (_r, _g, _b, a) in im.getdata()])
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    buf.seek(0)
    return slide.shapes.add_picture(buf, Inches(x), Inches(y),
                                    Inches(size), Inches(size))


# ----------------------------------------------------------------- pictures
def _crop_to(path, target_ratio, out_path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    r = w / h
    if r > target_ratio:                     # too wide -> crop sides
        nw = int(h * target_ratio)
        left = (w - nw) // 2
        im = im.crop((left, 0, left + nw, h))
    else:                                    # too tall -> crop top/bottom
        nh = int(w / target_ratio)
        top = int((h - nh) * 0.35)
        im = im.crop((0, top, w, top + nh))
    im.save(out_path, quality=92)
    return out_path


def pic_cover(slide, path, x, y, w, h):
    """Insert image cropped to exactly fill the x/y/w/h box (like cover-fit)."""
    tmp = "_tmp_cover.jpg"
    _crop_to(path, w / h, tmp)
    p = slide.shapes.add_picture(tmp, Inches(x), Inches(y), Inches(w), Inches(h))
    return p


def pic_fit(slide, path, x, y, w, h, bg=None):
    """Insert image scaled to fit inside x/y/w/h, centred. Optional bg box."""
    if bg is not None:
        rect(slide, x, y, w, h, fill=bg)
    im = Image.open(path)
    iw, ih = im.size
    r = iw / ih
    if r > w / h:
        nw, nh = w, w / r
    else:
        nh, nw = h, h * r
    px = x + (w - nw) / 2
    py = y + (h - nh) / 2
    return slide.shapes.add_picture(path, Inches(px), Inches(py),
                                    Inches(nw), Inches(nh))


# ----------------------------------------------------------------- chrome
def chrome(slide, logo=None):
    """Corner decorative shapes + logo, matching the reference content slides."""
    ellipse(slide, -1.10, 6.05, 2.60, 2.60, fill=TEAL)
    ellipse(slide, 1.15, 6.70, 0.45, 0.45, fill=ORANGE)
    ellipse(slide, 12.55, -0.35, 1.10, 1.10, fill=PURPLE)
    ellipse(slide, 11.95, 0.38, 0.72, 0.72, fill=TEAL)
    if logo:
        slide.shapes.add_picture(logo, Inches(12.11), Inches(0.54),
                                 Inches(0.40), Inches(0.40))


def header(slide, title):
    txbox(slide, 0.60, 0.36, 11.15, 0.72,
          [dict(t=title, sz=28, b=True, c=TEAL)], anchor='m')


def footer(slide, idx, total, right_text):
    txbox(slide, 0.50, 7.02, 1.40, 0.30,
          [dict(t="%s / %s" % (fa(idx), fa(total)), sz=10, c=MUTED)],
          align='l', rtl=False)
    txbox(slide, 6.30, 7.02, 6.50, 0.30,
          [dict(t=right_text, sz=10, c=MUTED)], align='r')


FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(s):
    return str(s).translate(FA_DIGITS)


# ----------------------------------------------------------------- components
def card(slide, x, y, w, h, tint, accent, icon_name, title, body_lines,
         title_sz=17, body_sz=13.5, badge=None):
    """Tinted rounded card with an accent circle + icon, title and body text."""
    rrect(slide, x, y, w, h, fill=tint, adj=0.09)
    # accent badge circle at the top-right (RTL reading start)
    bd = 0.62
    bx = x + w - bd - 0.16
    by = y + 0.17
    ellipse(slide, bx, by, bd, bd, fill=accent)
    if icon_name:
        icon(slide, icon_name, bx + 0.13, by + 0.13, bd - 0.26, WHITE)
    tw = w - bd - 0.30
    txbox(slide, x + 0.20, by, tw, 0.62,
          [dict(t=title, sz=title_sz, b=True, c=accent)], anchor='m')
    lines = []
    for b in body_lines:
        lines.append(dict(t=b, sz=body_sz, c=INK, sp=5, ls=1.16))
    txbox(slide, x + 0.20, y + 0.92, w - 0.40, h - 1.05, lines)


def stat_card(slide, x, y, w, h, tint, accent, value, label, sub=None,
              icon_name=None, value_sz=30):
    rrect(slide, x, y, w, h, fill=tint, adj=0.09)
    if icon_name:
        icon(slide, icon_name, x + w - 0.62, y + 0.14, 0.34, accent)
    txbox(slide, x + 0.18, y + 0.16, w - 0.36 - (0.45 if icon_name else 0), 0.72,
          [dict(t=value, sz=value_sz, b=True, c=accent)], anchor='m')
    lines = [dict(t=label, sz=13, b=True, c=INK, sp=2, ls=1.14)]
    if sub:
        lines.append(dict(t=sub, sz=11.5, c=MUTED, ls=1.12))
    txbox(slide, x + 0.18, y + 0.86, w - 0.36, h - 1.0, lines)


def banner(slide, x, y, w, h, fill, title, body, title_c=WHITE,
           body_c=WHITE, icon_name=None, title_sz=17, body_sz=14):
    rrect(slide, x, y, w, h, fill=fill, adj=0.09)
    if icon_name:
        bd = 0.62
        ellipse(slide, x + w - bd - 0.18, y + (h - bd) / 2, bd, bd, fill=WHITE)
        icon(slide, icon_name, x + w - bd - 0.05, y + (h - bd) / 2 + 0.13,
             bd - 0.26, fill)
    txbox(slide, x + 0.24, y + 0.14, w - 0.50, 0.56,
          [dict(t=title, sz=title_sz, b=True, c=title_c)], anchor='m')
    txbox(slide, x + 0.24, y + 0.70, w - 0.50, h - 0.84,
          [dict(t=body, sz=body_sz, c=body_c, ls=1.18)])


def chip(slide, x, y, w, h, fill, text, color, sz=13, bold=True):
    rrect(slide, x, y, w, h, fill=fill, adj=0.28)
    txbox(slide, x, y, w, h, [dict(t=text, sz=sz, b=bold, c=color)],
          align='c', anchor='m')


def figbox(slide, path, x, y, w, h, caption, cap_sz=11):
    """White card holding a fitted figure plus a caption strip underneath."""
    rrect(slide, x, y, w, h, fill=WHITE, line=RGBColor(0xDF, 0xE4, 0xE7), adj=0.05)
    cap_h = 0.46
    pic_fit(slide, path, x + 0.12, y + 0.10, w - 0.24, h - cap_h - 0.22)
    txbox(slide, x + 0.14, y + h - cap_h - 0.04, w - 0.28, cap_h,
          [dict(t=caption, sz=cap_sz, c=MUTED, ls=1.05)], anchor='t')


def table_grid(slide, x, y, w, col_w, rows, header_row, body_sz=12,
               head_sz=12, row_h=0.34, head_h=0.40, head_fill=TEAL,
               head_c=WHITE, zebra=T_GREY, align=None, row_colors=None):
    """Simple RTL table drawn with shapes. rows: list of list[str]."""
    n = len(col_w)
    scale = w / sum(col_w)
    col_w = [c * scale for c in col_w]
    align = align or ['c'] * n
    # header
    cx = x + w
    for i in range(n):
        cx -= col_w[i]
        rect(slide, cx, y, col_w[i], head_h, fill=head_fill)
        txbox(slide, cx, y, col_w[i], head_h,
              [dict(t=header_row[i], sz=head_sz, b=True, c=head_c)],
              align='c', anchor='m')
    ry = y + head_h
    for ri, row in enumerate(rows):
        fill = None
        if row_colors and row_colors[ri] is not None:
            fill = row_colors[ri]
        elif zebra is not None and ri % 2 == 1:
            fill = zebra
        cx = x + w
        for i in range(n):
            cx -= col_w[i]
            if fill is not None:
                rect(slide, cx, ry, col_w[i], row_h, fill=fill)
            val = row[i] if i < len(row) else ""
            bold = val.startswith('**')
            if bold:
                val = val[2:]
            txbox(slide, cx, ry, col_w[i], row_h,
                  [dict(t=val, sz=body_sz, b=bold, c=INK)],
                  align=align[i], anchor='m')
        hline(slide, x, ry, w, color=RGBColor(0xE3, 0xE7, 0xEA), weight=0.75)
        ry += row_h
    hline(slide, x, ry, w, color=RGBColor(0xD3, 0xD9, 0xDD), weight=1.0)
    return ry
