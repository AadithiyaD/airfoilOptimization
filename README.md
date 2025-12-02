# Overview

This was a repo for me to test out and learn optimization methods and just 
generally improve my Python scripting. My goal was to get an airfoil
optimizer setup for XFOIL, optimizing for max L/D. From there, it has now grown into a usable
single element airfoil optimizer tool, where you can perform bi objective optimisation for Cl and 
operational window.

Tested and developed on WSL2.

Usage
-----
Run ```airfoilOpt.py```. Parameters for XFOIL analysis and optimizer can be changed in ```src/config.py```

Requirements
------------
```pip install -r requirements.txt```

Requires XFOIL, xvfb and Xlaunch. Can be installed through 
```sudo apt-get update```
```sudo apt-get install xvfb```
```sudo apt install xfoil```
and Xlaunch can be installed through [Xming](https://sourceforge.net/projects/xming/) for Windows

