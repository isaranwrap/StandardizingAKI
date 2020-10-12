library(data.table)
library(tidyverse)
library(zoo)

# User-defined functions
addRollingWindowAKI <- function(dataframe, window1=as.difftime(2, units='days'), window2=as.difftime(7, units='days')) {
  #if (missing(window1)) window1 <- as.difftime(2, units='days')
  #if (missing(window2)) window2 <- as.difftime(7, units='days')
  df <- dataframe %>% group_by(mrn) %>%
    mutate(
      # Find the rolling minimum creats for both rolling windows
      min_creat48 = sapply(time, function(x) min(creat[between(time, x - window1, x)])), # Find minimum creatinine in the past 2 days
      min_creat7d = sapply(time, function(x) min(creat[between(time, x - window2, x)])), # Find minimum creatinine in the past 7 days
      
      condition1 = creat >= min_creat48 + 0.3, # Check if the creat jumps by 0.3; aka KDIGO criterion 1 
      condition2 = creat >= 1.5*min_creat7d, # Check if the creat jumps by 50%; aka KDIGO criterion 2
      
      stage1 = as.integer(condition1 | condition2), # Stage 1 AKI is either 0.3 OR 50% jump
      stage2 = as.integer(creat >= 2*min_creat7d), # Check if creat doubles; aka KDIGO Stage 2 AKI 
      stage3 = as.integer(creat >= 3*min_creat7d), # Check if creat triples; aka KDIGO Stage 3 AKI
      rw = stage1 + stage2 + stage3, # The resulting rw column; ultimate output we want added in
    )
  df %>% select(-min_creat7d, -min_creat48, -condition1, -condition2, -stage1, -stage2, -stage3)
}

addBackCalcAKI <- function(dataframe) {
  df <- dataframe %>% rowwise() %>%
    mutate(
      t365_7subset = between(time, admission - as.difftime(365, units = 'days'), admission - as.difftime(7, units = 'days')),
      ) %>% group_by(enc) %>%
    mutate(
      baseline_creatinine = round(median(creat[(!inpatient) & (t365_7subset)]), digits=2), 
      baseline_creat = na.locf(baseline_creatinine),
      stage1 = as.integer(creat >= 1.5*baseline_creat),
      stage2 = as.integer(creat >= 2*baseline_creat),
      stage3 = as.integer(creat >= 3*baseline_creat),
      bc = stage1 + stage2 + stage3,
      
      bc_na = is.na(baseline_creat)
      ) 
  df[df$bc_na, 'bc'] = 0
  df
  #df %>% select(-t365_7subset, -baseline_creat, -stage1, -stage2, -stage3, -bc_na)
}

# Read in data frame
dt <- fread('~/Desktop/toy.csv')#[1:1000] #Read in dataframe, grab first thousand rows
dt <- subset(dt, select=-V1) # Drop the redundant index 

# Convert time & admission columns to POSIXct format
dt <- transform(dt, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S'), 
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S'))
sapply(dt, class) # mrn, enc -> int; inpatient -> bool; admission, time -> POSIXct; creat -> numeric


# Add in AKI
aki <- addBackCalcAKI(addRollingWindowAKI(dt))
py <- fread('~/Desktop/out.csv')
# Convert time & admission columns to POSIXct format
py <- transform(py, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S'), 
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S'))
sapply(py, class) # mrn, enc -> int; inpatient -> bool; admission, time -> POSIXct; creat -> numeric

# Compare rw vals - 100% match (Oct. 11, 2020)
table(aki$rw)
table(py$rw)

# Compare back-calc vals
table(aki$bc)
table(py$bc)

# Check the mismatch 
comb <- merge(py, aki, by=c('mrn','time'))
mismatch <- which(comb$bc.x != comb$bc.y)
View(comb[mismatch])
View(aki)
