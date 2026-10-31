# -*- coding: utf-8 -*-
"""Footnote rules of the thesis guide.
mode 'remove'  : keep the first footnote of every repeated text, delete later ones (body
                 reference run, visible mark run, and the footnote part entry).
mode 'renumber': renumber the visible Persian marks per page (numbering restarts on each
                 page). The page of each footnote is found by searching its text in the
                 rendered PDF (footnote text is printed on the page that holds the mark).
Usage: patch_dedupe.py remove  |  patch_dedupe.py renumber <render.pdf>"""
import os, sys, re, zipfile, shutil, subprocess
from lxml import etree
import docx
from docx.oxml.ns import qn

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "_build", "thesis_v10_draft.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MODE = sys.argv[1]
DIG_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

def read_footnotes():
    z = zipfile.ZipFile(PATH)
    root = etree.fromstring(z.read("word/footnotes.xml"))
    z.close()
    return root

def ftext(fn):
    return "".join(t.text or "" for t in fn.iter(W + "t"))

def key_of(text):
    t = re.sub(r"^[0-9۰-۹]+\s*", "", text)
    t = re.sub(r"[‎‏\s]", "", t)
    return re.sub(r"[^\w؀-ۿ]", "", t).lower()[:18]

def body_refs(doc):
    out = []
    for r in doc.element.body.iter(W + "footnoteReference"):
        run = r.getparent()
        nxt = run.getnext()
        out.append((int(r.get(W + "id")), run, nxt))
    return out

d = docx.Document(PATH)
froot = read_footnotes()
fns = {int(f.get(W + "id")): f for f in froot.iter(W + "footnote") if int(f.get(W + "id")) > 0}
refs = body_refs(d)

if MODE == "remove":
    seen, remove = {}, set()
    for fid, run, nxt in refs:
        k = key_of(ftext(fns[fid]))
        if k in seen:
            remove.add(fid)
        else:
            seen[k] = fid
    removed = 0
    for fid, run, nxt in refs:
        if fid in remove:
            if nxt is not None and nxt.tag == W + "r" and re.fullmatch(r"[0-9۰-۹]+", "".join(t.text or "" for t in nxt.iter(W + "t"))):
                nxt.getparent().remove(nxt)
            run.getparent().remove(run)
            removed += 1
    d.save(PATH)
    z = zipfile.ZipFile(PATH)
    data = {n: z.read(n) for n in z.namelist()}
    z.close()
    root = etree.fromstring(data["word/footnotes.xml"])
    for f in list(root.iter(W + "footnote")):
        if int(f.get(W + "id")) in remove:
            f.getparent().remove(f)
    data["word/footnotes.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    tmp = PATH + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for n, b in data.items():
            zout.writestr(n, b)
    shutil.move(tmp, PATH)
    print("repeated footnotes removed:", removed)

elif MODE == "renumber":
    pdf = sys.argv[2]
    n_pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    def norm(s):
        return re.sub(r"[^؀-ۿA-Za-z0-9]", "", s)
    pages = {p: norm(subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", pdf, "-"],
                                   capture_output=True, text=True).stdout) for p in range(1, n_pages + 1)}
    page_of = {}
    unmatched = []
    last = 15
    for fid, run, nxt in refs:          # footnotes are in document order, so pages never decrease
        # context: the body text just before the mark (it is printed on the same page)
        par = run
        while par.tag != W + "p":
            par = par.getparent()
        before = []
        for el in par.iter():
            if el is run:
                break
            if el.tag == W + "t" and el.text:
                before.append(el.text)
        ctx = re.sub(r"[0-9۰-۹]", "", norm("".join(before)))[-12:]   # digits may be reordered by bidi text
        found = None
        if len(ctx) >= 6:
            cands = [q for q in range(15, n_pages + 1) if ctx in pages[q]]
            ahead = [q for q in cands if q >= last - 1]
            if ahead:
                found = ahead[0]
            elif cands:
                found = cands[-1] if False else cands[0]
        if found is None:
            unmatched.append(fid)
            found = last
        last = found
        page_of[fid] = found
    counter = {}
    for fid, run, nxt in refs:
        p = page_of[fid]
        counter[p] = counter.get(p, 0) + 1
        num = str(counter[p]).translate(DIG_FA)
        if nxt is not None and nxt.tag == W + "r":
            ts = list(nxt.iter(W + "t"))
            if ts and re.fullmatch(r"[0-9۰-۹]+", "".join(t.text or "" for t in ts)):
                ts[0].text = num
                for extra in ts[1:]: extra.text = ""
        # footnote text mark
        f = fns[fid]
        for t in f.iter(W + "t"):
            if re.fullmatch(r"[0-9۰-۹]+", (t.text or "").strip()):
                t.text = num
                break
    d.save(PATH)
    z = zipfile.ZipFile(PATH)
    data = {n: z.read(n) for n in z.namelist()}
    z.close()
    data["word/footnotes.xml"] = etree.tostring(froot, xml_declaration=True, encoding="UTF-8", standalone=True)
    tmp = PATH + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for n, b in data.items():
            zout.writestr(n, b)
    shutil.move(tmp, PATH)
    print("footnotes renumbered:", len(refs), "located:", len(refs) - len(unmatched), "placed by order:", len(unmatched))
