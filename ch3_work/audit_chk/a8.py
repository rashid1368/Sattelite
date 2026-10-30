import numpy as np, math, sys, time
sys.path.insert(0, "D:/Downloads/Documents/Satellite/ch3_code")
import decay_sim as ds, full_prop as fp

print("=== 1. Perigee event: is there a spurious near-zero-time perigee? ===")
# instrument by re-implementing the event logic on a short run
y0 = fp.initial_state(250.0, 0.0, 0.0)
S, M = fp.tables(3600.0 * 12, ds.JD_EPOCH)
orig = fp.solve_ivp
captured = {}


def spy(rhs, tspan, y0_, **kw):
    sol = orig(rhs, tspan, y0_, **kw)
    captured['t_events'] = sol.t_events
    captured['status'] = sol.status
    captured['t'] = sol.t
    return sol


fp.solve_ivp = spy
t0 = time.time()
out = fp.propagate(250.0, 0.0, a_sail=0.0, t_max_yr=1.0, f107=130.0, ap=10.0,
                   cd=ds.CD, rtol=1e-9, stop_km=(120.0,))
fp.solve_ivp = orig
te = captured['t_events']
print("  first 6 perigee event times (s):", np.round(te[0][:6], 4))
print("  n perigee events:", len(te[0]), " keep(>1s) count:", int((te[0] > 1.0).sum()))
print("  first kept perigee time:", te[0][te[0] > 1.0][0], "s   (orbital period ~37922 s)")
print("  peri_hp_km first 4:", np.round(out['peri_hp_km'][:4], 4))
print("  wall", round(time.time() - t0, 1), "s")

print()
print("=== 2. terminal-event default: stop_km=(175,120) vs (120,) ===")
for stop in [(120.0,), (175.0, 120.0)]:
    o = fp.propagate(250.0, 27.4864, raan_deg=175.6206, a_sail=0.0, t_max_yr=25.0,
                     f107=130.0, ap=10.0, cd=ds.CD, rtol=1e-9, stop_km=stop)
    print(f"  stop_km={stop}: t_stop={o['t_stop_yr']} status={o['status']} t_end_yr={o['t_end_yr']:.4f}")
