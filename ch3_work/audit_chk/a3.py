import numpy as np, math, sys, inspect
sys.path.insert(0, "D:/Downloads/Documents/Satellite/ch3_code")
import decay_sim as ds, full_prop as fp

print("=== A. terminal-event default ===")
print("propagate default stop_km:", inspect.signature(fp.propagate).parameters['stop_km'].default)
for stop in [(175.0, 120.0), (120.0,)]:
    terms = [(km, km in stop) for km in (175.0, 120.0)]
    print("  stop_km=", stop, "-> (radius, terminal):", terms)

print()
print("=== B. SRP direction ===")
am = ds.composite_am(140.0, 1.0)
print("am with 140 m2 sail =", am, "m2/kg")


def srp_acc(r, rs):
    u = rs / np.linalg.norm(rs)
    proj = r @ u
    in_sh = (proj < 0.0) and (np.linalg.norm(r - proj * u) < ds.R_E)
    if in_sh:
        return np.zeros(3), True
    ds_ = rs - r
    dd = np.linalg.norm(ds_)
    P = ds.P_SR * (ds.AU / dd) ** 2
    return -P * ds.CR * am * ds_ / dd, False


rs = np.array([ds.AU, 0, 0])            # sun toward +x
r = np.array([ds.R_E + 250e3, 0, 0])    # satellite between earth and sun
a, sh = srp_acc(r, rs)
print("  sat between earth & sun: acc =", a, "-> must point +x (away from sun):", a[0] > 0)
r2 = np.array([-(ds.R_E + 250e3), 0, 0])
a2, sh2 = srp_acc(r2, rs)
print("  sat anti-sun side: in_shadow =", sh2, " acc =", a2)
r3 = np.array([-(ds.R_E + 2.0e6), 0, 0])
a3, sh3 = srp_acc(r3, rs)
print("  sat anti-sun, 2000 km off-axis: in_shadow =", sh3, " acc =", a3)

print()
print("=== C. drag sign ===")
# v_rel = v - omega x r, omega = (0,0,W_E) -> omega x r = (-W*yy, W*x, 0)
for (x, y, vx, vy) in [(ds.R_E + 250e3, 0.0, 7600.0, 0.0), (0.0, ds.R_E + 250e3, 0.0, 7600.0)]:
    r = np.array([x, y, 0.0]); v = np.array([vx, vy, 0.0])
    om = np.array([0.0, 0.0, ds.W_E])
    vrel = v - np.cross(om, r)
    print("  r=", r[:2], "v=", v[:2], "-> omega x r =", np.cross(om, r), " v_rel =", vrel)

print()
print("=== D. third body term ===")
rs_ = np.array([1.5e11, 0.0, 0.0])
r_ = np.array([ds.R_E + 250e3, 0.0, 0.0])
term = ds.MU_S * (rs_ - r_) / np.linalg.norm(rs_ - r_) ** 3 - ds.MU_S * rs_ / np.linalg.norm(rs_) ** 3
print("  differential term acc =", term, " (x>0: sun pulls satellite toward sun, yes)")

print()
print("=== E. shadow geometry: proj uses r.u not r.s ===")
# full_prop uses proj = x*sx+yy*sy+z*sz (not divided by |s|) -- check consistency
sx, sy, sz = 1.0, 0.0, 0.0
for scale in (1.49e11,):
    S = np.array([scale, 0.0, 0.0])
    x, y, z = ds.R_E + 250e3, 0.0, 0.0
    proj_fp = x * sx + y * sy + z * sz          # full_prop style, raw dot with sun vector
    un = np.linalg.norm(S)
    proj_dec = x * S[0] / un + y * S[1] / un + z * S[2] / un
    print("  full_prop proj =", proj_fp, " decay_sim proj =", proj_dec, " same sign:", np.sign(proj_fp) == np.sign(proj_dec))
