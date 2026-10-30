import sys, time, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, decay_sim as ds, full_prop as fp, nrlmsis_atm as na
mode, tag, omega, raan, area, tmax = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
kw = {}
if tag == 'nosrp':
    kw['srp'] = False
if mode == 'nrlmsis':
    kw['atm_model'] = na.NrlmsisAtm(ds.JD_EPOCH, f107=130.0, ap=10.0)
t0 = time.time()
out = fp.propagate(250.0, omega, a_sail=area, sail_factor=1.0, deploy_day=0.0, t_max_yr=tmax,
                   f107=130.0, ap=10.0, cd=ds.CD, rtol=1e-9, stop_km=(120.0,),
                   raan_deg=raan, jd0=ds.JD_EPOCH, **kw)
t120 = out['t_stop_yr'][120.0]
print(json.dumps(dict(mode=mode, tag=tag, omega=omega, raan=raan, area=area, t_max=tmax,
                      t120_yr=(None if not np.isfinite(t120) else round(float(t120), 5)),
                      hp_min=round(float(out['peri_hp_km'].min()), 3) if len(out['peri_hp_km']) else None,
                      wall_s=round(time.time()-t0, 1))), flush=True)
