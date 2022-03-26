library(dplyr)
library(data.table)

dataIN <- data.table::fread("~/AKIFlagger/data/01test.csv")
#View(dataIN)

dataRMW <- returnAKIpatients(dataIN, RM_window = TRUE)
dataHBT <- returnAKIpatients(dataIN, HB_trumping = TRUE)
dataBCI <- returnAKIpatients(dataIN, eGFR_impute = TRUE)
