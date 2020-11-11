#' Back Calculation AKI
#'
#' @param dataframe patient dataset
#' @param lookforward amount of time to look forward after admission before the back-calculation method no longer applies
#' @param add_baseline_creat boolean to add the intermediate column generated during calculation
#'
#' @return patient dataset with the back-calculation AKI column added in
#' @importFrom stats median
#' @export
#'
#' @examples
#' \dontrun{
#' addBackCalcAKI(df)
#' }

addBackCalcAKI <- function(dataframe, lookforward=as.difftime(7, units='days'), add_baseline_creat = FALSE) {
  patient_id <- encounter_id <- time <- admission <- creatinine <- inpatient <- NULL
  baseline_creat <- stage1 <- stage2 <- stage3 <- bc <- NULL
  df <- copy(dataframe)
  # Take the MEDIAN OUTPATIENT creatinine values from 365 to 7 days prior to admission
  df[, baseline_creat := .SD[time >= admission - as.difftime(365, units='days') & time <= admission - as.difftime(7, units='days') & inpatient == F, round(median(creatinine), 4)], by = patient_id]

  # Only include baseline creatinine values from 6 hours prior to admission to 7 days after admission
  df[time < admission - as.difftime(6, units='hours') & time < admission + lookforward, baseline_creat := NA]

  #Add AKI stages
  df[, stage1 := (creatinine >= round(1.5 * baseline_creat, digits=2))] # Stage 1 is only the 50% increase condition now
  df[, stage2 := (creatinine >= 2 * baseline_creat)] # Stage 2 is a doubling of creatinine
  df[, stage3 := (creatinine >= 3 * baseline_creat)] # Stage 3 is a tripling of creatinine
  df[, bc := stage1 + stage2 + stage3] # The resulting bc column; ultimate output we care about
  df[is.na(bc), bc := 0] # Replace NAs with 0; i.e. no AKI if back-calculation method does not apply
  if (add_baseline_creat) return(df %>% select(-stage1, -stage2, -stage3))
  return(df %>% select(-baseline_creat, -stage1, -stage2, -stage3))
}
