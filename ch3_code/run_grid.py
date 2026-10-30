import sys, time, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, decay_sim as ds, full_prop as fp, nrlmsis_atm as na
# Table 3-4 (rows 1..16): (omega, Omega) in degrees, Latin hypercube, seed 42
ROWS = {1:(297.5900,282.6300),2:(228.1815,74.3092),3:(335.3800,203.0500),4:(72.8744,49.8136),
        5:(177.1200,192.3700),6:(261.6600,316.6500),7:(98.0130,3.9879),8:(282.5232,152.3871),
        9:(190.0218,268.5641),10:(138.8783,345.7876),11:(5.4430,307.0232),12:(113.1593,114.9048),
        13:(27.4864,175.6206),14:(349.4988,111.5144),15:(221.5285,29.6314),16:(50.7429,225.7310)}
mode, row, sail = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
w, o = ROWS[row]
kw = {}
if mode == 'nrlmsis':
    kw['atm_model'] = na.NrlmsisAtm(ds.JD_EPOCH, f107=130.0, ap=10.0)
t0 = time.time()
out = fp.propagate(250.0, w, a_sail=sail, sail_factor=1.0, deploy_day=0.0, t_max_yr=25.0,
                   f107=130.0, ap=10.0, cd=ds.CD, rtol=1e-9, stop_km=(120.0,),
                   raan_deg=o, jd0=ds.JD_EPOCH, **kw)
t120 = out['t_stop_yr'][120.0]
print(json.dumps(dict(mode=mode, row=row, omega=w, raan=o, sail=sail,
                      t120_yr=(None if not np.isfinite(t120) else round(float(t120), 5)),
                      hp_min=round(float(out['peri_hp_km'].min()), 3) if len(out['peri_hp_km']) else None,
                      wall_s=round(time.time()-t0, 1))), flush=True)
