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
