import numpy as np, math, sys
sys.path.insert(0, "D:/Downloads/Documents/Satellite/ch3_code")
import decay_sim as ds

U = 1.66053906660e-27   # atomic mass unit, kg
SPECIES = {
    200.0: dict(rho=1.9943e-10, N2=2.2107e15, O2=1.1730e14, O=3.3750e15, HE=7.7086e12,
                H=2.3001e11, AR=1.9711e12, N=2.2151e13),
    250.0: dict(rho=4.8438e-11, N2=3.5596e14, O2=1.4275e13, O=1.1597e15, HE=5.6015e12,
                H=1.6450e11, AR=1.4904e11, N=1.1293e13),
    300.0: dict(rho=1.4865e-11, N2=6.5000e13, O2=2.0451e12, O=4.3618e14, HE=4.3296e12,
                H=1.4714e11, AR=1.3272e10, N=4.9190e12),
}
MASS = dict(N2=28.0134, O2=31.9988, O=15.9994, HE=4.0026, H=1.008, AR=39.948, N=14.0067)
print("=== NRLMSIS-derived mean molecular mass vs Chen m(h)=27-0.012(h-200) ===")
print(f"{'alt/km':>7} {'n_tot[1/m3]':>13} {'mmw_MSIS':>9} {'m_Chen':>7} {'m_Chen/mmw':>10} "
      f"{'H_MSIS':>8} {'H_Chen':>7} {'Hratio':>7}")
for alt, d in SPECIES.items():
    ntot = sum(d[k] for k in d if k != "rho")
    mmw = d["rho"] / ntot / U
    m_chen = 27.0 - 0.012 * (alt - 200.0)
    T = 1065.0
    msum = sum(d[k] * MASS[k] * U for k in MASS)
    print(f"{alt:7.1f} {ntot:13.4e} {mmw:9.2f} {m_chen:7.3f} {m_chen/mmw:10.3f} "
          f"{T/mmw:8.1f} {T/m_chen:7.2f} {(T/m_chen)/(T/mmw):7.3f}  (masschk {msum:.3e} vs {d['rho']:.3e})")

print()
print("=== Chen scale height vs MSIS scale height from local density gradient ===")
# use MSIS density at 200/250/300 from pymsis_check_output
ms = {200.0: 1.9943e-10, 250.0: 4.8438e-11, 300.0: 1.4865e-11}
import math
H200 = -(250.0-200.0)/math.log(ms[250.0]/ms[200.0])
H250 = -(300.0-250.0)/math.log(ms[300.0]/ms[250.0])
print(f"  MSIS H(200-250) = {H200:.1f} km, H(250-300) = {H250:.1f} km")
print(f"  Chen H(200-250) = {1065/(27-0.012*50):.1f} / {1065/(27-0.012*100):.1f} km")
