# -*- coding: utf-8 -*-
"""Render a .pptx to PNG slides via PowerPoint COM."""
import os
import sys
import glob
import shutil
import win32com.client


def render(pptx_path, out_dir, width=1600, height=900):
    pptx_path = os.path.abspath(pptx_path)
    out_dir = os.path.abspath(out_dir)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = None
    try:
        pres = app.Presentations.Open(pptx_path, ReadOnly=True, WithWindow=False)
        pres.SaveCopyAs(os.path.join(out_dir, "deck.png"), 18)  # ppSaveAsPNG
        # SaveCopyAs PNG makes a folder; instead export slides individually
        for i, slide in enumerate(pres.Slides, 1):
            slide.Export(os.path.join(out_dir, "slide%02d.png" % i), "PNG",
                         width, height)
    finally:
        if pres is not None:
            pres.Close()
        app.Quit()
    files = sorted(glob.glob(os.path.join(out_dir, "slide*.png")))
    print("rendered %d slides to %s" % (len(files), out_dir))


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
