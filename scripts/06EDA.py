# Imports

import os
import re
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt 
from sklearn.metrics import confusion_matrix, roc_auc_score

import akiFlagger
from akiFlagger import AKIFlagger
print(akiFlagger.__version__)

# Parameters
dataFolder = r"C:\AKIFlagger\output"
dataPath = os.path.join(dataFolder, "flaggerOutput.csv")
outcomesPath = os.path.join(dataFolder, "flaggerOutcomes.csv")

creatinineCOLNAME = "creatinine"
timeCOLNAME = "time"
patient_idCOLNAME = "patient_id"
AKIdefinitions = ["RMW", "HBT", "BCI"]

xSTART = 0.05
xEND = 0.5
xN = 10

ySTART = 24
yEND = 180
yN = 14

x = np.linspace(xSTART, xEND, xN) # len(x): 10
y = np.linspace(ySTART, yEND, yN) # len(y): 14

xPCT_INCREASE =  [round(element, ndigits=2) for element in x]; x 
INyTIME = ['{}hours'.format(i) for i in y]

# Read in data
pDF1 = pd.read_csv(dataPath)
pDF1['time'] = pd.to_datetime(pDF1.time)
pDF1 = pDF1.drop('race', axis = 1)

outcomes = pd.read_csv(outcomesPath)
outcomes['time'] = pd.to_datetime(outcomes.time)