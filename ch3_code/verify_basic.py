# -*- coding: utf-8 -*-
"""Basic verification tests for the Chapter 3 propagator (run before any reported result).

T1  two-body motion: relative drift of specific energy and angular momentum over 10 orbits (rtol 1e-12).
T2  J2 only: numerically measured secular rate of the node (RAAN) over 10 orbits, compared with the
    analytic secular rate  dOmega/dt = -1.5 n J2 (R/p)^2 cos i  (mean elements of the initial orbit).
T3  perigee passage times (event detection, production tolerances) versus k*T, two-body motion.
Output: one JSON line, also written to logs/verify_basic.json.
"""
import json
import os
import time

import numpy as np
from scipy.integrate import solve_ivp

import full_prop as fp

MU = 3.986004418e14          # m^3 s^-2
RE = 6378.137e3              # m
J2 = 1.08262668e-3
INC = 27.0                   # deg


def acc_2body(r):
    rn = np.linalg.norm(r)
    return -MU * r / rn ** 3


def acc_j2(r):
    rn = np.linalg.norm(r)
    z2 = (r[2] / rn) ** 2
    k = 1.5 * J2 * MU * RE ** 2 / rn ** 5
    return k * np.array([r[0] * (5.0 * z2 - 1.0), r[1] * (5.0 * z2 - 1.0), r[2] * (5.0 * z2 - 3.0)])


def make_rhs(with_j2):
    def rhs(t, y):
        r = y[:3]
        a = acc_2body(r)
        if with_j2:
            a = a + acc_j2(r)
        return np.concatenate([y[3:], a])
    return rhs


def elements(y):
    r, v = y[:3], y[3:]
    rn = np.linalg.norm(r)
    energy = 0.5 * (v @ v) - MU / rn
    a = -MU / (2.0 * energy)
    h = np.cross(r, v)
    hn = np.linalg.norm(h)
    e = np.sqrt(max(1.0 + 2.0 * energy * hn ** 2 / MU ** 2, 0.0))
    return energy, hn, a, e


def t1_two_body(y0):
    E0, h0, a0, e0 = elements(y0)
    T = 2.0 * np.pi * np.sqrt(a0 ** 3 / MU)
    sol = solve_ivp(make_rhs(False), (0.0, 10.0 * T), y0, method="DOP853", rtol=1e-12, atol=1e-6)
    E1, h1, _, _ = elements(sol.y[:, -1])
    return dict(orbits=10, period_s=round(T, 2), max_rel_drift_energy=float(abs(E1 - E0) / abs(E0)),
                rel_drift_angular_momentum=float(abs(h1 - h0) / h0), status=int(sol.status))


def t2_j2_node_rate(y0):
    E0, h0, a0, e0 = elements(y0)
    n = np.sqrt(MU / a0 ** 3)
    p = a0 * (1.0 - e0 ** 2)
    rate_an = -1.5 * n * J2 * (RE / p) ** 2 * np.cos(np.radians(INC))

    def node_event(t, y):
        return y[2]
    node_event.direction = 1.0          # ascending node: z crosses zero upward
    T = 2.0 * np.pi * np.sqrt(a0 ** 3 / MU)
    sol = solve_ivp(make_rhs(True), (0.0, 10.0 * T + 0.5 * T), y0, method="DOP853", rtol=1e-12, atol=1e-6,
                    events=node_event)
    ys = sol.y_events[0]
    ts = sol.t_events[0]
    raan = np.unwrap(np.arctan2(ys[:, 1], ys[:, 0]))
    slope = np.polyfit(ts, raan, 1)[0]
    return dict(nodes=int(len(ts)), rate_numeric_deg_per_day=float(np.degrees(slope) * 86400.0),
                rate_analytic_deg_per_day=float(np.degrees(rate_an) * 86400.0),
                rel_diff_percent=float(100.0 * (slope - rate_an) / rate_an), status=int(sol.status))


def t3_perigee_timing(y0):
    """Perigee passages from event detection (r.v crosses zero upward) versus analytic k*T (two-body, production tolerances)."""
    E0, h0, a0, e0 = elements(y0)
    T = 2.0 * np.pi * np.sqrt(a0 ** 3 / MU)

    def perigee_event(t, y):
        return float(y[:3] @ y[3:])
    perigee_event.direction = 1.0       # r.v changes sign from negative to positive at perigee
    atol = np.array([1e-3] * 3 + [1e-7] * 3)
    sol = solve_ivp(make_rhs(False), (0.0, 10.5 * T), y0, method="DOP853", rtol=1e-9, atol=atol,
                    events=perigee_event)
    ts = np.asarray(sol.t_events[0])
    ts = ts[ts > 1.0]                    # discard the start point (r.v = 0 at t = 0)
    k = np.arange(1, len(ts) + 1)
    err = np.abs(ts - k * T)
    return dict(passages=int(len(ts)), period_s=round(T, 2),
                initial_r_dot_v_m2_s=float(y0[:3] @ y0[3:]),
                max_abs_timing_error_s=float(err.max()) if len(ts) else None,
                max_timing_error_rel_period=float(err.max() / T) if len(ts) else None,
                status=int(sol.status))


def main():
    t0 = time.time()
    # Initial state: perigee 250 km, apogee altitude 35786 km, inclination 27 deg, argument of perigee 0, node 0.
    y0 = fp.initial_state(250.0, 0.0, 0.0)
    rec = dict(test="verify_basic", perigee_km=250.0, inclination_deg=27.0)
    rec["T1_two_body"] = t1_two_body(y0)
    rec["T2_j2_node"] = t2_j2_node_rate(y0)
    rec["T3_perigee_timing"] = t3_perigee_timing(y0)
    rec["wall_s"] = round(time.time() - t0, 1)
    line = json.dumps(rec, ensure_ascii=False)
    print(line, flush=True)
    os.makedirs("logs", exist_ok=True)
    with open(os.path.join("logs", "verify_basic.json"), "w", encoding="utf-8") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    main()
