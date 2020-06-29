library(data.table)
library(stringr)
library(base)
library(stats)
library(dplyr)
library(shiny)

#Read in the data
dt <- fread('/Users/saranmedical-smile/Desktop/patr/StandardizingAKI/inpatient 2014-2018 creatinine.csv')


##### -------------------- PRE-PROCESSING ----------------------- #####

#Renaming mrn & enc columns
colnames(dt)[colnames(dt) %in% c('pat_mrn_id','pat_enc_csn_id')] = c('mrn', 'enc')


#Removing 'MR' from mrn #'s since numeric indexing is faster
dt$mrn <- substr(dt$mrn, 3, nchar(dt$mrn))
dt <- transform(dt, mrn = as.integer(mrn))


#Convert time to datetime POSIXct
dt <- transform(dt, time = as.POSIXct(time, format='%Y-%m-%dT%H:%M:%S'))
sapply(dt, class) #check to make sure that each column is dtype we want


#Create change in creatinine var
dt <- dt[, creat.shift := shift(creatinine, n = -1), by = enc] 
#data[, lag.value:=c(NA, value[-.N]), by=groups] ... ask Mike what the -.N index is & maybe what := is
dt$delta.creat <- shift(dt$creat.shift - dt$creatinine, n = 1)


#Create change in time var
dt <- dt[, time.shift := shift(time, n = -1), by = enc]
dt$delta.time <- shift(difftime(dt$time.shift, dt$time, units='hours'), n = 1)


#Removing the creat shifted & time shifted columns
dt$creat.shift <- NULL
dt$time.shift <- NULL


##### -------------------- Calculating Rolling Window AKI Cases ----------------------- #####

#Calculating those who satisfy condition 1 (more than 0.3 increase in creatinine in less than 48 hours)
t1 <- '2000-01-01'
t2 <- '2000-01-03' #Probably a slow and stupid way to see 8 hours but I'll ask Mike if there's a smarter way...
cond1 <- dt[, delta.creat > 0.3 & delta.time < difftime(t2, t1)]

#And condition 2 (more than 50% increase in creatinine in less than 7 days)
t3 <- '2000-01-01'
t4 <- '2000-01-08'
cond2 <- dt[, delta.creat > 0.5*shift(creatinine, n=1) & delta.time < difftime(t4, t3)]

table(cond1, useNA = 'ifany')
table(cond2, useNA = 'ifany')

#cond1[is.na(cond1)] <- FALSE
#cond2[is.na(cond2)] <- FALSE

dt$aki <- cond1 == TRUE | cond2 == TRUE
table(dt$aki) #matches Python code :)




















