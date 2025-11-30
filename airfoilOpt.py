import os
import time
import threading
import numpy as np
import multiprocessing
import pickle
from pathlib import Path
from airfoilTools import *
import subprocess
from multiprocessing.pool import ThreadPool
from pymoo.optimize import minimize
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.parallelization.starmap import StarmapParallelization
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.operators.sampling.rnd import IntegerRandomSampling


"""
Multi-objective airfoil optimizer using NSGA2 with XFOIL evaluation.
Supports NACA 4-digit and PARSEC parametrization.
Can optimize for: Cl, Cd, L/D and window (operational range). Case sensitive.
"""

# Configs are put here because of a quirk with the way multiprocessing works
# If you put these in the _main_ block, pymoo won't see them and crash
# *************************** Configs ***************************
# Set paths
final_output_dir = Path("data/final_output")
final_output_dir.mkdir(parents=True, exist_ok=True)
log_file_path = Path("data/optimization_datalog.csv")

# Setup counter for file management
eval_counter = multiprocessing.Value("i", 0)

# Set optimization parameters
airfoil_parametrization_mode = "NACA" # PARSEC or NACA
moo_objectives = ["window", "Cl"] 

# ******************** pymoo problem class defs ********************
class airfoilOptProblem(ElementwiseProblem):
    def __init__(self, xl, xu, baseline_data=None, **kwargs):
        """
        xl => lower bounds, np.ndarray
        xu => upper bounds, np.ndarray
        baseline_data => Dict or np.ndarray containing baseline
                        max_Cl and window (or whatever 2 params you care about)
                        for nomralization
        """
            
        super().__init__(n_var = len(xl),
                         n_obj = 2,
                         n_ieq_constr = 0,
                         xl = xl,
                         xu = xu,
                         elementwise_evaluation=True, **kwargs)
        self.baseline_data = baseline_data if baseline_data else {'Cl': 1.2, 'Window': 4.0}

    def _evaluate(self, x, out, *args, **kwargs):
        """
        Handles eval of one indidividual 'x' (array of 11 params)
        pymoo does the looping / parallelization
        """
        worker_id = os.getpid() * 1000 + (threading.get_ident() % 1000)
        
        try:
            name = "MOO_eval"
            # Support both PARSEC and NACA parametrizations
            if airfoil_parametrization_mode == "PARSEC":
                params = parsecParams.from_array(x)
                foil = Airfoil(name, params=params, pid=worker_id)
                mode = "PARSEC"

            elif airfoil_parametrization_mode == "NACA":
                # NACA expects integer 4-digit-like inputs (m, p, t)
                naca_params = np.round(x).astype(int)
                foil = Airfoil(name, nacaCode=naca_params, pid=worker_id)
                mode = "NACA"

            else:
                raise ValueError(f"Unknown parametrization mode: {airfoil_parametrization_mode}")

            foil.xfoil_analysis(mode=mode, Re=250000, alpha_sequence=[0, 20, 0.5])

            cl = foil.cl
            cd = foil.cd
            
            # Scoring logic
            # If empty data, penalize objective 1 nad 2
            if np.size(cl) == 0 or np.size(cd) == 0:
                f1 = 1e6
                f2 = 1e6
                
            else:
                # Objective 1: Max Cl
                # Normalize
                f1 = -1 * (np.max(cl) / self.baseline_data['Cl'])
                
                # Obj2 : Window
                threshold = 0.90 * np.max(cl)
                
                valid_indices = np.where(cl >= threshold)[0]
                
                if len(valid_indices) == 0:
                    window_score = 0 
                else:
                    diffs = np.diff(valid_indices)
                    split_indices = np.where(diffs > 1)[0] + 1
                    groups = np.split(valid_indices, split_indices)
                    window_score = max(len(g) for g in groups) / self.baseline_data['Window']
                    
                f2 = -1 * window_score
            
            foil.cleanup()
        
        except Exception as error:
            #print(f"Evaluation error: {error}")
            f1 = 1e6
            f2 = 1e6
            if 'foil' in locals(): foil.cleanup()
        
        # Return objectives
        # pymoo wants out["F"] to be list/array of objectives
        out["F"] = [f1, f2]
        
# ******************************************************************

# ******************** MAIN ********************
if __name__ == "__main__":    
    xvfb_display = ":88"
    print(f" Starting background xvfb server on {xvfb_display}")
    
    xvfb_process = subprocess.Popen(
        ["Xvfb", xvfb_display, "-screen", "0", "1024x768x24"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(1)
    
    # Set the environment variable for THIS process.
    # All worker processes spawned by differential_evolution will INHERIT this!
    os.environ["DISPLAY"] = xvfb_display
    
    n_threads = 6
    pool = ThreadPool(n_threads)
    runner = StarmapParallelization(pool.starmap)
    
    try:
        if airfoil_parametrization_mode == "PARSEC":
            param_centralDefs = {
                'r_le':      0.015,  
                'X_up':      0.3025, 
                'Z_up':      0.07,   
                'Z_XXup':    -0.5,   
                
                'X_lo':      0.3025, 
                'Z_lo':      -0.07,  
                'Z_XXlo':    0.5,    
                
                'Z_te':      0.0,    
                'delta_Z_te': 0.0,   
                'alpha_te':  0.0,     
                'beta_te':   0.0,    
            }
            
            bounds_margin = 0.2 
            xl = np.array([])
            xu = np.array([])
            
            for key, values in param_centralDefs.items():
                if values == 0.0:
                    low = values 
                    high = values
               
                else:
                    low = values * (1 - bounds_margin)
                    high = values * (1 + bounds_margin)
                
                xl = np.append(xl, min(low, high))
                xu = np.append(xu, max(low,high))
            
            sampling=FloatRandomSampling()
            crossover=SBX(prob=0.9, eta=2)
            mutation=PM(prob=0.09, eta=5)
            
            
        elif airfoil_parametrization_mode == "NACA":
            # Define NACA bounds
            # Digits => (max camber, dist of max camber from LE in tenths of chord, max thickness)
            xl = np.array([0, 0, 12])
            xu = np.array([5, 6, 24])
            sampling=IntegerRandomSampling()
            crossover=SBX(prob=0.9, eta=2, repair=RoundingRepair())
            mutation=PM(prob=0.33, eta=5, repair=RoundingRepair())

        # Run the optimization
        print("Starting optimization")

        problem = airfoilOptProblem(xl=xl, xu=xu, baseline_data={'Cl': 1.2, 'Window': 4.0}, 
                                        elementwise_runner=runner)
        algorithm = NSGA2(
            pop_size=40,
            n_offspring=40,
            sampling=sampling,
            crossover=crossover,
            mutation=mutation,
            eliminate_duplicates=True
        )
        
        res = minimize(
            problem,
            algorithm,
            ('n_gen', 5),
            seed=1,
            verbose=True)

        print("Optimization done")
        
        # Save results
        with open("optimization_results.pkl", "wb") as f:
            pickle.dump(res, f)
            print("Results saved to pickle file")
        
    finally:
        print(" Killing xvfb server")
        xvfb_process.terminate()
        xvfb_process.wait()
        