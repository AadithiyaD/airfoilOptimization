#!/home/durai/OpenFOAM/durai-v2506/run/dev-space/opt-test/.venv/bin/python3

description="""
Dump the contents of the configuration files
"""

from PyFoam import configuration as config
from os import path

from PyFoam.ThirdParty.six import print_

fName=path.join(path.curdir,"LocalConfigPyFoam")
if path.exists(fName):
    config().addFile(fName)

print_(config().dump())

# Should work with Python3 and Python2
