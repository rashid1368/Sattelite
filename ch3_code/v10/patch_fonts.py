"""Font, footnote and direction clean-up for IranDoc submission.

Usage: python3 patch_fonts.py <in.docx> [<out.docx>]

1. Theme and style fonts: Persian (complex script) = B Nazanin, Latin = Times New
   Roman everywhere (code listings keep Consolas, OMML equations keep Cambria Math).
   Latin text inside Persian paragraphs is 2 pt smaller than the Persian text.
2. Runs are split by script: Latin/Greek segments become left-to-right runs in
   Times New Roman; Persian segments stay right-to-left in B Nazanin.  Runs in
   English paragraphs lose the right-to-left flag.
3. Footnotes use Word's own numbering (restart each page) instead of hidden
   references plus typed digits.  Persian footnotes: right-to-left, justified,
   Persian digits.  English footnotes: left-to-right, left aligned, English
   digits, Times New Roman 10 pt.
4. Page numbers in the footer are right-to-left so they show Persian digits.
"""
import copy
import re
import sys
import zipfile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS = {"w": W, "a": A, "m": M}
FA_FONT = "B Nazanin"
EN_FONT = "Times New Roman"
CODE_FONTS = {"Consolas", "Courier New"}
OTHER_FA_FONTS = {"IranNastaliq"}


def q(tag):
    p, t = tag.split(":")
    return "{%s}%s" % (NS[p], t)


PERSIAN = re.compile(r"[ء-ي٠-٩ٮ-ۓەۮ-ۿﭐ-﷿ﹰ-ﻼ]")
PERSIAN_LETTER = re.compile(r"[ء-يٮ-ۓەۺ-ۿﭐ-﷿ﹰ-ﻼ]")
LATIN = re.compile(r"[A-Za-zÀ-ɏͰ-Ͽ]")
# characters allowed inside a Latin segment (between Latin letters)
LATIN_INNER = re.compile(r"[A-Za-zÀ-ɏͰ-Ͽ0-9 .,:;\-–/()'+&_²³⁰¹⁴-⁹₀-₉×·=%]")


def get_rpr(r):
    rpr = r.find(q("w:rPr"))
    if rpr is None:
        rpr = etree.SubElement(r, q("w:rPr"))
        r.remove(rpr)
        r.insert(0, rpr)
    return rpr


def rpr_child(rpr, tag, create=True):
    el = rpr.find(q(tag))
    if el is None and create:
        el = etree.SubElement(rpr, q(tag))
        reorder_rpr(rpr)
    return el


RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
             "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden",
             "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect",
             "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout",
             "specVanish", "oMath"]


def reorder_rpr(rpr):
    kids = list(rpr)
    def key(e):
        n = etree.QName(e).localname
        return RPR_ORDER.index(n) if n in RPR_ORDER else len(RPR_ORDER)
    kids.sort(key=key)
    for k in kids:
        rpr.remove(k)
    for k in kids:
        rpr.append(k)


def run_font(rpr):
    f = rpr.find(q("w:rFonts"))
    if f is None:
        return None
    return f.get(q("w:ascii")) or f.get(q("w:cs"))


def set_fonts(rpr, latin=True):
    f = rpr_child(rpr, "w:rFonts")
    for a in list(f.attrib):
        del f.attrib[a]
    f.set(q("w:ascii"), EN_FONT)
    f.set(q("w:hAnsi"), EN_FONT)
    f.set(q("w:eastAsia"), EN_FONT)
    f.set(q("w:cs"), FA_FONT if not latin else EN_FONT)
    if not latin:
        f.set(q("w:cs"), FA_FONT)


def set_rtl(rpr, on):
    el = rpr.find(q("w:rtl"))
    if on:
        if el is None:
            el = rpr_child(rpr, "w:rtl")
        if q("w:val") in el.attrib:
            del el.attrib[q("w:val")]
    elif el is not None:
        rpr.remove(el)


def set_lang(rpr, latin):
    el = rpr_child(rpr, "w:lang")
    if latin:
        el.set(q("w:val"), "en-US")
    else:
        el.set(q("w:bidi"), "fa-IR")


# --------------------------------------------------------------- styles
def style_map(styles):
    out = {}
    for s in styles.iter(q("w:style")):
        out[s.get(q("w:styleId"))] = s
    return out


def style_bidi(smap, sid, default_bidi):
    seen = 0
    while sid and sid in smap and seen < 20:
        s = smap[sid]
        b = s.find("w:pPr/w:bidi", NS)
        if b is not None:
            return b.get(q("w:val"), "1") not in ("0", "false")
        bo = s.find(q("w:basedOn"))
        sid = bo.get(q("w:val")) if bo is not None else None
        seen += 1
    return default_bidi


def fix_styles(styles):
    smap = style_map(styles)
    dd = styles.find("w:docDefaults/w:rPrDefault/w:rPr", NS)
    set_fonts(dd, latin=False)
    rpr_child(dd, "w:sz").set(q("w:val"), "24")
    rpr_child(dd, "w:szCs").set(q("w:val"), "28")
    en_styles = set()
    for sid, s in smap.items():
        rpr = s.find(q("w:rPr"))
        f = rpr.find(q("w:rFonts")) if rpr is not None else None
        if f is not None and (f.get(q("w:ascii")) in CODE_FONTS):
            continue  # code listing styles
        if f is not None and f.get(q("w:cs")) in OTHER_FA_FONTS:
            f.set(q("w:cs"), FA_FONT)
        if s.get(q("w:type")) not in ("paragraph", "character"):
            continue
        bidi = style_bidi(smap, sid, False) if s.get(q("w:type")) == "paragraph" else None
        english = (s.get(q("w:type")) == "paragraph" and not bidi and
                   (sid.endswith("EN") or sid.startswith("En") or sid in ("LogoLTR", "FrontTitleLTR", "RefEN")))
        if english:
            en_styles.add(sid)
        if rpr is None:
            if f is None and s.find(q("w:basedOn")) is not None:
                continue
            rpr = etree.SubElement(s, q("w:rPr"))
        if f is not None or s.find(q("w:basedOn")) is None:
            set_fonts(rpr, latin=english)
        # theme references removed by set_fonts; sizes: Latin 2 pt smaller in Persian styles
        sz, szcs = rpr.find(q("w:sz")), rpr.find(q("w:szCs"))
        if not english and szcs is not None:
            v = int(szcs.get(q("w:val")))
            if sz is None:
                sz = rpr_child(rpr, "w:sz")
            sz.set(q("w:val"), str(max(16, v - 4)))
        # no italic for Persian captions
        if sid in ("Caption", "TableCaption", "ImageCaption"):
            for t in ("w:i", "w:iCs"):
                e = rpr.find(q(t))
                if e is not None:
                    rpr.remove(e)
    # footnote text: Persian 12 pt, Latin 10 pt, no fixed alignment
    ft = smap.get("FootnoteText")
    if ft is not None:
        jc = ft.find("w:pPr/w:jc", NS)
        if jc is not None:
            jc.getparent().remove(jc)
        rpr = ft.find(q("w:rPr"))
        rpr_child(rpr, "w:sz").set(q("w:val"), "20")
        rpr_child(rpr, "w:szCs").set(q("w:val"), "24")
    return smap, en_styles


def fix_theme(theme):
    for tag in ("a:majorFont", "a:minorFont"):
        el = theme.find(".//" + tag, NS)
        if el is None:
            continue
        el.find("a:latin", NS).set("typeface", EN_FONT)
        cs = el.find("a:cs", NS)
        if cs is not None:
            cs.set("typeface", FA_FONT)
        for f in el.findall("a:font", NS):
            if f.get("script") in ("Arab",):
                f.set("typeface", FA_FONT)


# --------------------------------------------------------------- runs
def para_is_bidi(p, smap):
    b = p.find("w:pPr/w:bidi", NS)
    if b is not None:
        return b.get(q("w:val"), "1") not in ("0", "false")
    ps = p.find("w:pPr/w:pStyle", NS)
    sid = ps.get(q("w:val")) if ps is not None else "Normal"
    return style_bidi(smap, sid, True)


def segments(text):
    """Split text into (is_latin, chunk) pieces."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if LATIN.match(text[i]):
            j = i
            last = i
            while j < n and (LATIN_INNER.match(text[j]) or text[j] == " "):
                if LATIN.match(text[j]) or text[j].isdigit() or text[j] in ")²³":
                    last = j
                j += 1
            # balance: keep a trailing ')' only if a '(' is inside the segment
            seg = text[i:last + 1]
            if seg.endswith(")") and seg.count("(") < seg.count(")"):
                last -= 1
                seg = text[i:last + 1]
            out.append((True, seg))
            i = last + 1
        else:
            j = i
            while j < n and not LATIN.match(text[j]):
                j += 1
            out.append((False, text[i:j]))
            i = j
    # merge neighbours of equal kind
    merged = []
    for k, s in out:
        if merged and merged[-1][0] == k:
            merged[-1] = (k, merged[-1][1] + s)
        else:
            merged.append((k, s))
    return merged


def is_simple_text_run(r):
    kids = [k for k in r if k.tag != q("w:rPr")]
    return len(kids) == 1 and kids[0].tag == q("w:t")


def in_math(r):
    p = r.getparent()
    while p is not None:
        if etree.QName(p).namespace == M:
            return True
        p = p.getparent()
    return False


def shrink_latin(rpr):
    sz, szcs = rpr.find(q("w:sz")), rpr.find(q("w:szCs"))
    if sz is not None and szcs is not None and sz.get(q("w:val")) == szcs.get(q("w:val")):
        v = int(szcs.get(q("w:val")))
        if v >= 20:
            sz.set(q("w:val"), str(v - 4))


def fix_runs(root, smap, en_styles, stats):
    for lr in list(root.iter(q("w:lastRenderedPageBreak"))):
        lr.getparent().remove(lr)
    for p in root.iter(q("w:p")):
        if in_math(p):
            continue
        bidi = para_is_bidi(p, smap)
        ps = p.find("w:pPr/w:pStyle", NS)
        sid = ps.get(q("w:val")) if ps is not None else "Normal"
        ptext = "".join(t.text or "" for t in p.iter(q("w:t")))
        english_par = (not bidi) and not PERSIAN_LETTER.search(ptext)
        for r in list(p.iter(q("w:r"))):
            if in_math(r):
                continue
            rpr = r.find(q("w:rPr"))
            fnt = run_font(rpr) if rpr is not None else None
            if fnt in CODE_FONTS or fnt == "Cambria Math":
                continue
            if r.find(q("w:footnoteReference")) is not None or r.find(q("w:footnoteRef")) is not None:
                continue
            rpr = get_rpr(r)
            f = rpr.find(q("w:rFonts"))
            if f is not None and (f.get(q("w:asciiTheme")) or f.get(q("w:cstheme"))
                                  or (f.get(q("w:ascii")) not in (None, EN_FONT))
                                  or (f.get(q("w:cs")) not in (None, EN_FONT, FA_FONT))):
                stats["theme/foreign font runs"] += 1
                rpr.remove(f)
            elif f is not None and f.get(q("w:cs")) == EN_FONT and \
                    PERSIAN_LETTER.search("".join(t.text or "" for t in r.iter(q("w:t")))):
                stats["Persian runs with Latin cs font"] += 1
                rpr.remove(f)
            if english_par:
                if rpr.find(q("w:rtl")) is not None:
                    stats["rtl removed (English para)"] += 1
                set_rtl(rpr, False)
                set_fonts(rpr, latin=True)
                for t in r.iter(q("w:t")):
                    if t.text and "‎" in t.text:
                        t.text = t.text.replace("‎", "").replace("‏", "")
                continue
            if not is_simple_text_run(r):
                continue
            t = r.find(q("w:t"))
            text = t.text or ""
            if not LATIN.search(text):
                continue
            segs = segments(text)
            parent = r.getparent()
            idx = parent.index(r)
            new_runs = []
            for latin, chunk in segs:
                if not chunk:
                    continue
                nr = etree.Element(q("w:r"))
                nrpr = copy.deepcopy(rpr)
                nr.append(nrpr)
                nt = etree.SubElement(nr, q("w:t"))
                nt.text = chunk
                nt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                if latin:
                    set_rtl(nrpr, False)
                    set_fonts(nrpr, latin=True)
                    set_lang(nrpr, True)
                    shrink_latin(nrpr)
                    stats["latin segments"] += 1
                else:
                    if bidi or PERSIAN.search(chunk):
                        set_rtl(nrpr, True)
                    f2 = nrpr.find(q("w:rFonts"))
                    if f2 is not None:
                        nrpr.remove(f2)
                reorder_rpr(nrpr)
                new_runs.append(nr)
            parent.remove(r)
            for k, nr in enumerate(new_runs):
                parent.insert(idx + k, nr)


# --------------------------------------------------------------- footnotes
DIGITS = re.compile(r"^[\s۰-۹0-9]+$")


def drop_typed_mark(after_run):
    """Remove the typed-digit run that followed a hidden footnote reference."""
    if after_run is None or after_run.tag != q("w:r"):
        return False
    rs = after_run.find("w:rPr/w:rStyle", NS)
    t = after_run.find(q("w:t"))
    if rs is not None and rs.get(q("w:val")) == "FootnoteReference" and t is not None \
            and DIGITS.match(t.text or "") and is_simple_text_run(after_run):
        after_run.getparent().remove(after_run)
        return True
    return False


def unhide(r):
    rpr = r.find(q("w:rPr"))
    if rpr is not None:
        v = rpr.find(q("w:vanish"))
        if v is not None:
            rpr.remove(v)
    return get_rpr(r)


def fix_body_refs(doc, stats):
    for ref in doc.iter(q("w:footnoteReference")):
        r = ref.getparent()
        rpr = unhide(r)
        if not rpr.find("w:rStyle", NS) is not None:
            etree.SubElement(rpr, q("w:rStyle")).set(q("w:val"), "FootnoteReference")
        set_rtl(rpr, True)
        f = rpr.find(q("w:rFonts"))
        if f is not None:
            rpr.remove(f)
        reorder_rpr(rpr)
        if drop_typed_mark(r.getnext()):
            stats["typed body marks removed"] += 1


def fix_footnotes(fn, stats):
    for note in fn.findall("w:footnote", NS):
        if note.get(q("w:type")) in ("separator", "continuationSeparator", "continuationNotice"):
            continue
        text = "".join(t.text or "" for t in note.iter(q("w:t")))
        persian = bool(PERSIAN_LETTER.search(text))
        stats["footnotes persian" if persian else "footnotes english"] += 1
        for p in note.findall("w:p", NS):
            ppr = p.find(q("w:pPr"))
            if ppr is None:
                ppr = etree.Element(q("w:pPr"))
                p.insert(0, ppr)
            if ppr.find(q("w:pStyle")) is None:
                ps = etree.Element(q("w:pStyle"))
                ps.set(q("w:val"), "FootnoteText")
                ppr.insert(0, ps)
            for tag in ("w:bidi", "w:jc"):
                e = ppr.find(q(tag))
                if e is not None:
                    ppr.remove(e)
            b = etree.SubElement(ppr, q("w:bidi"))
            b.set(q("w:val"), "1" if persian else "0")
            jc = etree.SubElement(ppr, q("w:jc"))
            jc.set(q("w:val"), "both" if persian else "left")
            # pPr child order: pStyle ... bidi ... jc
            kids = list(ppr)
            order = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "widowControl", "numPr",
                     "pBdr", "shd", "tabs", "spacing", "ind", "bidi", "jc", "rPr"]
            kids.sort(key=lambda e: order.index(etree.QName(e).localname)
                      if etree.QName(e).localname in order else 99)
            for k in kids:
                ppr.remove(k)
            for k in kids:
                ppr.append(k)
            for r in list(p.findall("w:r", NS)):
                if r.find(q("w:footnoteRef")) is not None:
                    rpr = unhide(r)
                    set_rtl(rpr, persian)
                    if persian:
                        f = rpr.find(q("w:rFonts"))
                        if f is not None:
                            rpr.remove(f)
                    else:
                        set_fonts(rpr, latin=True)
                        set_lang(rpr, True)
                    reorder_rpr(rpr)
                    if drop_typed_mark(r.getnext()):
                        stats["typed footnote marks removed"] += 1
                    nxt = r.getnext()
                    # make sure one space follows the number
                    if nxt is not None and nxt.find(q("w:t")) is not None:
                        t = nxt.find(q("w:t"))
                        if t.text and not t.text.startswith((" ", "‎ ")):
                            t.text = " " + t.text
                            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    continue
                if not persian:
                    rpr = get_rpr(r)
                    set_rtl(rpr, False)
                    set_fonts(rpr, latin=True)
                    set_lang(rpr, True)
                    reorder_rpr(rpr)
                    for t in r.iter(q("w:t")):
                        if t.text:
                            t.text = t.text.replace("‎", "").replace("‏", "")


def drop_persian_name_notes(doc, fn, stats):
    """Remove footnotes that only repeat Persian author names already cited in the text."""
    notes = {n.get(q("w:id")): n for n in fn.findall("w:footnote", NS)}
    for ref in list(doc.iter(q("w:footnoteReference"))):
        nid = ref.get(q("w:id"))
        note = notes.get(nid)
        if note is None:
            continue
        text = "".join(t.text or "" for t in note.iter(q("w:t"))).strip()
        if not PERSIAN_LETTER.search(text) or LATIN.search(text) or len(text) > 40:
            continue
        words = [w for w in re.split(r"[\s،]+", text) if w and not DIGITS.match(w) and w not in ("و", "همکاران", "دیگران")]
        # text before the reference inside the same paragraph
        p = ref
        while p is not None and p.tag != q("w:p"):
            p = p.getparent()
        before = []
        for t in p.iter(q("w:t"), q("w:footnoteReference")):
            if t is ref:
                break
            if t.tag == q("w:t"):
                before.append(t.text or "")
        ctx = "".join(before)[-120:]
        nz = lambda x: re.sub(r"[\u200c\u200e\u200f\s]", "", x)
        if words and all(nz(w) in nz(ctx) for w in words):
            r = ref.getparent()
            nxt = r.getnext()
            drop_typed_mark(nxt)
            r.getparent().remove(r)
            fn.remove(note)
            stats["Persian name-only footnotes removed"] += 1


def fix_footer(ftr):
    for p in ftr.iter(q("w:p")):
        ppr = p.find(q("w:pPr"))
        if ppr is None:
            ppr = etree.Element(q("w:pPr"))
            p.insert(0, ppr)
        if ppr.find(q("w:bidi")) is None:
            jc = ppr.find(q("w:jc"))
            b = etree.Element(q("w:bidi"))
            if jc is not None:
                jc.addprevious(b)
            else:
                ppr.append(b)
        for r in p.findall("w:r", NS):
            rpr = get_rpr(r)
            set_rtl(rpr, True)
            f = rpr.find(q("w:rFonts"))
            if f is not None:
                rpr.remove(f)
            reorder_rpr(rpr)


def fix_settings(st):
    # Word: show digits by context (Persian in RTL runs)
    if st.find(q("w:footnotePr")) is None:
        return
    fp = st.find(q("w:footnotePr"))
    nr = fp.find(q("w:numRestart"))
    if nr is None:
        nr = etree.Element(q("w:numRestart"))
        fp.insert(0, nr)
    nr.set(q("w:val"), "eachPage")
    tfl = st.find(q("w:themeFontLang"))
    if tfl is not None:
        tfl.set(q("w:bidi"), "fa-IR")


def main(src, dst):
    from collections import Counter
    stats = Counter()
    zin = zipfile.ZipFile(src)
    parts = {n: zin.read(n) for n in zin.namelist()}
    parse = lambda n: etree.fromstring(parts[n])
    styles = parse("word/styles.xml")
    smap, en_styles = fix_styles(styles)
    parts["word/styles.xml"] = etree.tostring(styles, xml_declaration=True, encoding="UTF-8", standalone=True)
    for n in list(parts):
        if n.startswith("word/theme/") and n.endswith(".xml"):
            th = parse(n)
            fix_theme(th)
            parts[n] = etree.tostring(th, xml_declaration=True, encoding="UTF-8", standalone=True)
    doc = parse("word/document.xml")
    fn = parse("word/footnotes.xml")
    drop_persian_name_notes(doc, fn, stats)
    fix_body_refs(doc, stats)
    fix_runs(doc, smap, en_styles, stats)
    parts["word/document.xml"] = etree.tostring(doc, xml_declaration=True, encoding="UTF-8", standalone=True)
    fix_footnotes(fn, stats)
    # Persian footnotes may contain Latin words: split those runs too
    for note in fn.findall("w:footnote", NS):
        if PERSIAN_LETTER.search("".join(t.text or "" for t in note.iter(q("w:t")))):
            fix_runs(note, smap, en_styles, stats)
    parts["word/footnotes.xml"] = etree.tostring(fn, xml_declaration=True, encoding="UTF-8", standalone=True)
    for n in list(parts):
        if re.match(r"word/(footer|header)\d*\.xml", n):
            x = parse(n)
            if n.startswith("word/footer"):
                fix_footer(x)
            fix_runs(x, smap, en_styles, stats)
            parts[n] = etree.tostring(x, xml_declaration=True, encoding="UTF-8", standalone=True)
    st = parse("word/settings.xml")
    fix_settings(st)
    parts["word/settings.xml"] = etree.tostring(st, xml_declaration=True, encoding="UTF-8", standalone=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n in zin.namelist():
            z.writestr(n, parts[n])
    for k, v in sorted(stats.items()):
        print(f"{k}: {v}")


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    main(src, dst)
