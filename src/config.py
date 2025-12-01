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

# Set log path
LOG_FILE_PATH = Path("data/optimization_datalog.csv")

# Number of threads for parallel evaluation
N_THREADS = 6

# Parametrization mode: "NACA" or "PARSEC"
AIRFOIL_PARAMETRIZATION_MODE = "NACA"

# Multi-objective targets (case-sensitive)
MOO_OBJECTIVES = ["window", "Cl"]

# XFOIL analysis parameters
RE = 250000  
ALPHA_SEQ = [0, 20, 0.5]  # [start, end, step] 

# NSGA2 algorithm parameters
POP_SIZE = 40
N_OFFSPRING = 40
N_GEN = 5
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
    # PARSEC parameter central definitions
    PARAM_CENTRAL_DEFS = {
        'r_le': 0.015,
        'X_up': 0.3025,
        'Z_up': 0.07,
        'Z_XXup': -0.5,
        
        'X_lo': 0.3025,
        'Z_lo': -0.07,
        'Z_XXlo': 0.5,
        
        'Z_te': 0,
        'delta_Z_te': 0,
        'alpha_te': 0,
        'beta_te': 0,
    }

    BOUNDS_MARGIN = 0.2
    XL = np.array([])
    XU = np.array([])

    for key, value in PARAM_CENTRAL_DEFS.items():
        # Set the last 4 params manually. They can easily create invalid foils if not bounded properly.
        # Set Z_te and delta_Z_te to 0 for sharp trailing edge
        # If you want to manually adjust a specfic param, do it here with an elif block.
        if key == 'Z_te' or key == 'delta_Z_te':
            low = 0
            high = 0
            
        elif key == 'alpha_te':
            low = 0
            high = 0
            
        elif key == 'beta_te':
            low = 0
            high = 0
            
        else:
            low = value * (1 - BOUNDS_MARGIN)
            high = value * (1 + BOUNDS_MARGIN)

        XL = np.append(XL, min(low, high))
        XU = np.append(XU, max(low, high))

elif AIRFOIL_PARAMETRIZATION_MODE == "NACA":
    # NACA 4-digit bounds
    # Digits: (max camber, dist of max camber from LE in tenths of chord, max thickness)
    XL = np.array([0, 0, 12])
    XU = np.array([5, 6, 24])

# Baseline data for normalization in multi-objective scoring
BASELINE_DATA = {'Cl': 1.2, 'Window': 4.0}
