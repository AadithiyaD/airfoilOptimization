# Overview

This is a repo for me to test out and learn optimization methods. For now, my goal is to get an airfoil
optimizer setup for XFOIL

Requires Xfoil. Can be installed through ```sudo apt install xfoil```. Here, I will first do a simple L/D maximizer. 

8-11-25
-------
V1 has been done. airfoilOpt.py can be run and will maximize L/D using NACA 4-digit parametrization.

20-11-25
--------
V2 has been done. We can now use parsec parametrization, and can run a script in the end to view evolution
of L/D throughout the optimization


Next Steps - 
- [x] First, I need to create a function for running xfoil and saving the outputs
- [x] Think how to parametrize and modify airfoil
    - For V1 i'll start with the xfoil's built-in NACA gen
- [x] Implement a more comprehensive airfoil parametrization method for V2
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
    - ~parsecOpt.py has PARSEC implemented~
- [x] Better file handling



# References

Della Vecchia, P., Daniele, E., & DʼAmato, E. (2013). An airfoil shape optimization technique coupling PARSEC parameterization and evolutionary algorithm. Aerospace Science and Technology, 32(1), 103–110. https://doi.org/10.1016/j.ast.2013.11.006