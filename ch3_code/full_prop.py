"""full_prop.py - Model A (numerical, full dynamics), faster implementation.

Same force model as decay_sim.accel_full (2-body, J2, co-rotating drag with
exponential atmosphere, Sun and Moon third-body, cannonball SRP with cylindrical
shadow). Differences from accel_full, all for speed and documented in the thesis:
  * Sun and Moon positions are tabulated every 1800 s (linear interpolation).
    Position error of the Moon from this interpolation is < 1.5 km, i.e. < 0.01 %
    of the lunar tidal acceleration.
  * Scalar arithmetic in the right-hand side instead of small numpy arrays.
Perigee passages are located exactly with the event function r.v = 0 (not by
sampling), and the lifetime events (r = R_E + 175 km and R_E + 120 km) are terminal.
"""
import math
import time
import numpy as np
from scipy.integrate import solve_ivp
import decay_sim as ds

MU = ds.MU_E
RE = ds.R_E
J2 = ds.J2
WE = ds.W_E
MUS = ds.MU_S
MUM = ds.MU_M
AU = ds.AU
PSR = ds.P_SR
CR = ds.CR
YR_S = 365.25 * 86400.0
TAB_DT = 1800.0
GRID_OK = True


def tables(t_end, jd0=None):
    if jd0 is None:
        jd0 = ds.JD_EPOCH
    n = int(t_end / TAB_DT) + 4
    jd = jd0 + np.arange(n) * TAB_DT / 86400.0
    S = ds.sun_eci(jd).T.tolist()
    M = ds.moon_eci(jd).T.tolist()
    return S, M


def initial_state(hp_km, argp_deg=0.0, raan_deg=0.0, inc_deg=27.0, ha_km=35786.0):
    """Osculating GTO state at perigee. argp_deg = 0 reproduces decay_sim.gto_initial_state."""
    rp = RE + hp_km * 1e3
    ra = RE + ha_km * 1e3
    a = 0.5 * (rp + ra)
    e = (ra - rp) / (ra + rp)
    vp = math.sqrt(MU * (1.0 + e) / rp)
    r_pf = np.array([rp, 0.0, 0.0])
    v_pf = np.array([0.0, vp, 0.0])
    i = math.radians(inc_deg)
    O = math.radians(raan_deg)
    w = math.radians(argp_deg)

    def Rz(t):
        c, s = math.cos(t), math.sin(t)
        return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])

    def Rx(t):
        c, s = math.cos(t), math.sin(t)
        return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])

    R = Rz(O) @ Rx(i) @ Rz(w)
    return np.concatenate([R @ r_pf, R @ v_pf])


def rho_scalar(h_m, f107, ap, T_cache=None):
    h = h_m / 1000.0
    if h < 0.0 or h > 1000.0:
        return 0.0
    hc = min(max(h, 0.0), 1000.0)
    T = 900.0 + 2.5 * (f107 - 70.0) + 1.5 * ap
    H = T / (27.0 - 0.012 * (hc - 200.0))
    return 6e-10 * math.exp(-(hc - 175.0) / H)


def propagate(hp0_km, argp_deg=0.0, a_sail=0.0, sail_factor=1.0, deploy_day=0.0,
               t_max_yr=25.0, f107=130.0, ap=10.0, cd=ds.CD, third=True, srp=True,
               rtol=1e-9, atol_r=1e-3, atol_v=1e-7, stop_km=(175.0, 120.0),
               raan_deg=0.0, jd0=None,
               inc_deg=27.0, ha_km=35786.0, am_nat=None, am_sail=None,
               am_srp_nat=None, am_srp_sail=None,
               f107_series=None, ap_series=None, sample_step_s=None, atm_model=None,
               event_km=(175.0, 120.0)):
    """Model A propagation of the osculating state.

    Returns dict: peri_t_yr, peri_hp_km (every perigee passage), t_stop_yr {km: years or inf}.

    The optional keyword arguments extend the model to cases other than the baseline
    GTO stage. Their defaults reproduce the published Chapter 3 results exactly:
      inc_deg, ha_km     : orbit geometry (baseline 27 deg, apogee 35786 km)
      am_nat, am_sail    : area-to-mass overrides for DRAG (m^2/kg); default from
                           ds.composite_am
      am_srp_nat, am_srp_sail : area-to-mass overrides for SOLAR RADIATION PRESSURE.
                           The baseline uses the same value as drag (cannonball sail),
                           which is the right approximation only when the sail and the
                           body present the same area to the flow. For a drag flag whose
                           projected area differs from the body, they must be set apart.
      f107_series, ap_series : (times_s, values) arrays for a time-varying atmosphere;
                              default is the constant f107/ap of the baseline
      sample_step_s      : if given, also return the sampled state history
      atm_model          : optional nrlmsis_atm.NrlmsisAtm instance; when given, the
                           density comes from NRLMSIS 2.0 instead of the exponential
                           model of Chen et al. (2024). The default (None) is the
                           exponential model, i.e. the published Chapter 3 results.
      event_km           : radius thresholds (km) whose first inbound crossing is
                           recorded. The default reproduces the published results.
    """
    t_max = t_max_yr * YR_S
    S, M = tables(t_max, jd0)
    am_nat = ds.composite_am(0.0) if am_nat is None else am_nat
    am_sail = ds.composite_am(a_sail, sail_factor) if am_sail is None else am_sail
    am_srp_nat = am_nat if am_srp_nat is None else am_srp_nat
    am_srp_sail = am_sail if am_srp_sail is None else am_srp_sail
    td = deploy_day * 86400.0
    k_drag = 0.5 * cd
    j2c = 1.5 * J2 * MU * RE * RE

    # Time-varying solar/geomagnetic indices (optional). The baseline uses the
    # constant f107/ap, in which case no interpolation is done at all.
    if f107_series is None:
        f107_of_t = None
        ap_of_t = None
    else:
        ft, fv = (np.asarray(x, dtype=float) for x in f107_series)
        f107_of_t = lambda t: float(np.interp(t, ft, fv))
        if ap_series is None:
            ap_of_t = lambda t: float(ap)
        else:
            at, av = (np.asarray(x, dtype=float) for x in ap_series)
            ap_of_t = lambda t: float(np.interp(t, at, av))

    def rhs(t, y):
        x, yy, z, vx, vy, vz = y[0], y[1], y[2], y[3], y[4], y[5]
        r2 = x * x + yy * yy + z * z
        rn = math.sqrt(r2)
        r3 = r2 * rn
        r5 = r3 * r2
        ax = -MU * x / r3
        ay = -MU * yy / r3
        az = -MU * z / r3
        kJ = j2c / r5
        z2r2 = z * z / r2
        ax += kJ * x * (5.0 * z2r2 - 1.0)
        ay += kJ * yy * (5.0 * z2r2 - 1.0)
        az += kJ * z * (5.0 * z2r2 - 3.0)
        # drag, co-rotating atmosphere: v_rel = v - w x r, w x r = (-WE*y, WE*x, 0)
        vrx = vx + WE * yy
        vry = vy - WE * x
        vr = math.sqrt(vrx * vrx + vry * vry + vz * vz)
        am = am_nat if t < td else am_sail
        h_m = rn - RE
        if h_m >= 0.0:
            h = h_m / 1000.0
            if h <= 1000.0:
                hc = h if h > 0.0 else 0.0
                if atm_model is not None:
                    # Empirical NRLMSIS 2.0 field (latitude and time dependent).
                    lat_deg = math.degrees(math.asin(max(-1.0, min(1.0, z / rn))))
                    rho = atm_model.density(hc, lat_deg, t)
                else:
                    f107_t = f107 if f107_of_t is None else f107_of_t(t)
                    ap_t = ap if ap_of_t is None else ap_of_t(t)
                    T_atm = 900.0 + 2.5 * (f107_t - 70.0) + 1.5 * ap_t
                    Hs = T_atm / (27.0 - 0.012 * (hc - 200.0))
                    rho = 6e-10 * math.exp(-(hc - 175.0) / Hs)
                fac = -k_drag * am * rho * vr
                ax += fac * vrx
                ay += fac * vry
                az += fac * vz
        if third or srp:
            idx = t / TAB_DT
            i0 = int(idx)
            f = idx - i0
            s0 = S[i0]
            s1 = S[i0 + 1]
            sx = s0[0] + f * (s1[0] - s0[0])
            sy = s0[1] + f * (s1[1] - s0[1])
            sz = s0[2] + f * (s1[2] - s0[2])
            dx, dy, dz = sx - x, sy - yy, sz - z
            dd = math.sqrt(dx * dx + dy * dy + dz * dz)
            srn = math.sqrt(sx * sx + sy * sy + sz * sz)
            if third:
                c1 = MUS / (dd ** 3)
                c2 = MUS / (srn ** 3)
                ax += c1 * dx - c2 * sx
                ay += c1 * dy - c2 * sy
                az += c1 * dz - c2 * sz
                m0 = M[i0]
                m1 = M[i0 + 1]
                mx = m0[0] + f * (m1[0] - m0[0])
                my = m0[1] + f * (m1[1] - m0[1])
                mz = m0[2] + f * (m1[2] - m0[2])
                ex, ey, ez = mx - x, my - yy, mz - z
                de = math.sqrt(ex * ex + ey * ey + ez * ez)
                mrn = math.sqrt(mx * mx + my * my + mz * mz)
                c3 = MUM / (de ** 3)
                c4 = MUM / (mrn ** 3)
                ax += c3 * ex - c4 * mx
                ay += c3 * ey - c4 * my
                az += c3 * ez - c4 * mz
            if srp:
                # cylindrical Earth shadow, Sun direction from the Sun vector
                proj = x * sx + yy * sy + z * sz
                if proj < 0.0:
                    # perpendicular distance to the Sun-Earth line
                    un = srn
                    ux, uy, uz = sx / un, sy / un, sz / un
                    px = x - proj / (un * un) * sx
                    py = yy - proj / (un * un) * sy
                    pz = z - proj / (un * un) * sz
                    perp = math.sqrt(px * px + py * py + pz * pz)
                    in_sh = perp < RE
                else:
                    in_sh = False
                if not in_sh:
                    P = PSR * (AU / dd) ** 2
                    am_srp = am_srp_nat if t < td else am_srp_sail
                    f_srp = -P * CR * am_srp / dd
                    ax += f_srp * dx
                    ay += f_srp * dy
                    az += f_srp * dz
        return np.array([vx, vy, vz, ax, ay, az])

    def ev_peri(t, y):
        return y[0] * y[3] + y[1] * y[4] + y[2] * y[5]
    ev_peri.direction = 1.0

    evs = [ev_peri]
    # Radius events. The baseline always records the inbound crossing of 175 km and
    # 120 km; a caller may add its own thresholds (e.g. 400 km for the ALE-1 case).
    for km in event_km:
        rs_ = RE + km * 1e3

        def ev(t, y, rs_=rs_):
            return math.sqrt(y[0] * y[0] + y[1] * y[1] + y[2] * y[2]) - rs_
        ev.terminal = km in stop_km  # integration stops at the first crossing of these radii
        ev.direction = -1.0
        evs.append(ev)

    y0 = initial_state(hp0_km, argp_deg, raan_deg, inc_deg=inc_deg, ha_km=ha_km)
    t_eval = None if sample_step_s is None else np.arange(0.0, t_max + 1e-6, sample_step_s)
    sol = solve_ivp(rhs, (0.0, t_max), y0, method="DOP853", rtol=rtol,
                    atol=np.array([atol_r] * 3 + [atol_v] * 3), events=evs, t_eval=t_eval)
    pt = sol.t_events[0]
    pr = np.linalg.norm(sol.y_events[0][:, :3], axis=1) if len(pt) else np.array([])
    keep = pt > 1.0
    peri_t_yr = pt[keep] / YR_S
    peri_hp = (pr[keep] - RE) / 1e3
    t_stop = {}
    for k, km in enumerate(event_km):
        tk = sol.t_events[k + 1]
        t_stop[km] = float(tk[0] / YR_S) if len(tk) else float("inf")
    out = dict(peri_t_yr=peri_t_yr, peri_hp_km=peri_hp, t_stop_yr=t_stop, status=sol.status,
               t_end_yr=float(sol.t[-1] / YR_S))
    if sample_step_s is not None:
        rn = np.linalg.norm(sol.y[:3, :], axis=0)
        out["t_s"] = sol.t
        out["r_km"] = rn / 1e3
        out["a_km"] = np.array([ds.elements_from_state(sol.y[:3, k], sol.y[3:, k])[0] / 1e3
                                for k in range(sol.t.size)])
        out["e"] = np.array([ds.elements_from_state(sol.y[:3, k], sol.y[3:, k])[1]
                             for k in range(sol.t.size)])
        out["hp_km"] = (out["a_km"] * (1.0 - out["e"]) - RE / 1e3)
    return out


if __name__ == "__main__":
    t0 = time.time()
    out = propagate(250.0, 0.0, t_max_yr=1.0)
    hp = out["peri_hp_km"]
    print("ω=0 natural, 1 yr: passages", hp.size, "first", np.round(hp[:4], 3), "min %.2f max %.2f last %.2f" % (hp.min(), hp.max(), hp[-1]), "stops", out["t_stop_yr"], round(time.time() - t0, 1), "s")
