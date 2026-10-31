# -*- coding: utf-8 -*-
"""Fill the Chapter 4 gaps: natural lifetime of the 16 LHS geometries + one-at-a-time
sensitivity cases at the base geometry, all with Model A (exponential atmosphere).
Writes one JSON line per run to logs/ch4_missing2.jsonl."""
import json, time, sys
import numpy as np
from multiprocessing import Pool
import decay_sim as ds
import full_prop as fp

GEOM = {
    1: (228.1815, 74.3092), 2: (335.3765, 203.0479), 3: (72.8744, 49.8136),
    4: (177.1236, 192.3741), 5: (261.6618, 316.6510), 6: (98.0130, 3.9879),
    7: (282.5232, 152.3871), 8: (190.0218, 268.5641), 9: (138.8783, 345.7876),
    10: (5.4430, 307.0232), 11: (113.1593, 114.9048), 12: (27.4948, 175.6242),
    13: (349.4988, 111.5144), 14: (221.5285, 29.6314), 15: (50.7429, 225.7310),
    16: (335.3765, 203.0479),
}
# Fall back to the exact table-3-4 values where the set above is a placeholder
TABLE34 = {
    1: (297.59, 282.63), 2: (228.18, 74.31), 3: (335.38, 203.05), 4: (72.87, 49.81),
    5: (177.12, 192.37), 6: (261.66, 316.65), 7: (98.01, 3.99), 8: (282.52, 152.39),
    9: (190.02, 268.56), 10: (138.88, 345.79), 11: (5.44, 307.02), 12: (113.16, 114.90),
    13: (27.49, 175.62), 14: (349.50, 111.51), 15: (221.53, 29.63), 16: (50.74, 225.73),
}

A_ST, M_TOT = ds.A_STAGE, ds.M_STAGE + ds.M_MOD

def run(job):
    name = job["name"]
    t0 = time.time()
    kw = dict(t_max_yr=25.0, f107=job.get("f107", 130.0), ap=10.0, cd=job.get("cd", ds.CD),
              rtol=1e-9, stop_km=(120.0,), event_km=(175.0, 120.0),
              raan_deg=job.get("raan", 0.0), jd0=ds.JD_EPOCH + job.get("djd", 0.0))
    hp0 = job.get("hp0", 250.0)
    a_sail = job.get("A", 0.0)
    sf = job.get("sf", 1.0)
    area_scale = job.get("area_scale", 1.0)
    am_nat = job.get("am_nat")
    if area_scale != 1.0:
        am_nat = area_scale * A_ST / M_TOT
        am_sail = (area_scale * A_ST + sf * a_sail) / (M_TOT + ds.SIGMA_SAIL * a_sail)
    else:
        am_sail = None
    try:
        out = fp.propagate(hp0, job.get("omega", 0.0), a_sail=a_sail, sail_factor=sf,
                           deploy_day=job.get("deploy_day", 0.0), am_nat=am_nat, am_sail=am_sail,
                           **kw)
        t120 = float(out["t_stop_yr"][120.0])
        rec = dict(job=name, t120_yr=(round(t120, 4) if np.isfinite(t120) else None),
                   t175_yr=(round(float(out["t_stop_yr"][175.0]), 4)
                            if np.isfinite(out["t_stop_yr"][175.0]) else None),
                   hp_min_km=(round(float(out["peri_hp_km"].min()), 2) if out["peri_hp_km"].size else None),
                   wall_s=round(time.time() - t0, 1))
    except Exception as e:
        rec = dict(job=name, error=repr(e), wall_s=round(time.time() - t0, 1))
    return rec

jobs = []
for i in range(1, 17):
    w, o = TABLE34[i]
    jobs.append(dict(name=f"nat_g{i:02d}", omega=w, raan=o, A=0.0))
base = dict(omega=0.0, raan=0.0, A=140.0)
for tag, over in [
    ("sens_cd_1.1", dict(cd=1.1)), ("sens_cd_2.0", dict(cd=2.0)),
    ("sens_cd_2.4", dict(cd=2.4)), ("sens_cd_4.4", dict(cd=4.4)),
    ("sens_area_0.8", dict(area_scale=0.8)), ("sens_area_1.2", dict(area_scale=1.2)),
    ("sens_delay_90", dict(deploy_day=90.0)), ("sens_delay_180", dict(deploy_day=180.0)),
    ("sens_tumble", dict(sf=0.5)),
    ("sens_f107_70", dict(f107=70.0)), ("sens_f107_200", dict(f107=200.0)),
    ("sens_epoch181", dict(djd=181.0)),
    ("sens_raan_90", dict(raan=90.0)), ("sens_raan_180", dict(raan=180.0)),
    ("sens_hp0_300", dict(hp0=300.0)),
]:
    jobs.append(dict(base, **over, name=tag))

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "nat":
        sel = [j for j in jobs if j["name"].startswith("nat_")]
    elif which == "sens":
        sel = [j for j in jobs if j["name"].startswith("sens_")]
    else:
        sel = jobs
    with open("logs/ch4_missing2.jsonl", "a", encoding="utf8") as f, Pool(7) as p:
        for rec in p.imap_unordered(run, sel):
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(json.dumps(rec), flush=True)
