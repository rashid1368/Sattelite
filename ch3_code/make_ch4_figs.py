# -*- coding: utf-8 -*-
"""Figures for Chapter 4 (plus the T7 density figure for Chapter 3).

matplotlib 3.11 shapes and bidi-orders Persian text natively through the font,
so the labels are passed as raw strings (no arabic_reshaper / python-bidi).
Output: _build/figs_ch4/*.png at 300 dpi.
"""
import csv
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, FixedLocator

OUT = os.path.join("_build", "figs_ch4")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.family"] = "Vazirmatn"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 9
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["savefig.bbox"] = "tight"

GREEN = "#2e7d4f"
RED = "#b3352c"
BLUE = "#2f5d8a"
ORANGE = "#c47a1c"
GREY = "#6b6b6b"

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def pd(x, dec=0):
    """Numeric label for ticks and annotations.

    Latin digits are kept on purpose: this matplotlib build rotates tick labels
    whose text is classified as Arabic-Indic numbers, and mixed Latin/Persian
    numerals in one figure look inconsistent.
    """
    return f"{x:.{dec}f}" if dec else f"{x:g}"


def fa(s):
    return s


def persian_axis(ax, which="x", ticks=None, fmt=pd):
    """Set ticks with explicit Persian-digit labels.

    A FuncFormatter returning Persian digits makes matplotlib rotate the tick
    labels in this build, so the labels are attached directly instead.
    """
    if ticks is None:
        return
    labels = [fmt(v) for v in ticks]
    if which == "x":
        ax.set_xticks(ticks, labels=labels, minor=False)
        ax.xaxis.set_minor_locator(FixedLocator([]))
    else:
        ax.set_yticks(ticks, labels=labels, minor=False)
        ax.yaxis.set_minor_locator(FixedLocator([]))


# ---------------------------------------------------------------- data
GRID = json.load(open("ch3_code/logs/grid_all.json", encoding="utf8"))
AREAS = [40, 80, 140, 200, 300, 400]
GD = {(r["idx"], int(r["A"])): r for r in GRID}
IDX = sorted({r["idx"] for r in GRID})


def load_nat():
    nat = {}
    p = "ch3_code/logs/ch4_missing2.jsonl"
    if os.path.exists(p):
        for line in open(p, encoding="utf8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("job", "").startswith("nat_") and "t120_yr" in r:
                nat[int(r["job"].split("_g")[1])] = r["t120_yr"]
    return nat


NAT = load_nat()
LONG = [i + 1 for i in IDX]
SHORT = [1, 3, 5, 6, 13]


def natural_value(row):
    if row in NAT and NAT[row] is not None:
        return NAT[row], False
    return 25.0, True


# ============================================ fig 3-7 density comparison
def fig37():
    rows = list(csv.DictReader(open("ch3_code/logs/t7_density.csv", encoding="utf8")))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 3.1))
    cols = {70: BLUE, 130: GREEN, 200: ORANGE}
    alt = sorted({float(r["alt_km"]) for r in rows})
    for f107, c in cols.items():
        sel = [r for r in rows if float(r["f107"]) == f107]
        ax1.plot([float(r["alt_km"]) for r in sel],
                 [float(r["ratio_chen_over_msis"]) for r in sel],
                 "-o", ms=3, lw=1.2, color=c, label=fa(f"F10.7 = {pd(f107)}"))
        ax2.semilogy([float(r["alt_km"]) for r in sel],
                     [float(r["rho_msis_kgm3"]) for r in sel], "--", lw=1.0, color=c)
        ax2.semilogy([float(r["alt_km"]) for r in sel],
                     [float(r["rho_chen_kgm3"]) for r in sel], "-", lw=1.3, color=c)
    ax1.axhline(1.0, color=GREY, lw=0.9, ls=":")
    ax1.text(201, 2.95, fa("پایین‌ترین خط: هم‌ارزی کامل"), fontsize=7,
             color=GREY, ha="left", va="top")
    ax1.set_xlabel(fa("ارتفاع (کیلومتر)"), labelpad=3)
    ax1.set_ylabel(fa("نسبت چگالی"), labelpad=5, fontsize=9)
    ax1.set_xlim(197, 303)
    ax1.grid(ls=":", lw=0.6, alpha=0.6)
    ax1.set_axisbelow(True)
    ax1.legend(fontsize=7.2, frameon=False, loc="lower right")
    persian_axis(ax1, "x", [200, 220, 240, 260, 280, 300])
    persian_axis(ax1, "y", [1.0, 1.5, 2.0, 2.5, 3.0], lambda v: pd(v, 1))

    ax2.set_xlabel(fa("ارتفاع (کیلومتر)"), labelpad=3)
    ax2.set_ylabel(fa("چگالی (kg/m³)"), labelpad=5, fontsize=8.5)
    ax2.set_xlim(197, 303)
    ax2.grid(ls=":", lw=0.6, alpha=0.6)
    ax2.set_axisbelow(True)
    ax2.set_yticks([1e-11, 1e-10])
    ax2.set_yticklabels([r"$10^{-11}$", r"$10^{-10}$"])
    proxy = [Line2D([], [], color=GREY, ls="-", lw=1.3, label=fa("مدل نمایی")),
             Line2D([], [], color=GREY, ls="--", lw=1.0, label=fa("NRLMSIS 2.0"))]
    ax2.legend(handles=proxy, fontsize=7, frameon=False, loc="lower left")
    persian_axis(ax2, "x", [200, 220, 240, 260, 280, 300])
    for a in (ax1, ax2):
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_7_density_ratio.png"), dpi=300)
    plt.close(fig)


# ============================================ fig 4-1 natural lifetime
def fig41():
    rows = list(range(1, 17))
    order = sorted(rows, key=lambda r: natural_value(r)[0], reverse=True)
    fig, ax = plt.subplots(figsize=(6.3, 3.7))
    for k, r in enumerate(order):
        v, lb = natural_value(r)
        if lb:
            ax.barh(k, 25.0, height=0.62, color="none", edgecolor=GREY, hatch="///",
                    linewidth=0.7, zorder=2)
            ax.text(25.7, k, fa("بیش از ۲۵"), va="center", ha="left", fontsize=7.5,
                    color=GREY)
        else:
            ax.barh(k, v, height=0.62, color=BLUE, zorder=2)
            ax.text(v + 0.55, k, pd(v, 2), va="center", ha="left", fontsize=7.5,
                    color=BLUE)
    ax.axvline(25.0, color=RED, lw=1.2, ls="--", zorder=3)
    ax.text(24.3, -1.02, fa("مهلت ۲۵ ساله"), color=RED, fontsize=7.5, ha="right",
            va="top")
    ax.set_yticks(range(len(order)), labels=[pd(r) for r in order], fontsize=8)
    ax.set_ylabel(fa("شماره هندسه"), labelpad=4)
    ax.set_xlabel(fa("عمر مداری طبیعی (سال)"), labelpad=4)
    ax.set_xlim(0, 33)
    ax.set_ylim(-1.1, len(order) - 0.35)
    ax.grid(axis="x", ls=":", lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    persian_axis(ax, "x", [0, 5, 10, 15, 20, 25, 30])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(os.path.join(OUT, "fig4_1_natural_lifetime.png"), dpi=300)
    plt.close(fig)


# ============================================ fig 4-2 model comparison
def fig42():
    cases = [
        ("مدل B: میانگین‌گیری مداری، فقط پسا", 60.77, BLUE),
        ("مدل A: فقط J2 و پسا", None, ORANGE),
        ("مدل A: بدون فشار تابش", 12.94, ORANGE),
        ("مدل A: کامل", 7.50, RED),
    ]
    fig, ax = plt.subplots(figsize=(6.3, 2.5))
    for k, (lbl, v, c) in enumerate(cases):
        if v is None:
            ax.barh(k, 100.0, height=0.55, color="none", edgecolor=c, hatch="///",
                    linewidth=0.9, zorder=2)
            ax.annotate("", xy=(150, k), xytext=(103, k),
                        arrowprops=dict(arrowstyle="-|>", color=c, lw=1.2))
            ax.text(158, k, fa("بدون خروج در ۲۵ سال"), va="center", ha="left",
                    fontsize=7.5, color=c)
        else:
            ax.barh(k, v, height=0.55, color=c, zorder=2)
            ax.text(v * 1.14, k, pd(v, 2), va="center", ha="left", fontsize=8, color=c)
    ax.set_yticks(range(len(cases)), labels=[c[0] for c in cases], fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(3, 700)
    ax.set_xlabel(fa("زمان رسیدن حضیض به ۱۲۰ کیلومتر (سال)"), labelpad=4)
    ax.axvline(25.0, color=RED, lw=1.0, ls="--", zorder=1)
    ax.text(25, -0.72, fa("۲۵ سال"), color=RED, fontsize=7, ha="center", va="bottom")
    ax.grid(axis="x", ls=":", lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(-0.85, len(cases) - 0.4)
    persian_axis(ax, "x", [5, 10, 25, 50, 100, 300, 600])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(os.path.join(OUT, "fig4_2_model_comparison.png"), dpi=300)
    plt.close(fig)


# ============================================ fig 4-3 t120 vs area
def fig43():
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    cmap = plt.get_cmap("tab20")
    handles = []
    for k, idx in enumerate(IDX):
        xs, ys = [], []
        for A in AREAS:
            r = GD[(idx, A)]
            xs.append(A)
            ys.append(np.nan if r["t120_yr"] is None else r["t120_yr"])
        ln, = ax.plot(xs, ys, "-o", ms=3.4, lw=1.0, color=cmap(k % 20),
                      label=fa(f"هندسه {pd(idx + 1)}"))
        handles.append(ln)
        for A in AREAS:
            if GD[(idx, A)]["t120_yr"] is None:
                ax.plot([A], [26.8], marker="^", ms=4.2, mfc="white",
                        mec=cmap(k % 20), mew=0.9, ls="none", zorder=4)
    ax.axhline(25.0, color=RED, lw=1.2, ls="--", zorder=1)
    ax.text(25, 0.78, fa("مهلت ۲۵ ساله"), color=RED, fontsize=7.5, ha="center",
            va="bottom", transform=ax.get_xaxis_transform())
    ax.set_yscale("log")
    ax.set_ylim(0.7, 80)
    ax.set_xlim(15, 430)
    ax.set_xlabel(fa("مساحت بادبان (متر مربع)"), labelpad=4)
    ax.set_ylabel(fa("زمان رسیدن به ۱۲۰ کیلومتر (سال)"), labelpad=4)
    ax.grid(ls=":", lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    persian_axis(ax, "x", AREAS)
    ax.set_yticks([1, 2, 3, 5, 10, 20, 30, 60],
                  labels=[pd(v) for v in [1, 2, 3, 5, 10, 20, 30, 60]])
    handles = handles + [plt.Line2D([], [], marker="^", ms=4.2, mfc="white",
                                    mec=GREY, mew=0.9, ls="none",
                                    label=fa("بدون خروج در ۲۵ سال"))]
    ax.legend(handles=handles, fontsize=6.8, ncol=4, frameon=False,
              loc="upper center", bbox_to_anchor=(0.5, -0.19),
              handlelength=1.5, columnspacing=1.0, labelspacing=0.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(os.path.join(OUT, "fig4_3_t120_vs_area.png"), dpi=300)
    plt.close(fig)


# ============================================ fig 4-4 compliance map
def fig44():
    nrow, ncol = len(IDX), len(AREAS)
    M = np.zeros((nrow, ncol))
    T = []
    for i, idx in enumerate(IDX):
        rowtxt = []
        for j, A in enumerate(AREAS):
            v = GD[(idx, A)]["t120_yr"]
            M[i, j] = 1.0 if (v is not None and v <= 25.0) else 0.0
            rowtxt.append("—" if v is None else pd(v, 1))
        T.append(rowtxt)
    fig, ax = plt.subplots(figsize=(5.9, 4.0))
    ax.imshow(M, cmap=matplotlib.colors.ListedColormap(["#e8b4ae", "#a9cfb5"]),
              aspect="auto", vmin=0, vmax=1)
    for i in range(nrow):
        for j in range(ncol):
            ax.text(j, i, T[i][j], ha="center", va="center", fontsize=7.5,
                    color="#1c1c1c")
    ax.set_xticks(range(ncol), labels=[pd(a) for a in AREAS], fontsize=8)
    ax.set_yticks(range(nrow), labels=[pd(i + 1) for i in IDX], fontsize=8)
    ax.set_xlabel(fa("مساحت بادبان (متر مربع)"), labelpad=4)
    ax.set_ylabel(fa("شماره هندسه"), labelpad=4)
    ax.set_xticks(np.arange(-0.5, ncol, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nrow, 1), minor=True)
    ax.grid(which="minor", color="white", lw=1.2)
    ax.tick_params(which="minor", length=0)
    ax.legend(handles=[Patch(facecolor="#a9cfb5", label=fa("منطبق (کمتر از ۲۵ سال)")),
                       Patch(facecolor="#e8b4ae", label=fa("نامنطبق یا بدون خروج"))],
              fontsize=7.3, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.14), ncol=2)
    fig.savefig(os.path.join(OUT, "fig4_4_compliance_map.png"), dpi=300)
    plt.close(fig)


# ============================================ fig 4-5 sensitivity
def fig45():
    p = "ch3_code/logs/ch4_missing2.jsonl"
    if not os.path.exists(p):
        return False
    recs = {}
    for line in open(p, encoding="utf8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            if r.get("job", "").startswith("sens_"):
                recs[r["job"]] = r
    if len(recs) < 10:
        print(f"  fig4_5 skipped: only {len(recs)} sensitivity runs")
        return False
    labels = {
        "sens_cd_1.1": fa("ضریب پسا 1.1"), "sens_cd_2.0": fa("ضریب پسا 2.0"),
        "sens_cd_2.4": fa("ضریب پسا 2.4"), "sens_cd_4.4": fa("ضریب پسا 4.4"),
        "sens_area_0.8": fa("مساحت استیج ×0.8"), "sens_area_1.2": fa("مساحت استیج ×1.2"),
        "sens_delay_90": fa("تأخیر استقرار 90 روز"),
        "sens_delay_180": fa("تأخیر استقرار 180 روز"),
        "sens_tumble": fa("چرخش آشفته (چگالی مؤثر ×0.5)"),
        "sens_f107_70": fa("شاخص F10.7 برابر 70"),
        "sens_f107_200": fa("شاخص F10.7 برابر 200"),
        "sens_epoch181": fa("جدایش 181 روز دیرتر"),
        "sens_raan_90": fa("طول گره 90 درجه"),
        "sens_raan_180": fa("طول گره 180 درجه"),
        "sens_hp0_300": fa("حضیض اولیه 300 کیلومتر"),
    }
    items = []
    for k, r in recs.items():
        if k in labels:
            v = r.get("t120_yr")
            items.append((labels[k], v if v is not None else 200.0, v is None))
    items.sort(key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ys = np.arange(len(items))
    for k, (lab, v, isnull) in enumerate(items):
        if isnull:
            ax.plot(200.0, k, marker=">", ms=6, mfc="none", mec=BLUE)
            ax.text(215, k, fa("بدون خروج تا 25 سال"), va="center", ha="left",
                    fontsize=7.5)
        else:
            ax.plot([1.138, v], [k, k], color=BLUE, lw=0.9, alpha=0.55, zorder=2)
            ax.plot(v, k, "o", ms=5.5, color=BLUE, zorder=3)
            ax.text(v * 1.12, k, pd(v, 2), va="center", ha="left", fontsize=7.5)
    ax.set_yticks(ys, labels=[t[0] for t in items], fontsize=7.8)
    ax.set_xscale("log")
    ax.set_xlim(0.4, 400)
    ax.set_ylim(-0.7, len(items) - 0.3)
    ax.set_xlabel(fa("زمان رسیدن به 120 کیلومتر (سال)"), labelpad=4)
    ax.axvline(1.138, color=GREY, lw=0.9, ls="-.", zorder=1)
    ax.text(1.138 * 0.93, len(items) - 0.45, fa("حالت مبنا: 1.14 سال"), color=GREY,
            fontsize=7, ha="right", va="center", rotation=0)
    ax.axvline(25.0, color=RED, lw=1.0, ls="--", zorder=1)
    ax.text(25 * 1.06, -0.55, fa("مهلت 25 ساله"), color=RED, fontsize=7, ha="left",
            va="center")
    ax.grid(axis="x", ls=":", lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    persian_axis(ax, "x", [0.5, 1, 2, 5, 10, 25, 100])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(os.path.join(OUT, "fig4_5_sensitivity.png"), dpi=300)
    plt.close(fig)
    return True


if __name__ == "__main__":
    fig37(); print("fig3_7 done")
    fig41(); print("fig4_1 done")
    fig42(); print("fig4_2 done")
    fig43(); print("fig4_3 done")
    fig44(); print("fig4_4 done")
    print("fig4_5", "done" if fig45() else "pending")
    print("NAT:", NAT, "| SHORT:", SHORT)
