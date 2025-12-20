from pymoo.core.callback import Callback
import numpy as np
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from src.config import XL, XU

class RestartCallback(Callback):
    """
    A callback to restart a portion of the population every 20 generations.
    20% of the worst solutions are replaced with new random solutions.
    """
    def notify(self, algorithm):
        if algorithm.n_gen % 20 == 0:  # Every 20 gens
            # Replace worst 20% with random solutions
            n_restart = int(0.2 * algorithm.pop_size)
            algorithm.pop[-n_restart:] = algorithm.initialization.do(
                algorithm.problem, n_restart, algorithm=algorithm
            )
            print(f"Restarted {n_restart} solutions")
            
class store_ndsData(Callback):
    """
    A callback to store the number of non-dominated solutions (NDS) during optimization.
    """
    def __init__(self):
        super().__init__()
        self.data["n_nds"] = []
        self.nds = NonDominatedSorting()
        
    def notify(self, algorithm):
        # Get objective vals of current pop
        F = algorithm.pop.get("F")
        
        # Do NDS on the objective vals
        fronts = self.nds.do(F)
        
        # Store count of nds
        # fronts[0] contains the indices of the nds solns
        self.data["n_nds"].append(len(fronts[0]))
    
def seededSampleGen(base_params, points_to_seed: int, n_samples:int,
                 perturbation=0.05, seed:int=1, n_var:int=11):
    """
    Function to generate gen 0 sample using a baseline input
    Note - Could this be a custom sample class? Probably, but for now this works.
    
    Args:
        base_params: parsecParams instance representing the baseline airfoil
        points_to_seed: Number of perturbed samples to generate around baseline
        perturbation: Max percentage perturbation (+-) to apply to each parameter
        n_samples: Total number of samples to generate (including baseline and perturbed)
        seed: Set seed for reproducibility in the rng gen used in random selection
        n_var: Number of design variables (parameters)
    """
    
    rng = np.random.default_rng(seed)
    seeded_points = base_params.to_array().reshape(1,-1)
    
    for _ in range(points_to_seed):
        random_factor = rng.uniform(
            low=-perturbation,
            high=perturbation,
            size=n_var
        )
        
        perturbed_values = base_params.to_array() * (1 + random_factor)
        
        # Clip to bounds
        perturbed_values = np.clip(perturbed_values, XL, XU)
        
        seeded_points = np.vstack([seeded_points, perturbed_values])
    
    # Fill remaining samples randomly
    n_random = n_samples - (points_to_seed + 1)
    random_points = np.random.uniform(
        low=XL,
        high=XU, 
        size=(n_random, n_var)
    )
    
    all_points = np.vstack([seeded_points, random_points])
    return all_points
