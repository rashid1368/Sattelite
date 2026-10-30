import sys, time, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, decay_sim as ds, full_prop as fp, nrlmsis_atm as na
mode, name = sys.argv[1], sys.argv[2]
CASES = {
 'tiny':    dict(argp=27.4864, raan=175.6206, a=0.0),
 'natural': dict(argp=0.0, raan=0.0, a=0.0),
 'natural270': dict(argp=270.0, raan=0.0, a=0.0),
 'sail140': dict(argp=270.0, raan=0.0, a=140.0),
}
kw = {}
t_max = 25.0
if mode == 'nrlmsis':
    kw['atm_model'] = na.NrlmsisAtm(ds.JD_EPOCH, f107=130.0, ap=10.0)
if name == 'j2drag100':
    c = dict(argp=0.0, raan=0.0, a=0.0); kw.update(third=False, srp=False); t_max = 100.0
else:
    c = CASES[name]
t0 = time.time()
out = fp.propagate(250.0, c['argp'], a_sail=c['a'], sail_factor=1.0, deploy_day=0.0, t_max_yr=t_max,
                   f107=130.0, ap=10.0, cd=ds.CD, rtol=1e-9, stop_km=(120.0,),
                   raan_deg=c['raan'], jd0=ds.JD_EPOCH, **kw)
t120 = out['t_stop_yr'][120.0]
print(json.dumps(dict(mode=mode, case=name, t120_yr=(None if not np.isfinite(t120) else round(float(t120), 5)),
                      hp_min=round(float(out['peri_hp_km'].min()), 3) if len(out['peri_hp_km']) else None,
                      t_max=t_max, wall_s=round(time.time()-t0, 1))), flush=True)
