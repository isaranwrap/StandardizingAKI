#' Rolling Window AKI
#'
#' @param dataframe The patient dataset
#' @param window1 The rolling window length of the shorter time window; defaults to 48 hours
#' @param window2 The rolling window length of the longer time window; defaults to 162 hours
#'
#' @return The patient dataset with the rolling-window AKI column added in
#'
#' @import data.table
#' @import dplyr
#' @import zoo
#'
#' @export
#'
#' @examples
#' \dontrun{
#' addRollingWindowAKI(df)
#' }

addRollingWindowAKI <- function(dataframe, window1 = as.difftime(2, units='days'), window2 = as.difftime(7, units='days'),
                                add_min_creat = FALSE) {
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

