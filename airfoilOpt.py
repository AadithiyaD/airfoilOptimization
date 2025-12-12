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
from pymoo.algorithms.moo.cmopso import CMOPSO
from pymoo.parallelization.starmap import StarmapParallelization
from pymoo.core.evaluator import Evaluator
from pymoo.core.population import Population

# Import configuration and problem class from src
from src.config import *
from src.problem import airfoilOptProblem
from src.customDefs import store_ndsData, seededSampleGen


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
    
    # Sleep to allow Xvfb to start
    time.sleep(1)
    
    # Set the environment variable for this process.
    os.environ["DISPLAY"] = XVFB_DISPLAY
    
    # Setup threads for parallel evaluation
    pool = ThreadPool(N_THREADS)
    runner = StarmapParallelization(pool.starmap)
    
    
    
    try:
        # Create and run the opt problem
        print("Creating optimization problem")
        problem = airfoilOptProblem(
            xl=XL,
            xu=XU,
            baseline_data=BASELINE_DATA,
            elementwise_runner=runner
        )

        if USE_SEEDED_SAMPLING:
            # Generate seeded sampling
            seeded_sample = seededSampleGen(base_params=BASE_PARSECPARAMS,
                                            points_to_seed=POINTS_TO_SEED,
                                            perturbation=0.05,
                                            n_samples=POP_SIZE,
                                        seed=1,
                                        n_var=problem.n_var)
            pop = Population.new("X", seeded_sample)
            Evaluator().eval(problem, pop)
                   
        if OPT_ALGO == "NSGA2":
            
            if USE_SEEDED_SAMPLING:
                # Use pre-generated seeded sample as initial population
                algorithm = NSGA2(
                    pop_size=POP_SIZE,
                    n_offspring=N_OFFSPRING,
                    sampling=seeded_sample,
                    crossover=CROSSOVER,
                    mutation=MUTATION,
                    eliminate_duplicates=ELIMINATE_DUPLICATES
                )
            else:                
                algorithm = NSGA2(
                pop_size=POP_SIZE,
                n_offspring=N_OFFSPRING,
                sampling=SAMPLING,
                crossover=CROSSOVER,
                mutation=MUTATION,
                eliminate_duplicates=ELIMINATE_DUPLICATES
                )        

        elif OPT_ALGO == "CMOPSO":
            algorithm = CMOPSO(
            pop_size=CMOPSO_POP_SIZE,
            max_velocity_rate=CMOPSO_MAX_VELOCITY_RATE,
            elite_size=CMOPSO_ELITE_SIZE,
            mutation_rate=CMOPSO_MUTATION_RATE,
            seed=1
            )
        
        else:
            raise ValueError(f"Unknown optimization algorithm: {OPT_ALGO}")
        

        
        print("Starting optimization")
        res = minimize(
            problem,
            algorithm,
            ('n_gen', N_GEN),
            seed=1,
            verbose=True,
            callback=store_ndsData(),
            save_history=True
            
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
        