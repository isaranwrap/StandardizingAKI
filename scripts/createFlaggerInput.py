# Imports
import os
import pandas as pd


# Parameters
inputFilePath =  r"H:\Data\Standardized AKI definition\dataset\flagger data 3-30-2021.csv"
baseFolder = os.path.join("C:", os.sep, "AKIFlagger")
outFolder = os.path.join(baseFolder, "output")
minimalInputoutPath = os.path.join(outFolder, "flaggerMinimalInput.csv")
demographicInputoutPath = os.path.join(outFolder, "flaggerDemographicInput.csv")

selectcolumnsInput = ["pat_mrn_id", "outpatient", "creatinine", "time", "death", "dialysis", "los", "age", "sex", "race"]
selectcolumnsMinimalOutput = ["patient_id", "inpatient", "creatinine", "time"]
selectcolumnsDemographicOutput = selectcolumnsMinimalOutput + ["age", "sex", "race"]

# Read in data
pFP1 = pd.read_csv(inputFilePath)


# Selet columns of interest 
pFP1 = pFP1.loc[:, selectcolumnsInput]


# Shape data
pFP1 = pFP1.rename(mapper = {"pat_mrn_id": "patient_id"},
            axis = 1)
pFP1['time'] = pd.to_datetime(pFP1.time)
pFP1['death'] = pFP1.death.astype("bool")
pFP1['dialysis'] = pFP1.dialysis.astype("bool")
pFP1['inpatient'] = ~pFP1.outpatient.astype("bool")

pFP1.loc[:, selectcolumnsMinimalOutput].to_csv(minimalInputoutPath, index = False)
pFP1.loc[:, selectcolumnsDemographicOutput].to_csv(demographicInputoutPath, index = False)