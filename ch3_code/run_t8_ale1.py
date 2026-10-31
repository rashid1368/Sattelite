# -*- coding: utf-8 -*-
"""T8: reproduce the ALE-1 de-orbit with the exponential-atmosphere Model A.

ALE-1 (Takeda et al. 2023): 68.16 kg at launch, 65.29 kg after SDOM separation,
CD = 2.2, mean cross-section 3.4 m^2 with the film fully deployed and 0.4 m^2
without it, initial circular orbit at 500 km, i = 97.04 deg.  The mission target
was to drop below 400 km.

The paper announced ~650 days to reach the ISS altitude with the nominal area,
but two of the four film corners failed in late 2019 and the film became a drag
flag; the paper derives CD*A = 4.0 m^2 for the as-flown configuration, i.e. a
mean area of 1.8 m^2 at CD = 2.2.  The descent from the film deployment on
25 December 2019 to the 400 km hand-over on 27 July 2022 therefore took 945 days,
not 650.

Two area cases are run (nominal 3.4 m^2 and as-flown 1.8 m^2) at two activity
levels, and the time to 400 km is recorded together with the times to 175 and
120 km.  A 500 km circular orbit at i = 97 deg lies outside the GTO envelope the
model was built for, so this is a check on the drag/atmosphere chain, not a full
flight validation.
"""
import json
import os
import time

import numpy as np

import full_prop as fp

M_ALE = 65.29
AM_NAT = 0.4 / M_ALE

CASES = [
    dict(tag="ale1_nominal_f107_90", area=3.4, f107=90.0),
    dict(tag="ale1_nominal_f107_130", area=3.4, f107=130.0),
    dict(tag="ale1_asflown_f107_90", area=1.8, f107=90.0),
    dict(tag="ale1_asflown_f107_130", area=1.8, f107=130.0),
]


def run(c):
    t0 = time.time()
    out = fp.propagate(500.0, 0.0, a_sail=0.0, sail_factor=0.0,
                       deploy_day=0.0, am_nat=AM_NAT, am_sail=c["area"] / M_ALE,
                       t_max_yr=12.0, f107=c["f107"], ap=10.0, cd=2.2, rtol=1e-9,
                       stop_km=(120.0,), event_km=(400.0, 175.0, 120.0),
                       inc_deg=97.04, ha_km=500.0)
    t = {k: float(v) for k, v in out["t_stop_yr"].items()}
    return dict(tag=c["tag"], area_m2=c["area"], f107=c["f107"],
                t400_days=(round(t[400.0] * 365.25, 1) if np.isfinite(t[400.0]) else None),
                t175_days=(round(t[175.0] * 365.25, 1) if np.isfinite(t[175.0]) else None),
                t120_days=(round(t[120.0] * 365.25, 1) if np.isfinite(t[120.0]) else None),
                wall_s=round(time.time() - t0, 1))


if __name__ == "__main__":
    log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "t8_ale1.jsonl")
    with open(log, "w", encoding="utf8") as f:
        for c in CASES:
            rec = run(c)
            f.write(json.dumps(rec) + "\n")
            f.flush()
            print(json.dumps(rec), flush=True)
