import os
import subprocess
import numpy as np
from scipy.optimize import differential_evolution
from xfoil_runner import xFoil

"""
Optimizes a given airfoil for max L/D. Currently works with NACA 4-digit parametrization
"""


# Specify digits of NACA airfoil
max_camber = 0
max_camber_loc = 0
max_thickness = 12

# Create params list
#! I do realize that this setup does not handle the NACA0009 foil, but I 
#! don't want to support it anyway, since I know it'll be worse than the base
params = [max_camber, max_camber_loc, max_thickness]

# Define objective. Here, we want to max L/D, so at the end return - L/D peak, so that we
# can use a minimizing optimizer
# i.e min(-peak_efficiency) == max(+peak_efficiency)
def objective_function(params):
    params_int = [int(round(p)) for p in params]
    
    airfoil_name = f"NACA{params_int[0]}{params_int[1]}{params_int[2]}"
    
    xFoil(params_int)
    
    if os.path.exists(f"data/output/NACA{params_int[0]}{params_int[1]}{params_int[2]}Polar.txt"):
        data = np.genfromtxt(f'data/output/NACA{params_int[0]}{params_int[1]}{params_int[2]}Polar.txt',skip_header=12)
        
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
        
        return -peak_efficiency
        
    else:
        return 1e6

# Run the optimization loop
result = differential_evolution(objective_function, bounds=[(0, 5),(3, 6),(12, 24)],
                                maxiter=50, popsize=10, seed=40, disp=True, workers=1)


# ----------------------- NEED TO REWRITE ---------------------------
# Print results
print("\n" + "="*70)
print("OPTIMIZATION COMPLETE")
print("="*70)

camber_opt = int(result.x[0])
camber_pos_opt = int(result.x[1])
thickness_opt = int(result.x[2])

print(f"\nOptimal Airfoil: NACA{camber_opt}{camber_pos_opt}{thickness_opt}")
print(f"  Max Camber: {camber_opt}% of chord")
print(f"  Camber Position: {camber_pos_opt*10}% chord")
print(f"  Max Thickness: {thickness_opt}% of chord")
print(f"\nMaximum L/D: {-result.fun:.2f}")

print("="*70)