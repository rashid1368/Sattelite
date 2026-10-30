# Chapter 3 reference code (Python)

Python is the reference implementation of the thesis simulations. The MATLAB file is not used for any reported result.

Files
- decay_sim.py: constants, exponential atmosphere (Chen et al., 2024), low-precision Sun and Moon ephemerides, initial state, Model B (orbit-averaged, drag only).
- full_prop.py: Model A, full numerical propagation (J2, co-rotating drag, Sun and Moon third-body, cannonball SRP with cylindrical shadow). Reference model of the thesis. Requires decay_sim.py in the same folder.
- reproduce_base.py: reproduces three baseline results of Chapter 3 (cases tiny, natural, sail140).
- verify_basic.py: verification tests T1 to T3 of Section 3-9-1 (two-body energy and angular momentum, J2 nodal rate against the analytic rate, perigee passage timing). Writes logs/verify_basic.json.
- grid_ch3.py: full-model sail-area sweep (Model A) for the geometries of the Latin hypercube sample whose natural lifetime exceeds 25 years. Requires decay_sim.py and full_prop.py.
- pymsis_check.py: checks the NRLMSIS 2.0 interface (pymsis) for the density comparison. Not needed for the reproduction.
- baseline_reproduction_sandbox.txt: the reproduction output used in the thesis.
- baseline_reproduction_pc_windows.txt: the reproduction and verification output on the Windows PC (environment B).
- logs/verify_basic.json: output of verify_basic.py.

Geometry indices
Geometry indices in grid_ch3.py are 0-based. Index k is row k+1 of Table 3-4, which lists the 16 (omega, Omega) points of the Latin hypercube sample (seed 42).

Versions used for all reported results
Environment A (cloud Linux): Python 3.13.17, numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.2 (figures only).
Environment B (Windows PC, 8 cores): Python 3.13.14, numpy 2.5.3, scipy 1.18.1.
Optional: pymsis 0.13.0, only for pymsis_check.py and the NRLMSIS 2.0 density comparison.

Install (Windows, PowerShell or CMD)
    python3 -m pip install "numpy==2.5.3" "scipy==1.18.1" "matplotlib==3.11.2"
    python3 -m pip install "pymsis==0.13.0"

Run (from the folder that contains the .py files)
    python3 verify_basic.py                  tests T1 to T3 (well under 1 s)
    python3 reproduce_base.py tiny           expected t120 = 0.2935 yr  (about 5 s)
    python3 reproduce_base.py natural        expected t120 = 7.50 yr    (about 1.5 min in environment A, about 3 min in B)
    python3 reproduce_base.py sail140        expected t120 = 11.90 yr   (about 2 min in environment A, about 4.5 min in B)
    python3 grid_ch3.py 1,6,8,10,13,15       one JSON line per run (geometry index, sail area, t120)

reproduce_base.py prints one JSON line with t120, the difference from the reported value, the lowest perigee and the versions used. grid_ch3.py prints one JSON line per run; t120_yr is null when the 120 km threshold is not reached within 25 years.
