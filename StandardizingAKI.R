# Import libraries
library(zoo)
library(tidyverse)
library(data.table)

# User-defined functions
returnAKIpatients <- function(dataframe, HB_trumping = FALSE, eGFR_impute = FALSE,
                              window1 = as.difftime(2, units='days'), window2 = as.difftime(7, units='days'),
                              add_min_creat = FALSE, add_baseline_creat = FALSE, padding = NULL) {
  patient_id <- encounter_id <- inpatient <- admission <- creatinine <- time <- NULL # Erase any variables in case duplicate variable names coexist
  df <- copy(dataframe) # Copy the input so it doesn't modify the data frame in place

  # Add padding to windows
  if (!is.null(padding)) {
    window1 <- window1 + padding
    window2 <- window2 + padding
  }
  
  # Rolling minimum creatinine values in the past 48 hours and 7 days, respectively
  df[, min_creat48 := sapply(.SD[, time], function(x) min(creatinine[between(.SD[, time], x - window1, x)])), by=patient_id]
  df[, min_creat7d := sapply(.SD[, time], function(x) min(creatinine[between(.SD[, time], x - window2, x)])), by=patient_id]

  # If HB_trumping is set to True, we want to add condition2, then do RM calculations, then do HB calculations, then add condition1 back in
  if (HB_trumping){
    # Baseline creatinine is defined as the median of the outpatient creatinine values from 365 to 7 days prior to admission
    df[, baseline_creat := .SD[time >= admission - as.difftime(365, units='days') &
                                 time <= admission - as.difftime(7, units='days') & inpatient == F,
                               round(median(creatinine), 4)], by = encounter_id]

    # Two different conditions for how stage 1 can be met (with two distinct rolling window periods)
    condition1 <- round(df[, creatinine], digits=4) >= round(df[, min_creat48] + 0.3, digits=4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    condition2 <- round(df[, creatinine], digits=4) >= round(1.5*df[, min_creat7d], digits=4) # Check if the creat increases by 50%; KDIGO criterion 2

    # Masks from admission to 2 & 7 days into the future, respectively
    mask_2d <- (df[, time] >= df[, admission]) & (df[, time] <= df[, admission] + as.difftime(2, units='days'))
    mask_7d <- (df[, time] >= df[, admission]) & (df[, time] <= df[, admission] + as.difftime(7, units='days'))
    bc_mask <- is.na(df[, baseline_creat]) # We don't want to capture null values
    mask <- !bc_mask & mask_7d

    # Rolling minimum definitions
    stage1 <- as.integer(condition2) # Note now that stage1 is just condition 2; re-insert condition1 after HB calculations
    stage2 <- as.integer(round(df[, creatinine], digits=4) >= round(2*df[, min_creat7d], digits=4))
    stage3 <- as.integer(round(df[, creatinine], digits=4) >= round(3*df[, min_creat7d], digits=4))
    df[, aki := stage1 + stage2 + stage3]

    # Historical baseline calculations
    condition1hb <- round(df[mask, creatinine], digits=4) >= round(df[mask, baseline_creat] + 0.3, digits=4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    condition2hb <- round(df[mask, creatinine], digits=4) >= round(1.5*df[mask, baseline_creat], digits=4)

    stage1hb <- as.integer(condition1hb | condition2hb)
    stage2hb <- as.integer(round(df[mask, creatinine], digits=4) >= round(2*df[mask, baseline_creat], digits=4))
    stage3hb <- as.integer(round(df[mask, creatinine], digits=4) >= round(3*df[mask, baseline_creat], digits=4))
    df[mask, aki := stage1hb + stage2hb + stage3hb]

    # Now, add the 0.3 bump rolling min condition back in
    mask_empty = df[,aki == 0]
    mask_rw = (!mask_2d & mask_empty) | bc_mask
    df[mask_rw, aki := condition1[mask_rw]]

    if (!add_baseline_creat) df <- df %>% select(-baseline_creat)
  } else {

    # If HB_trumping is False, just implement the rolling minimum definitions
    condition1 <- round(df[, creatinine], digits=4) >= round(df[, min_creat48] + 0.3, digits=4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    condition2 <- round(df[, creatinine], digits=4) >= round(1.5*df[, min_creat7d], digits=4) # Check if the creat increases by 50%; KDIGO criterion 2
    stage1 <- as.integer(condition1 | condition2)
    stage2 <- as.integer(round(df[, creatinine], digits=4) >= round(2*df[, min_creat7d], digits=4))
    stage3 <- as.integer(round(df[, creatinine], digits=4) >= round(3*df[, min_creat7d], digits=4))

    df[, aki := stage1 + stage2 + stage3]
  }
  if (!add_min_creat) df <- df %>% select(-min_creat48, -min_creat7d)
  return(df)
}

patient_id   <- 'mrn'
encounter_id <- 'enc' #optional
inpatient    <- 'inpatient'
admission    <- 'admission' #optional
creatinine   <- 'creat'
time         <- 'time'

# Read in data frame
dt <- fread('~/Desktop/toy.csv')#[1:1000] #Read in dataframe, grab first thousand rows
dt <- subset(dt, select=-V1) # Drop the redundant index

# Convert time & admission columns to POSIXct format - many ways to do this... here's one:
dt <- transform(dt, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S'),
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S'))

dt <- dt %>% rename('patient_id' = patient_id, 'encounter_id' = encounter_id, 'inpatient' = inpatient,
                    'creatinine' = creatinine, 'admission' = admission, 'time' = time)
head(dt)


#Here's another:
time_cols <- c('time', 'admission')
dt[, (time_cols) := lapply(.SD, as.POSIXct), .SDcols = time_cols]
sapply(dt, class) # mrn, enc -> int; inpatient -> bool; admission, time -> POSIXct; creat -> numeric


patient_id   <- 'mrn'
encounter_id <- 'enc' #optional
inpatient    <- 'inpatient'
admission    <- 'admission' #optional
creatinine   <- 'creat'
time         <- 'time'

dt <- dt %>% rename('patient_id' = patient_id, 'encounter_id' = encounter_id, 'inpatient' = inpatient,
                    'creatinine' = creatinine, 'admission' = admission, 'time' = time)
# Add AKI
aki <- returnAKIpatients(dt, HB_trumping = T)

# Check output against Python version
py <- fread('~/Desktop/out.csv')
# Convert time & admission columns to POSIXct format
py <- transform(py, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S'),
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S'))
sapply(py, class) # mrn, enc -> int; inpatient -> bool; admission, time -> POSIXct; creat -> numeric


