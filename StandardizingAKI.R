# Import libraries
library(data.table)
library(tidyverse)
library(zoo)

# User-defined functions
addRollingWindowAKI <- function(dataframe, window1=as.difftime(2, units='days'), window2=as.difftime(7, units='days'),
                                add_min_creat = FALSE) {

  df <- dataframe %>% group_by(mrn) %>%
    mutate(
      # Find the rolling minimum creats for both rolling windows
      min_creat48 = sapply(time, function(x) min(creat[between(time, x - window1, x)])), # Find minimum creatinine in the past 2 days
      min_creat7d = sapply(time, function(x) min(creat[between(time, x - window2, x)])), # Find minimum creatinine in the past 7 days

      condition1 = creat >= min_creat48 + 0.3, # Check if the creat jumps by 0.3; aka KDIGO criterion 1
      condition2 = round(creat, digits=4) >= round(1.5*min_creat7d, digits=4), # Check if the creat jumps by 50%; aka KDIGO criterion 2

      stage1 = as.integer(condition1 | condition2), # Stage 1 AKI is either 0.3 OR 50% jump
      stage2 = as.integer(creat >= 2*min_creat7d), # Check if creat doubles; aka KDIGO Stage 2 AKI
      stage3 = as.integer(creat >= 3*min_creat7d), # Check if creat triples; aka KDIGO Stage 3 AKI
      rw = stage1 + stage2 + stage3, # The resulting rw column; ultimate output we want added in
    )
  if (add_min_creat) return(df %>% select(-condition1, -condition2, -stage1, -stage2, -stage3))
  return(df %>% select(-min_creat7d, -min_creat48, -condition1, -condition2, -stage1, -stage2, -stage3))
}

addBackCalcAKI <- function(dataframe, lookforward=as.difftime(7, units='days')) {
  df <- dataframe
  # Take the MEDIAN OUTPATIENT creatinine values from 365 to 7 days prior to admission
  df[, baseline_creat := .SD[time >= admission - as.difftime(365, units='days') & time <= admission - as.difftime(7, units='days') & inpatient == F, round(median(creat), 4)], by = mrn]

  # Only include baseline creatinine values from 6 hours prior to admission to 7 days after admission
  df[time <= admission - as.difftime(6, units='hours') & time >= admission + lookforward, baseline_creat := NA]

  #Add AKI stages
  df[, stage1 := (creat >= round(1.5 * baseline_creat, digits=2))] # Stage 1 is only the 50% increase now
  df[, stage2 := (creat >= 2 * baseline_creat)] # Stage 2 is a doubling of creatinine
  df[, stage3 := (creat >= 3 * baseline_creat)] # Stage 3 is a tripling of creatinine
  df[, bc := stage1 + stage2 + stage3] # The resulting bc column; ultimate output we care about
  df[is.na(bc), bc := 0] # Replace NAs with 0; i.e. no AKI if back-calculation method does not apply
  return(df %>% select(-baseline_creat, -stage1, -stage2, -stage3))
}

# Read in data frame
dt <- fread('~/Desktop/toy.csv')#[1:1000] #Read in dataframe, grab first thousand rows
dt <- subset(dt, select=-V1) # Drop the redundant index

# Convert time & admission columns to POSIXct format
dt <- transform(dt, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S'),
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S'))
sapply(dt, class) # mrn, enc -> int; inpatient -> bool; admission, time -> POSIXct; creat -> numeric


# Add AKI
aki <- addRollingWindowAKI(addBackCalcAKI(dt))

# Check output against Python version
py <- fread('~/Desktop/out.csv')
# Convert time & admission columns to POSIXct format
py <- transform(py, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S'),
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S'))
sapply(py, class) # mrn, enc -> int; inpatient -> bool; admission, time -> POSIXct; creat -> numeric

# Compare rw vals - 100% match (Oct. 11, 2020)
table(aki$rw)
table(py$rw)

# Compare back-calc vals - 100% match (Oct. 12, 2020)
table(aki$bc)
table(py$bc)

# Check the mismatch  (if any, None as of now)
comb <- merge(py, aki, by=c('mrn','time'))
mismatch <- which(comb$bc.x != comb$bc.y)
View(comb[mismatch])
View(comb)

View(dt)
View(addBackCalcAKI(dt))
