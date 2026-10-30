# -*- coding: utf-8 -*-
"""Audit checks on the Chapter 3 reference cases and the Model A / Model B comparison.

C1  Is the sail actually compared at a fixed geometry?  The three reference cases
    are "tiny" = (omega 27.4864, Omega 175.6206) natural, "natural" = (0, 0) natural,
    and "sail140" = (270, 0) with a 140 m^2 sail.  The sail case therefore sits on a
    DIFFERENT geometry from the natural case.  Compute the natural lifetime of the
    sail140 geometry so the sail effect can be separated from the geometry effect.

C2  Model A with J2 and drag only (no Moon, no Sun, no SRP) at (0, 0): the thesis
    Table 3-6 reports 60.36 yr.

C3  Model B (orbit-averaged, drag only) at (0, 0): the thesis Table 3-6 reports
    60.77 yr.

C4  Reproducibility: the same case run twice must give a bit-identical answer.

C5  Sensitivity: a physically negligible perturbation (epoch shifted by 1 s, and
    rtol 1e-9 vs 1e-10) must not move the result much.  This separates chaos from
    a systematic environment difference.

Usage:  python3 audit_checks.py [c1 c2 c3 c4 c5]
"""
import json
import sys
import time

import numpy as np

import decay_sim as ds
import full_prop as fp


def prop(hp0=250.0, argp=0.0, raan=0.0, a_sail=0.0, t_max=25.0, third=True, srp=True,
         rtol=1e-9, jd0=None):
    out = fp.propagate(hp0, argp, a_sail=a_sail, sail_factor=1.0, deploy_day=0.0,
                       t_max_yr=t_max, f107=130.0, ap=10.0, cd=ds.CD, rtol=rtol,
                       stop_km=(120.0,), raan_deg=raan, jd0=jd0, third=third, srp=srp)
    t = float(out["t_stop_yr"][120.0])
    return (round(t, 4) if np.isfinite(t) else None)


def c1():
    """Natural lifetime on the geometry of the sail140 reference case."""
    recs = []
    for tag, a_sail in (("natural_on_sail140_geometry", 0.0), ("sail140", 140.0)):
        t0 = time.time()
        t120 = prop(argp=270.0, raan=0.0, a_sail=a_sail)
        recs.append(dict(tag=tag, omega=270.0, raan=0.0, a_sail=a_sail, t120_yr=t120,
                         wall_s=round(time.time() - t0, 1)))
        print(json.dumps(recs[-1]), flush=True)
    nat = recs[0]["t120_yr"]
    sail = recs[1]["t120_yr"]
    if nat and sail:
        print(f"\n  sail effect at FIXED geometry: {nat} yr -> {sail} yr "
              f"({100.0*(sail-nat)/nat:+.1f} %)")
    print(f"  thesis headline: natural (omega=0) = 7.50 yr vs sail140 (omega=270) = 11.90 yr "
          f"-> the pair as reported differs by {100.0*(11.90-7.50)/7.50:+.1f} %\n")
    return recs


def c2():
    """Model A with J2 and drag only."""
    t0 = time.time()
    t120 = prop(argp=0.0, raan=0.0, third=False, srp=False)
    rec = dict(tag="modelA_j2_drag_only", omega=0.0, raan=0.0, t120_yr=t120,
               thesis_reported=60.36, wall_s=round(time.time() - t0, 1))
    print(json.dumps(rec), flush=True)
    return [rec]


def c3():
    """Model B: orbit-averaged drag only."""
    import decay_sim as ds2
    t0 = time.time()
    a0, e0 = ds2.gto_initial_state(250.0)[:2]
    res = ds2.lifetime_days(250.0, a_sail=0.0)
    t120 = float(res[120.0]) / 365.25
    rec = dict(tag="modelB_orbit_averaged_drag", osculating_init=True,
               t120_yr=round(t120, 4) if np.isfinite(t120) else None,
               thesis_reported=60.77, wall_s=round(time.time() - t0, 1))
    print(json.dumps(rec), flush=True)
    # also with the orbit-averaged (mean) elements as the initial condition
    a_m, e_m = ds2.mean_gto_elements(250.0)
    res2 = ds2.lifetime_days(250.0, a_sail=0.0, mean0=(a_m, e_m))
    t2 = float(res2[120.0]) / 365.25
    rec2 = dict(tag="modelB_mean_element_init", t120_yr=round(t2, 4) if np.isfinite(t2) else None,
                wall_s=round(time.time() - t0, 1))
    print(json.dumps(rec2), flush=True)
    return [rec, rec2]


def c4():
    """Same case twice: bit-reproducible?"""
    a = prop(argp=27.4864, raan=175.6206, t_max=1.0)
    b = prop(argp=27.4864, raan=175.6206, t_max=1.0)
    rec = dict(tag="repeatability", run1=a, run2=b, identical=(a == b))
    print(json.dumps(rec), flush=True)
    return [rec]


def c5():
    """Chaos check: negligible input perturbations."""
    recs = []
    base = prop(argp=0.0, raan=0.0, a_sail=140.0, t_max=25.0)
    recs.append(dict(tag="baseline_sail140_omega0", t120_yr=base))
    print(json.dumps(recs[-1]), flush=True)

    # epoch shifted by one second
    v = prop(argp=0.0, raan=0.0, a_sail=140.0, t_max=25.0, jd0=ds.JD_EPOCH + 1.0 / 86400.0)
    recs.append(dict(tag="epoch_plus_1s", t120_yr=v,
                     delta_percent=round(100.0 * (v - base) / base, 4) if base and v else None))
    print(json.dumps(recs[-1]), flush=True)

    # tighter tolerance
    v2 = prop(argp=0.0, raan=0.0, a_sail=140.0, t_max=25.0, rtol=1e-10)
    recs.append(dict(tag="rtol_1e-10", t120_yr=v2,
                     delta_percent=round(100.0 * (v2 - base) / base, 4) if base and v2 else None))
    print(json.dumps(recs[-1]), flush=True)
    return recs


CHECKS = {"c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5}

if __name__ == "__main__":
    which = sys.argv[1:] or list(CHECKS)
    out = {}
    for k in which:
        out[k] = CHECKS[k]()
    with open("logs/audit_checks.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
