#' Add in rolling-window AKI
#'
#' Add in the AKI column in a patient dataframe according to the rolling-window KDIGO criterion
#'
#' @param dataframe patient dataset
#' @param window1 rolling window length of the shorter time window; defaults to 48 hours
#' @param window2 rolling window length of the longer time window; defaults to 162 hours
#' @param add_min_creat boolean to add the intermediate columns generated during calculation
#'
#'
#' @return patient dataset with the rolling-window AKI column added in
#'
#' #Imports
#' @import zoo
#' @importFrom dplyr select
#' @importFrom dplyr group_by
#' @importFrom dplyr between
#' @importFrom dplyr mutate
#' @importFrom dplyr %>%
#'
#' @importFrom data.table fread
#' @importFrom data.table first
#' @importFrom data.table last
#' @importFrom data.table copy
#' @importFrom data.table :=
#' @importFrom data.table .SD
#'
#' @export
#'
#' @examples
#' \dontrun{
#' addRollingWindowAKI(df)
#' }

addRollingWindowAKI <- function(dataframe, window1 = as.difftime(2, units='days'), window2 = as.difftime(7, units='days'),
                                add_min_creat = FALSE) {
  # TEMP RETURN TO CHECK FUNCTION WORKS PROPERLY
  #return(paste0(getwd()))
  patient_id <- encounter_id <- time <- creatinine <- NULL
  condition1 <- condition2 <- stage1 <- stage2 <- stage3 <- NULL
  min_creat48 <- min_creat7d <- NULL

  df <- dataframe %>% group_by(patient_id) %>%
    mutate(
      min_creat48 = sapply(time, function(x) min(creatinine[between(time, x - window1, x)])), # Find minimum creatinine in the past 2 days
      min_creat7d = sapply(time, function(x) min(creatinine[between(time, x - window2, x)])), # Find minimum creatinine in the past 7 days

      condition1 = creatinine >= min_creat48 + 0.3, # Check if the creat jumps by 0.3; aka KDIGO criterion 1
      condition2 = round(creatinine, digits=4) >= round(1.5*min_creat7d, digits=4), # Check if the creat jumps by 50%; aka KDIGO criterion 2

      stage1 = as.integer(condition1 | condition2), # Stage 1 AKI is either 0.3 OR 50% jump
      stage2 = as.integer(creatinine >= 2*min_creat7d), # Check if creat doubles; aka KDIGO Stage 2 AKI
      stage3 = as.integer(creatinine >= 3*min_creat7d), # Check if creat triples; aka KDIGO Stage 3 AKI
      rw = stage1 + stage2 + stage3, # The resulting rw column; ultimate output we want added in
    )
  if (add_min_creat) return(df %>% select(-condition1, -condition2, -stage1, -stage2, -stage3))
  return(df %>% select(-min_creat7d, -min_creat48, -condition1, -condition2, -stage1, -stage2, -stage3))
}
