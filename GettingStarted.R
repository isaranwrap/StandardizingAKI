# Import libraries
library(tidyverse)
library(akiFlagger)
library(zoo)

patient_id    <- "___________"
encounter_id  <- "___________"
inpatient     <- "___________"
admission     <- "___________"
time          <- "___________"
creatinine    <- "___________"

# This package is meant to handle patient data, which is PHI. Instead, we use a toy dataset.
dt <- fread('~/Desktop/toy.csv')
head(dt)

#Pre-processing
dt <- subset(dt, select=-V1) # Drop the redundant index
dt <- transform(dt, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S'), # Convert time & admission columns to POSIXct format
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S'))
sapply(dt, class) # mrn, enc -> int; inpatient -> bool; admission, time -> POSIXct; creat -> numeric

View(dt)
# Add in rolling-window AKI
out <- addRollingWindowAKI(dt)
View(out)

# Add in back-calc AKI
out <- addBackCalcAKI(dt)
View(out)

# You can add in both at the same time
out <- addBackCalcAKI(addRollingWindowAKI(dt))

# You can add minimum creatinine for the rolling windows - an intermediate column generated in the calculation process
out <- addRollingWindowAKI(dt, add_min_creat = TRUE)
# Similarly, you can add in the imputed baseline creatinine for the back-calculation method
out <- addBackCalcAKI(dt, add_baseline_creat = TRUE)
