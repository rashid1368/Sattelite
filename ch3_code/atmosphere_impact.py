# -*- coding: utf-8 -*-
"""Impact of the T7 density finding on the reported Chapter 3 lifetimes.

Test T7 showed that the exponential atmosphere of Chen et al. (2024) overestimates
the NRLMSIS 2.0 density by a factor of about 1.3 to 2.9 in the 200-300 km band. The
drag deceleration scales with the density, so the reported lifetimes may be
systematically short. This script recomputes the three reference cases of the thesis
with the empirical NRLMSIS 2.0 atmosphere and compares them with the published values.

Cases (Section 3-7): tiny, natural, sail140. See reproduce_base.py.

Output: logs/t8b_atmosphere_impact.json
"""
import json
import os
import time

import numpy as np

import decay_sim as ds
import full_prop as fp
import nrlmsis_atm as na

CASES = {
    "tiny": dict(argp=27.4864, raan=175.6206, a_sail=0.0, expected=0.2935),
    "natural": dict(argp=0.0, raan=0.0, a_sail=0.0, expected=7.50),
    "sail140": dict(argp=270.0, raan=0.0, a_sail=140.0, expected=11.90),
}


def run(case, atm):
    c = CASES[case]
    t0 = time.time()
    out = fp.propagate(250.0, c["argp"], a_sail=c["a_sail"], sail_factor=1.0,
                       deploy_day=0.0, t_max_yr=25.0, f107=130.0, ap=10.0,
                       cd=ds.CD, rtol=1e-9, stop_km=(120.0,),
                       raan_deg=c["raan"], jd0=ds.JD_EPOCH, atm_model=atm)
    t120 = float(out["t_stop_yr"][120.0])
    ok = bool(np.isfinite(t120))
    return dict(case=case, atmosphere="NRLMSIS 2.0",
                t120_yr=round(t120, 4) if ok else None,
                expected_exp_yr=c["expected"],
                rel_diff_percent=round(100.0 * (t120 - c["expected"]) / c["expected"], 2) if ok else None,
                hp_min_km=round(float(out["peri_hp_km"].min()), 2) if out["peri_hp_km"].size else None,
                wall_s=round(time.time() - t0, 1))


def main():
    cases = sys.argv[1].split(",") if len(sys.argv) > 1 else list(CASES)
    atm = na.NrlmsisAtm(ds.JD_EPOCH)
    recs = []
    for case in cases:
        r = run(case, atm)
        recs.append(r)
        print(json.dumps(r), flush=True)
    out = dict(test="atmosphere_impact_NRLMSIS_vs_exponential", recs=recs)
    os.makedirs("logs", exist_ok=True)
    with open(os.path.join("logs", "t8b_atmosphere_impact.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    main()
