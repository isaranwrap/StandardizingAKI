## 二零二二年二月三号
# 星期四  |  旭谙深
# PI: Dr. F Perry Wilson

# Imports

import os
import re
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt 
from sklearn.metrics import confusion_matrix, roc_auc_score

#from akiFlagger import AKIFlagger


# Parameters
dataFolder = r"C:\AKIFlagger\output"
dataPath = os.path.join(dataFolder, "flaggerOutput.csv")
outPath  = os.path.join(dataFolder, "toSTATA.csv")
fullDFPath = os.path.join(dataFolder, "predictionTimeSeries.csv")

creatinineCOLNAME = "creatinine"
timeCOLNAME = "time"
patient_idCOLNAME = "patient_id"
AKIdefinitions = ["RMW", "HBT", "BCI"]


xSTART = 0.05
xEND = 5.0
xN = 100

ySTART = 12
yEND = 240
yN = 19

minCOLS_startINDX = 10
numBINS = 100

x = np.linspace(xSTART, xEND, xN) # len(x): 100
y = np.linspace(ySTART, yEND, yN) # len(y): 19

xPCT_INCREASE =  [round(element, ndigits=2) for element in x]; x 
INyTIME = ['{}hours'.format(i) for i in y]

# Parameters END

# Read in data
pDF1 = pd.read_csv(dataPath)
pDF1['time'] = pd.to_datetime(pDF1.time)
pDF1['age'] = pDF1.age.round(decimals=0)
pDF1 = pDF1.drop('race', axis = 1)
for definition in AKIdefinitions:
    pDF1[definition] = pDF1[definition].astype('bool')

qDF2 = pDF1.copy() # Create a copy of the data.. this is what we'll work with.

# Add admission column
f = AKIFlagger(padding = '4hours', HB_trumping = True, add_admission_col = True) 
qDF2 = f.returnAKIpatients(qDF2) # Run the flagger on qDF2 to get admission column
qDF2 = qDF2.rename(columns = {"imputed_admission": "admission"})
qDF2 = qDF2.reset_index()#.set_index("time")

# Find creatinine at admission
qDF2["creat_atADMISSION"] = qDF2.loc[qDF2.time == qDF2.admission].creatinine 
qDF2["creat_atADMISSION"] = qDF2.creat_atADMISSION.ffill() # Forward-fill


# Prediction framework:
yTRUE = qDF2.creatinine >= (1+0.5)*qDF2.creat_atADMISSION 
yTRUE = qDF2.creatinine <= qDF2.groupby("patient_id").creatinine.shift(-1)
yPRED = qDF2.RMW

## Outcome 1
qDF2["creatNext"] = qDF2.groupby("patient_id").creatinine.shift(-1)
qDF2["outcome1"] = qDF2.creatinine <= qDF2.creatNext
qDF2.loc[qDF2.creatNext.isnull(), "outcome1"] = None

toSTATA_selectCOLS = ["patient_id", "creatinine", "RMW", "HBT", "BCI", "creatNext", "outcome1"]
sDF2 = qDF2.loc[:, toSTATA_selectCOLS]
sDF2.to_csv(outPath) ## Send to Perry 二月四号 | 发给 Perry


#confusion_matrix(yTRUE, yPRED)

qDF2[::-1].groupby('patient_id', as_index = False).rolling(pd.Timedelta(INyTIME[0]))

tmp = qDF2.groupby(patient_idCOLNAME).get_group("MR1004729")



##### QUESTIONS #####

# Q: What columns do I have in my initial dataFRAME?

# pDF1.columns
# ANS:  ['patient_id', 'time', 'inpatient', 'creatinine', 'age', 'sex', 'race',
       # 'RMW', 'HBT', 'BCI']


# Q: What columns do I change during pre-processing?

# pDF1['time'] = pd.to_datetime(pDF1.time)
# pDF1['RMW'] = pDF1.RMW.astype('bool')
# pDF1['HBT'] = pDF1.HBT.astype('bool')
# pDF1['BCI'] = pDF1.BCI.astype('bool')
# pDF1 = pDF1.drop('race', axis = 1)
# ANS: I drop race (race is no longer relevant as of 2021) and convert time format
# ANS: & convert the definitions to BOOLEAN variables

# Q: How many timestamps are admission timestamps? 

# qDF2.loc[qDF2.index == qDF2.admission] 
# ANS: 79764 / 718220 = 11.1% (qDF2.shape)
# 
# 
# Q: 


## Create outcome1 to send to Perry; whereby checking if m_creat is + / 0 / - 
##

##
## Three more representative patients: MR1