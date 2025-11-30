"""
pymoo problem definition for airfoil optimization.
Defines the airfoilOptProblem class that encapsulates the optimization objectives.
"""

import os
import threading
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from src.airfoilTools import Airfoil, parsecParams
from src.config import (
    AIRFOIL_PARAMETRIZATION_MODE,
    RE,
    ALPHA_SEQ,
)


class airfoilOptProblem(ElementwiseProblem):
    """
    Multi-objective airfoil optimization problem using pymoo.

    Evaluates airfoil designs for Cl (lift coefficient) and window (operational range).
    Supports both NACA 4-digit and PARSEC parametrization modes.
    """

    def __init__(self, xl, xu, baseline_data=None, **kwargs):
        """
        Initialize the optimization problem.

        Args:
            xl: Lower bounds for design variables (np.ndarray)
            xu: Upper bounds for design variables (np.ndarray)
            baseline_data: Dict with baseline 'Cl' and 'Window' values for normalization
            **kwargs: Additional arguments passed to ElementwiseProblem
        """
        super().__init__(
            n_var=len(xl),
            n_obj=2,
            n_ieq_constr=0,
            xl=xl,
            xu=xu,
            elementwise_evaluation=True,
            **kwargs
        )
        self.baseline_data = baseline_data if baseline_data else {'Cl': 1.2, 'Window': 4.0}

    def _evaluate(self, x, out, *args, **kwargs):
        """
        Evaluate a single airfoil design.

        Args:
            x: Design variables (array of parameters)
            out: Output dictionary to store objectives
            *args, **kwargs: Additional arguments from pymoo
        """
        worker_id = os.getpid() * 1000 + (threading.get_ident() % 1000)

        try:
            name = "MOO_eval"

            # Create airfoil instance based on parametrization mode
            if AIRFOIL_PARAMETRIZATION_MODE == "PARSEC":
                params = parsecParams.from_array(x)
                foil = Airfoil(name, params=params, pid=worker_id)
                mode = "PARSEC"

            elif AIRFOIL_PARAMETRIZATION_MODE == "NACA":
                # NACA expects integer 4-digit-like inputs (m, p, t)
                naca_params = np.round(x).astype(int)
                foil = Airfoil(name, nacaCode=naca_params, pid=worker_id)
                mode = "NACA"

            else:
                raise ValueError(
                    f"Unknown parametrization mode: {AIRFOIL_PARAMETRIZATION_MODE}"
                )

            # Run XFOIL analysis
            foil.xfoil_analysis(mode=mode, Re=RE, alpha_sequence=ALPHA_SEQ)

            cl = foil.cl
            cd = foil.cd

            # Scoring logic
            if np.size(cl) == 0 or np.size(cd) == 0:
                # Penalize failed evaluations
                f1 = 1e6
                f2 = 1e6
            else:
                # Objective 1: Maximize Cl (return negative for minimization)
                f1 = -1 * (np.max(cl) / self.baseline_data['Cl'])

                # Objective 2: Maximize operational window at 90% Cl_max
                threshold = 0.90 * np.max(cl)
                valid_indices = np.where(cl >= threshold)[0]

                if len(valid_indices) == 0:
                    window_score = 0
                else:
                    # Find continuous ranges above threshold
                    diffs = np.diff(valid_indices)
                    split_indices = np.where(diffs > 1)[0] + 1
                    groups = np.split(valid_indices, split_indices)
                    window_score = max(len(g) for g in groups) / self.baseline_data['Window']

                f2 = -1 * window_score

            foil.cleanup()

        except Exception as error:
            # Penalize evaluation errors
            f1 = 1e6
            f2 = 1e6
            if 'foil' in locals():
                foil.cleanup()

        # Return objectives to pymoo
        out["F"] = [f1, f2]