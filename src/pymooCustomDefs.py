from pymoo.core.callback import Callback


class convergenceCheck(Callback):
    """
    Callback function to get variables for convergence analysis.
    Stores the optimum objective value of each generation, and the number of function evaluations.
    """
    
    def __init__(self):
        super().__init__()
        self.opt = []
        self.n_evals = []

    def notify(self, algorithm):
        # Store the number of evaluations and the optimum objective value
        self.n_evals.append(algorithm.evalator.n_eval)
        self.opt.append(algorithm.opt[0].F)