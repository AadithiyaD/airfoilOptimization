"""
Global configuration for airfoil optimization.
"""

import numpy as np
from pathlib import Path
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from src.airfoilTools import parsecParams
from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.operators.sampling.rnd import FloatRandomSampling, IntegerRandomSampling
from pymoo.operators.repair.rounding import RoundingRepair

#* ======================== Common Configuration ========================

# Number of threads for parallel evaluation
N_THREADS = 16

# Xvfb display for headless XFOIL
XVFB_DISPLAY = ":88"

# Parametrization mode: "NACA" or "PARSEC"
AIRFOIL_PARAMETRIZATION_MODE = "PARSEC"

# Multi-objective targets (case-sensitive)
MOO_OBJECTIVES = ["window", "Cl"]

# Theoretical max data used for normalization in multi-objective scoring
# Yes, it is confusing to call this 'baseline' data
BASELINE_DATA = {'Cl': 2.5, 'Window': 5.0}

# XFOIL analysis parameters
RE = 250000  
ALPHA_SEQ = [0, 20, 1]  # [start, end, step] 

# Cl and window constraints
CL_CSTR = 2
WINDOW_CSTR = 5

# Termination criterion
TERMINATION = DefaultMultiObjectiveTermination(
    xtol=1e-8,
    cvtol=1e-6,
    ftol=0.001,
    period=100,
    n_max_gen=1000,
    n_max_evals=100000
)

# If choosing seeded sampling, specify baseline
USE_SEEDED_SAMPLING = False
BASE_PARSECPARAMS = parsecParams(
    r_le=0.5,
    X_up=0.425,
    Z_up=0.17,
    Z_XXup=-0.92,
    
    X_lo=0.625,
    Z_lo=0.10,
    Z_XXlo=-1.05,
    
    Z_te=0,
    delta_Z_te=0,
    alpha_te=-27.5,
    beta_te=5,
)

# Optimization algorithm, NSGA2 or CMOPSO
OPT_ALGO = "NSGA2"
N_GEN = 1000

#* ====================== Algo and mode specific Configuration =====================
# NSGA2 algorithm parameters
POP_SIZE = 120
N_OFFSPRING = 40
ELIMINATE_DUPLICATES = True

# CMOPSO algorithm parameters
CMOPSO_POP_SIZE = 100
CMOPSO_MAX_VELOCITY_RATE = 0.2
CMOPSO_ELITE_SIZE = 10
CMOPSO_MUTATION_RATE = 0.5

# Initialize sampling, crossover, and mutation operators based on parametrization mode
if AIRFOIL_PARAMETRIZATION_MODE == "PARSEC":
    CROSSOVER = SBX(prob=0.9, eta=2)
    MUTATION = PM(prob=0.09, eta=5)
    
    if USE_SEEDED_SAMPLING:
        # Number of points to seed, excluding baseline input. Remainder of pop size will be
        # randomly sampled
        POINTS_TO_SEED = 9 
    else:
        SAMPLING = FloatRandomSampling()


elif AIRFOIL_PARAMETRIZATION_MODE == "NACA":
    SAMPLING = IntegerRandomSampling()
    CROSSOVER = SBX(prob=0.9, eta=2, repair=RoundingRepair())
    MUTATION = PM(prob=0.33, eta=5, repair=RoundingRepair())

else:
    raise ValueError(f"Unknown parametrization mode: {AIRFOIL_PARAMETRIZATION_MODE}")

# Design space bounds
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
        'delta_Z_te': (0, 0),     
        'alpha_te': (-30, -25),       
        'beta_te': (2.01, 10),        
    }

    # Construct bounds arrays
    param_order = ['r_le', 'X_up', 'Z_up', 'Z_XXup', 'X_lo', 
                   'Z_lo', 'Z_XXlo', 'Z_te', 'delta_Z_te', 'alpha_te', 'beta_te']
    XL = np.array([PARSEC_BOUNDS[p][0] for p in param_order])
    XU = np.array([PARSEC_BOUNDS[p][1] for p in param_order])

elif AIRFOIL_PARAMETRIZATION_MODE == "NACA":
    # NACA 4-digit bounds
    # Digits: (max camber, dist of max camber from LE in tenths of chord, max thickness)
    XL = np.array([0, 0, 12])
    XU = np.array([5, 6, 24])


