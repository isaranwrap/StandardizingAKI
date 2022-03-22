library(dplyr)
library(tidyverse)

#' Main logic for calculating and returning patients with AKI
#'
#' @param dataframe Your input dataset, of class c(data.table, data.frame).
#' @param RM_window Boolean definition selector, whether you would like to implement the rolling-minimum window \href{https://akiflagger.readthedocs.io/}{(RMW)} definition.
#' @param HB_trumping Boolean definition selector, whether you would like to implement the Historical Baseline Trumping \href{https://akiflagger.readthedocs.io/}{(HBT)} definition.
#' @param eGFR_impute Boolean definition selector, whether you would like to implement the Baseline Creatinine Imputation \href{https://akiflagger.readthedocs.io/}{(BCI)} definition.
#' @param padding The amount of padding you would like to add to the rolling windows. Enter this as a c(`integer`, `string`) vector where
#'   `integer` is the amount of time and `string` are the units of time. Defaults to \code{c(4L, "hours")}.
#' @param window1,window2 The amount of time in the shorter and longer rolling windows, respectively. The default values are 48 and 172 hours (2 and 7 days), respectively.
#'   The vector (same format as \code{\link{padding}}) is fed into a `difftime()` object.
#' @param addIntermediateCols Boolean selector, whether you would like to add in the intermediate columns generated during calculation; namely the minimum creatinine & the baseline creatinines.
#'   Defaults to \code{FALSE}.
#' @param returnMinimalInput Boolean selector, whether to return a minimal version of the flagger input.
#'
#' @return
#' @export
#'
#' @examples
#' returnAKIpatients(toy)
returnAKIpatients <- function(dataframe, RM_window = TRUE, HB_trumping = FALSE, eGFR_impute = FALSE,
                                  padding = c(4L, "hours"), window1 = c(2L, "days"), window2 = c(7L, "days"),
                                  addIntermediateCols = FALSE, returnMinimalInput = FALSE) {

  shortTIMEFRAME <- as.difftime(as.numeric(window1[1]), units = window1[2]) + as.difftime(as.numeric(padding[1]), units = padding[2])
  longTIMEFRAME  <-  as.difftime(as.numeric(window2[1]), units = window2[2]) + as.difftime(as.numeric(padding[1]), units = padding[2])
  consecutiveCreatinineFORAdmission <- 72 * 3600 #

  inpatient <- time <- creatinine <- patient_id <- NULL
  min_creat48 <- min_creat7d <- aki <- NULL
  admissionConditions <- admissionMask <- admissionImputed <- NULL
  baseline_creat <- sex <- age <- creat_over_kappa <- NULL
  timeBetweenRows <- inpShiftedBack <- NULL

  if (RM_window) {

    dataframe[, min_creat48 := sapply(.SD[, time], function(x) min(creatinine[data.table::between(.SD[, time], x - shortTIMEFRAME, x)])), by = patient_id]
    dataframe[, min_creat7d := sapply(.SD[, time], function(x) min(creatinine[data.table::between(.SD[, time], x - shortTIMEFRAME, x)])), by = patient_id]

    stage1.condition1 <- round(dataframe$creatinine, digits = 4) >= round(dataframe$min_creat48 + 0.3, digits = 4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    stage1.condition2 <- round(dataframe$creatinine, digits = 4) >= round(dataframe$min_creat7d * 1.5, digits = 4)

    stage1 <- as.integer(stage1.condition1 | stage1.condition2)
    stage2 <- as.integer(round(dataframe$creatinine, digits = 4) >= round(2 * dataframe$min_creat7d, digits = 4))
    stage3 <- as.integer(round(dataframe$creatinine, digits = 4) >= round(3 * dataframe$min_creat7d, digits = 4))

    dataframe[, aki := stage1 + stage2 + stage3]

    }

  if (HB_trumping) {

    dataframe[, timeBetweenRows := data.table::shift(time, type = "lead") - time, by = patient_id] # Time difference between current row and next
    dataframe[, inpShiftedBack := data.table::shift(inpatient, type = "lead"), by = patient_id] # Inpatient column shifted backwards

    admission.condition1 <- dataframe$timeBetweenRows <= consecutiveCreatinineFORAdmission # Check to make sure times are within 72 hours from each other
    admission.condition2 <- dataframe$inpatient & dataframe$inpShiftedBack # Two consecutive inpatient measurements
    admission.condition3 <- dataframe[, admission.condition3 := as.logical(cumsum(inpatient) == 1), by = patient_id]$admission.condition3

    # Admission imputation
    dataframe[, admissionConditions := admission.condition1 & admission.condition2 & admission.condition3]
    dataframe[, admissionMask := admissionConditions & !data.table::shift(admissionConditions, fill = F), by = patient_id] # Admit mask requires F -> T transition
    dataframe[ dataframe$admissionMask, admissionImputed := time] # Use mask to grab time stamps that will be used for admission
    dataframe[, admissionImputed := zoo::na.locf(zoo::na.locf(admissionImputed, na.rm = F), fromLast = T), by = patient_id] # Forward-fill then back-fill

    dataframe <- dataframe %>% dplyr::select(-admissionConditions, -admissionMask,
                                             -admission.condition3,
                                             -timeBetweenRows, -inpShiftedBack)

    # Rolling minimum conditions
    dataframe[, min_creat48 := sapply(.SD[, time], function(x) min(creatinine[data.table::between(.SD[, time], x - shortTIMEFRAME, x)])), by = patient_id]
    dataframe[, min_creat7d := sapply(.SD[, time], function(x) min(creatinine[data.table::between(.SD[, time], x - shortTIMEFRAME, x)])), by = patient_id]

    # Calculate baseline creatinine
    dataframe <- dataframe %>% dplyr::group_by(patient_id) %>% returnBaselineCreat(eGFR_impute = eGFR_impute) %>% dplyr::ungroup()
    data.table::setDT(dataframe)
    # Create masks (i.e. select those times from )
    maskShortTF <- dataframe$time >= dataframe$admissionImputed & (dataframe$time <= dataframe$admissionImputed + shortTIMEFRAME)
    maskLongTF <- dataframe$time >= dataframe$admissionImputed & (dataframe$time <= dataframe$admissionImputed + longTIMEFRAME)
    maskBCNull <- !is.na(dataframe$baseline_creat)
    mask.HBT <- maskBCNull & maskLongTF

    # Rolling minimum calculations (RMW)
    stage1.condition1 <- round(dataframe$creatinine, digits = 4) >= round(dataframe$min_creat48 + 0.3, digits = 4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    stage1.condition2 <- round(dataframe$creatinine, digits = 4) >= round(dataframe$min_creat48 * 1.5, digits = 4)

    # Historical baseline calculations (HBT)
    stage1.condition1.HBT <- round(dataframe[mask.HBT, creatinine], digits = 4) >= round(dataframe[mask.HBT, baseline_creat] + 0.3, digits = 4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    stage1.condition2.HBT <- round(dataframe[mask.HBT, creatinine], digits = 4) >= round(1.5 * dataframe[mask.HBT, baseline_creat], digits = 4)


    stage1 <- as.integer(stage1.condition2) # NOTE: Stage 1 is simply condition 2 ... condition 1 will get re-inserted after HB conditions are applied
    stage2 <- as.integer(round(dataframe$creatinine, digits = 4) >= round(2 * dataframe$min_creat7d, digits = 4))
    stage3 <- as.integer(round(dataframe$creatinine, digits = 4) >= round(3 * dataframe$min_creat7d, digits = 4))

    dataframe[, aki := stage1 + stage2 + stage3]

    if (!all(!mask.HBT)) {
      stage1.HBT <- as.integer(stage1.condition1.HBT | stage1.condition2.HBT)
      stage2.HBT <- as.integer(round(dataframe[mask.HBT, creatinine], digits = 4) >= round(2 * dataframe[mask.HBT, baseline_creat], digits = 4))
      stage3.HBT <- as.integer(round(dataframe[mask.HBT, creatinine], digits = 4) >= round(3 * dataframe[mask.HBT, baseline_creat], digits = 4))

      dataframe[mask.HBT, aki := stage1.HBT + stage2.HBT + stage3.HBT]
    }

    # After HBT conditions are applied, we add the 0.3 bump back in
    maskNoAKI <- dataframe$aki == 0
    maskShortTF[is.na(maskShortTF)] <- FALSE # Replace NULL values with FALSE
    mask.RMW <- (!maskShortTF & maskNoAKI) | (!maskBCNull & maskNoAKI)
    dataframe[mask.RMW, aki := stage1.condition1[mask.RMW]]
  }

  if (eGFR_impute) {

    dataframe[, timeBetweenRows := data.table::shift(time, type = "lead") - time, by = patient_id] # Time difference between current row and next
    dataframe[, inpShiftedBack := data.table::shift(inpatient, type = "lead"), by = patient_id] # Inpatient column shifted backwards

    admission.condition1 <- dataframe$timeBetweenRows <= consecutiveCreatinineFORAdmission # Check to make sure times are within 72 hours from each other
    admission.condition2 <- dataframe$inpatient & dataframe$inpShiftedBack # Two consecutive inpatient measurements
    admission.condition3 <- dataframe[, admission.condition3 := as.logical(cumsum(inpatient) == 1), by = patient_id]$admission.condition3

    # Admission imputation
    dataframe[, admissionConditions := admission.condition1 & admission.condition2 & admission.condition3]
    dataframe[, admissionMask := admissionConditions & !data.table::shift(admissionConditions, fill = F), by = patient_id] # Admit mask requires F -> T transition
    dataframe[ dataframe$admissionMask, admissionImputed := time] # Use mask to grab time stamps that will be used for admission
    dataframe[, admissionImputed := zoo::na.locf(zoo::na.locf(admissionImputed, na.rm = F), fromLast = T), by = patient_id] # Forward-fill then back-fill

    dataframe <- dataframe %>% dplyr::select(-admissionConditions, -admissionMask,
                                             -admission.condition3,
                                             -timeBetweenRows, -inpShiftedBack)

    # Rolling minimum conditions
    dataframe[, min_creat48 := sapply(.SD[, time], function(x) min(creatinine[data.table::between(.SD[, time], x - shortTIMEFRAME, x)])), by = patient_id]
    dataframe[, min_creat7d := sapply(.SD[, time], function(x) min(creatinine[data.table::between(.SD[, time], x - shortTIMEFRAME, x)])), by = patient_id]

    # Calculate baseline creatinine
    dataframe <- dataframe %>% dplyr::group_by(patient_id) %>% returnBaselineCreat(eGFR_impute = eGFR_impute) %>% dplyr::ungroup()
    data.table::setDT(dataframe)

    # Create masks (i.e. select those times from )
    maskShortTF <- dataframe$time >= dataframe$admissionImputed & (dataframe$time <= dataframe$admissionImputed + shortTIMEFRAME)
    maskLongTF <- dataframe$time >= dataframe$admissionImputed & (dataframe$time <= dataframe$admissionImputed + longTIMEFRAME)
    maskBCNull <- !is.na(dataframe$baseline_creat)
    mask.HBT <- maskBCNull & maskLongTF

    # Rolling minimum calculations (RMW)
    stage1.condition1 <- round(dataframe$creatinine, digits = 4) >= round(dataframe$min_creat48 + 0.3, digits = 4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    stage1.condition2 <- round(dataframe$creatinine, digits = 4) >= round(dataframe$min_creat48 * 1.5, digits = 4)

    # Historical baseline calculations (HBT)
    stage1.condition1.HBT <- round(dataframe[mask.HBT, creatinine], digits = 4) >= round(dataframe[mask.HBT, baseline_creat] + 0.3, digits = 4) # Check if the creat jumps by 0.3; aka KDIGO criterion 1
    stage1.condition2.HBT <- round(dataframe[mask.HBT, creatinine], digits = 4) >= round(1.5 * dataframe[mask.HBT, baseline_creat], digits = 4)


    stage1 <- as.integer(stage1.condition2) # NOTE: Stage 1 is simply condition 2 ... condition 1 will get re-inserted after HB conditions are applied
    stage2 <- as.integer(round(dataframe$creatinine, digits = 4) >= round(2 * dataframe$min_creat7d, digits = 4))
    stage3 <- as.integer(round(dataframe$creatinine, digits = 4) >= round(3 * dataframe$min_creat7d, digits = 4))

    dataframe[, aki := stage1 + stage2 + stage3]

    if (!all(!mask.HBT)) {
      stage1.HBT <- as.integer(stage1.condition1.HBT | stage1.condition2.HBT)
      stage2.HBT <- as.integer(round(dataframe[mask.HBT, creatinine], digits = 4) >= round(2 * dataframe[mask.HBT, baseline_creat], digits = 4))
      stage3.HBT <- as.integer(round(dataframe[mask.HBT, creatinine], digits = 4) >= round(3 * dataframe[mask.HBT, baseline_creat], digits = 4))

      dataframe[mask.HBT, aki := stage1.HBT + stage2.HBT + stage3.HBT]
    }

    # After HBT conditions are applied, we add the 0.3 bump back in
    maskNoAKI <- dataframe$aki == 0
    maskShortTF[is.na(maskShortTF)] <- FALSE # Replace NULL values with FALSE
    mask.RMW <- (!maskShortTF & maskNoAKI) | (!maskBCNull & maskNoAKI)
    dataframe[mask.RMW, aki := stage1.condition1[mask.RMW]]
  }

  if (!addIntermediateCols & !RM_window) {
   dataframe <- dataframe %>% dplyr::select(-min_creat48, -min_creat7d, -baseline_creat, -admissionImputed)
  } else if (!addIntermediateCols & RM_window) {
    dataframe <- dataframe %>% dplyr::select(-min_creat48, -min_creat7d)
  }

  # if (returnMinimalInput) {
  #dataframe <- dataframe %>% dplyr::select(patient_id, inpatient, time, creatinine)
  #}

  return(dataframe)
}

#' Helper function to run all THREE definitions for acute kidney injury (AKI)
#'
#' @param dataframe Your input dataset, of class c(data.table, data.frame).
#' @param padding The amount of padding you would like to add to the rolling windows. Enter this as a c(`integer`, `string`) vector where
#'   `integer` is the amount of time and `string` are the units of time. Defaults to \code{c(4L, "hours")}.
#' @return The input patient dataset with the 3 AKI columns added in, titled `RMW`, `HBT` and `BCI`.
#' @export
#'
#' @examples
#' runAllDefinitions(toy)
runAllDefinitions <- function(dataframe, padding = c(4, "hours")) {
  dataframe.RMW <- returnAKIpatients(dataframe, RM_window = TRUE)
  dataframe.HBT <- returnAKIpatients(dataframe, HB_trumping = TRUE)
  dataframe.BCI <- returnAKIpatients(dataframe, eGFR_impute = TRUE)

  dataframe$RMW <- dataframe.RMW$aki
  dataframe$HBT <- dataframe.HBT$aki
  dataframe$BCI <- dataframe.BCI$aki
  return(dataframe)
}

# Baseline creatinine is defined as the MEDIAN of the OUTPATIENT creatinine values from 365 to 7 days prior to admission
#' Return the baseline creatinine, helper function
#'
#' @param dataframe Input patient dataset of a single patient, of class c(data.table, data.frame).
#' @param eGFR_impute Boolean value, whether to impute the creatinine based on the updated \url{https://www.nejm.org/doi/full/10.1056/NEJMoa2102953}{CKD-EPI equation} (Inker et. Al, 2021).
#'
#' @return The dataframe inputted with the `baseline_creat` column added in
#' @export
#'
#' @examples
#' returnBaselineCreat(toy.demo, eGFR_impute = TRUE)
returnBaselineCreat <- function(dataframe, eGFR_impute = F) {
  kappa <- alpha <- baseline_creat <- NULL

  if (eGFR_impute) {
    # Imputed based on updated CKD-EPI equation (Inker et. Al, 2021)
    eGFR <- 75

    dataframe$kappa <- 0
    dataframe$alpha <- 0
    dataframe$baseline_creat <- NA

    dataframe$kappa[dataframe$sex == T] <- 0.7
    dataframe$kappa[dataframe$sex == F] <- 0.9

    dataframe$alpha[dataframe$sex == T] <- -0.341
    dataframe$alpha[dataframe$sex == F] <- -0.201

    dataframe <- dataframe %>% dplyr::mutate(
      creat_over_kappa = 75 / (141*(1 + 0.018*sex)*0.993**age)
    )


    dataframe$baseline_creat[dataframe$creat_over_kappa < 1] <- dataframe$kappa*dataframe$creat_over_kappa**(-1/1.209)
    dataframe$baseline_creat[dataframe$creat_over_kappa >= 1] <- dataframe$kappa*dataframe$creat_over_kappa**(-1/dataframe$alpha)

    dataframe <- dataframe %>% dplyr::select(-creat_over_kappa, -kappa, -alpha)
    return(dataframe)

  } else {
    dataframe.im <- dataframe %>% dplyr::filter(inpatient == FALSE) %>%
      dplyr::filter(time <= admissionImputed - as.difftime(7, units = "days") & time >= admissionImputed - as.difftime(365, units = "days")) %>%
      dplyr::group_by(patient_id) %>%
        dplyr::mutate(baseline_creat = stats::median(creatinine))

    dataframe$baseline_creat <- dataframe.im$baseline_creat[match(dataframe$patient_id, dataframe.im$patient_id)]
    dataframe$baseline_creat <- round(dataframe$baseline_creat, digits = 3)

    return(dataframe)
  }
}

helper.multipleDefinitions <- function(RM_window, HB_trumping, eGFR_impute) {
  return(sum(c(RM_window, HB_trumping, eGFR_impute)) > 1)
}

if (helper.multipleDefinitions(RM_window = NULL,
                               HB_trumping = NULL,
                               eGFR_impute = NULL)) {
  akiColNames = c("aki", "aki", "aki")
}
