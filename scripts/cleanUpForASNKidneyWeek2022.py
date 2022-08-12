# Imports
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import os
import sys

# Parameters
param1 = 'test'
baseFolder = r'/Users/saranmedical-smile/AKIFlagger/scripts/StandardizingAKI/PyPkg'
pythonCSVsDirectory = os.path.join(baseFolder, "doc_csvs/python/")
rCSVsDirectory = os.path.join(baseFolder, "doc_csvs/r/")
fileNames = [f for f in os.listdir(os.path.join(baseFolder, pythonCSVsDirectory))]

# General directory structures
print(fileNames)


#file1 = 

# Read in data
egfr_out = pd.read_csv(os.path.join(baseFolder, pythonCSVsDirectory, fileNames[-1])) # ../egfr_out.csv


# Remove black variable


# Keeping a running tally of the modifications to the documentation (rst files, namely)
# which are built into the readthedocs.io 

# Minor modifications to Introduction & Installation ReStructured Text files, but the real changes are in GettingStarted.rst

# How are we to remove the black variable systematically; from the documentation strings as well as the dataframes?

