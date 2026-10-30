# -*- coding: utf-8 -*-
"""Reproduce the baseline full-dynamics (Model A) results reported in Chapter 3.

Usage:  python3 reproduce_base.py <case>
  tiny     omega = 27.4864 deg, Omega = 175.6206 deg, no sail   expected t120 = 0.2935 yr
  natural  omega = 0 deg, Omega = 0 deg, no sail                expected t120 = 7.50 yr
  sail140  omega = 270 deg, Omega = 0 deg, 140 m^2 ideal sail    expected t120 = 11.90 yr
Perigee 250 km, F10.7 = 130, Ap = 10, Cd = 2.2, rtol = 1e-9, epoch 2026-01-01 00:00 UT.
Prints one JSON line. Requires numpy and scipy only.
"""
import json
import sys
import time

import numpy as np
import scipy

import decay_sim as ds
import full_prop as fp

CASES = {
    "tiny": dict(argp=27.4864, raan=175.6206, a_sail=0.0, expected=0.2935),
    "natural": dict(argp=0.0, raan=0.0, a_sail=0.0, expected=7.50),
    "sail140": dict(argp=270.0, raan=0.0, a_sail=140.0, expected=11.90),
}


def main(name):
    c = CASES[name]
    t0 = time.time()
    out = fp.propagate(250.0, c["argp"], a_sail=c["a_sail"], sail_factor=1.0,
                       deploy_day=0.0, t_max_yr=25.0, f107=130.0, ap=10.0,
                       cd=ds.CD, rtol=1e-9, stop_km=(120.0,),
                       raan_deg=c["raan"], jd0=ds.JD_EPOCH)
    t120 = float(out["t_stop_yr"][120.0])
    ok = bool(np.isfinite(t120))
    rec = dict(case=name,
               t120_yr=round(t120, 4) if ok else None,
               expected_yr=c["expected"],
               rel_diff_percent=round(100.0 * (t120 - c["expected"]) / c["expected"], 3) if ok else None,
               hp_min_km=round(float(out["peri_hp_km"].min()), 2) if out["peri_hp_km"].size else None,
               wall_s=round(time.time() - t0, 1),
               python=sys.version.split()[0], numpy=np.__version__, scipy=scipy.__version__)
    print(json.dumps(rec, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
