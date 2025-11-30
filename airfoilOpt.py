"""
Multi-objective airfoil optimizer using NSGA2 with XFOIL evaluation.
Main entry point for running the optimization.

Supports NACA 4-digit and PARSEC parametrization modes.
Can optimize for: Cl, Cd, L/D and window (operational range).

To modify optimization parameters, edit src/config.py
"""

import os
import time
import subprocess
import pickle
from multiprocessing.pool import ThreadPool
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.parallelization.starmap import StarmapParallelization

# Import configuration and problem class from src
from src.config import (
    AIRFOIL_PARAMETRIZATION_MODE,
    N_THREADS,
    POP_SIZE,
    N_OFFSPRING,
    N_GEN,
    ELIMINATE_DUPLICATES,
    XVFB_DISPLAY,
    XL,
    XU,
    BASELINE_DATA,
    SAMPLING,
    CROSSOVER,
    MUTATION,
)
from src.problem import airfoilOptProblem


def run_optimization():
    """
    Execute the multi-objective airfoil optimization using NSGA2.
    
    Sets up Xvfb display for headless XFOIL, creates thread pool for parallel evaluation,
    and runs the optimization algorithm.
    """
    print(f"Starting background xvfb server on {XVFB_DISPLAY}")
    
    xvfb_process = subprocess.Popen(
        ["Xvfb", XVFB_DISPLAY, "-screen", "0", "1024x768x24"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(1)
    
    # Set the environment variable for this process.
    os.environ["DISPLAY"] = XVFB_DISPLAY
    
    # Setup threads for parallel evaluation
    pool = ThreadPool(N_THREADS)
    runner = StarmapParallelization(pool.starmap)
    
    try:
        # Create the optimization problem
        print("Creating optimization problem")
        problem = airfoilOptProblem(
            xl=XL,
            xu=XU,
            baseline_data=BASELINE_DATA,
            elementwise_runner=runner
        )
        
        # Create the NSGA2 algorithm
        algorithm = NSGA2(
            pop_size=POP_SIZE,
            n_offspring=N_OFFSPRING,
            sampling=SAMPLING,
            crossover=CROSSOVER,
            mutation=MUTATION,
            eliminate_duplicates=ELIMINATE_DUPLICATES
        )
        
        # Run the optimization
        print("Starting optimization")
        res = minimize(
            problem,
            algorithm,
            ('n_gen', N_GEN),
            seed=1,
            verbose=True
        )
        
        print("Optimization done")
        
        # Save results
        with open("optimization_results.pkl", "wb") as f:
            pickle.dump(res, f)
            print("Results saved to optimization_results.pkl")
        
        return res
        
    finally:
        print("Killing xvfb server")
        xvfb_process.terminate()
        xvfb_process.wait()
        pool.close()
        pool.join()


if __name__ == "__main__":
    run_optimization()
        