#' Toy dataset
#'
#' Since real patient data is probably protected health information (PHI),
#' this toy dataset contains all the relevant columns the flagger takes in.
#'
#' @format A data frame (1078 x 6) consisting of relevant AKI measurements for patients
#' \describe{
#'    \item{patient_id}{int, the patient identifier}
#'    \item{inpatient}{boolean, whether or not the creatinine measurement taken was an inpatient measurement}
#'    \item{time}{POSIXct, the time at which the creatinine measurement was taken}
#'    \item{creatinine}{float, the creatinine value of the measurement taken}
#'    @source \url{http://akiflagger.readthedocs.io/}
#' }
"toy"

#' Toy dataset
#'
#' Since real patient data is probably protected health information (PHI),
#' this toy dataset contains all the relevant columns the flagger takes in.
#'
#' @format A data frame (1078 x 6) consisting of relevant AKI measurements for patients
#' \describe{
#'    \item{patient_id}{int, the patient identifier}
#'    \item{age}{float, the age of the patient}
#'    \item{sex}{boolean, whether the patient is female or not}
#'    \item{race}{boolean, whether the patient is black or not}
#'    \item{inpatient}{boolean, whether or not the creatinine measurement taken was an inpatient measurement}
#'    \item{time}{POSIXct, the time at which the creatinine measurement was taken}
#'    \item{creatinine}{float, the creatinine value of the measurement taken}
#'    @source \url{http://akiflagger.readthedocs.io/}
#' }
"toy.demo"
