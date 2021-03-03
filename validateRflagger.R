library(data.table)
library(tidyverse)
source('C:/Users/ishan/Desktop/Projects/StandardizeAKI/StandardizingAKI.R')

patient_id   <- 'pat_mrn_id'
encounter_id <- 'pat_enc_csn_id' #optional
inpatient    <- 'inpatient'
admission    <- 'admission' #optional
creatinine   <- 'creatinine'
time         <- 'time'

# Read in data frame
dt <- fread("H:/Data/Standardized AKI definition/dataset/covid aki flagger 2-3-2021.csv")


# Convert time & admission columns to POSIXct format - many ways to do this... here's one:
dt <- transform(dt, time = as.POSIXct(time, format='%Y-%m-%dT%H:%M:%S', tz = 'GMT'),
                admission = as.POSIXct(admission, format='%Y-%m-%dT%H:%M:%S', tz = 'GMT'))
dt[, inpatient] = !as.logical(dt[, outpatient])

dt <- dt %>% rename('patient_id' = patient_id, 'encounter_id' = encounter_id, 'inpatient' = inpatient,
                    'creatinine' = creatinine, 'admission' = admission, 'time' = time)
head(dt)
runtime <- system.time(
  out <- returnAKIpatients(dt, padding = as.difftime(4, units='hours'), add_min_creat = T)
)

tmp <- out %>% select(patient_id, time, creatinine, running_aki_stage, min_creat48, min_creat7d, aki)

mismatch <- which(tmp[, aki] != tmp[, running_aki_stage])

outHB <- returnAKIpatients(dt, padding = as.difftime(4, units = 'hours'), add_baseline_creat = TRUE, HB_trumping = TRUE)

write.csv(outHB, 'H:/Data/Standardized AKI definition/dataset/covid-2-3-2021-rflagger.csv')

print(mismatch) # Mismatch indices --> These only mismatch if you don't specify a timezone while converting time/admission
# 283278  445843  461098  619641  627817  627840  627863  755286  755307  834181 1023461 1023587 1023713 1023839
# 1023965 1024091 1024217 1183471 1183566 1218258 1292896 1292958 1431266 1431350

## WOW THE FLAGGER IS ACCOUNTING FOR DAYLIGHT SAVINGS
time2 <- tmp[283278, time]
time1 <- tmp[283276, time]
print(as.difftime(time2 - time1))


