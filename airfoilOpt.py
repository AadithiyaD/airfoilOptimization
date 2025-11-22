import os
import csv
import shutil
import numpy as np
import multiprocessing
from pathlib import Path
from scipy.optimize import differential_evolution
from airfoilTools import *

"""
Optimizes a given airfoil for max L/D. Currently works with NACA 4-digit and PARSEC parametrization
"""

# Define objective. Here, we want to max L/D, so at the end return - L/D peak, so that we
# can use a minimizing optimizer
# i.e min(-peak_efficiency) == max(+peak_efficiency)
def objective_function(input: np.ndarray):
    worker_id = os.getpid()
    
    if airfoil_parametrization_mode == "NACA":
        naca_params = np.round(input).astype(int)
        
        airfoil_name = f"NACA{naca_params[0]}{naca_params[1]}{naca_params[2]}"
        airfoil_obj = Airfoil(airfoil_name, nacaCode=naca_params, pid=worker_id)
        airfoil_obj.xfoil_analysis(mode="NACA", Re=250000, alpha_sequence=[0, 15, 1])
        
    elif airfoil_parametrization_mode == "PARSEC":
        # SciPy optimizers will pass in the params as ndarrays
        # So, convert input them back to parsecParams
        try:
            params = parsecParams.from_array(input)
            airfoil_name = "PARSEC_foil"
            airfoil_obj = Airfoil(airfoil_name, params=params, pid=worker_id)
            airfoil_obj.xfoil_analysis(mode="PARSEC", Re=250000, alpha_sequence=[0, 15, 1])
        
        except TypeError:
            return 1e6    
    else:
        print(f"Invalid mode {airfoil_parametrization_mode} specified. Must be 'NACA' or 'PARSEC'")
    
    score = airfoil_obj.peak_efficiency
    
    # Counter increment
    with eval_counter.get_lock():
        eval_counter.value += 1
        current_count = eval_counter.value
    
    # Write out L/D and params to CSV for logging and plotting
    try:
        with open(log_file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if airfoil_parametrization_mode == "NACA":
                writer.writerow([current_count, score, list(naca_params)])
            elif airfoil_parametrization_mode == "PARSEC":
                writer.writerow([current_count, score, params.to_str_labelled()])
    
    except Exception as e:
        print(f"Logger failed to write in iteration {current_count} due to: {e}")
        
    # Save dat files every 50th iteration
    save_file = (current_count % 50 == 0)
    if save_file:
        if airfoil_obj.dat_file.exists():
            eff_score_str = f"{(-airfoil_obj.peak_efficiency):.2f}"
            save_file_name = Path(f"{history_dir}/iter_{current_count}_LD_{eff_score_str}.dat")
            shutil.copy(airfoil_obj.dat_file, save_file_name)
    
    airfoil_obj.cleanup()
    return score

def save_bestFoil(paramBest, convergence):
    """
        Runs at end of every generation to save the best airfoil
    """
    print(f"Generation finished. Saving best solution so far.")
    
    if airfoil_parametrization_mode == "NACA":
        naca_params = np.round(paramBest).astype(int)
        airfoil_name = f"best_NACA{naca_params[0]}{naca_params[1]}{naca_params[2]}"
        best_foil = Airfoil(airfoil_name, nacaCode=naca_params, pid=999)
        best_foil.write_dat_file()
        
    elif airfoil_parametrization_mode == "PARSEC":
        airfoil_name = "best_PARSEC_foil"
        params = parsecParams.from_array(paramBest)
        best_foil = Airfoil(airfoil_name, params=params, pid=999)
        best_foil.write_dat_file()
    
    print(f"saved {best_foil.dat_file}")
    
    
           
if __name__ == "__main__":
    history_dir = "data/history/"
    log_file_path = "data/optimization_datalog.csv"

    # Setup counter for file management
    eval_counter = multiprocessing.Value("i", 0)

    # Set airfoil parametrization mode. PARSEC or NACA available
    airfoil_parametrization_mode = "PARSEC"
    
    if airfoil_parametrization_mode == "PARSEC":
        param_centralDefs = {
            'r_le':     {'default': 0.015,  'bounds': (0.0012, 0.018)},
            'X_up':     {'default': 0.3025, 'bounds': (0.242, 0.363)},
            'Z_up':     {'default': 0.07,   'bounds': (0.048, 0.072)},
            'Z_XXup':   {'default': -0.5,   'bounds': (-0.6, -0.4)},
            
            'X_lo':     {'default': 0.3025, 'bounds': (0.242, 0.363)},
            'Z_lo':     {'default': -0.07,  'bounds': (-0.072, -0.048)},
            'Z_XXlo':   {'default': 0.5,    'bounds': (0.4, 0.6)},
            
            'Z_te':     {'default': 0.0,    'bounds': (-0.004, 0.004)},
            'delta_Z_te':{'default': 0.0,   'bounds': (0, 0.012)},
            'alpha_te': {'default': 0.0,    'bounds': (0, 11.1)},
            'beta_te':  {'default': 0.0,    'bounds': (-3.335, 0)}
        }

        params_keys = param_centralDefs.keys()

        # Assemble input, x0, and bounds from central definition
        input = {}
        x0 = []
        bounds = []

        for key in params_keys:
            input[key] = param_centralDefs[key]['default']
            x0.append(param_centralDefs[key]['default'])
            bounds.append(param_centralDefs[key]['bounds'])

    elif airfoil_parametrization_mode == "NACA":
        x0 = [0, 0 ,12]
        bounds=[(0, 5), (0, 6), (12, 24)]
    
    # Run the optimization loop
    result = differential_evolution(objective_function, 
                                bounds=bounds,
                                x0 = x0,
                                maxiter=15, popsize=10, disp=True, 
                                workers=6, callback=save_bestFoil)
    
    print(f"\nOptimization complete")
    print(f"Best L/D: {-result.fun:.2f}")
    print(f"Best parameters: {result.x}")