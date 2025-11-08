# Overview

This is a repo for me to test out and learn optimization methods. For now, my goal is to get an airfoil
optimizer setup for XFOIL

Requires Xfoil installed through sudo get

Here, I will first do a simple L/D maximizer. 



8-11-25
V1 has been done. airfoilOpt.py can be run and will maximize L/D using NACA 4-digit parametrization.

Next Steps - 
- [x] First, I need to create a function for running xfoil and saving the outputs
- [x] Think how to parametrize and modify airfoil
    - For V1 i'll start with the xfoil's built-in NACA gen
- [ ] Implement a more comprehensive airfoil parametrization method for V2
