## 二零二二年二月十五号
# 星期三 |  旭谙深
# PI: Dr. F Perry Wilson

# Imports
import os
import re
from unicodedata import decimal
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt 
from sklearn.metrics import confusion_matrix, roc_auc_score


# Parameters
dataFolder = r"C:\AKIFlagger\output"
outcomesPath = os.path.join(dataFolder, "flaggerOutcomes.csv")
definitnPath = os.path.join(dataFolder, "flaggerOutput.csv")

creatinineCOLNAME = "creatinine"
timeCOLNAME = "time"
patient_idCOLNAME = "patient_id"
AKIdefinitions = ["RMW", "HBT", "BCI"]

minCOLS_startINDX = 10

xSTART = 0.05
xEND = 5
xN = 100

ySTART = 24
yEND = 240
yN = 19

x = np.linspace(xSTART, xEND, xN) # len(x): 10
y = np.linspace(ySTART, yEND, yN) # len(y): 14

xPCT_INCREASE =  [round(element, ndigits=2) for element in x]; x 
INyTIME = ['{}hours'.format(i) for i in y]

# Parameters END here

# User-defined functions
def printDescriptiveStatistics(definitionOfInterest = "RMW", dataFRAME = None,
                               yTRUE = None, yPRED = None):
    ''' 
    For a given definition & percent increase, find the confusion matrix (& print corresponding descriptive statistics)
    Each of these. 
    '''

    #yTRUE = dataFRAME.outcome
    #yPRED = dataFRAME[AKIdefinitions[AKIdefinitions.index(definitionOfInterest)]]
    yTRUE = dataFRAME[yTRUE]
    yPRED = dataFRAME[yPRED]
    
    TN, FP, FN, TP = confusion_matrix(yTRUE, yPRED).ravel()
    AUC = roc_auc_score(yTRUE, yPRED)

    SENS = TP / (TP + FN)
    SPEC = TN / (TN + FP)
    PREC = TP / (TP + FP)
    F1Sc = 2*TP / (2*TP + (FP+FN))

    PPV = TP / (TP + FP)
    NPV = TN / (TN + FN)

    STATS = np.array([SENS, SPEC, PREC, F1Sc, PPV, NPV, AUC])

    print('''
    SENS: {}
    SPEC: {}
    PREC: {}
    F1 score: {}

    PPV: {}
    NPV: {}

    AUC: {}

    '''.format(*np.round(STATS, decimals = 3)))
    print("TN: {}, FP: {}. FN: {}, TP: {}".format(TN, FP, FN, TP), " <- CM raveled")

    return(confusion_matrix(yTRUE, yPRED))



# Read in data
definitions = pd.read_csv(definitnPath)
outcomes = pd.read_csv(outcomesPath)

combined = definitions.merge(outcomes) # Merge data 
comb = combined.loc[combined.groupby("patient_id")['creatinine'].idxmax()] # OLPP

# Any case of AKI during hospitalization
comb['RMW'] = combined.groupby("patient_id")["RMW"].apply(lambda x: np.any(x)).values
comb['HBT'] = combined.groupby("patient_id")["HBT"].apply(lambda x: np.any(x)).values
comb['BCI'] = combined.groupby("patient_id")["BCI"].apply(lambda x: np.any(x)).values

yTRUE = comb['death']
yPRED = comb['RMW']

for definition in AKIdefinitions:
    print("{}  DEATH: ".format(definition))
    printDescriptiveStatistics(dataFRAME= comb,
                           yTRUE = "death", yPRED = definition)
    print("\n{}  DIALYSIS: ".format(definition))
    printDescriptiveStatistics(dataFRAME= comb,
                           yTRUE = "dialysis", yPRED = definition)
    print("\n\n")



# Convert definitions to type boolean
for definition in AKIdefinitions:
    pDF1[definition] = pDF1[definition].astype('bool')


# Add admission column
f = AKIFlagger(padding = '4hours', HB_trumping = True, add_admission_col = True) 
qDF2 = f.returnAKIpatients(qDF2) # Run the flagger on qDF2 to get admission column
qDF2 = qDF2.rename(columns = {"imputed_admission": "admission"})
qDF2 = qDF2.drop(["race", "aki"], axis = 1) # HBT is aki; 718220 x 10
qDF2 = qDF2.reset_index()


# Find creatinine at admission
qDF2["creat_atADMISSION"] = qDF2.loc[qDF2.time == qDF2.admission].creatinine 
qDF2["creat_atADMISSION"] = qDF2.creat_atADMISSION.ffill() # Forward-fill


# Find rows with maximum creatinine
maxCREAT = qDF2.loc[qDF2.groupby(patient_idCOLNAME)['creatinine'].idxmax()] # 40106 x 12


# Single confusion matrix:



yTRUE = maxCREAT.outcome3 
yPRED = maxCREAT[AKIdefinitions[0]] 

# confusionMatrix: doubling of creatinine (any timeframe)
TN, FP, FN, TP = confusion_matrix(yTRUE, yPRED).ravel()
AUC = roc_auc_score(yTRUE, yPRED)

SENS = TP / (TP + FN)
SPEC = TN / (TN + FP)
PREC = TP / (TP + FP)
F1Sc = 2*TP / (2*TP + (FP+FN))

PPV = TP / (TP + FP)
NPV = TN / (TN + FN)

STATS = np.array([SENS, SPEC, PREC, F1Sc, PPV, NPV, AUC])

# confusionMatrix: 5% increase in <= 52 hours 
TN, FP, FN, TP = confusion_matrix(maxCREAT.outcome2, maxCREAT.RMW).ravel() 
AUC = roc_auc_score(maxCREAT.outcome2, maxCREAT.RMW)
# where outcome2 ~ yTRUE
# where DEF ~ yPRED

SENS = TP / (TP + FN)
SPEC = TN / (TN + FP)
PREC = TP / (TP + FP)
F1Sc = 2*TP / (2*TP + (FP+FN))

dataOUT = np.zeros((len(x), len(y), 5, len(AKIdefinitions))) # 100 x 19 x 5 x 3


for indxX, x_percent_increase in enumerate(xPCT_INCREASE):
    print(indxX, 1 + x_percent_increase)

    for indxY, in_y_time in enumerate(INyTIME):
        print(indxY, pd.Timedelta(in_y_time))

        maxCREAT['outcome2.condition1'] = maxCREAT.creatinine >= (1+x_percent_increase)*maxCREAT.creat_atADMISSION
        maxCREAT['outcome2.condition2'] = (maxCREAT.time - maxCREAT.admission) <= pd.Timedelta(in_y_time)
        maxCREAT['outcome2'] = np.logical_and(maxCREAT['outcome2.condition1'], maxCREAT['outcome2.condition2'])

        dataOUT[indxX, indxY, :4, 0] = confusion_matrix(maxCREAT.outcome2, maxCREAT[AKIdefinitions[0]]).ravel()
        dataOUT[indxX, indxY, 4, 0] = roc_auc_score(maxCREAT.outcome2, maxCREAT[AKIdefinitions[0]])

        dataOUT[indxX, indxY, :4, 1] = confusion_matrix(maxCREAT.outcome2, maxCREAT[AKIdefinitions[1]]).ravel()
        dataOUT[indxX, indxY, 4, 1] = roc_auc_score(maxCREAT.outcome2, maxCREAT[AKIdefinitions[1]])

        dataOUT[indxX, indxY, :4, 2] = confusion_matrix(maxCREAT.outcome2, maxCREAT[AKIdefinitions[2]]).ravel()
        dataOUT[indxX, indxY, 4, 2] = roc_auc_score(maxCREAT.outcome2, maxCREAT[AKIdefinitions[2]])


dataOUT


def printDescriptiveStatistics(arr_like):
    print("Max val: {}".format(arr_like.max()))
    print("Min val: {}".format(arr_like.min()))

def plotColorPlot(arr_like):
    plt.figure(figsize=(10,18))
    plt.imshow(arr_like)
    plt.gca().invert_yaxis()
    plt.colorbar()
    plt.xlabel("")
        

plotColorPlot(dataOUT[:,:,-1,0])

# 0 ~ TN
# 1 ~ FP
# 2 ~ FN
# 3 ~ TP
# 4 ~ AUC




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


tmp = qDF2.groupby(patient_idCOLNAME).get_group("MR999273")



