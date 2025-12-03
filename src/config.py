"""
Global configuration for airfoil optimization.
"""

import numpy as np
from pathlib import Path
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling, IntegerRandomSampling
from pymoo.operators.repair.rounding import RoundingRepair

#* ======================== Common Configuration ========================
# Number of threads for parallel evaluation
N_THREADS = 10

# Parametrization mode: "NACA" or "PARSEC"
AIRFOIL_PARAMETRIZATION_MODE = "PARSEC"

# Multi-objective targets (case-sensitive)
MOO_OBJECTIVES = ["window", "Cl"]

# XFOIL analysis parameters
RE = 250000  
ALPHA_SEQ = [0, 20, 0.5]  # [start, end, step] 

# NSGA2 algorithm parameters
POP_SIZE = 40
N_OFFSPRING = 40
N_GEN = 500
ELIMINATE_DUPLICATES = True

# Xvfb display for headless XFOIL
XVFB_DISPLAY = ":88"

#* ================ Parametrization specific Configuration ============

# Initialize sampling, crossover, and mutation operators based on parametrization mode
if AIRFOIL_PARAMETRIZATION_MODE == "PARSEC":
    SAMPLING = FloatRandomSampling()
    CROSSOVER = SBX(prob=0.9, eta=2)
    MUTATION = PM(prob=0.09, eta=5)

elif AIRFOIL_PARAMETRIZATION_MODE == "NACA":
    SAMPLING = IntegerRandomSampling()
    CROSSOVER = SBX(prob=0.9, eta=2, repair=RoundingRepair())
    MUTATION = PM(prob=0.33, eta=5, repair=RoundingRepair())

else:
    raise ValueError(f"Unknown parametrization mode: {AIRFOIL_PARAMETRIZATION_MODE}")

# Design space bounds based on parametrization mode
if AIRFOIL_PARAMETRIZATION_MODE == "PARSEC":
    # PARSEC parameter bounds (lower and upper for each parameter)
    PARSEC_BOUNDS = {
        'r_le': (0.02, 0.038),
        'X_up': (0.14, 0.20),
        'Z_up': (0.10, 0.15),
        'Z_XXup': (-1.0, 0.0),
        
        'X_lo': (0.14, 0.20),
        'Z_lo': (-0.15, -0.10),
        'Z_XXlo': (0.0, 1.0),
        
        'Z_te': (-0.03, -0.01),           
        'delta_Z_te': (0.0, 0.0),     # Sharp TE (fixed)
        'alpha_te': (0.0, 0.0),       # No direction change at TE (fixed)
        'beta_te': (0.0, 0.0),        # No wedge at TE (fixed)
    }

    # Extract bounds in order
    param_order = ['r_le', 'X_up', 'Z_up', 'Z_XXup', 'X_lo', 
                   'Z_lo', 'Z_XXlo', 'Z_te', 'delta_Z_te', 'alpha_te', 'beta_te']
    XL = np.array([PARSEC_BOUNDS[p][0] for p in param_order])
    XU = np.array([PARSEC_BOUNDS[p][1] for p in param_order])

elif AIRFOIL_PARAMETRIZATION_MODE == "NACA":
    # NACA 4-digit bounds
    # Digits: (max camber, dist of max camber from LE in tenths of chord, max thickness)
    XL = np.array([0, 0, 12])
    XU = np.array([5, 6, 24])

# Baseline data for normalization in multi-objective scoring
BASELINE_DATA = {'Cl': 1.2, 'Window': 4.0}
