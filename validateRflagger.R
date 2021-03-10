library(data.table)
library(tidyverse)
library(zoo)
source('C:/Users/ishan/Desktop/Projects/StandardizeAKI/StandardizingAKI.R')

# Read in data frames
dt <- fread("H:/Data/Standardized AKI definition/dataset/covid aki flagger 2-3-2021.csv")
py <- fread("H:/Data/Standardized AKI definition/dataset/covid-flagger-imputedvals.csv")


# Convert time & admission columns to POSIXct format
dt <- transform(dt, time = as.POSIXct(time, format='%Y-%m-%dT%H:%M:%S', tz = 'GMT'),
                admission = as.POSIXct(admission, format='%Y-%m-%dT%H:%M:%S', tz = 'GMT'))
py <- transform(py, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S', tz = 'GMT'),
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S', tz = 'GMT'),
                imputed_admission = as.POSIXct(imputed_admission, format='%Y-%m-%d %H:%M:%S', tz = 'GMT'))

# Flagger expects inpatient, not outpatient
dt[, inpatient := !as.logical(dt[, outpatient])]

patient_id   <- 'pat_mrn_id'
inpatient    <- 'inpatient'
creatinine   <- 'creatinine'
time         <- 'time'

dt <- dt %>% rename('patient_id' = patient_id, 'inpatient' = inpatient, 'creatinine' = creatinine, 'time' = time)
head(dt)

# Subset columns
df <- dt[, .(patient_id, inpatient, creatinine, time)]

#runtime <- system.time(
#  out <- returnAKIpatients(df, padding = as.difftime(4, units='hours'))
#)
runtime <- system.time(
  outHB <- returnAKIpatients(df, HB_trumping = T, padding = as.difftime(4, units='hours'),
                             add_baseline_creat = T, add_imputed_admission = T)
)

comb <- merge(outHB, py, by = c('patient_id', 'time'))

mismatch <- comb[comb$aki.x != comb$aki.y]





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


