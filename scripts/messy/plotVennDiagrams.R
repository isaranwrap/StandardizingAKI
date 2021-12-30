# Imports
library(data.table)
library(eulerr)
library(tidyverse)


# Parameters
folderPath <- file.path("C:", "AKIFlagger") # file.path("H:", "AKIFlagger")
dataPath <- "output/flaggerOutput.csv"
definitions <- c("RMW", "HBT", "BCI")


# Set file systems in order
setwd(folderPath)


# Read in data
flaggerOutput <- data.table::fread(dataPath)#, nrows=10000)
setDT(flaggerOutput)

stage <- 1
# User-defined functions
plotVennDiagrams <- function(dataframe, stage = 1) {
  dataframe <- dataframe %>% mutate(defsum = 0)
  dataframe <- dataframe %>% mutate(defsum = ifelse(RMW > 0 & HBT > 0 & BCI > 0, 3, ifelse(RMW > 0 & BCI > 0 |
                                                                                             RMW > 0 & HBT > 0 |
                                                                                             BCI > 0 & HBT > 0, 2,
                                                                                           ifelse(RMW > 0 | BCI > 0 | HBT > 0, 1,0))))
  noAKI <- dataframe %>% filter(defsum==0)
  dataframe <- dataframe %>% filter(defsum != 0)
  dataframe <- dataframe %>% group_by(patient_id) %>% top_n(1, defsum)
  dataframe <- dataframe %>% filter(duplicated(patient_id) == FALSE)


  df.RMW <- dataframe %>% filter(RMW > stage - 1 & HBT == 0 & BCI == 0)
  df.HBT <- dataframe %>% filter(HBT > stage - 1 & RMW == 0 & BCI == 0)
  df.BCI <- dataframe %>% filter(BCI > stage - 1 & RMW == 0 & HBT == 0)

  df.RMW_HBT <- dataframe %>% filter(RMW > (stage - 1) & HBT > (stage - 1) & RMW == 0)
  df.RMW_BCI <- dataframe %>% filter(RMW > (stage - 1) & BCI > (stage - 1) & HBT == 0)
  df.HBT_BCI <- dataframe %>% filter(HBT > (stage - 1) & BCI > (stage - 1) & RMW == 0)
  df.RMW_HBT_BCI <- dataframe %>% filter(RMW > (stage - 1) & HBT > (stage - 1) & BCI > (stage - 1))

  fit <- eulerr::euler(c("RMW" = nrow(df.RMW), "HBT" = nrow(df.HBT), "BCI" = nrow(df.BCI),
                         "RMW&HBT" = nrow(df.RMW_HBT), "HBT&BCI" = nrow(df.HBT_BCI), "RMW&BCI" = nrow(df.RMW_BCI), "RMW&HBT&BCI" = nrow(df.RMW_HBT_BCI)), shape = 'ellipse')
  return(fit)
}

fit1 <- plotVennDiagrams(flaggerOutput, stage = 1)
fit2 <- plotVennDiagrams(flaggerOutput, stage = 2)
fit3 <- plotVennDiagrams(flaggerOutput, stage = 3)

plot(fit1, quantities = T)

# Old plotting func:
# Imports
# library(eulerr)
#
# dataPath <- file.path("/Users", "Ishan", "Desktop", "toydata")
# filePath <- file.path(dataPath, "flaggerOutput.csv")
# flaggerOutput <- fread(filePath)
#
# patRMW <- unique(flaggerOutput[flaggerOutput$RMW > 0]$patient_id)
# patHBT <- unique(flaggerOutput[flaggerOutput$HBT > 0]$patient_id)
# patBCI <- unique(flaggerOutput[flaggerOutput$BCI > 0]$patient_id)
#
# length(patHBT)

