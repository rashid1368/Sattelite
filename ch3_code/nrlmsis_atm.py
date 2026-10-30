# -*- coding: utf-8 -*-
"""nrlmsis_atm.py - NRLMSIS 2.0 atmosphere for the Chapter 3 propagator.

The baseline model of decay_sim.rho_atm is the exponential form of Chen et al. (2024).
Test T7 (density_compare.py) showed that this model overestimates the density of
NRLMSIS 2.0 by a factor of about 1.3 to 2.9 in the 200-300 km band, and by about
2.4 to 2.9 in the 350-550 km band that the ALE-1 flight data of Takeda et al. (2023)
occupy. A flight-data validation (test T8) therefore cannot use the exponential model:
the drag area would have to absorb an error of nearly a factor of three and the
comparison would no longer test the propagator.

This module provides the empirical density field as a time-dependent table:
    rho(altitude, latitude, t)
built from pymsis (NRLMSIS 2.0) with the historical daily F10.7, F10.7 81-day average
and Ap indices. The table is rebuilt every `rebuild_days` of simulated time, so a
multi-year propagation follows the real solar and geomagnetic history.

The field is pre-computed on an (altitude, latitude) grid and interpolated
bilinearly inside the right-hand side of the propagator. No call to pymsis is made
during integration.

Sign convention: the returned density is in kg/m^3 and the altitude is geodetic, in km.
"""
import numpy as np
import pymsis
from pymsis.utils import get_f107_ap

# Altitude grid (km). The drag is negligible below 100 km and above 600 km for the
# cases of interest; the exponential model is used outside the band if requested.
ALT_MIN, ALT_MAX, ALT_STEP = 100.0, 600.0, 2.0
# Latitude grid (deg). NRLMSIS density varies strongly with latitude: the equatorial
# bulge and the diurnal bulge make the density at 400 km roughly a factor of two
# higher at 400 km local midnight than at 400 km local noon.
LAT_MIN, LAT_MAX, LAT_STEP = -90.0, 90.0, 15.0

_ALTS = np.arange(ALT_MIN, ALT_MAX + 0.5 * ALT_STEP, ALT_STEP)
_LATS = np.arange(LAT_MIN, LAT_MAX + 0.5 * LAT_STEP, LAT_STEP)


def _indices(times_s, jd0):
    """Historical F10.7, F10.7a and Ap for a list of Julian dates."""
    dates = np.array([np.datetime64("1970-01-01T00:00") + np.timedelta64(int(t), "s")
                      for t in times_s], dtype="datetime64[s]")
    f107s, f107as, aps = get_f107_ap(dates)
    return (np.atleast_1d(np.asarray(f107s, dtype=float)),
            np.atleast_1d(np.asarray(f107as, dtype=float)),
            np.atleast_1d(np.asarray(aps, dtype=float)))


class NrlmsisAtm:
    """Time-dependent NRLMSIS 2.0 density field, tabulated on (altitude, latitude).

    Parameters
    ----------
    jd0        : Julian date of the simulation epoch (ds.JD_EPOCH by default)
    rebuild_days : interval of simulated time between table rebuilds
    alt_grid, lat_grid : optional override of the tabulation grid
    """

    def __init__(self, jd0, rebuild_days=30.0, alt_grid=None, lat_grid=None):
        self.jd0 = float(jd0)
        self.rebuild_days = float(rebuild_days)
        self.alts = _ALTS if alt_grid is None else np.asarray(alt_grid, dtype=float)
        self.lats = _LATS if lat_grid is None else np.asarray(lat_grid, dtype=float)
        self._t_tab = None      # simulated times of the tabulated fields
        self._rho_tab = None    # (n_tab, n_lat, n_alt)
        self._next_build = None

    # -- table construction ------------------------------------------------
    def _build(self, t0, t1):
        """Build the density tables covering simulated times [t0, t1]."""
        step = self.rebuild_days * 86400.0
        n = max(1, int(np.ceil((t1 - t0) / step)))
        times = t0 + np.arange(n + 1) * step
        jds = self.jd0 + times / 86400.0
        f107s, f107as, aps = _indices(times, self.jd0)
        rho = np.empty((len(times), len(self.lats), len(self.alts)), dtype=float)
        for k in range(len(times)):
            dates = np.array([np.datetime64("1970-01-01T00:00")
                              + np.timedelta64(int(times[k]), "s")], dtype="datetime64[s]")
            ap7 = np.atleast_2d(np.asarray(aps[k], dtype=float))
            out = pymsis.calculate(dates, self.lats, [0.0], self.alts,
                                   f107s=[f107s[k]], f107as=[f107as[k]],
                                   aps=ap7, version=2.0)
            arr = np.squeeze(np.asarray(out))          # (n_lat, n_alt, n_var)
            names = [v.name for v in pymsis.Variable]
            rho[k] = arr[:, :, names.index("MASS_DENSITY")]
        return times, rho

    def _ensure(self, t):
        """Make sure tables cover simulated time t; returns the index into the table."""
        if self._t_tab is None:
            self._t_tab, self._rho_tab = self._build(0.0, max(t, self.rebuild_days * 86400.0))
            self._next_build = self._t_tab[-1]
        while t > self._next_build:
            self._t_tab, self._rho_tab = self._build(self._next_build + 1.0,
                                                     self._next_build + 1.0 + self.rebuild_days * 86400.0)
            self._next_build = self._t_tab[-1]
        idx = int(np.clip(np.searchsorted(self._t_tab, t, side="right") - 1,
                          0, len(self._t_tab) - 1))
        return idx

    # -- queries -----------------------------------------------------------
    def density(self, alt_km, lat_deg, t_s):
        """Density (kg/m^3) at geodetic altitude (km), latitude (deg), simulated time (s).

        Altitudes outside the tabulated band return 0 (the atmosphere is cut off),
        matching the behaviour of the exponential model above 1000 km.
        """
        idx = self._ensure(float(t_s))
        h = float(alt_km)
        la = float(lat_deg)
        if h < self.alts[0] or h > self.alts[-1]:
            return 0.0
        field = self._rho_tab[idx]
        # bilinear interpolation on the (latitude, altitude) grid
        j = int(np.clip(np.searchsorted(self.alts, h) - 1, 0, len(self.alts) - 2))
        k = int(np.clip(np.searchsorted(self.lats, la) - 1, 0, len(self.lats) - 2))
        ha = (h - self.alts[j]) / (self.alts[j + 1] - self.alts[j])
        la_ = (la - self.lats[k]) / (self.lats[k + 1] - self.lats[k])
        v = (field[k, j] * (1 - ha) * (1 - la_) + field[k + 1, j] * ha * (1 - la_)
             + field[k, j + 1] * (1 - ha) * la_ + field[k + 1, j + 1] * ha * la_)
        return float(v)

    def density_profile(self, alt_km, lat_deg, t_s):
        """Density (kg/m^3) at every altitude of the tabulation grid."""
        idx = self._ensure(float(t_s))
        return self._rho_tab[idx, :, :].copy()
