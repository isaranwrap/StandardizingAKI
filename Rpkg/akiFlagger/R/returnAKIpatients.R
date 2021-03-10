#' Flag patients for AKI
#'
#' Add in the AKI column in a patient dataframe according to the  KDIGO criterion
#'
#' @param dataframe patient dataset
#' @param HB_trumping boolean on whether to have historical baseline creatinine values trump the local minimum creatinine values
#' @param eGFR_impute boolean on whether to impute missing baseline creatinine values with CKD-EPI equation
#' @param window1 rolling window length of the shorter time window; defaults to 48 hours
#' @param window2 rolling window length of the longer time window; defaults to 162 hours
#' @param add_min_creat boolean on whether to add the intermediate columns generated during calculation
#' @param add_baseline_creat boolean on whether to add the baseline creatinine values in
#'
#' @return patient dataset with AKI column added in
#'
#' #Imports
#' @import zoo
#' @importFrom dplyr select
#' @importFrom dplyr between
#' @importFrom dplyr %>%
#'
#' @importFrom data.table fread
#' @importFrom data.table first
#' @importFrom data.table last
#' @importFrom data.table copy
#' @importFrom data.table :=
#' @importFrom data.table .SD
#' @importFrom data.table shift
#'
#' @importFrom stats median
#'
#' @export
#'
#' @examples
#' returnAKIpatients(toy)

returnAKIpatients <- function(dataframe, HB_trumping = FALSE, eGFR_impute = FALSE,
                              window1 = as.difftime(2, units='days'), window2 = as.difftime(7, units='days'),
                              padding = as.difftime(0, units = 'days'),
                              add_min_creat = FALSE, add_baseline_creat = FALSE,
                              add_imputed_admission = FALSE, add_imputed_encounter = FALSE) {

  age <- sex <- race <- NULL # Add a visible binding (even if it's null) so R CMD Check doesn't complain
  patient_id <- inpatient <- creatinine <- time <- NULL
  min_creat48 <- min_creat7d <- baseline_creat <- aki <- NULL # Also, erase any variables in case duplicate variable names coexist

  window1 <- window1 + padding
  window2 <- window2 + padding

  # Ensure the data frame being fed in contains the patient_id, inpatient, admission, and time columns
  if (!('patient_id' %in% colnames(dataframe))) return("Sorry! Patient ID not found in dataframe.")
  if (!('inpatient' %in% colnames(dataframe))) return("Sorry! Inpatient column not found in dataframe.")
  if (!('time' %in% colnames(dataframe))) return("Sorry! Time column not found in dataframe.")

  # If eGFR imputation is wanted, additional columns are required.
  if (eGFR_impute) {
    if (!('age' %in% colnames(dataframe))) return("The age column is needed for eGFR imputation!")
    if (!('sex' %in% colnames(dataframe))) return("The sex column is needed for eGFR imputation!")
    if (!('race' %in% colnames(dataframe))) return("The race column is needed for eGFR imputation!")

  }

  df <- dataframe[, .(patient_id, inpatient, creatinine, time)] # Select the columns of interest
  df <- df[!duplicated(df)] # Remove duplicated rows
  df <- df[order(time), .SD ,by = patient_id]

  # Rolling minimum creatinine values in the past 48 hours and 7 days, respectively
  df[, min_creat48 := sapply(.SD[, time], function(x) min(creatinine[between(.SD[, time], x - window1, x)])), by=patient_id]
  df[, min_creat7d := sapply(.SD[, time], function(x) min(creatinine[between(.SD[, time], x - window2, x)])), by=patient_id]

  # If HB_trumping is set to True, we want to add condition2, then do RM calcs, then do HB cacls, then add condition1 back in
  if (HB_trumping){

    # Impute estimated admission and encounter columns
    df[, delta_t := shift(time, type = 'lead') - time, by = patient_id] # Time difference between current row and next
    df[, inp_lag := shift(inpatient, fill = F), by = patient_id] # Inpatient column shifted forward
    df[, inp_lead:= shift(inpatient, type = 'lead'), by = patient_id] # Inpatient column shifted backwards

    cond1 <- df[, delta_t] <= 72*3600 # Check to make sure times are within 72 hours (in units of seconds) from each other
    cond2 <- df[, inpatient] & df[, inp_lead] # Ensure that a True is followed by a True (i.e. at least 2 visits)
    cond3 <- df[, inpatient] & !df[, inp_lag] # Ensure that a True is preceded by a False (i.e. outpatient -> inpatient transition)

    df[cond1 & cond2 & cond3, imputed_admission := time]
    df[, imputed_admission := na.locf(na.locf(imputed_admission, na.rm = F), fromLast = T), by = patient_id] # Forward-fill then back-fill
    df[, imputed_encounter_id := .GRP, by = c('imputed_admission', 'patient_id')] # Group by encounter and count each group

    # Remove delta_t, inp_lag, & inp_lead from the dataframe
    df <- df %>% select(-delta_t, -inp_lag, -inp_lead)

    # Baseline creatinine is defined as the median of the outpatient creatinine values from 365 to 7 days prior to admission
    df[, baseline_creat := .SD[time >= imputed_admission - as.difftime(365, units='days') &
                                 time <= imputed_admission - as.difftime(7, units='days') & inpatient == F,
                               round(median(creatinine), 4)], by = imputed_encounter_id]

    # Imputation of baseline creatinine from CKD-EPI equation; i.e. eGFR-based imputation (assuming an eGFR of 75)
    if (eGFR_impute) {

      # Only want to apply the eGFR imputation to those who have a missing baseline creatinine
      null_bc = is.na(df[, baseline_creat])

      # Coefficients used in the CKD-EPI equation (Levey et. Al, 2009)
      kappa <- 0.9 - 0.2*df[null_bc, sex]
      alpha <- -0.411 + 0.082*df[null_bc, sex]

      creat_over_kappa <- 75/(141*(1 + 0.018*df[null_bc, sex])*(1 + 0.159*df[null_bc, race])*0.993**df[null_bc, age])

      df[null_bc & creat_over_kappa < 1, baseline_creat] <- kappa*creat_over_kappa**(-1/1.209)
      df[null_bc & creat_over_kappa >=1, baseline_creat] <- kappa*creat_over_kappa**(1/alpha)

    }

    # Two different conditions for how stage 1 can be met (with two distinct rolling window periods)
    condition1 <- round(df[, creatinine], digits=4) >= round(df[, min_creat48] + 0.3, digits=4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    condition2 <- round(df[, creatinine], digits=4) >= round(1.5*df[, min_creat7d], digits=4) # Check if the creat increases by 50%; KDIGO criterion 2

    # Masks from admission to 2 & 7 days into the future, respectively
    mask_2d <- (df[, time] >= df[, imputed_admission]) & (df[, time] <= df[, imputed_admission] + window1)
    mask_7d <- (df[, time] >= df[, imputed_admission]) & (df[, time] <= df[, imputed_admission] + window2)
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

    if (!add_imputed_admission) df <- df %>% select(-imputed_admission)
    if (!add_imputed_encounter) df <- df %>% select(-imputed_encounter_id)

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
  if (!add_baseline_creat) df <- df %>% select(-baseline_creat)
  return(df)
}
