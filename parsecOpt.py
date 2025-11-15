import os
import subprocess
import numpy as np
from scipy.optimize import differential_evolution
from airfoilTools import xFoil, parsec, writeAirfoil

"""
Optimizes a given airfoil for max L/D. Currently works with NACA 4-digit and PARSEC parametrization
"""

#! Reformatting to for PARSEC foils
#! Implement a new bounds implementeation - if user does not give naything keep a default for that
#! Else, take +- 20% of input params as bounds

# Initialize iteration var, and create a param list for the first iteration
iter = 0
parsec_paramsInitialize = {
    "r_le"          : 0.015, 
    "X_up"          : 0.3025, 
    "Z_up"          : 0.07,
    "Z_XXup"        : -0.5,
        
    "X_lo"          : 0.3025,
    "Z_lo"          : -0.07,
    "Z_XXlo"        : 0.5,
        
    "Z_te"          : 0.0,
    "delta_Z_te"    : 0.00,
    "alpha_te"      : 0.0, # In degs
    "beta_te"       : 0.0  # In degs
}

input_parsecParams = list(parsec_paramsInitialize.values())

# Define objective. Here, we want to max L/D, so at the end return - L/D peak, so that we
# can use a minimizing optimizer
# i.e min(-peak_efficiency) == max(+peak_efficiency)
def objective_function(input):
    global iter
    airfoil_name = f"PARSEC-FOIL-{iter}"
    
    # Generate parsec airfoil
    x_airfoil, y_airfoil, parsecIPCoeffs = parsec(input)
    writeAirfoil(x_airfoil, y_airfoil, airfoil_header=airfoil_name, coeffs=input)
    
    # Run xfoil
    xFoil(input, airfoil_name, mode="PARSEC")
    
    if os.path.exists(f"./data/output/{airfoil_name}Polar.txt"):
        data = np.genfromtxt(f'./data/output/{airfoil_name}Polar.txt',skip_header=12)
        
        # If data is written but empty, return penalty
        if data.size == 0:
            return 1e6

        # If only one AoA converges, skip
        elif len(data.shape) == 1:
            print (f"{airfoil_name}: Only one AoA converged, skipping")
            return 1e6
        
        cl_data = data[:, 1]
        cd_data = data[:, 2]
        
        efficiency_data = cl_data / cd_data
        peak_efficiency = np.max(efficiency_data)
        
        iter += 1
        return -peak_efficiency
        
    else:
        # Increase iteration count
        iter += 1   
        return 1e6
    

if __name__ == "__main__":
    # Run the optimization loop
    result = differential_evolution(objective_function, 
                                bounds=[(0.0012, 0.018),    # r_le
                                        (0.242, 0.363),     # X_up
                                        (0.048, 0.072),     # Z_up
                                        (-0.6, -0.4),       # Z_XXup
                                        
                                        (0.242, 0.363),     # X_lo
                                        (-0.072, -0.048),   # Z_lo
                                        (0.4, 0.6),         # Z_XXlo
                                        
                                        (-0.004, 0.004),    # Z_te
                                        (0, 0.012),    # delta_Z_te
                                        (0, 11.1),        # alpha_te
                                        (-3.335, 0)    # beta_te
                                        ],
                                x0 = input_parsecParams,
                                maxiter=50, popsize=10, disp=True, workers=1)
    
    print(f"\nOptimization complete")
    print(f"Best L/D: {-result.fun:.2f}")
    print(f"Best parameters: {result.x}")