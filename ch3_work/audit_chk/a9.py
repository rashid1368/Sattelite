import numpy as np, math, sys, time
sys.path.insert(0, "D:/Downloads/Documents/Satellite/ch3_code")
import decay_sim as ds

print("=== A. Model B: osculating vs mean-element initialisation ===")
hp0 = 250.0
a0_o, e0_o, _ = ds.gto_initial_state(hp0)
a0_m, e0_m = ds.mean_gto_elements(hp0)
print(f"  osculating: a={a0_o/1e3:.3f} km  e={e0_o:.6f}  hp={hp0:.1f} km")
print(f"  mean      : a={a0_m/1e3:.3f} km  e={e0_m:.6f}  hp={(a0_m*(1-e0_m)-ds.R_E)/1e3:.2f} km")
print(f"  da = {1000*(a0_o-a0_m)/1e3:.2f} km (osculating higher), de = {e0_o-e0_m:+.6f}")

am_nat = ds.composite_am(0.0)
am_fn = lambda t: am_nat
for label, (aa, ee) in [("osculating (what lifetime_days uses by default)", (a0_o, e0_o)),
                        ("mean (what mean_gto_elements docstring prescribes)", (a0_m, e0_m))]:
    t0 = time.time()
    res = ds.propagate_averaged(aa, ee, am_fn, stops_km=(175.0, 120.0), n_quad=2048,
                                 dt_max_days=2.0)
    c = res["t_cross_days"]
    print(f"  {label}: t175={c[175.0]/365.25:.3f} yr  t120={c[120.0]/365.25:.3f} yr "
          f"({time.time()-t0:.1f} s)")

print()
print("=== B. Model B monotonicity of lifetime vs sail area (bisection validity) ===")
for A in (0., 40., 80., 140., 200., 300., 400.):
    am = ds.composite_am(A, 1.0)
    f = lambda t: am
    res = ds.propagate_averaged(a0_o, e0_o, f, stops_km=(120.0,), n_quad=2048, dt_max_days=2.0,
                                t_max_days=200*365.25)
    c = res["t_cross_days"][120.0]
    print(f"   A={A:6.1f} m2  am={am:.5f}  t120={'inf' if not np.isfinite(c) else f'{c/365.25:9.3f} yr'}")

print()
print("=== C. T5: Sun/Moon linear-interpolation error over 25 yr (thesis claims Sun 2.48 km, Moon 1.27 km) ===")
TAB = 1800.0
yr = 25.0
n = int(yr * 365.25 * 86400.0)
rng = np.random.default_rng(12345)
ts = rng.uniform(0, n, 4000)
esun, emoon = [], []
for t in ts:
    jd = ds.JD_EPOCH + t / 86400.0
    i0 = int(t / TAB)
    f = t / TAB - i0
    jd0 = ds.JD_EPOCH + i0 * TAB / 86400.0
    jd1 = ds.JD_EPOCH + (i0 + 1) * TAB / 86400.0
    S0, S1 = ds.sun_eci(jd0), ds.sun_eci(jd1)
    M0, M1 = ds.moon_eci(jd0), ds.moon_eci(jd1)
    esun.append(np.linalg.norm((S0 + f * (S1 - S0)) - ds.sun_eci(jd)))
    emoon.append(np.linalg.norm((M0 + f * (M1 - M0)) - ds.moon_eci(jd)))
esun = np.array(esun) / 1e3
emoon = np.array(emoon) / 1e3
print(f"  Sun : max {esun.max():.3f} km  rms {np.sqrt((esun**2).mean()):.3f} km")
print(f"  Moon: max {emoon.max():.3f} km  rms {np.sqrt((emoon**2).mean()):.3f} km")
print("  thesis line 824 claims: Sun max 2.48 km rms 1.76 km; Moon max 1.27 km rms 0.81 km")

print()
print("=== D. drag vs SRP at perigee (thesis line 819: 'more than 1000x') ===")
am = ds.composite_am(0.0)
rp = ds.R_E + 250e3
vp = math.sqrt(ds.MU_E * (2.0 / rp - 1.0 / (0.5 * (rp + ds.R_E + 35786e3))))
rho = float(ds.rho_atm(250e3, 130., 10.))
a_drag = 0.5 * ds.CD * am * rho * vp * vp
P = ds.P_SR * (ds.AU / (ds.AU - rp)) ** 2
a_srp = P * ds.CR * am / (ds.AU - rp)
print(f"  a_drag={a_drag:.4e} m/s^2   a_srp={a_srp:.4e} m/s^2   ratio={a_drag/a_srp:.1f}")
print(f"  perigee speed {vp:.1f} m/s ; Earth rotation at perigee {ds.W_E*rp:.1f} m/s "
      f"= {100*ds.W_E*rp/vp:.2f}% of v")
