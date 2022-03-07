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


# Step 0: Merge datasets

# Combine outcomes with definition dataframe
comb = pDF1.merge(outcomes) # Combine outcomes with definition dataframe
print(comb.columns) # Resulting shape is 718220 x 12
print('INITIAL COMBINED DATAFRAME: {}'.format(comb.shape))

# Step 1: Convert definitions to boolean T/F
for defin in AKIdefinitions:
    comb[defin] = comb[defin].astype('bool')
    
# Step 2: Convert dataframe to one line per patient 
olpp = comb.loc[comb.groupby("patient_id")['creatinine'].idxmax()] # OLPP
print('ONE LINE PER PATIENT: {}'.format(olpp.shape)) # 40106 x 12
olpp.head()

printDescriptiveStatistics(dataFRAME = olpp,
                           yTRUE = "death", yPRED = "RMW")

# HAS AKI vs
# HAS Kidney Dysfunction
o0 = 'death'
o1 = 'creatRise'
o2 = 'creatRisefromAdmit'
o3 = 'creatRisexPCTyTIME'

           | HAS Kidney dysf |
           |   N   |  Y  | 
|HAS   | N | 32837 | 477 |
    AKI| Y | 6102  | 690 | 

So, prob(kidney dysf) is:

= 
First, 32837 + 477 + 6102 + 690 = 40106 patients

Given that a person is flagged as having AKI: 
the prob(death) is:
(690 / (690 + 6102))