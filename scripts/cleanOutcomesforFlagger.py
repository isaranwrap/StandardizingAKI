# Imports
import pandas as pd


# Parameters
inputFilePath = r"H:\Data\Standardized AKI definition\dataset\flagger data 3-30-2021.csv"
outputFilePath = r"C:\AKIFlagger\output\flaggerOutcomes.csv"

selectcolumnsInput = ["pat_mrn_id", "outpatient", "creatinine", "time", "death", "dialysis", "los"]
selectcolumnsOutput = ["patient_id", "inpatient", "creatinine", "time", "death", "dialysis", "los"]


# Read in data
pFP1 = pd.read_csv(inputFilePath)
qFP2 = pd.read_csv(outputFilePath)


# Selet columns of interest 
pFP1 = pFP1.loc[:, selectcolumnsInput]


# Shape data
pFP1 = pFP1.rename(mapper = {"pat_mrn_id": "patient_id"},
            axis = 1)
pFP1['time'] = pd.to_datetime(pFP1.time)
pFP1['death'] = pFP1.death.astype("bool")
pFP1['dialysis'] = pFP1.dialysis.astype("bool")
pFP1['inpatient'] = ~pFP1.outpatient.astype("bool")
pFP1 = pFP1.loc[:, selectcolumnsOutput]


# Write out 
pFP1.to_csv(outputFilePath, index = False)

# Check correct output
#qFP2.head()