"""
Global configuration for airfoil optimization.
"""

import numpy as np
from pathlib import Path
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from src.airfoilTools import parsecParams
# from pymoo.termination import get_termination
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
ALPHA_SEQ = [0, 20, 1]  # [start, end, step] 

# Xvfb display for headless XFOIL
XVFB_DISPLAY = ":88"

#* ====================== Optimization Configuration =====================

# Optimization algorithm, NSGA2 or CMOPSO
OPT_ALGO = "NSGA2"
N_GEN = 10

# If choosing seeded sampling, specify baseline
BASE_PARSECPARAMS = parsecParams(
    r_le=0.015,
    X_up=0.3025,
    Z_up=0.07,
    Z_XXup=-0.5,
    
    X_lo=0.3025,
    Z_lo=-0.07,
    Z_XXlo=0.5,
    
    Z_te=0.0,
    delta_Z_te=0.0,
    alpha_te=0.0,
    beta_te=0.0,
)

# Number of points to seed, excluding baseline input. Remainder of pop size will be
# randomly sampled
POINTS_TO_SEED = 9 

# Termination criterion: time-based (30 mins)
# TERMINATION = get_termination("time", "00:30:00")

# NSGA2 algorithm parameters
POP_SIZE = 110
N_OFFSPRING = 40
ELIMINATE_DUPLICATES = True

# CMOPSO algorithm parameters
CMOPSO_POP_SIZE = 100
CMOPSO_MAX_VELOCITY_RATE = 0.2
CMOPSO_ELITE_SIZE = 10
CMOPSO_MUTATION_RATE = 0.5

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
        'r_le': (0.025, 0.11),
        'X_up': (0.4, 0.45),
        'Z_up': (0.16, 0.18),
        'Z_XXup': (-0.92, -0.92),
        
        'X_lo': (0.6, 0.65),
        'Z_lo': (0.09, 0.11),
        'Z_XXlo': (-1.1, -1.03),
        
        'Z_te': (0, 0),           
        'delta_Z_te': (0.0, 0.0),     # Sharp TE (fixed)
        'alpha_te': (-30, -25),       
        'beta_te': (2, 10),        
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

# Theoretical max data for normalization in multi-objective scoring
# Yes, it is confusing to call this 'baseline' data
BASELINE_DATA = {'Cl': 2.5, 'Window': 5.0}
