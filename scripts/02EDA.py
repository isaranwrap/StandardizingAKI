## 二零二二年二月四号
# 星期五  |  旭谙深
# PI: Dr. F Perry Wilson

# Imports
import os
import re
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt 
from sklearn.metrics import confusion_matrix, roc_auc_score


# Parameters
dataFolder = r"C:\AKIFlagger\output"
dataPath = os.path.join(dataFolder, "flaggerOutput.csv")
outPath  = os.path.join(dataFolder, "confusionMatrices.txt")

creatinineCOLNAME = "creatinine"
timeCOLNAME = "time"
patient_idCOLNAME = "patient_id"
AKIdefinitions = ["RMW", "HBT", "BCI"]


xSTART = 0.05
xEND = 0.5
xN = 10  # # # # # # #COME BACK TO THIS SCRIPT l8r 

ySTART = 24
yEND = 180
yN = 14

minCOLS_startINDX = 10

x = np.linspace(xSTART, xEND, xN) # len(x): 10
y = np.linspace(ySTART, yEND, yN) # len(y): 14

xPCT_INCREASE =  [round(element, ndigits=2) for element in x]; x 
INyTIME = ['{}hours'.format(i) for i in y]

# Parameters END here


# Read in data
pDF1 = pd.read_csv(dataPath)
pDF1['time'] = pd.to_datetime(pDF1.time)
pDF1['age'] = pDF1.age.round(decimals=0)
pDF1 = pDF1.drop('race', axis = 1)


groupbyOBJECT = pDF1.loc[:, [creatinineCOLNAME, timeCOLNAME, patient_idCOLNAME]].set_index([timeCOLNAME]).groupby(patient_idCOLNAME, as_index = False)
minCREAT_MATRIX = np.array([groupbyOBJECT.rolling(pd.Timedelta(TIME)).min() for TIME in INyTIME]) # Matrix housing minimum creatinine in past y hours 
print(minCREAT_MATRIX.shape) # 14 x 718220 x 1 (small technicality: slice the matrix to only grab the col by rows after transposing)
qDF_2 = pd.DataFrame(data = minCREAT_MATRIX.T[0,:,:], # Create a new dataframe of the minimum creatinine time series
                        columns = ['mincreat{}'.format(int(i)) for i in y])
minCREAT = pd.concat([pDF1, qDF_2], axis = 1)

for indxY, creatinineCOLUMN in enumerate(minCREAT.columns[minCOLS_startINDX:minCOLS_startINDX+2]):
    print(indxY, creatinineCOLUMN)
    for indxX, pct_inc in enumerate(xPCT_INCREASE):
        print(indxX, pct_inc)
        print("{}% increase in less than {} hours".format(pct_inc*100, creatinineCOLUMN[8:]))
        minCREAT['x{}xPCT_INC__INyTIME{}y'.format(pct_inc, creatinineCOLUMN[8:])] = minCREAT.creatinine * (1 + pct_inc) >= minCREAT.loc[:, "creatinine"]

for definition in AKIdefinitions:
    minCREAT[definition] = minCREAT[definition].astype("bool")


        
dataOUT = np.zeros((10, 14, 5, 3))
# dataOUT[indxX, indxY, , 0] <- RMW
# dataOUT[indxX, indxY, , 1] <- HBT
# dataOUT[indxX, indxY, , 2] <- BCI

# Start calcuting confusion matrices:

# FOR RMW
yTRUE = minCREAT.groupby('patient_id', as_index = True)['x0.25xPCT_INC__INyTIMEmincreat48y'].any() # ANY TRUE 
yPRED = minCREAT.groupby('patient_id', as_index = True).RMW_bool.any() 

yTRUE = yTRUE.set_index('patient_id')
yPRED = yPRED.set_index('patient_id')

confusion_matrix(yTRUE, yPRED).ravel()

saveOutput = True
if saveOutput:
    minCREAT.to_csv(fullDFPath) # 164 columns

# Start calcuting confusion matrices
yTRUE = minCREAT["x{}xPCT_INC__INyTIME{}y".format(pct_inc, creatinineCOLUMN)] # GROUND TRUTH; i.e. observed rise in creatinine

with open(outPath, "w") as fileOBJECT:
    fileOBJECT.writelines(str(confusion_matrix(yTRUE, yPRED)[0, 0])) # TRUE  POSITIVE
    fileOBJECT.writelines(confusion_matrix(yTRUE, yPRED)[0, 1]) # FALSE NEGATIVE
    fileOBJECT.writelines(confusion_matrix(yTRUE, yPRED)[1, 0]) # FALSE POSITIVE
    fileOBJECT.writelines(confusion_matrix(yTRUE, yPRED)[1, 1]) # TRUE  POSITIVE
confusion_matrix(yTRUE, yPRED)


def predictCreatinineRise(dataframe, x_percent_increase = 0.25, in_y_time = '36hours',
                        xSTART = 0.05, xEND = 0.5, xN = 10,
                        ySTART = 24, yEND = 180, yN = 14,
                        saveOutput = False, minCOLS_startINDX = 10,
                        saveOutPath = fullDFPath):
    ''' Use a prediction framework to estimate whether there will be a future rise in creatinine.
    
    Args:
        dataframe (pd.DataFrame): The dataframe containing the patient_id, creatinine and AKI definitions.
        x (numpy float array): the array of percent increases you would like to calculate over.
        y (list of strings): a list of the timeframes you would like to find the percent increase over.
          


    '''

    creatinineCOLNAME = "creatinine"
    timeCOLNAME = "time"
    patient_idCOLNAME = "patient_id"
    
    xSTART = 0.05
    xEND = 0.5
    xN = 10

    ySTART = 24
    yEND = 180
    yN = 14

    x = np.linspace(xSTART, xEND, xN)
    y = np.linspace(ySTART, yEND, yN)
    
    xPCT_INCREASE = x
    INyTIME = ['{}hours'.format(i) for i in y]


    groupbyOBJECT = pDF1.loc[:, ["creatinine", "time", "patient_id"]].set_index(['time']).groupby("patient_id", as_index = False)
    minCREAT_MATRIX = np.array([groupbyOBJECT.rolling(pd.Timedelta(TIME)).min() for TIME in INyTIME]) # Matrix housing minimum creatinine in past y hours 
    print(minCREAT_MATRIX.shape) # 14 x 718220 x 1 (small technicality: slice the matrix to only grab the col by rows after transposing)
    qDF2 = pd.DataFrame(data = minCREAT_MATRIX.T[0,:,:], # Create a new dataframe of the minimum creatinine time series
                        columns = ['mincreat{}'.format(int(i)) for i in y])
    
    minCREAT = pd.concat([pDF1, qDF2], axis = 1)
    return(minCREAT)
    


yTRUE = minCREAT.creatinine > minCREAT.loc[:, 'mincreat{}'.format(int(24))]# GROUND TRUTH; i.e. observed rise in creatinine
yPRED = minCREAT.RMW > 0 # PREDICTION; i.e. AKI definition


# Rolling minimum, first: 
gb = df.loc[:, [self.creatinine]].reset_index(self.patient_id).groupby(self.patient_id, sort=False) # Groupby on patients
max_creat48 = gb.rolling(self.cond1time).max().reindex(df.index)[self.creatinine] # Rolling 48hr minimum creatinine time series 
min_creat7d = gb.rolling(self.cond2time).min().reindex(df.index)[self.creatinine] # Rolling 7day minimum creatinine time series

#
with open(outPath, "w") as fileOBJECT:
    fileOBJECT.writelines()


tmp = minCREAT.groupby(patient_idCOLNAME).get_group("MR1004729")


## IMPORTANT 
minCREAT.loc[~pDF1.inpatient].patient_id.nunique()



## Messy code down here:
# X & Y 
# np.linspace(0.05, 0.5, 10)
# np.linspace(1, 10, 10) * 0.05
# ['{}hours'.format(i) for i in np.linspace(24, 180, 14)] # 12*6 = 72; 12*9 = 108 -> (6+9) - 2 + 1 
# ['{}hours'.format(i) for i in np.linspace(2, 15, 14)*12] # EQUIVALENTLY a

# Perry:
# sns.heatmap(tmp.iloc[:, minCOLS_startINDX:])

#sns.heatmap(minCREAT.iloc[:, minCOLS_startINDX:].corr());


