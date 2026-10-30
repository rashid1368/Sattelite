# -*- coding: utf-8 -*-
"""T7: comparison of the Chapter 3 exponential atmosphere with NRLMSIS 2.0 (pymsis).

Protocol (Section 3-9-3): total mass density and temperature at 200-300 km for
three solar activity levels (F10.7 = 70, 130, 200) with Ap = 10, compared against
the exponential model of Chen et al. (2024) as implemented in decay_sim.rho_atm.

Reference geometry: latitude 0, longitude 0, epoch 2026-01-01 00:00 UT.
Output: logs/t7_density.json and logs/t7_density.csv
"""
import csv
import json
import os

import numpy as np
import pymsis

import decay_sim as ds

EPOCH = "2026-01-01T00:00"
ALTS = np.arange(200.0, 300.1, 10.0)          # 200 ... 300 km
F107S = (70.0, 130.0, 200.0)
AP = 10.0
LAT, LON = 0.0, 0.0


def nrlmsis_density_temperature(f107):
    """Total mass density (kg/m^3) and temperature (K) from NRLMSIS 2.0.

    pymsis expects aps as a 2-D array of shape (ndates, 7): column 0 is the daily
    Ap, columns 1-6 are the 3-hourly Ap indices and their averages.  Only column 0
    is used unless the storm-time switch (geomagnetic_activity=-1) is set, so all
    seven columns are filled with the same value here.
    """
    dates = np.array([EPOCH], dtype="datetime64[s]")
    aps = np.full((1, 7), AP)
    out = pymsis.calculate(dates, [LON], [LAT], ALTS,
                           f107s=[f107], f107as=[f107], aps=aps, version=2.0)
    arr = np.asarray(out)
    arr = np.squeeze(arr)                        # (n_alts, n_vars)
    names = [v.name for v in pymsis.Variable]
    i_rho = names.index("MASS_DENSITY")
    i_t = names.index("TEMPERATURE")
    return arr[:, i_rho], arr[:, i_t]


def main():
    rows = []
    for f107 in F107S:
        rho_ms, t_ms = nrlmsis_density_temperature(f107)
        for k, alt in enumerate(ALTS):
            h_m = alt * 1000.0
            rho_chen = float(ds.rho_atm(h_m, f107=f107, ap=AP))
            # scale height and temperature implied by the exponential model
            t_chen = 900.0 + 2.5 * (f107 - 70.0) + 1.5 * AP
            h_scale = t_chen / (27.0 - 0.012 * (alt - 200.0))
            rows.append(dict(
                f107=f107, ap=AP, alt_km=float(alt),
                rho_msis_kgm3=float(rho_ms[k]), rho_chen_kgm3=rho_chen,
                ratio_chen_over_msis=rho_chen / float(rho_ms[k]),
                t_msis_K=float(t_ms[k]), t_chen_K=t_chen,
                scale_height_chen_km=float(h_scale),
            ))

    with open(os.path.join("logs", "t7_density.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    summary = {}
    for f107 in F107S:
        sel = [r for r in rows if r["f107"] == f107]
        ratios = [r["ratio_chen_over_msis"] for r in sel]
        summary[f"F10.7={f107:.0f}"] = dict(
            ratio_min=min(ratios), ratio_max=max(ratios),
            ratio_mean=float(np.mean(ratios)),
            t_msis_range_K=[min(r["t_msis_K"] for r in sel), max(r["t_msis_K"] for r in sel)],
            t_chen_K=sel[0]["t_chen_K"],
            rho_at_250=dict(msis=sel[5]["rho_msis_kgm3"], chen=sel[5]["rho_chen_kgm3"],
                            ratio=sel[5]["ratio_chen_over_msis"]),
        )
    rec = dict(test="T7_density_comparison", epoch=EPOCH, lat=LAT, lon=LON, ap=AP,
               altitudes_km=[float(a) for a in ALTS], f107_levels=list(F107S),
               model="Chen et al. (2024) exponential vs NRLMSIS 2.0 (pymsis)",
               pymsis_version=getattr(pymsis, "__version__", "unknown"), summary=summary)
    os.makedirs("logs", exist_ok=True)
    with open(os.path.join("logs", "t7_density.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)

    print(json.dumps(rec["summary"], ensure_ascii=False, indent=2))
    print()
    print(f"{'F10.7':>6} {'alt/km':>7} {'NRLMSIS':>12} {'Chen':>12} {'ratio':>7} "
          f"{'T_msis/K':>9} {'T_chen/K':>9}")
    for r in rows:
        print(f"{r['f107']:6.0f} {r['alt_km']:7.0f} {r['rho_msis_kgm3']:12.4e} "
              f"{r['rho_chen_kgm3']:12.4e} {r['ratio_chen_over_msis']:7.3f} "
              f"{r['t_msis_K']:9.1f} {r['t_chen_K']:9.1f}")


if __name__ == "__main__":
    main()
