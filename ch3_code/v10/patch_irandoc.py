"""Layout per the IranDoc thesis guide (rah.irandoc.ac.ir, 2nd ed., 1402), run after patch_fonts.py.

Usage: python3 patch_irandoc.py <in.docx> [<out.docx>]

Fonts and sizes follow the user's rule: Persian B Nazanin 14, English Times New Roman 12.
Everything else follows the IranDoc guide:
  * A4, margins: left/right 3 cm, top 3.5 cm, bottom 2.5 cm (guide 3-2).
  * Line spacing 1.15; paragraphs 0 pt before/after, first line indent 0.5 cm (3-3).
  * Headings: chapter 16 bold; level 2: 18 pt before, 4 pt after; level 3+: 12/4 (3-3, 3-7).
  * Section numbers end with a Persian full stop: "۱-۲. عنوان" (3-6).
  * Captions bold and centred; table caption 12/4 pt, figure caption 4/12 pt; "شکل ۱-۲. عنوان" (3-5).
  * Equations numbered "(فصل-ردیف)" at the right side of the line (4-2).
  * Page numbers in the header at the outer corner with the chapter title and a rule;
    no header or number on front matter, chapter title pages and English pages; numbering
    is continuous from the first page (3-1, 3-4).
  * Footnotes: full-width separator, hanging indent, English footnotes start with a capital
    and have no final full stop when they are a word or a name (4-4).
  * Persian digits in Persian text (4-3).
"""
import copy
import re
import sys
import zipfile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W, "m": M, "r": R}
REL_HDR = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
CT_HDR = "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"
FA_DIG = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
CM = 567  # twips per cm (approx.)


def q(tag):
    p, t = tag.split(":")
    return "{%s}%s" % (NS[p], t)


def text_of(el):
    out = []
    for n in el.iter(q("w:t"), q("w:br")):
        out.append("\n" if n.tag == q("w:br") else (n.text or ""))
    return "".join(out)


def pstyle(p):
    ps = p.find("w:pPr/w:pStyle", NS)
    return ps.get(q("w:val")) if ps is not None else ""


PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
             "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
             "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
             "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr",
             "sectPr", "pPrChange"]


def sort_children(el, order):
    kids = list(el)
    kids.sort(key=lambda e: order.index(etree.QName(e).localname) if etree.QName(e).localname in order else 99)
    for k in kids:
        el.remove(k)
    for k in kids:
        el.append(k)


def ppr_of(p):
    ppr = p.find(q("w:pPr"))
    if ppr is None:
        ppr = etree.Element(q("w:pPr"))
        p.insert(0, ppr)
    return ppr


def set_ppr(ppr, tag, **attrs):
    el = ppr.find(q(tag))
    if el is None:
        el = etree.SubElement(ppr, q(tag))
    for k, v in attrs.items():
        if v is None:
            el.attrib.pop(q("w:" + k), None)
        else:
            el.set(q("w:" + k), str(v))
    sort_children(ppr, PPR_ORDER)
    return el


RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
             "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden",
             "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect",
             "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout",
             "specVanish", "oMath"]


def set_rpr(rpr, tag, **attrs):
    el = rpr.find(q(tag))
    if el is None:
        el = etree.SubElement(rpr, q(tag))
    for k, v in attrs.items():
        el.set(q("w:" + k), str(v))
    sort_children(rpr, RPR_ORDER)
    return el


# ------------------------------------------------------------------ styles
def fix_styles(st):
    smap = {s.get(q("w:styleId")): s for s in st.iter(q("w:style"))}

    def ppr(sid):
        s = smap[sid]
        p = s.find(q("w:pPr"))
        if p is None:
            p = etree.Element(q("w:pPr"))
            name = s.find(q("w:name"))
            idx = list(s).index(s.find(q("w:rPr"))) if s.find(q("w:rPr")) is not None else len(s)
            s.insert(idx, p)
        return p

    def rpr(sid):
        s = smap[sid]
        r = s.find(q("w:rPr"))
        if r is None:
            r = etree.SubElement(s, q("w:rPr"))
        return r

    def size(sid, fa_pt, en_pt=None):
        r = rpr(sid)
        set_rpr(r, "w:szCs", val=int(fa_pt * 2))
        set_rpr(r, "w:sz", val=int((en_pt if en_pt else fa_pt - 2) * 2))

    # body: 1.15 lines, no paragraph spacing
    set_ppr(ppr("Normal"), "w:spacing", before=0, after=0, line=276, lineRule="auto")
    for sid in ("BodyText", "FirstParagraph"):
        set_ppr(ppr(sid), "w:ind", firstLine=int(0.5 * CM))
    # styles derived from BodyText that must not get the first-line indent
    def based_on_body(sid, seen=0):
        s = smap.get(sid)
        while s is not None and seen < 20:
            b = s.find(q("w:basedOn"))
            if b is None:
                return False
            if b.get(q("w:val")) == "BodyText":
                return True
            s = smap.get(b.get(q("w:val")))
            seen += 1
        return False
    for sid in smap:
        if sid in ("BodyText", "FirstParagraph") or not based_on_body(sid):
            continue
        p = ppr(sid)
        if p.find(q("w:ind")) is None:
            set_ppr(p, "w:ind", firstLine=0)
    # headings
    size("Heading11", 16)
    set_ppr(ppr("Heading21"), "w:spacing", before=360, after=80)
    size("Heading21", 14)
    for sid in ("Heading31", "Heading4", "Heading5"):
        if sid in smap:
            set_ppr(ppr(sid), "w:spacing", before=240, after=80)
            size(sid, 13)
            r = rpr(sid)
            set_rpr(r, "w:b")
            set_rpr(r, "w:bCs")
            for t in ("w:i", "w:iCs"):
                e = r.find(q(t))
                if e is not None:
                    r.remove(e)
            for t in ("w:color",):
                e = r.find(q(t))
                if e is not None:
                    e.set(q("w:val"), "000000")
    # captions: bold, centred, 11 pt
    r = rpr("CaptionFa")
    set_rpr(r, "w:b")
    set_rpr(r, "w:bCs")
    size("CaptionFa", 11, 10)
    set_ppr(ppr("CaptionFa"), "w:keepLines")
    # Persian body-like text at 14 pt, English pages at 12 pt
    for sid in ("FrontBody", "RefBodyFa"):
        size(sid, 14, 12)
    size("RefEN", 12, 12)
    size("AbstractEN", 12, 12)
    size("Compact", 11, 10)
    # TOC entries: start-aligned (justification squeezes the words before the dot leader)
    jc = ppr("TocEntry").find(q("w:jc"))
    if jc is not None:
        jc.getparent().remove(jc)
    # equations: 12 pt, number on the right, equation centred
    p = ppr("EqLine")
    set_ppr(p, "w:spacing", before=120, after=120)
    jc = p.find(q("w:jc"))
    if jc is not None:
        p.remove(jc)
    # footnotes: Persian 12, English 10, single spacing
    set_ppr(ppr("FootnoteText"), "w:spacing", before=0, after=0, line=240, lineRule="auto")
    # header style text: B Nazanin 12
    return smap


# ------------------------------------------------------------------ body text
HEAD_NUM = re.compile(r"^(\s*[۰-۹]+(?:-[۰-۹]+)+)(\s)(?!\.)")
CAP_NUM = re.compile(r"^((?:شکل|جدول|نمودار)\s+[۰-۹]+-[۰-۹]+)\s*:\s*")
TOC_NUM = re.compile(r"^([  ]*[۰-۹]+(?:-[۰-۹]+)+)(\s)")


def first_text_node(p):
    for t in p.iter(q("w:t")):
        if t.text and t.text.strip():
            return t
    return None


def fix_heading_numbers(body, stats):
    for p in body.iter(q("w:p")):
        s = pstyle(p)
        t = first_text_node(p)
        if t is None:
            continue
        if s in ("Heading21", "Heading31", "Heading4", "Heading5"):
            new = HEAD_NUM.sub(r"\1.\2", t.text, count=1)
            if new != t.text:
                t.text = new
                stats["heading numbers with full stop"] += 1
        elif s == "TocEntry":
            new = TOC_NUM.sub(r"\1.\2", t.text, count=1)
            new = CAP_NUM.sub(r"\1. ", new, count=1)
            if new != t.text:
                t.text = new
                stats["TOC/list entries"] += 1
            for tab in p.iter(q("w:tab")):
                if tab.getparent().tag == q("w:tabs") and tab.get(q("w:pos")) == "9637":
                    tab.set(q("w:pos"), str(int(15 * CM)))
            # replace leading no-break spaces by a real 0.5 cm indent per level
            m = re.match(r"^([ ]+)", t.text)
            if m:
                level = len(m.group(1)) // 4
                t.text = t.text[len(m.group(1)):]
                set_ppr(ppr_of(p), "w:ind", right=int(level * 0.5 * CM), left=0)
        elif s == "CaptionFa":
            new = CAP_NUM.sub(r"\1. ", t.text, count=1)
            if new != t.text:
                t.text = new
                stats["captions"] += 1
            # no final full stop
            last = None
            for x in p.iter(q("w:t")):
                if x.text and x.text.strip():
                    last = x
            if last is not None and last.text.rstrip().endswith("."):
                last.text = last.text.rstrip()[:-1]
            ppr = ppr_of(p)
            if t.text.lstrip().startswith("جدول"):
                set_ppr(ppr, "w:spacing", before=240, after=80)
                set_ppr(ppr, "w:keepNext")
            else:
                set_ppr(ppr, "w:spacing", before=80, after=240)


def persian_digits_in_rtl(body, stats):
    for r in body.iter(q("w:r")):
        if r.find("w:rPr/w:rtl", NS) is None:
            continue
        f = r.find("w:rPr/w:rFonts", NS)
        if f is not None and f.get(q("w:ascii")) == "Consolas":
            continue
        for t in r.findall(q("w:t")):
            if t.text and re.search(r"[0-9]", t.text):
                t.text = t.text.translate(FA_DIG)
                stats["ASCII digits -> Persian (RTL runs)"] += 1


# ------------------------------------------------------------------ equations
def number_equations(body, chapters_of, stats):
    count = {}
    for p in list(body.iter(q("w:p"))):
        if pstyle(p) != "EqLine":
            continue
        ch = chapters_of(p)
        if ch is None:
            continue
        count[ch] = count.get(ch, 0) + 1
        label = "(" + str(ch).translate(FA_DIG) + "-" + str(count[ch]).translate(FA_DIG) + ")"
        ppr = ppr_of(p)
        set_ppr(ppr, "w:bidi")
        tabs = set_ppr(ppr, "w:tabs")
        for t in list(tabs):
            tabs.remove(t)
        tab = etree.SubElement(tabs, q("w:tab"))
        tab.set(q("w:val"), "center")
        tab.set(q("w:pos"), str(int(7.5 * CM)))
        set_ppr(ppr, "w:jc", val="both")
        # unwrap oMathPara so the equation can sit after the tab
        for omp in p.findall(q("m:oMathPara")):
            idx = p.index(omp)
            maths = omp.findall(q("m:oMath"))
            p.remove(omp)
            for k, m in enumerate(maths):
                p.insert(idx + k, m)
        first_math = p.find(q("m:oMath"))
        idx = p.index(first_math) if first_math is not None else len(p)
        rn = etree.Element(q("w:r"))
        rpr = etree.SubElement(rn, q("w:rPr"))
        etree.SubElement(rpr, q("w:rtl"))
        tn = etree.SubElement(rn, q("w:t"))
        tn.text = label
        rt = etree.Element(q("w:r"))
        etree.SubElement(rt, q("w:tab"))
        p.insert(idx, rt)
        p.insert(idx, rn)
        stats["equations numbered"] += 1


# ------------------------------------------------------------------ headers and sections
def header_xml(kind, title=None):
    """kind: 'empty', 'odd' (title right, number left), 'even' (number right, title left)."""
    ns = 'xmlns:w="%s" xmlns:r="%s"' % (W, R)
    if kind == "empty":
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr %s><w:p><w:pPr>'
                '<w:pStyle w:val="Normal"/></w:pPr></w:p></w:hdr>' % ns).encode()
    rtl_run = lambda txt: ('<w:r><w:rPr><w:rtl/><w:sz w:val="20"/><w:szCs w:val="24"/></w:rPr>'
                           '<w:t xml:space="preserve">%s</w:t></w:r>' % txt)
    page = ('<w:r><w:rPr><w:rtl/><w:szCs w:val="24"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r><w:rPr><w:rtl/><w:szCs w:val="24"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
            '<w:r><w:rPr><w:rtl/><w:szCs w:val="24"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
            '<w:r><w:rPr><w:rtl/><w:szCs w:val="24"/></w:rPr><w:t>۱</w:t></w:r>'
            '<w:r><w:rPr><w:rtl/><w:szCs w:val="24"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>')
    sp = '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
    cell_rtl_start = '<w:p><w:pPr><w:bidi/>%s<w:ind w:firstLine="0"/></w:pPr>%s</w:p>'
    cell_ltr_left = '<w:p><w:pPr><w:bidi w:val="0"/>%s<w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr>%s</w:p>'
    title_rtl = rtl_run(title)
    if kind == "odd":
        right = cell_rtl_start % (sp, title_rtl)
        left = cell_ltr_left % (sp, page)
    else:
        right = cell_rtl_start % (sp, page)
        left = cell_ltr_left % (sp, rtl_run("‏" + title + "‏"))
    tbl = ('<w:tbl><w:tblPr><w:bidiVisual/><w:tblW w:w="5000" w:type="pct"/>'
           '<w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:right w:val="nil"/>'
           '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="808080"/>'
           '<w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
           '<w:tblLook w:val="0000"/></w:tblPr>'
           '<w:tblGrid><w:gridCol w:w="6804"/><w:gridCol w:w="1700"/></w:tblGrid>'
           '<w:tr><w:tc><w:tcPr><w:tcW w:w="6804" w:type="dxa"/></w:tcPr>%s</w:tc>'
           '<w:tc><w:tcPr><w:tcW w:w="1700" w:type="dxa"/></w:tcPr>%s</w:tc></w:tr></w:tbl>')
    if kind == "even":
        tbl = tbl.replace('<w:gridCol w:w="6804"/><w:gridCol w:w="1700"/>', '<w:gridCol w:w="1700"/><w:gridCol w:w="6804"/>')
        tbl = tbl.replace('<w:tcW w:w="6804" w:type="dxa"/></w:tcPr>%s</w:tc><w:tc><w:tcPr><w:tcW w:w="1700"',
                          '<w:tcW w:w="1700" w:type="dxa"/></w:tcPr>%s</w:tc><w:tc><w:tcPr><w:tcW w:w="6804"')
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr %s>' % ns
           + tbl % (right, left)
           + '<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="120" w:lineRule="exact"/></w:pPr></w:p></w:hdr>')
    return xml.encode()


def make_sectpr(template, hdr_ids, title_pg, start=None):
    sp = copy.deepcopy(template)
    for tag in ("w:headerReference", "w:footerReference", "w:titlePg", "w:pgNumType", "w:type"):
        for e in sp.findall(q(tag)):
            sp.remove(e)
    # header references must come first
    pos = 0
    for typ in ("default", "even", "first"):
        if typ in hdr_ids:
            e = etree.Element(q("w:headerReference"))
            e.set(q("w:type"), typ)
            e.set(q("r:id"), hdr_ids[typ])
            sp.insert(pos, e)
            pos += 1
    t = etree.Element(q("w:type"))
    t.set(q("w:val"), "nextPage")
    sp.insert(pos, t)
    pm = sp.find(q("w:pgMar"))
    pm.set(q("w:top"), str(int(3.5 * CM)))
    pm.set(q("w:bottom"), str(int(2.5 * CM)))
    pm.set(q("w:left"), str(int(3 * CM)))
    pm.set(q("w:right"), str(int(3 * CM)))
    pm.set(q("w:header"), str(int(2.25 * CM)))
    pm.set(q("w:footer"), str(int(1.25 * CM)))
    pg = etree.Element(q("w:pgNumType"))
    pg.set(q("w:fmt"), "decimal")
    if start:
        pg.set(q("w:start"), str(start))
    pm.addnext(pg)
    if title_pg:
        tp = etree.Element(q("w:titlePg"))
        anchor = sp.find(q("w:docGrid"))
        if anchor is not None:
            anchor.addprevious(tp)
        else:
            sp.append(tp)
    bidi = sp.find(q("w:bidi"))
    if bidi is None:
        b = etree.Element(q("w:bidi"))
        anchor = sp.find(q("w:docGrid")) or sp.find(q("w:titlePg"))
        sp.append(b)
    return sp


SECT_ORDER = ["headerReference", "footerReference", "footnotePr", "endnotePr", "type", "pgSz", "pgMar",
              "paperSrc", "pgBorders", "lnNumType", "pgNumType", "cols", "formProt", "vAlign", "noEndnote",
              "titlePg", "textDirection", "bidi", "rtlGutter", "docGrid", "printerSettings", "sectPrChange"]


def build_sections(doc, parts, rels, ctypes, stats):
    body = doc.find(q("w:body"))
    final_sp = body.find(q("w:sectPr"))
    template = copy.deepcopy(final_sp)
    # remove existing inner section breaks and footers
    for p in body.findall(q("w:p")):
        sp = p.find("w:pPr/w:sectPr", NS)
        if sp is not None:
            sp.getparent().remove(sp)
    kids = list(body)
    # section starts: chapters (Heading11), references (first RefHeadingCenter), English abstract
    starts = []
    seen_ref = False
    for i, el in enumerate(kids):
        if el.tag != q("w:p"):
            continue
        s = pstyle(el)
        txt = text_of(el).strip()
        if s == "Heading11":
            if txt.startswith("Abstract"):
                starts.append((i, "english", None))
            elif txt.startswith("فصل"):
                # chapter cover page = its own section without header; content follows in the next one
                title = re.sub(r"\s*\n\s*", ": ", txt)
                starts.append((i, "cover", None))
                j = i + 1
                while j < len(kids) and not (kids[j].tag == q("w:p") and pstyle(kids[j]) == "Heading21"):
                    j += 1
                starts.append((j, "body", title))
            else:
                starts.append((i, "chapter", re.sub(r"\s*\n\s*", ": ", txt)))
        elif s == "RefHeadingCenter" and not seen_ref:
            seen_ref = True
            starts.append((i, "chapter", txt))
    # header parts
    rid_n = [1000]
    hdr_n = [0]

    def add_header(xml):
        hdr_n[0] += 1
        name = "header%d.xml" % hdr_n[0]
        parts["word/" + name] = xml
        rid_n[0] += 1
        rid = "rIdH%d" % rid_n[0]
        rel = etree.SubElement(rels, "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
        rel.set("Id", rid)
        rel.set("Type", REL_HDR)
        rel.set("Target", name)
        ov = etree.SubElement(ctypes, "{http://schemas.openxmlformats.org/package/2006/content-types}Override")
        ov.set("PartName", "/word/" + name)
        ov.set("ContentType", CT_HDR)
        return rid

    empty = add_header(header_xml("empty"))
    empty_ids = {"default": empty, "even": empty, "first": empty}

    def close_section_before(idx, sectpr):
        """Attach sectPr to the paragraph just before kids[idx]; drop page breaks it makes redundant."""
        prev = kids[idx - 1]
        heading = kids[idx]
        hp = heading.find("w:pPr/w:pageBreakBefore", NS)
        if hp is not None:
            hp.getparent().remove(hp)
        if prev.tag == q("w:p") and not text_of(prev).strip() and prev.find(".//" + q("w:drawing")) is None:
            for br in prev.iter(q("w:br")):
                if br.get(q("w:type")) == "page":
                    br.getparent().remove(br)
            target = prev
        else:
            target = etree.Element(q("w:p"))
            ppr = etree.SubElement(target, q("w:pPr"))
            sp_ = etree.SubElement(ppr, q("w:spacing"))
            sp_.set(q("w:before"), "0")
            sp_.set(q("w:after"), "0")
            sp_.set(q("w:line"), "20")
            sp_.set(q("w:lineRule"), "exact")
            heading.addprevious(target)
        ppr = ppr_of(target)
        ppr.append(sectpr)
        sort_children(ppr, PPR_ORDER)

    # section 0: front matter, then one per start
    sections = [("front", None)] + [(k, t) for (_, k, t) in starts]
    sect_props = []
    for kind, title in sections:
        if kind in ("front", "english", "cover"):
            ids = {"default": empty, "even": empty}
            sp = make_sectpr(template, ids, title_pg=False, start=1 if kind == "front" else None)
        elif kind == "body":
            odd = add_header(header_xml("odd", title))
            even = add_header(header_xml("even", title))
            sp = make_sectpr(template, {"default": odd, "even": even}, title_pg=False)
        else:
            odd = add_header(header_xml("odd", title))
            even = add_header(header_xml("even", title))
            sp = make_sectpr(template, {"default": odd, "even": even, "first": empty}, title_pg=True)
        sort_children(sp, SECT_ORDER)
        sect_props.append(sp)
    # attach: section k ends before start k
    for k, (idx, kind, title) in enumerate(starts):
        close_section_before(idx, sect_props[k])
        stats["sections"] += 1
    body.remove(final_sp)
    body.append(sect_props[-1])
    stats["sections"] += 1


# ------------------------------------------------------------------ footnotes
LATIN_FIRST = re.compile(r"^(\s*)([a-z])")


def fix_footnotes(fn, stats, fixes):
    for note in fn.findall("w:footnote", NS):
        typ = note.get(q("w:type"))
        if typ in ("separator", "continuationSeparator"):
            for p in note.findall("w:p", NS):
                for r in list(p.findall("w:r", NS)):
                    if r.find(q("w:separator")) is not None or r.find(q("w:continuationSeparator")) is not None:
                        p.remove(r)
                ppr = ppr_of(p)
                bdr = set_ppr(ppr, "w:pBdr")
                b = etree.SubElement(bdr, q("w:top"))
                b.set(q("w:val"), "single")
                b.set(q("w:sz"), "4")
                b.set(q("w:space"), "1")
                b.set(q("w:color"), "auto")
                set_ppr(ppr, "w:spacing", before=0, after=0, line=120, lineRule="exact")
            stats["footnote separators full width"] += 1
            continue
        txt = text_of(note).strip()
        persian = bool(re.search(r"[ا-ی]", txt))
        for p in note.findall("w:p", NS):
            ppr = ppr_of(p)
            if persian:
                set_ppr(ppr, "w:ind", right=227, hanging=227, left=0, firstLine=None)
            else:
                set_ppr(ppr, "w:ind", left=227, hanging=227, right=0, firstLine=None)
        if persian:
            continue
        ts = [t for t in note.iter(q("w:t")) if t.text and t.text.strip()]
        if not ts:
            continue
        for old, new in fixes.items():
            joined = "".join(t.text for t in ts)
            if joined.strip() == old:
                ts[0].text = " " + new
                for t in ts[1:]:
                    t.text = ""
                stats["English footnotes: 3-author names"] += 1
                ts = [ts[0]]
                break
        m = LATIN_FIRST.match(ts[0].text)
        if m:
            ts[0].text = m.group(1) + m.group(2).upper() + ts[0].text[m.end():]
            stats["English footnotes capitalised"] += 1
        last = ts[-1]
        stripped = last.text.rstrip()
        if stripped.endswith(".") and not stripped.endswith("al.") and len("".join(t.text for t in ts).split()) <= 8:
            last.text = stripped[:-1]
            stats["English footnotes: final full stop removed"] += 1


THREE_AUTHORS = {
    "Carvalho et al.": "Carvalho, Vilhena de Moraes, and Prado",
    "Hairer et al.": "Hairer, Nørsett, and Wanner",
    "McKay et al.": "McKay, Beckman, and Conover",
    "San Juan et al.": "San Juan, Letizia, and Lara",
    "Talu et al.": "Talu, Alessi, and Tommei",
}


def main(src, dst):
    from collections import Counter
    stats = Counter()
    zin = zipfile.ZipFile(src)
    parts = {n: zin.read(n) for n in zin.namelist()}
    names = list(zin.namelist())
    st = etree.fromstring(parts["word/styles.xml"])
    fix_styles(st)
    parts["word/styles.xml"] = etree.tostring(st, xml_declaration=True, encoding="UTF-8", standalone=True)

    doc = etree.fromstring(parts["word/document.xml"])
    body = doc.find(q("w:body"))
    fix_heading_numbers(body, stats)
    persian_digits_in_rtl(body, stats)

    # chapter index of each paragraph (by Heading11 order: فصل اول..پنجم)
    chap_map = {}
    ch = None
    order = {"اول": 1, "دوم": 2, "سوم": 3, "چهارم": 4, "پنجم": 5, "ششم": 6}
    for el in body.iter(q("w:p")):
        if pstyle(el) == "Heading11":
            m = re.match(r"\s*فصل\s+(\S+)", text_of(el))
            ch = order.get(m.group(1)) if m else None
        chap_map[el] = ch
    number_equations(body, lambda p: chap_map.get(p), stats)

    rels = etree.fromstring(parts["word/_rels/document.xml.rels"])
    ctypes = etree.fromstring(parts["[Content_Types].xml"])
    # drop old footers (page numbers now in the header)
    for rel in list(rels):
        if rel.get("Type", "").endswith("/footer"):
            rels.remove(rel)
    for ov in list(ctypes):
        if (ov.get("PartName") or "").startswith("/word/footer"):
            ctypes.remove(ov)
    for n in list(parts):
        if re.match(r"word/footer\d*\.xml$", n):
            del parts[n]
            names.remove(n)
    build_sections(doc, parts, rels, ctypes, stats)
    parts["word/document.xml"] = etree.tostring(doc, xml_declaration=True, encoding="UTF-8", standalone=True)
    parts["word/_rels/document.xml.rels"] = etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
    parts["[Content_Types].xml"] = etree.tostring(ctypes, xml_declaration=True, encoding="UTF-8", standalone=True)

    fn = etree.fromstring(parts["word/footnotes.xml"])
    fix_footnotes(fn, stats, THREE_AUTHORS)
    parts["word/footnotes.xml"] = etree.tostring(fn, xml_declaration=True, encoding="UTF-8", standalone=True)

    settings = etree.fromstring(parts["word/settings.xml"])
    if settings.find(q("w:evenAndOddHeaders")) is None:
        e = etree.Element(q("w:evenAndOddHeaders"))
        before = ["writeProtection", "view", "zoom", "removePersonalInformation", "removeDateAndTime",
                  "doNotDisplayPageBoundaries", "displayBackgroundShape", "printPostScriptOverText",
                  "printFractionalCharacterWidth", "printFormsData", "embedTrueTypeFonts", "embedSystemFonts",
                  "saveSubsetFonts", "saveFormsData", "mirrorMargins", "alignBordersAndEdges",
                  "bordersDoNotSurroundHeader", "bordersDoNotSurroundFooter", "gutterAtTop",
                  "hideSpellingErrors", "hideGrammaticalErrors", "activeWritingStyle", "proofState",
                  "formsDesign", "attachedTemplate", "linkStyles", "stylePaneFormatFilter",
                  "stylePaneSortMethod", "documentType", "mailMerge", "revisionView", "trackRevisions",
                  "doNotTrackMoves", "doNotTrackFormatting", "documentProtection", "autoFormatOverride",
                  "styleLockTheme", "styleLockQFSet", "defaultTabStop", "autoHyphenation",
                  "consecutiveHyphenLimit", "hyphenationZone", "doNotHyphenateCaps", "showEnvelope",
                  "summaryLength", "clickAndTypeStyle", "defaultTableStyle"]
        last = None
        for child in settings:
            if etree.QName(child).localname in before:
                last = child
        if last is not None:
            last.addnext(e)
        else:
            settings.insert(0, e)
    parts["word/settings.xml"] = etree.tostring(settings, xml_declaration=True, encoding="UTF-8", standalone=True)

    for n in parts:
        if n not in names:
            names.append(n)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, parts[n])
    for k, v in sorted(stats.items()):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else sys.argv[1])
