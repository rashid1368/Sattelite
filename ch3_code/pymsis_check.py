# -*- coding: utf-8 -*-
"""Check the pymsis interface (NRLMSIS 2.0) before the density comparison.

Usage: python3 pymsis_check.py
Prints the pymsis version, the signature of calculate(), the available variable names and
the output at 200, 250 and 300 km for 2026-01-01 with F10.7 = 130 and Ap = 10.
Errors are printed in full on purpose; paste the whole output back.
"""
import importlib.metadata as md
import inspect
import traceback

import numpy as np
import pymsis

print("pymsis", md.version("pymsis"))
print(inspect.signature(pymsis.calculate))
print("variables:", [v.name for v in pymsis.Variable] if hasattr(pymsis, "Variable") else "no Variable enum")

dates = np.array(["2026-01-01T00:00"], dtype="datetime64[s]")
for alt in (200.0, 250.0, 300.0):
    try:
        out = pymsis.calculate(dates, [0.0], [0.0], [alt], f107s=[130.0], f107as=[130.0],
                               aps=[10.0], version=2.0)
        print("alt", alt, "shape", np.shape(out))
        print("values", np.array2string(np.ravel(np.asarray(out)), precision=4, max_line_width=200))
    except Exception:
        traceback.print_exc()
        break
