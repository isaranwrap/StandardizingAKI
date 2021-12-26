library("akiFlagger")
library("VennDiagram")

dataPath <- "~/Desktop/toydata/toy.txt"
inputDataFrame <- data.frame(read.csv(dataPath, sep = "\t"))
# aki <- returnAKIpatients(setDT(inputDataFrame))
#

dataFilePath <- file.path("/Users", "Ishan", "Desktop", "toydata")
toyDemographicFilePath <- file.path(dataFilePath, "05toy-demographic.csv")

toy <- fread(toyDemographicFilePath)
toy$time <- as.POSIXct(toy$time)

aki <- returnAKIpatients(toy, eGFR_impute = T)
flaggerOutput <- aki[,1:7]

flaggerOutput$BCI <- aki$aki

aki <- returnAKIpatients(toy, HB_trumping = T)

flaggerOutput$HBT <- aki$aki

aki <- returnAKIpatients(toy)

flaggerOutput$RMW <- aki$aki

patRMW <- unique(flaggerOutput[flaggerOutput$RMW > 0]$patient_id)
patHBT <- unique(flaggerOutput[flaggerOutput$HBT > 0]$patient_id)
patBCI <- unique(flaggerOutput[flaggerOutput$BCI > 0]$patient_id)
