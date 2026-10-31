# -*- coding: utf-8 -*-
"""Model B convergence (quadrature points and maximum step) for the 140 m2 sail case at
omega = Omega = 0 with the osculating initial state. Writes results/model_B_convergence.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decay_sim as ds

a0, e0, _ = ds.gto_initial_state(250.0)
am = ds.composite_am(140.0, 1.0)
out = {"case": "Model B, sail 140 m2, omega=Omega=0, osculating initial state", "quadrature": {}, "max_step": {}}
for n in (256, 1024, 4096, 16384):
    r = ds.propagate_averaged(a0, e0, lambda t: am, stops_km=(120.0,), n_quad=n,
                              dt_max_days=2.0, t_max_days=400 * 365.25)
    out["quadrature"][str(n)] = round(r["t_cross_days"][120.0] / 365.25, 4)
    print("n_quad", n, out["quadrature"][str(n)], flush=True)
for dtm in (4.0, 2.0, 1.0, 0.5):
    r = ds.propagate_averaged(a0, e0, lambda t: am, stops_km=(120.0,), n_quad=2048,
                              dt_max_days=dtm, t_max_days=400 * 365.25)
    out["max_step"][str(dtm)] = round(r["t_cross_days"][120.0] / 365.25, 4)
    print("dt_max", dtm, out["max_step"][str(dtm)], flush=True)
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "model_B_convergence.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print("saved", path)
