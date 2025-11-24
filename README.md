# Overview

This was a repo for me to test out and learn optimization methods and just 
generally improve my Python scripting. My goal was to get an airfoil
optimizer setup for XFOIL, optimizing for max L/D. From there, it has now grown into a somewhat usable
single element airfoil design tool, where you can optimize for Cl, Cd, Cl/Cd, and operational window

Usage
-----
Run airfoilOpt.py

Requirements
------------

```pip install -r requirements.txt```

Requires XFOIL, xvfb and Xlaunch. Can be installed through 
```sudo apt-get update```
```sudo apt-get install xvfb```
```sudo apt install xfoil```
, and Xlaunch from its website.

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
- [] Multi objective optimize
    - Optimize for widest operation zone
- [x] Parallel execution of monitor.py and airfoilOpt.py
    - As it stands, xfoil "hijacks" the terminal and prevents the execution of any other scripts
- [] Script to plot airfoils and aero polars
- [] Check how other optimization algorithms perform
- [] Multi element airfoil optimization
    - Probably best to use JavaFoil for this


#! NEW PROBLEM
- PARSEC mode - after a while it just seems to shit itself and not try new searches that actually work
    Same for naca sa well