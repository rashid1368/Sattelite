# -*- coding: utf-8 -*-
"""Full-model (Model A) sail-area grid for the Latin-hypercube geometries whose natural lifetime exceeds 25 years.

Usage: python3 grid_ch3.py <geometry indices, comma separated>
Index is 0-based: index k is row k+1 of Table 3-4 (16-point Latin hypercube sample, seed 42, Chapter 3);
(omega, Omega) are the values of that row.
Writes one JSON line per run: index, omega, raan, sail area, t120 in years (null if not reached in 25 years),
lowest perigee altitude. Perigee 250 km, F10.7 = 130, Ap = 10, Cd = 2.2, rtol = 1e-9, epoch 2026-01-01 00:00 UT.
"""
import json
import sys
import time

import numpy as np

import decay_sim as ds
import full_prop as fp

GEOM = {
    1: (228.1815, 74.3092), 3: (72.8744, 49.8136), 6: (98.0130, 3.9879), 7: (282.5232, 152.3871),
    8: (190.0218, 268.5641), 9: (138.8783, 345.7876), 10: (5.4430, 307.0232), 11: (113.1593, 114.9048),
    13: (349.4988, 111.5144), 14: (221.5285, 29.6314), 15: (50.7429, 225.7310),
}
AREAS = [40.0, 80.0, 140.0, 200.0, 300.0, 400.0]


def main(indices):
    for idx in indices:
        w, o = GEOM[idx]
        for A in AREAS:
            t0 = time.time()
            out = fp.propagate(250.0, w, a_sail=A, sail_factor=1.0, deploy_day=0.0, t_max_yr=25.0,
                               f107=130.0, ap=10.0, cd=ds.CD, rtol=1e-9, stop_km=(120.0,),
                               raan_deg=o, jd0=ds.JD_EPOCH)
            t120 = float(out["t_stop_yr"][120.0])
            ok = bool(np.isfinite(t120))
            rec = dict(idx=idx, omega=w, raan=o, A=A, sf=1.0, f107=130.0, ap=10.0, cd=ds.CD,
                       t120_yr=round(t120, 4) if ok else None,
                       hp_min_km=round(float(out["peri_hp_km"].min()), 2) if out["peri_hp_km"].size else None,
                       wall_s=round(time.time() - t0, 1))
            print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1].split(",")])
