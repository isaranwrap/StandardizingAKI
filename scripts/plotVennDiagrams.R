# Imports
library(eulerr)

dataPath <- file.path("/Users", "Ishan", "Desktop", "toydata")
filePath <- file.path(dataPath, "flaggerOutput.csv")
flaggerOutput <- fread(filePath)

patRMW <- unique(flaggerOutput[flaggerOutput$RMW > 0]$patient_id)
patHBT <- unique(flaggerOutput[flaggerOutput$HBT > 0]$patient_id)
patBCI <- unique(flaggerOutput[flaggerOutput$BCI > 0]$patient_id)

length(patHBT)
