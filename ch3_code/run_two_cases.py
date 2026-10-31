import json, time, numpy as np
import decay_sim as ds, full_prop as fp
for tag, w, a in [("nat_270_0", 270.0, 0.0), ("sail140_at_0_0", 0.0, 140.0), ("nat_0_0", 0.0, 0.0)]:
    t0=time.time()
    o=fp.propagate(250.0, w, a_sail=a, t_max_yr=25.0, f107=130.0, ap=10.0, cd=ds.CD,
                   rtol=1e-9, stop_km=(120.0,))
    t=float(o['t_stop_yr'][120.0])
    print(json.dumps(dict(job=tag, t120_yr=round(t,4) if np.isfinite(t) else None,
                          hp_min_km=round(float(o['peri_hp_km'].min()),2) if o['peri_hp_km'].size else None,
                          wall_s=round(time.time()-t0,1))), flush=True)
