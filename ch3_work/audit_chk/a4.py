import numpy as np, math, sys
sys.path.insert(0, "D:/Downloads/Documents/Satellite/ch3_code")
import decay_sim as ds
from scipy.integrate import solve_ivp

MU, RE, WE = ds.MU_E, ds.R_E, ds.W_E
I = np.radians(ds.INC_DEG)


def acc_drag_only(t, y, am, f107, ap, cd):
    r = y[:3]; v = y[3:]
    rn = np.linalg.norm(r)
    a = -MU * r / rn ** 3
    vrel = v - np.cross(np.array([0.0, 0.0, WE]), r)
    vr = np.linalg.norm(vrel)
    rho = float(ds.rho_atm(rn - RE, f107, ap))
    a = a - 0.5 * cd * am * rho * vr * vrel
    return np.concatenate([v, a])


def state_from_a_e(a, e, inc=I, argp=0.0):
    p = a * (1 - e * e)
    r = p / (1 + e)
    v = math.sqrt(MU * (1 + e) / r)
    # perigee on +x, velocity in plane
    return np.array([r, 0.0, 0.0]), np.array([0.0, v * math.cos(inc), v * math.sin(inc)])


def elems(y):
    r = y[:3]; v = y[3:]
    rn = np.linalg.norm(r)
    en = 0.5 * v @ v - MU / rn
    a = -MU / (2 * en)
    h = np.cross(r, v)
    e = np.linalg.norm(np.cross(v, h) / MU - r / rn)
    return a, e, en


print("=== VALIDATION of Model B averaged_rates against direct drag-only Cartesian integration ===")
for (a_km, e, am, f107, ap) in [(24396.1e3, 0.7283, ds.composite_am(0.0), 130., 10.),
                                 (24396.1e3, 0.7283, ds.composite_am(140.0, 1.0), 130., 10.),
                                 (24396.1e3, 0.7283, ds.composite_am(0.0), 70., 10.),
                                 (24396.1e3, 0.20, ds.composite_am(0.0), 130., 10.)]:
    r0, v0 = state_from_a_e(a_km, e)
    y0 = np.concatenate([r0, v0])
    T = 2 * math.pi * math.sqrt(a_km ** 3 / MU)
    sol = solve_ivp(acc_drag_only, (0, T), y0, args=(am, f107, ap, ds.CD),
                     method="DOP853", rtol=1e-11, atol=[1e-3] * 3 + [1e-7] * 3, dense_output=False)
    a1, e1, _ = elems(sol.y[:, -1])
    da_direct = (a1 - a_km) / T
    de2_direct = (e1 ** 2 - e ** 2) / T
    adot, e2dot = ds.averaged_rates(a_km, e * e, am, f107, ap, ds.CD)
    print(f" a={a_km/1e3:8.1f} km e={e:.4f} am={am:.5f} f107={f107:.0f}")
    print(f"   direct  da/dt = {da_direct:.6e} m/s   de2/dt = {de2_direct:+.6e} 1/s")
    print(f"   Model B da/dt = {adot:.6e} m/s   de2/dt = {e2dot:+.6e} 1/s")
    print(f"   ratio da: {adot/da_direct:.4f}   ratio de2: {e2dot/de2_direct:.4f}")
