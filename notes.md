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
- [] BIG QUESTION - Does this need to be a moo problem? Can I just optimize for window,
    and put my Cl req as a criteria i.e Can I just do a single objective opt?
- [] Check how other optimization algorithms perform
- [] Maybe redo the window calculation?
- [] A better way to select which foil to plot from Pareto Front
    - A slider? or something else thats interactive?
- [] Multi element airfoil optimization
    - Probably best to use JavaFoil for this


Notes
------
- I removed single objective optimisation since I think it would produce unphysical designs most of the time
- I did not allow for the optimizer to start from an initial airfoil and then explore the space around it. pymoo
    Does not have a clean implementation for this. You can specify your bounds around the airfoil you have in mind
    and then compare the results in post processing
- The slowdown is NOT due to Xvfb. Its just because of my ASEQ range 0 20 0.5

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
and give me an output that has similar characteristics. I think