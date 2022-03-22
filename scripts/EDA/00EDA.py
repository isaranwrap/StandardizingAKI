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
outPath  = os.path.join(dataFolder, "confusionMatrices.txt")
fullDFPath = os.path.join(dataFolder, "predictionTimeSeries.csv")
###pd.read_csv(fullDFPath)
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

minCOLS_startINDX = 10
numBINS = 100

x = np.linspace(xSTART, xEND, xN) # len(x): 10
y = np.linspace(ySTART, yEND, yN) # len(y): 14
# Parameters END

# Read in data
pDF1 = pd.read_csv(dataPath)
pDF1['time'] = pd.to_datetime(pDF1.time)
pDF1['age'] = pDF1.age.round(decimals=0)
qDF2 = pDF1.copy()

# Q: How many AKI rows (diff. from AKI events) occur for each patient?
# ANS: pDF1.groupby(patient_idCOLNAME)[AKIdefinitions[0]].agg(lambda aki_flag: (aki_flag>0).sum())

# Q: How many patients have outpatient creatinine measurements (i.e. PRIOR creatinines)?
# ANS: pDF1.loc[~pDF1.inpatient].patient_id.nunique()
# 22819/40106

# Q: How many patients are there who have NO inpatient measurements (i.e. are all patients hospitalized?)
# pDF1['outpatient'] = ~pDF1.inpatient
# pDF1.groupby('patient_id').outpatient.all().sum() # 0 
# ANS: 0, yes.


# Add in the admissions column 

# Admission col definition: First timestamp where THIS occurs:
# 2 consecutive inpatient creatinine measurements <= 72 hours apart

flagger = AKIFlagger(padding = '4hours', HB_trumping = True, add_admission_col = True)
qDF2 = flagger.returnAKIpatients(qDF2)
qDF2 = qDF2.reset_index()
qDF2 = qDF2.set_index("time")

qDF2['creat_atAKI'] = qDF2[qDF2[AKIdefinitions[0]] > 0].creatinine
qDF2['time_atAKI'] = qDF2[qDF2[AKIdefinitions[0]] > 0].time

selectionINDEX = qDF2.loc[qDF2[AKIdefinitions[0]].astype('bool')].index

TIME = "24hours"
qDF2.loc[:, 'mincreat24'] = qDF2.groupby(patient_idCOLNAME)['creatinine'].rolling(pd.Timedelta(TIME)).min()


# LOOKING at INDIVIDUAL patients who have been flagged by AKI:
tmp = qDF2.groupby(patient_idCOLNAME).get_group("MR1004729")
tmp.head()

tmp = qDF2.groupby(patient_idCOLNAME).get_group("MR1004999")
tmp.head()

tmp = qDF2.groupby(patient_idCOLNAME).get_group("MR1005023")
tmp.head()

# NEW DF, boolean DEFINITIONS
pDF2 = qDF2.copy()
pDF2['RMW'] = qDF2.RMW.astype('bool')

# Continue to 01EDA.py

# Plot histogram
fig, ax = plt.subplots(figsize=(14, 10))
sns.histplot(qDF2.creatinine, ax = ax, bins = numBINS, kde = True)
sns.histplot(qDF2.creat_atAKI, ax = ax, bins = numBINS, kde = True, color = "orange")

# Plot normalized density
fig, ax = plt.subplots(figsize=(14, 10))
sns.distplot(qDF2.creatinine, bins = numBINS, kde = True)
sns.distplot(qDF2.creat_atAKI, bins = numBINS, kde = True, color = "orange")


# Plotting function
def plotPatientCreatinineTrajectory(dataframe, patient_id = "MR1004999"):
    patientOfINTEREST = dataframe.groupby(patient_idCOLNAME).get_group(patient_id) # Global var
    print(list(patientOfINTEREST.creatinine))
    print(list(patientOfINTEREST.time))
    
    plt.figure(figsize=(14,10))
    g = plt.plot(patientOfINTEREST.time, patientOfINTEREST.creatinine)
    locs, labels = plt.xticks()
    plt.setp(labels, rotation = 30)
plotPatientCreatinineTrajectory(tmp)

## Added admission column, CTS @ admission; found 3 individuals with AKI
## 

## Wrote plotting functions for creatinine trajectory & histograms of creatinines
##