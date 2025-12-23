Next Steps 
----------
- [x] First, I need to create a function for running xfoil and saving the outputs
- [x] Think how to parametrize and modify airfoil
    - For V1 i'll start with the xfoil's built-in NACA gen
- [x] Implement a more detailed airfoil parametrization method for V2
    - [x] Parsec method formulae implemented
    - [x] Need to add cosine spacing
    - [x] Need to add dat file write
- [x] Implement some cleanups and refactors for clarity and maintainabilty
    - [x] Dataclass for parsec param handling
    - [x] dict for parsec param inputs
    - [x] Parallel safe objective function
    - [x] Programmatically generate bounds for optimizer
    - [x] Classes in airfoilTools.py
- [x] Rewrite the main airfoilOpt.py to support multiple parametrizations
    - ~parsecOpt.py has PARSEC implemented~ Implemented in main airofilOpt.py
- [x] Better file handling
- [x] Optimization workflow verification
    - I know Xfoil is verified, and I know the optimizer is also verified. The results now depend on my bounds
- [x] Multi objective optimize
    - Optimize for widest operation zone
- [x] Parallel execution of monitor.py and airfoilOpt.py
    - As it stands, xfoil "hijacks" the terminal and prevents the execution of any other scripts
- [x] Script to plot airfoils and aero polars
- [x] Update plotter to support naca mode
- [x] Reorganize and cleaup code for clarity and readability
- [x] Change parsec bounds to be manually set
- [x] Redo the window calculation?
    - Window can go upto 5, but Cl can at best go to around 2
    - Values are now normalized wrt a pre-defined max, rather than baselien
    - Window now counts total degrees of stable op, rather than num of points
- [x] BIG QUESTION - Does this need to be a moo problem? Can I just optimize for window,
    and put my Cl req as a criteria i.e Can I just do a single objective opt?
    - This is possible. This is called scalarization
    - Implement this?
        - No
- [x] Check how other optimization algorithms perform
    - [x] CMOPSO implemeted
- [x] Implement constraints
    - On geometry to check validity ex: thickness constraint
        - [x] Implemented intersection check
        - [x] Implement hump check
            - Not sure how this could be implemented. The humps are kind of irregular in the way they parsec creates them,
                sometimes its an obvious hump where you have 2 local maxima and a dip on either side, other times
                the surface crests, flattens out and then crests again. 
            - I also think that these airfoils would be worse performing in my objectives anyway, so they should get filtered 
                out (ideally)
    - [x] On aero param for performance specification
        - [x] Implement Cl and window constraint

Notes
------
- With `verbose=True`, you will see $\epsilon$ in the console. This is the value compared against the threshold
    for determination of termination. 
    $\epsilon = max(delta_{ideal}, delta_{nadir}, delta_{f})$. 
    Whenever the $\epsilon$ value changes, the indicator column shows which variable has caused this change. `f` 
    indicates a new optimum has been found, and its delta with the previous optimum is greater than the threshold.

8-11-25
-------
V1 has been done. airfoilOpt.py can be run and will maximize L/D using NACA 4-digit parametrization.

20-11-25
--------
V2 has been done. We can now use parsec parametrization, and can run a script in the end to view evolution
of L/D throughout the optimization

29-11-25
--------
V3 is almost done i'd say. I'm removing the single objective optimizer mode, as I realize that its probably
going to produce unphysical designs. This mode just optimizes, say Cl, and does not care about which angle it
occurs at, or how the lift curve looks like. Therefore, you could get a foil that has super high lift, but
horrible stall, too little thickness, or a number of any other problems. 

Theoretically, the multi objective mode with window should address this. You're basically maximizing Cl
at several AoAs so this should provide usable foils, provided the design space bounds are appropriate

V3 finished and pushed on 30-11-25

07-12-25
--------
By giving bounds around the MSHD airfoil, the algorithm is able to somewhat recreate the airfoil
and give me an output that has similar characteristics. I think.

CMOPSO needs a larger timeout value, around 10s

The current issue im dealing with is why my pareto front has only 3 or 4 solutions even after 800 gens of nsga2,
and the algo seems to converge. I think this is probably due to the hyperparameters needed some tuning, and
almost definitely due to the window score being greater than the Cl score. ANS - Pop size was too small. 
Recommended to set Pop_size >= 10 * numberOfParams_inDesignSpace i.e here, Pop_size >= 110

NACA mode was meant to be an initial testing ground. All of the main features are implemented for PARSEC
parametrisation

13-12-25
--------
MOPSO is not a good fit for this opt problem. PSO depends on the previous design point for deciding where to
go next. Unlike evollutionary algos, it cannot bring in random mutation to try and escape local optima, or 
failing designs. If an XFOIL eval fails for a point, it is unlikely that its associated particle in the swarm
will be able to improve much. So, you should really stick to algos like NSGA2, or other GAs

23-12-25
--------
For some reason, calling xfoil in the jupyter notebook on the pareto airfoils does not work. I tried
running XFOIL from the command line on the desired pareto foil and it doesn't work either. However,
running the same file on xflr5 on my windows side seems to work. Why is this? I don't know. The main
optimizer is based on XFOIL, and its apparently able to "solve" the airfoil flow during the opt run,
but fails when I try to do the same airfoil calc individually.

If this happens, just use xflr5 on windows.

V4 finished on 23-12-25. With this I think I'm done with the major code for the script. My initial goals
were to get a better understanding of black box optimisation and scripting, and I think i've achieved that.
I might try and improve one of the airfoils on the pareto front to see if i can make an improvement (This
is the main use case i envisioned; you'd use the script to get a front of foils better than your input,
then you modify those to get an even better foil)