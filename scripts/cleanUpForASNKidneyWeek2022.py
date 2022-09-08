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
fileNamesPy = [f for f in os.listdir(os.path.join(baseFolder, pythonCSVsDirectory))]
filePaths = [os.path.join(baseFolder, pythonCSVsDirectory, f) for f in fileNamesPy]

fileNamesR = [f for f in os.listdir(os.path.join(baseFolder, rCSVsDirectory))]
filePathsR = [os.path.join(baseFolder, rCSVsDirectory, f) for f in fileNamesR]


# General directory structures
print(fileNamesPy)




# Read in data
example1 = pd.read_csv(filePaths[-4]) # ../example1.csv
if 'RACE' in example1.columns:
    example1 = example1.drop('RACE', axis = 1)
if example1
example1.to_csv(filePaths[-4], index = False)

# Remove black from dataFRAME and write OUT 
for file in filePaths:
    dataFRAME = pd.read_csv(file, index_col = [0])
    if 'race' in dataFRAME.columns:
        dataFRAME = dataFRAME.drop('race', axis=1)
    dataFRAME.to_csv(file)
# Python done

for file in filePathsR:
    dataFRAME = pd.read_csv(file, index_col = [0])
    if 'race' in dataFRAME.columns:
        dataFRAME = dataFRAME.drop('race', axis=1)
    dataFRAME.to_csv(file)
# R done

# 2022-11-02 black / race removed from documentation strings

#3---

# Rename fileNames and filePaths variables
# Parameters II

# Remove Unnamed: 0.1 column from example1.csv in python doc_csvs/ folder
if 'Unnamed: 0' in example1.columns:
    example1 = example1.drop('Unnamed: 0', axis=1)
example1.to_csv(filePaths[-4])




# OUTPUT
#    patient_id                 time  inpatient  creatinine  aki
# 4       19845  2020-05-08 00:02:54      False        0.76    0
#                            time  inpatient  creatinine  aki
# patient_id                                                 
# 12732       2020-02-23 17:42:42      False        1.42    0
#    patient_id  inpatient                 time  creatinine
# 0       12732      False  2020-02-23 23:42:42        1.06
#    patient_id   age  female  black  inpatient                 time  creatinine
# 0       12732  64.5    True   True      False  2020-02-23 23:42:42        1.45
#                            time  inpatient  creatinine  min_creat48  \
# patient_id                                                            
# 12732       2020-02-22 17:42:42      False        1.05         1.05   

#             min_creat168  aki  
# patient_id                     
# 12732               1.05    0  
#                            time   age  female  black  inpatient  creatinine  \
# patient_id                                                                    
# 12732       2020-02-22 11:42:42  64.5    True   True      False        1.62   

#             baseline_creat  aki  
# patient_id                       
# 12732             0.930077    0  
#                            TIME   AGE   SEX  RACE  INPATIENT  CREATININE  aki
# PAT_MRN_ID                                                                   
# 12732       2020-02-22 11:42:42  64.5  True  True      False        1.62    0
#                            time  inpatient  creatinine  aki
# patient_id                                                 
# 12732       2020-02-24 23:42:42      False        1.61    1
#                            time  inpatient  creatinine  baseline_creat  aki
# patient_id                                                                 
# 12732       2020-02-22 23:42:42      False        1.26             NaN    0
#                            time   age  female  black  inpatient  creatinine  \
# patient_id                                                                    
# 12732       2020-02-23 23:42:42  64.5    True   True      False        1.45   

#             baseline_creat  aki  
# patient_id                       
# 12732             0.930077    0  
# Remove black variable


# Keeping a running tally of the modifications to the documentation (rst files, namely)
# which are built into the readthedocs.io 

# Minor modifications to Introduction & Installation ReStructured Text files, but the real changes are in GettingStarted.rst

# How are we to remove the black variable systematically; from the documentation strings as well as the dataframes?

