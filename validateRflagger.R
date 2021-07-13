library(data.table)
library(tidyverse)
library(zoo)
source('C:/Users/ishan/Desktop/Projects/StandardizeAKI/StandardizingAKI.R')

# Read in data frames
dt <- fread("H:/Data/Standardized AKI definition/dataset/flagger/covid-dataset.csv")
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

# Subset columns
df <- dt[1:10000, .(patient_id, inpatient, creatinine, time, age, sex, race)]
head(df)

runtimeA <- system.time(
  outA <- returnAKIpatients(df)
)

runtimeB <- system.time(
  outB <- returnAKIpatients(df, padding = as.difftime(4, units='hours'))
)

runtimeC <- system.time(
  outC <- returnAKIpatients(df, HB_trumping = T)
)

runtimeD <- system.time(
  outD <- returnAKIpatients(df, HB_trumping = T, padding = as.difftime(4, units='hours'))
)

runtimeE <- system.time(
  outE <- returnAKIpatients(df, HB_trumping = T, eGFR_impute = T)
)

runtimeF <- system.time(
  outF <- returnAKIpatients(df, HB_trumping = T, eGFR_impute = T, padding = as.difftime(4, units='hours'))
)


tmp <- merge(pyA, outA, by = c("patient_id", "time"), all.y = TRUE)
#tmp <- subset(merge(pyA, outA, by = c("patient_id", "time"), all.y = TRUE), is.na(SPID.x) == TRUE)

tmp <- out %>% select(patient_id, time, creatinine, running_aki_stage, min_creat48, min_creat7d, aki)

mismatch <- which(tmp[, aki] != tmp[, running_aki_stage])

outHB <- returnAKIpatients(dt, padding = as.difftime(4, units = 'hours'), add_baseline_creat = TRUE, HB_trumping = TRUE)

#write.csv(outHB, 'H:/Data/Standardized AKI definition/dataset/covid-2-3-2021-rflagger.csv')

# OLD -- fixed by specifying time zone -- keeping in case future problem arises
print(mismatch) # Mismatch indices --> These only mismatch if you don't specify a timezone while converting time/admission
# 283278  445843  461098  619641  627817  627840  627863  755286  755307  834181 1023461 1023587 1023713 1023839
# 1023965 1024091 1024217 1183471 1183566 1218258 1292896 1292958 1431266 1431350

## WOW THE FLAGGER IS ACCOUNTING FOR DAYLIGHT SAVINGS
time2 <- tmp[283278, time]
time1 <- tmp[283276, time]
print(as.difftime(time2 - time1))


## Check mismatch
tmp <- df[df$patient_id == 'MR1000347']
tmpo <- returnAKIpatients(tmp, HB_trumping = T, add_baseline_creat = T, add_imputed_admission = T)

for (admn in unique(tmpo$imputed_admission)) {
  print(as.POSIXct(admn, tz = 'GMT', origin = '1970-01-01'))
  print(class(admn))
  print(typeof(admn))

  c1 <- (as.POSIXct(admn, tz = 'GMT', origin = '1970-01-01') - as.difftime(365, units = 'days')) <= tmpo$time
  c2 <- (as.POSIXct(admn, tz = 'GMT', origin = '1970-01-01') - as.difftime(7, units = 'days')) >= tmpo$time
  c3 <- !tmpo$inpatient
  c4 <- tmpo$imputed_admission == as.POSIXct(admn, tz = 'GMT', origin = '1970-01-01')

  tmpo[c4, baseline_creat := tmpo[, median(as.numeric(.SD[c1 & c2 & c3])), .SDcols = 'creatinine']]

}


## Dummy functions
returnBaselineCreat <- function(dt) {
  c1 <- (as.POSIXct(dt$imputed_admission[1], tz = 'GMT', origin = '1970-01-01') - as.difftime(365, units = 'days')) <= dt$time
  c2 <- (as.POSIXct(dt$imputed_admission[1], tz = 'GMT', origin = '1970-01-01') - as.difftime(7, units = 'days')) >= dt$time
  c3 <- !dt$inpatient

  dt[c1 & c2 & c3]

  return(baseline_creat)
}

# This one works to get baseline creatinine from a SINGLE patient dataframe; I just groupby patient_id & run this
returnBaselineCreat <- function(dataframe) {
  for (admn in unique(dataframe$imputed_admission)) {

    c1 <- (as.POSIXct(admn, tz = 'GMT', origin = '1970-01-01') - as.difftime(365, units = 'days')) <= dataframe$time
    c2 <- (as.POSIXct(admn, tz = 'GMT', origin = '1970-01-01') - as.difftime(7, units = 'days')) >= dataframe$time
    c3 <- !dataframe$inpatient
    c4 <- dataframe$imputed_admission == as.POSIXct(admn, tz = 'GMT', origin = '1970-01-01')

    setDT(dataframe)[c4, baseline_creat := dataframe[, median(as.numeric(as.character(unlist(.SD[c1 & c2 & c3])))), .SDcols = 'creatinine']]
  }
  return(dataframe$baseline_creat)
}

dfo[, baseline_creat := returnBaselineCreat(c(unique(.SD))), by = patient_id]

tmp <- dfo[dfo$patient_id == 'MR1005023']


