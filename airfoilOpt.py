import os
import csv
import shutil
import numpy as np
import multiprocessing
from pathlib import Path
from scipy.optimize import differential_evolution
from rewrite import *

"""
Optimizes a given airfoil for max L/D. Currently works with NACA 4-digit and PARSEC parametrization
"""

# Configs are put here because of a quirk with the way multiprocessing works with diff evo
# If you put these in the _main_ block, diff evo won't see them and crash
# *************************** Configs ***************************
# Set paths
history_dir = Path("data/history/")
log_file_path = Path("data/optimization_datalog.csv")

# Setup counter for file management
eval_counter = multiprocessing.Value("i", 0)

# Set optimization parameters
airfoil_parametrization_mode = "PARSEC" # PARSEC or NACA
modality = "multi" # single or multi
singleVar_opt = "Cl" # Cl, Cd, L/D
multiVar_opt = ["window", "Cl"] # window, Cl, Cd, L/D
# ***************************************************************



def objective_function(input: np.ndarray):
    worker_id = os.getpid()
    
    # Init as penalty, for error handling purposes
    score = 1e6
    
    # Counter increment
    with eval_counter.get_lock():
        eval_counter.value += 1
        current_count = eval_counter.value    
        
    try:
        # Main airfoil evaluation block
        if airfoil_parametrization_mode == "NACA":
            naca_params = np.round(input).astype(int)
            airfoil_name = f"NACA{naca_params[0]}{naca_params[1]}{naca_params[2]}"
            airfoil_obj = Airfoil(airfoil_name, nacaCode=naca_params, pid=worker_id)
            airfoil_obj.xfoil_analysis(mode="NACA", Re=250000, alpha_sequence=[0, 20, 0.5])
            
        elif airfoil_parametrization_mode == "PARSEC":
            # SciPy optimizers will pass in the params as ndarrays
            # So, convert input them back to parsecParams
            params = parsecParams.from_array(input)
            airfoil_name = "PARSEC_foil"
            airfoil_obj = Airfoil(airfoil_name, params=params, pid=worker_id)
            airfoil_obj.xfoil_analysis(mode="PARSEC", Re=250000, alpha_sequence=[0, 20, 0.5])
            
        else:
            print(f"Invalid mode {airfoil_parametrization_mode} specified. Must be 'NACA' or 'PARSEC'")
            return 1e6

        # Extract data
        aoa_data = airfoil_obj.aoa
        cl_data = airfoil_obj.cl
        cd_data = airfoil_obj.cd
        efficiency_data= airfoil_obj.efficiency
    
        missing_data =  (np.size(aoa_data) == 0 or
                        np.size(cl_data) == 0 or
                        np.size(cd_data) == 0 or
                        np.size(efficiency_data)) == 0
        
        # Proceed with scoring only if no data is missing
        if not missing_data:
            # Scoring logic
            if modality == "single":
                if singleVar_opt == "L/D":
                    score = -np.max(efficiency_data)
                
                elif singleVar_opt == "Cl":
                    score = -np.max(cl_data)
                
                elif singleVar_opt == "Cd":
                    score = -np.min(cd_data)
                else:
                    print("Invalid singleVar_opt specified. Must be 'L/D', 'Cl', or 'Cd'")
                
            elif modality == "multi":
                # initialize data from baselineData.csv into variables
                baselineData = np.genfromtxt("./baselineData.csv", delimiter=",")
                aoa_baseline = baselineData[:, 0]
                cl_baseline = baselineData[:, 1]
                cd_baseline = baselineData[:, 2]
                efficiency_baseline = baselineData[:, 3]

                # Set weights for each var
                # Init to 0 so that it doesnt break the final score construction
                wt_cl = 0.5 if "Cl" in multiVar_opt else 0.0
                wt_cd = 0.2 if "Cd" in multiVar_opt else 0.0
                wt_eff = 0.4 if "L/D" in multiVar_opt else 0.0
                wt_window = 1.0 if "window" in multiVar_opt else 0.0
                
                # Calculate window score        
                """
                    Logic for assessing window of operation:
                    check if Cl values to the left and right are within 90% of the max Cl
                    if yes, keep checking left and right, and add 1 to window_score_count for each hit
                """
                max_cl_idx = int(np.argmax(cl_data))
                window_score_count = 0
                threshold = 0.9 * np.max(cl_data)
                
                idx_right = max_cl_idx + 1
                idx_left = max_cl_idx - 1 
                
                while idx_right < len(cl_data) and cl_data[idx_right] >= threshold:
                    window_score_count += 1
                    idx_right += 1
                
                while idx_left >= 0 and cl_data[idx_left] >= threshold:
                    window_score_count += 1
                    idx_left -= 1
                    
                # Normalize each variable w.r.t the baseline
                # Normalize window score w.r.t target operational window
                normalized_cl_max = np.max(cl_data) / np.max(cl_baseline) 
                normalized_cd_min = np.min(cd_data) / np.min(cd_baseline) 
                normalized_efficiency_max = np.max(efficiency_data) / np.max(efficiency_baseline) 
                normalized_window_score = window_score_count / 10
                
                # Construct score and return
                score = -((wt_cl * normalized_cl_max) + (wt_cd * normalized_cd_min) + (wt_eff * normalized_efficiency_max) + (wt_window * normalized_window_score))    
            
            else:
                print("Invalid modality specified. Must be 'single' or 'multi'")
    
    except Exception as e:
        print(f"Failed for iteration {current_count}, due to {e}")
        score = 1e6

    # Write out L/D and params to CSV for logging and plotting
    try:
        with open(log_file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            
            param_str = "placeholder"
            if airfoil_parametrization_mode == "NACA" and naca_params is not None:
                param_str = list(naca_params)
            elif airfoil_parametrization_mode == "PARSEC" and params is not None:
                param_str = params.to_str_labelled()
            
            writer.writerow([current_count, score, param_str])
    
    except Exception as e:
        print(f"Logger failed to write in iteration {current_count} due to: {e}")
        
    # Save dat files every 50th iteration, ignore failed iterations
    if (current_count % 50 == 0) and (score < 1e5):
        if airfoil_obj.dat_file.exists():
            score_ForStr = -score if score < 0 else score
            save_file_name = Path(f"{history_dir}/iter_{current_count}_score_{score_ForStr:.2f}.dat")
            shutil.copy(airfoil_obj.dat_file, save_file_name)
    
    airfoil_obj.cleanup()
    
    return score

def save_bestFoil(paramBest, convergence):
    """
        Runs at end of every iteration to save the best airfoil
    """
    print(f"Iteration finished. Saving best solution so far.")
    
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
    

    print("\n" + "=" * 40)
    print("Optimization Complete")
    print("=" * 40)
    
    if result.success:
        print(f"Converged: ({result.message})")
    else:
        print(f"Not converged: ({result.message})")
    print("-" * 40)
    
    if modality == "multi":
        print(f"Best Score (Weighted): {-result.fun:.4f}") 
    elif modality == "single":
        print(f"Best Score: {-result.fun:.4f}")
        
    print(f"Best Parameters: {result.x}")
    print("-" * 40)
    
    print(f"Total number of iterations: {result.nit}")
    print(f"Total number of function evaluations i.e XFOIL Runs: {result.nfev}")
    print("="*40)


"""
Note on nfev and nit

nit = number of iterations
nfev = number of function evaluations

For genetic algorithms,
nfev = nit * popsize * number_of_parameters

Therefore, diff evo is probably not a good idea for this use case. PARSEC is also probably a bad option 
to use for parametrization because of the number of params used. 
Since XFOIL is fast, I guess its not the worst option, but still, finding a better parametrization option
with fewer params would be better.
"""