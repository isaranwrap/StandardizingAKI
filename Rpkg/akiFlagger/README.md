
# akiFlagger

<!-- badges: start -->
<!-- badges: end -->

## Introduction

Acute Kidney Injury (AKI) is a sudden onset of kidney failure and damage marked by an increase in the serum creatinine levels (amongst other biomarkers) of the patient. Kidney Disease Improving Global Outcomes (KDIGO) has a set of [guidelines](https://kdigo.org/guidelines/acute-kidney-injury/) and [standard definitions](http://www.european-renal-best-practice.org/sites/default/files/u33/ndt.gfs375.full_.pdf) of AKI:

* *Stage 1*: 50% increase in creatinine in < 7 days or 0.3 increase in creatinine in < 48 hours

* *Stage 2*: 100% increase in (or doubling of) creatinine in < 7 days

* *Stage 3*: 200% increase in (or tripling of) creatinine in < 7 days

This package contains a flagger to determine if a patient has developed AKI based on longitudinal data of serum creatinine measurements. More information about the specific data input format can be found in the documentation.

## Installation

You can install the released version of akiFlagger from [CRAN](https://CRAN.R-project.org) with:

``` r
install.packages("akiFlagger")
```

## Getting Started

It's often the case that you are dealing with protected health information. So, this walk-through uses a toy dataset. We start
off by reading in the dataset and doing some light preprocessing (turning the time columns into POSIXct format, for example).

``` r
library(akiFlagger)
library(tidyverse)
library(zoo)

dt <- fread('~/Desktop/toy.csv')

# Pre-processing
dt <- subset(dt, select=-V1) # Drop the redundant index
dt <- transform(dt, time = as.POSIXct(time, format='%Y-%m-%d %H:%M:%S'), # Convert time & admission columns to POSIXct format
                admission = as.POSIXct(admission, format='%Y-%m-%d %H:%M:%S'))
sapply(dt, class) # mrn, enc -> int; inpatient -> bool; admission, time -> POSIXct; creat -> numeric
```

## Example: Rolling Window AKI

Applying the flagger to the dataset is simple. Just run the ``addRollingWindowAKI()`` function on the dataset and the returned output will be the same dataset with the rolling window column added in. 
``` r
out <- addRollingWindowAKI(dt)
table(out$rw)
head(out)
```
