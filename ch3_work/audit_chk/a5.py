import numpy as np, math, sys, time
sys.path.insert(0, "D:/Downloads/Documents/Satellite/ch3_code")
import decay_sim as ds, full_prop as fp

U = 1.66053906660e-27   # atomic mass unit, kg

print("=== 1. NRLMSIS-derived mean molecular mass vs Chen's m(h) = 27 - 0.012(h-200) ===")
# species number densities from pymsis_check_output.txt (lat0/lon0, 2026-01-01)
SPECIES = {
    200.0: dict(rho=1.9943e-10, N2=2.2107e15, O2=1.1730e14, O=3.3750e15, HE=7.7086e12,
                H=2.3001e11, AR=1.9711e12, N=2.2151e13),
    250.0: dict(rho=4.8438e-11, N2=3.5596e14, O2=1.4275e13, O=1.1597e15, HE=5.6015e12,
                H=1.6450e11, AR=1.4904e11, N=1.1293e13),
    300.0: dict(rho=1.4865e-11, N2=6.5000e13, O2=2.0451e12, O=4.3618e14, HE=4.3296e12,
                H=1.4714e11, AR=1.3272e10, N=4.9190e12),
}
MASS = dict(N2=28.0134, O2=31.9988, O=15.9994, HE=4.0026, H=1.008, AR=39.948, N=14.0067)
print(f"{'alt/km':>7} {'n_tot[1/m3]':>14} {'mmw_MSIS':>10} {'m_Chen':>8} {'ratio':>7} "
      f"{'H_MSIS(T=1065)':>15} {'H_Chen':>8} {'ratio':>7}")
for alt, d in SPECIES.items():
    ntot = sum(d[k] for k in d if k != "rho")
    mmw = d["rho"] / ntot / U
    # mass check
    msum = sum(d[k] * MASS[k] * U for k in MASS)
    m_chen = 27.0 - 0.012 * (alt - 200.0)
    T = 1065.0
    print(f"{alt:7.1f} {ntot:14.4e} {mmw:10.2f} {m_chen:8.3f} {m_chen/mmw:7.3f} "
          f"{T/mmw:15.1f} {T/m_chen:8.2f} {(T/m_chen)/(T/mmw):7.3f}   (mass check {msum:.4e} vs {d['rho']:.4e})")

print()
print("=== 2. terminal-event default: does stop_km=(175,120) kill t120? ===")
t0 = time.time()
out = fp.propagate(250.0, 0.0, a_sail=0.0, t_max_yr=25.0, f107=130.0, ap=10.0,
                   cd=ds.CD, rtol=1e-9, stop_km=(175.0, 120.0))
print("DEFAULT stop_km=(175,120):", out["t_stop_yr"], "status", out["status"], "t_end_yr", out["t_end_yr"])
print("   -> t_stop[120] is inf because the 175 km event is terminal and fires first")
