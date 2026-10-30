# -*- coding: utf-8 -*-
"""
decay_sim.py
Passive disposal of a GTO upper stage with a CubeSat-deployed drag sail.

Two propagators (Python is the reference implementation):

  Model A  Numerical propagation of the Cartesian state (Earth-centred inertial).
           Accelerations: 2-body + J2 + atmospheric drag (atmosphere co-rotates
           with the Earth) + Sun and Moon third-body + cannonball solar radiation
           pressure with a cylindrical Earth shadow.

  Model B  Orbit-averaged drag model. Gauss-type rates for the semi-major axis a
           and the semi-latus rectum p (hence e) are averaged over one orbit using
           the eccentric anomaly E, including atmospheric co-rotation. Integrated
           with RK4 and an adaptive step. Used for lifetime studies over decades.

Atmosphere (both models), exponential form of Chen et al. (2024), Aerospace
11(4):315, Eqs. (3)-(5):
    rho(h) = 6e-10 * exp(-(h - 175) / H),   H = T / m,
    T = 900 + 2.5 (F10.7 - 70) + 1.5 Ap,    m = 27 - 0.012 (h - 200),
with h in km and rho in kg/m^3. Applied for 0 <= h <= 1000 km.

Units: SI (m, s, kg) internally. Altitudes in reports are in km.
"""
import numpy as np
from scipy.integrate import solve_ivp

# ----------------------------------------------------------------------------
# Constants (SI)
# ----------------------------------------------------------------------------
MU_E = 3.986004418e14       # m^3 s^-2, Earth gravitational parameter
R_E = 6378137.0             # m, Earth equatorial radius (WGS-84)
J2 = 1.08262668e-3          # Earth oblateness coefficient
W_E = 7.2921159e-5          # rad s^-1, Earth rotation rate
MU_S = 1.32712440018e20     # m^3 s^-2, Sun
MU_M = 4.9028695e12         # m^3 s^-2, Moon
AU = 1.495978707e11         # m
P_SR = 4.56e-6              # N m^-2, solar radiation pressure at 1 AU
JD_J2000 = 2451545.0
JD_EPOCH = 2461041.5        # 2026-01-01 00:00 UT (Julian date)
OBLIQ_DEG = 23.439          # mean obliquity of the ecliptic (deg)

# ----------------------------------------------------------------------------
# Mission and spacecraft parameters (baseline; see thesis Chapter 3)
# ----------------------------------------------------------------------------
HA_KM = 35786.0             # GTO apogee altitude (km)
INC_DEG = 27.0              # GTO inclination (deg)
COS_I = np.cos(np.radians(INC_DEG))
M_STAGE = 2000.0            # kg, separated upper stage
D_STAGE = 2.6               # m, stage diameter
L_STAGE = 5.0               # m, stage length
# Tumbling-averaged cross-section of a convex body = total surface / 4 (Cauchy)
A_STAGE = (np.pi * D_STAGE * L_STAGE + np.pi * D_STAGE ** 2 / 2.0) / 4.0   # m^2
M_MOD = 12.0                # kg, 6U-12U CubeSat-class module
SIGMA_SAIL = 0.1            # kg m^-2, areal density of the membrane sail (assumed)
CD = 2.2                    # drag coefficient (assumed)
CR = 1.3                    # SRP coefficient (assumed)


def composite_am(a_sail, sail_factor=1.0):
    """Area-to-mass ratio (m^2/kg) of stage + module + sail.

    sail_factor = 1.0 : sail presents its full area to the flow (ideal attitude)
    sail_factor = 0.5 : sail presents half its area on average (tumbling)
    """
    area = A_STAGE + sail_factor * a_sail
    mass = M_STAGE + M_MOD + SIGMA_SAIL * a_sail
    return area / mass


# ----------------------------------------------------------------------------
# Atmosphere
# ----------------------------------------------------------------------------
def rho_atm(h_m, f107=130.0, ap=10.0):
    """Exponential density (kg/m^3), Chen et al. (2024) Eqs. (3)-(5). h_m in metres."""
    h = np.asarray(h_m, dtype=float) / 1000.0                       # km
    h_c = np.clip(h, 0.0, 1000.0)
    T = 900.0 + 2.5 * (f107 - 70.0) + 1.5 * ap                      # K
    H = T / (27.0 - 0.012 * (h_c - 200.0))                          # km
    rho = 6e-10 * np.exp(-(h_c - 175.0) / H)
    return np.where((h < 0.0) | (h > 1000.0), 0.0, rho)


# ----------------------------------------------------------------------------
# Low-precision ephemerides (Sun, Moon) in the equatorial inertial frame
# ----------------------------------------------------------------------------
def sun_eci(jd):
    """Geocentric Sun position (m), low-precision series."""
    n = jd - JD_J2000
    L = np.radians((280.460 + 0.9856474 * n) % 360.0)
    g = np.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = L + np.radians(1.915 * np.sin(g) + 0.020 * np.sin(2.0 * g))
    R = 1.00014 - 0.01671 * np.cos(g) - 0.00014 * np.cos(2.0 * g)   # AU
    eps = np.radians(OBLIQ_DEG - 0.0000004 * n)
    return R * AU * np.array([np.cos(lam),
                              np.sin(lam) * np.cos(eps),
                              np.sin(lam) * np.sin(eps)])


def moon_eci(jd):
    """Geocentric Moon position (m), truncated lunar series (Meeus-type)."""
    T = (jd - JD_J2000) / 36525.0
    d = np.radians
    lam = (218.32 + 481267.8813 * T
           + 6.29 * np.sin(d(134.9 + 477198.85 * T))
           - 1.27 * np.sin(d(259.2 - 413335.38 * T))
           + 0.66 * np.sin(d(235.7 + 890534.23 * T))
           + 0.21 * np.sin(d(269.9 + 954397.70 * T))
           - 0.19 * np.sin(d(357.5 + 35999.05 * T))
           - 0.11 * np.sin(d(186.5 + 966404.05 * T)))
    beta = (5.13 * np.sin(d(93.3 + 483202.03 * T))
            + 0.28 * np.sin(d(228.2 + 960400.87 * T))
            - 0.28 * np.sin(d(318.3 + 6003.18 * T))
            - 0.17 * np.sin(d(217.6 - 407332.20 * T)))
    par = (0.9508 + 0.0518 * np.cos(d(134.9 + 477198.85 * T))
           + 0.0095 * np.cos(d(259.2 - 413335.38 * T))
           + 0.0078 * np.cos(d(235.7 + 890534.23 * T))
           + 0.0028 * np.cos(d(269.9 + 954397.70 * T)))
    dist = R_E / np.sin(d(par))
    lr, br = d(lam % 360.0), d(beta)
    x_e = dist * np.cos(br) * np.cos(lr)
    y_e = dist * np.cos(br) * np.sin(lr)
    z_e = dist * np.sin(br)
    eps = d(OBLIQ_DEG - 0.0000004 * (jd - JD_J2000))
    return np.array([x_e,
                     y_e * np.cos(eps) - z_e * np.sin(eps),
                     y_e * np.sin(eps) + z_e * np.cos(eps)])


# ----------------------------------------------------------------------------
# Initial conditions
# ----------------------------------------------------------------------------
def gto_initial_state(hp_km, ha_km=HA_KM, inc_deg=INC_DEG):
    """Osculating state at perigee: perigee on +x axis, omega = Omega = 0."""
    rp = R_E + hp_km * 1e3
    ra = R_E + ha_km * 1e3
    a0 = 0.5 * (rp + ra)
    e0 = (ra - rp) / (ra + rp)
    vp = np.sqrt(MU_E * (2.0 / rp - 1.0 / a0))
    i = np.radians(inc_deg)
    r0 = np.array([rp, 0.0, 0.0])
    v0 = np.array([0.0, vp * np.cos(i), vp * np.sin(i)])
    return a0, e0, np.concatenate([r0, v0])


def elements_from_state(r, v):
    """Osculating semi-major axis (m) and eccentricity from a Cartesian state."""
    rn = np.linalg.norm(r)
    energy = 0.5 * (v @ v) - MU_E / rn
    a = -MU_E / (2.0 * energy)
    h = np.cross(r, v)
    e_vec = np.cross(v, h) / MU_E - r / rn
    return a, np.linalg.norm(e_vec)


def _j2_only_acc(r):
    rn = np.linalg.norm(r)
    k = 1.5 * J2 * MU_E * R_E ** 2 / rn ** 5
    z2r2 = r[2] * r[2] / (rn * rn)
    return -MU_E * r / rn ** 3 + k * np.array([r[0] * (5.0 * z2r2 - 1.0),
                                                r[1] * (5.0 * z2r2 - 1.0),
                                                r[2] * (5.0 * z2r2 - 3.0)])


def mean_gto_elements(hp_km, ha_km=HA_KM, inc_deg=INC_DEG, n_samp=2000):
    """Orbit-averaged (a, e) of the initial osculating state under 2-body + J2.

    Short-period J2 terms are large at a 250 km perigee (tens of km in a), so the
    mean elements, not the osculating ones, initialise the averaged model."""
    a0, e0, y0 = gto_initial_state(hp_km, ha_km, inc_deg)
    T = 2.0 * np.pi * np.sqrt(a0 ** 3 / MU_E)
    sol = solve_ivp(lambda t, y: np.concatenate([y[3:], _j2_only_acc(y[:3])]),
                    (0.0, T), y0, method="DOP853", rtol=1e-12, atol=1e-6,
                    t_eval=np.linspace(0.0, T, n_samp, endpoint=False))
    a_arr = np.empty(sol.t.size)
    e_arr = np.empty(sol.t.size)
    for k in range(sol.t.size):
        a_arr[k], e_arr[k] = elements_from_state(sol.y[:3, k], sol.y[3:, k])
    return a_arr.mean(), e_arr.mean()


# ----------------------------------------------------------------------------
# Model A: full numerical propagation
# ----------------------------------------------------------------------------
def accel_full(t, y, p):
    """Acceleration vector for state y = [x, y, z, vx, vy, vz] (SI). t in seconds from epoch."""
    r = y[:3]
    v = y[3:]
    rn = np.sqrt(r @ r)
    acc = -MU_E * r / rn ** 3

    # J2 zonal harmonic
    k = 1.5 * J2 * MU_E * R_E ** 2 / rn ** 5
    z2r2 = r[2] * r[2] / (rn * rn)
    acc = acc + k * np.array([r[0] * (5.0 * z2r2 - 1.0),
                              r[1] * (5.0 * z2r2 - 1.0),
                              r[2] * (5.0 * z2r2 - 3.0)])

    # Atmospheric drag with a co-rotating atmosphere
    vrel = v - np.cross(np.array([0.0, 0.0, W_E]), r)
    vr = np.sqrt(vrel @ vrel)
    am = p["am"](t)
    rho = float(rho_atm(rn - R_E, p["f107"], p["ap"]))
    acc = acc - 0.5 * p["cd"] * am * rho * vr * vrel

    jd = JD_EPOCH + t / 86400.0
    if p["third_body"] or p["srp"]:
        rs = sun_eci(jd)
    if p["third_body"]:
        rm = moon_eci(jd)
        ds_ = rs - r
        dm_ = rm - r
        acc = acc + MU_S * (ds_ / np.linalg.norm(ds_) ** 3 - rs / np.linalg.norm(rs) ** 3)
        acc = acc + MU_M * (dm_ / np.linalg.norm(dm_) ** 3 - rm / np.linalg.norm(rm) ** 3)

    if p["srp"]:
        u = rs / np.linalg.norm(rs)
        proj = r @ u
        in_shadow = (proj < 0.0) and (np.linalg.norm(r - proj * u) < R_E)
        if not in_shadow:
            ds_ = rs - r
            dd = np.linalg.norm(ds_)
            P = P_SR * (AU / dd) ** 2
            acc = acc - P * CR * am * ds_ / dd

    return np.concatenate([v, acc])


def run_full(hp_km, am_fn, days, f107=130.0, ap=10.0, cd=CD, third_body=True, srp=True,
             out_step_s=600.0, rtol=1e-9):
    """Model A. Returns dict with t_days, osculating hp_km, a_km, e."""
    _, _, y0 = gto_initial_state(hp_km)
    p = dict(am=am_fn, f107=f107, ap=ap, cd=cd, third_body=third_body, srp=srp)
    t_end = days * 86400.0
    t_eval = np.arange(0.0, t_end + 1e-6, out_step_s)
    atol = np.array([1e-3, 1e-3, 1e-3, 1e-7, 1e-7, 1e-7])
    sol = solve_ivp(lambda t, y: accel_full(t, y, p), (0.0, t_end), y0,
                    method="DOP853", rtol=rtol, atol=atol, t_eval=t_eval)
    a_arr = np.empty(sol.t.size)
    e_arr = np.empty(sol.t.size)
    for k in range(sol.t.size):
        a_arr[k], e_arr[k] = elements_from_state(sol.y[:3, k], sol.y[3:, k])
    hp = (a_arr * (1.0 - e_arr) - R_E) / 1e3
    return dict(t_days=sol.t / 86400.0, hp_km=hp, a_km=a_arr / 1e3, e=e_arr,
                status=sol.status, message=sol.message)


# ----------------------------------------------------------------------------
# Model B: orbit-averaged drag with co-rotation
# ----------------------------------------------------------------------------
N_QUAD = 4096
_THETA = np.linspace(0.0, 2.0 * np.pi, N_QUAD, endpoint=False)   # eccentric anomaly grid


def averaged_rates(a, e2, am, f107=130.0, ap=10.0, cd=CD, n_quad=None):
    """Orbit-averaged da/dt (m/s) and d(e^2)/dt (1/s) for atmospheric drag.

    With a_D = -D v_rel, D = 0.5 Cd (A/m) rho |v_rel|, and v_rel = v - w x r:
        v . v_rel = v^2 - w h cos i                 (energy rate)
        h_vec-rate: dh/dt = -D (h - w r^2 cos i)    (angular momentum)
        da/dt   = -(2 a^2 / mu) D (v^2 - w h cos i)
        dp/dt   = -2 D p (1 - w r^2 cos i / h),     p = a (1 - e^2)
        d(e^2)/dt = -(dp/dt)/a + p (da/dt)/a^2
        |v_rel|^2 = v^2 - 2 w h cos i + w^2 r^2 (1 - sin^2 i / 2)
    Orbit average: <X> = (1/2 pi) * integral_0^{2 pi} X (1 - e cos E) dE.
    """
    if n_quad is None:
        theta = _THETA
    else:
        theta = np.linspace(0.0, 2.0 * np.pi, n_quad, endpoint=False)
    cose = np.cos(theta)
    e = np.sqrt(max(e2, 0.0))
    p = a * (1.0 - e2)
    w = 1.0 - e * cose
    r = a * w
    v2 = MU_E * (2.0 / r - 1.0 / a)
    h = np.sqrt(MU_E * p)
    vrel2 = v2 - 2.0 * W_E * h * COS_I + (W_E ** 2) * r * r * (1.0 - 0.5 * (1.0 - COS_I ** 2))
    rho = rho_atm(r - R_E, f107, ap)
    D = 0.5 * cd * am * rho * np.sqrt(vrel2)
    adot = -np.mean((2.0 * a * a / MU_E) * D * (v2 - W_E * h * COS_I) * w)
    pdot = -np.mean(2.0 * D * p * (1.0 - W_E * r * r * COS_I / h) * w)
    e2dot = -pdot / a + p * adot / (a * a)
    return adot, e2dot


def propagate_averaged(a0, e0, am_fn, stops_km=(175.0, 120.0), f107=130.0, ap=10.0, cd=CD,
                       t_max_days=400.0 * 365.25, dt_max_days=2.0, dh_km=0.5, n_quad=None,
                       record=False, record_every_days=1.0):
    """Integrate Model B (RK4, adaptive step). Detects mean-perigee crossings of stops_km.

    Returns dict with t_cross_days (dict, np.inf if not reached) and, if record, history.
    """
    a = a0
    e2 = e0 * e0
    t = 0.0
    t_max = t_max_days * 86400.0
    dt_cap = dt_max_days * 86400.0
    crossings = {s: np.inf for s in stops_km}
    pending = sorted(stops_km, reverse=True)
    hist_t, hist_hp, hist_a, hist_e = [], [], [], []
    next_rec = 0.0

    def hp_of(a_, e2_):
        return (a_ * (1.0 - np.sqrt(max(e2_, 0.0))) - R_E) / 1e3

    while t < t_max and pending:
        hp_old = hp_of(a, e2)
        if record and t >= next_rec:
            hist_t.append(t / 86400.0)
            hist_hp.append(hp_old)
            hist_a.append(a / 1e3)
            hist_e.append(np.sqrt(max(e2, 0.0)))
            next_rec = t + record_every_days * 86400.0
        k1a, k1e = averaged_rates(a, e2, am_fn(t), f107, ap, cd, n_quad)
        e = np.sqrt(max(e2, 1e-12))
        hpdot = abs(k1a * (1.0 - e) - a * k1e / (2.0 * e)) / 1e3        # km/s
        dt = min(dt_cap, dh_km / max(hpdot, 1e-15))
        h2 = 0.5 * dt
        k2a, k2e = averaged_rates(a + h2 * k1a, e2 + h2 * k1e, am_fn(t + h2), f107, ap, cd, n_quad)
        k3a, k3e = averaged_rates(a + h2 * k2a, e2 + h2 * k2e, am_fn(t + h2), f107, ap, cd, n_quad)
        k4a, k4e = averaged_rates(a + dt * k3a, e2 + dt * k3e, am_fn(t + dt), f107, ap, cd, n_quad)
        a_new = a + dt / 6.0 * (k1a + 2.0 * k2a + 2.0 * k3a + k4a)
        e2_new = e2 + dt / 6.0 * (k1e + 2.0 * k2e + 2.0 * k3e + k4e)
        hp_new = hp_of(a_new, e2_new)
        while pending and hp_new <= pending[0]:
            s = pending.pop(0)
            frac = (hp_old - s) / (hp_old - hp_new)
            crossings[s] = (t + frac * dt) / 86400.0
        a, e2, t = a_new, e2_new, t + dt
        if e2 <= 0.0:
            break
    out = dict(t_cross_days=crossings)
    if record:
        out.update(t_days=np.array(hist_t), hp_km=np.array(hist_hp),
                   a_km=np.array(hist_a), e=np.array(hist_e))
    return out


def lifetime_days(hp0_km, a_sail=0.0, sail_factor=1.0, f107=130.0, ap=10.0, cd=CD,
                  deploy_day=0.0, stops_km=(175.0, 120.0), n_quad=2048, dt_max_days=2.0,
                  mean0=None, t_max_days=400.0 * 365.25):
    """Days from separation to mean-perigee crossing of each stop altitude (Model B).

    mean0 : optional (a0, e0) mean elements; if None they are computed from the
            initial osculating state (cached)."""
    if mean0 is None:
        a0, e0, _ = gto_initial_state(hp0_km)     # osculating state at perigee (injection)
    else:
        a0, e0 = mean0
    am_nat = composite_am(0.0)
    am_sail = composite_am(a_sail, sail_factor)
    td = deploy_day * 86400.0

    def am_fn(t):
        return am_nat if t < td else am_sail

    res = propagate_averaged(a0, e0, am_fn, stops_km=stops_km, f107=f107, ap=ap, cd=cd,
                             t_max_days=t_max_days, n_quad=n_quad, dt_max_days=dt_max_days)
    return res["t_cross_days"]


_MEAN_CACHE = {}


def _mean0_cache(hp_km):
    key = round(float(hp_km), 6)
    if key not in _MEAN_CACHE:
        _MEAN_CACHE[key] = mean_gto_elements(hp_km)
    return _MEAN_CACHE[key]


def required_sail_area(hp0_km, target_days, sail_factor=1.0, f107=130.0, ap=10.0, cd=CD,
                       stop_km=175.0, a_hi=400.0, deploy_day=0.0):
    """Smallest sail area (m^2) that brings the mean perigee to stop_km within target_days.
    Bisection on A_sail. Returns 0.0 if no sail is needed, np.nan if a_hi is insufficient."""
    horizon = 1.2 * target_days

    def ok(a_sail):
        t = lifetime_days(hp0_km, a_sail, sail_factor, f107, ap, cd, deploy_day, (stop_km,),
                          t_max_days=horizon)[stop_km]
        return t <= target_days
    if ok(0.0):
        return 0.0
    if not ok(a_hi):
        return np.nan
    lo, hi = 0.0, a_hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if ok(mid):
            hi = mid
        else:
            lo = mid
        if hi - lo < 0.01:
            break
    return hi


if __name__ == "__main__":
    print("A_STAGE [m^2] =", round(A_STAGE, 3), " natural A/m =", round(composite_am(0.0), 6))
