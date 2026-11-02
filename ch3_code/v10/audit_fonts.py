"""Report effective fonts per script in a docx (document, footnotes, footers).

Usage: python3 audit_fonts.py <file.docx>
A Persian letter is checked against the complex-script font, a Latin letter
against the ascii font (or the complex-script font if the run is right-to-left).
"""
import re
import sys
import zipfile
from collections import Counter

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
q = lambda t: "{%s}%s" % (W, t)
FA = re.compile(r"[ء-يٮ-ۓۺ-ۿ]")
LA = re.compile(r"[A-Za-z]")


def main(path):
    z = zipfile.ZipFile(path)
    st = etree.fromstring(z.read("word/styles.xml"))
    theme = z.read("word/theme/theme1.xml").decode()
    smap = {s.get(q("styleId")): s for s in st.iter(q("style"))}
    dd = st.find(".//" + q("rPrDefault"))

    def fonts_of(rpr):
        out = {}
        if rpr is None:
            return out
        f = rpr.find(q("rFonts"))
        if f is not None:
            for k in ("ascii", "cs", "asciiTheme", "cstheme"):
                v = f.get(q(k))
                if v:
                    out[k] = v
        r = rpr.find(q("rtl"))
        if r is not None:
            out["rtl"] = r.get(q("val"), "1") not in ("0", "false")
        return out

    def chain(sid):
        res = []
        while sid and sid in smap:
            s = smap[sid]
            res.append(fonts_of(s.find(q("rPr"))))
            b = s.find(q("basedOn"))
            sid = b.get(q("val")) if b is not None else None
        return res

    def resolve(layers, key):
        for L in layers:
            if key in L:
                return L[key]
            th = {"ascii": "asciiTheme", "cs": "cstheme"}[key] if key in ("ascii", "cs") else None
            if th and th in L:
                return "THEME:" + L[th]
        return None

    bad = Counter()
    good = Counter()
    for part in [n for n in z.namelist() if re.match(r"word/(document|footnotes|footer\d*|header\d*)\.xml", n)]:
        root = etree.fromstring(z.read(part))
        for p in root.iter(q("p")):
            ps = p.find(q("pPr") + "/" + q("pStyle"))
            pchain = chain(ps.get(q("val")) if ps is not None else "Normal")
            for r in p.iter(q("r")):
                anc = r.getparent()
                if etree.QName(anc).namespace == M:
                    continue
                txt = "".join(t.text or "" for t in r.iter(q("t")))
                if not txt:
                    continue
                rpr = r.find(q("rPr"))
                rs = rpr.find(q("rStyle")) if rpr is not None else None
                layers = [fonts_of(rpr)] + (chain(rs.get(q("val"))) if rs is not None else []) + pchain + [fonts_of(dd)]
                rtl = bool(resolve(layers, "rtl"))
                csf = resolve(layers, "cs")
                asf = resolve(layers, "ascii")
                if FA.search(txt):
                    key = (part, "Persian", csf)
                    (good if csf == "B Nazanin" else bad)[key] += 1
                if LA.search(txt):
                    f = csf if rtl else asf
                    key = (part, "Latin" + (" in RTL run" if rtl else ""), f)
                    (good if f in ("Times New Roman", "Consolas") and not rtl else bad)[key] += 1
    print("OK:")
    for k, v in sorted(good.items(), key=str):
        print("  ", v, k)
    print("PROBLEMS:")
    for k, v in sorted(bad.items(), key=str):
        print("  ", v, k)


if __name__ == "__main__":
    main(sys.argv[1])
