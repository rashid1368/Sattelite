import numpy as np, math, sys, time
sys.path.insert(0, "D:/Downloads/Documents/Satellite/ch3_code")
import decay_sim as ds, full_prop as fp

print("=== A. Attribution of the 8x: full model vs third-body-only vs SRP-only (omega=0,Omega=0) ===")
for label, third, srp in [("full (2body+J2+drag+moon+sun+SRP)", True, True),
                          ("no SRP (2body+J2+drag+moon+sun)", True, False),
                          ("no third body, no SRP (2body+J2+drag)", False, False)]:
    t0 = time.time()
    o = fp.propagate(250.0, 0.0, a_sail=0.0, t_max_yr=25.0, f107=130.0, ap=10.0,
                     cd=ds.CD, rtol=1e-9, stop_km=(120.0,), third=third, srp=srp)
    print(f"  {label:42s} t120 = {o['t_stop_yr'][120.0]:.4f} yr  ({time.time()-t0:.1f} s)")

print()
print("=== B. T4 tolerance convergence reproduced on the short case (thesis says 0.8%) ===")
for rtol in (1e-9, 1e-10, 1e-11):
    t0 = time.time()
    o = fp.propagate(250.0, 27.4864, raan_deg=175.6206, a_sail=0.0, t_max_yr=25.0,
                     f107=130.0, ap=10.0, cd=ds.CD, rtol=rtol, stop_km=(120.0,))
    print(f"  rtol={rtol:.0e}: t120 = {o['t_stop_yr'][120.0]:.6f} yr  ({time.time()-t0:.1f} s)")

print()
print("=== C. Model B quadrature convergence (N_QUAD) ===")
a0, e0, _ = ds.gto_initial_state(250.0)
am = ds.composite_am(140.0, 1.0)
for n in (256, 1024, 4096, 16384):
    r = ds.propagate_averaged(a0, e0, lambda t: am, stops_km=(120.0,), n_quad=n,
                              dt_max_days=2.0, t_max_days=400 * 365.25)
    print(f"  n_quad={n:6d}: t120 = {r['t_cross_days'][120.0]/365.25:.4f} yr")

print()
print("=== D. Model B dt_max_days sensitivity ===")
for dtm in (4.0, 2.0, 1.0, 0.5):
    r = ds.propagate_averaged(a0, e0, lambda t: am, stops_km=(120.0,), n_quad=2048,
                              dt_max_days=dtm, t_max_days=400 * 365.25)
    print(f"  dt_max_days={dtm:4.1f}: t120 = {r['t_cross_days'][120.0]/365.25:.4f} yr")
