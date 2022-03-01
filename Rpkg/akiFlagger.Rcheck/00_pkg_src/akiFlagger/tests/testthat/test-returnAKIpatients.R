### Test the toy dataset initialization
test_that("Toy loads properly", {
  expect_equal(head(toy$creatinine), c(1.05, 1.61, 1.42, 1.26, 1.06, 0.89))
})

### TESTING PATIENT A: RMW & HBT should both flag, whereas BCI should NOT ###
test_that("Test RMW (rolling minimum window) on patient A", {
  testDATA.patientA <- data.table::data.table(
    patient_id = replicate(6, 1),
    inpatient = c(F, F, F, T, T, T),
    admission = as.POSIXct(replicate(6, 1), origin = "2020-01-01 12:00:00", tz = "UTC"),
    # KEEP time = as.POSIXct(c(-8, -7, -2, 0, 3, 10), origin = "2020-01-01 12:00:00", tz = "UTC") KEEP
    time = c(as.POSIXct('2019-12-24 12:00:00'),
             as.POSIXct('2019-12-25 12:00:00'),
             as.POSIXct('2019-12-30 12:00:00'),
             as.POSIXct('2020-01-01 12:00:00'),
             as.POSIXct('2020-01-03 12:00:00'),
             as.POSIXct('2020-01-11 12:00:00')),
    creatinine = c(1, 1, 1, 1, 1.3, 1.3)
  )
  aki <- returnAKIpatients_RMW(testDATA.patientA)
  expect_equal(aki$aki, c(0, 0, 0, 0, 1, 0))
})

# test_that("Test HBT (historical baseline trumping) on patient A", {
#   testDATA.patientA <- data.table::data.table(
#     patient_id = replicate(6, 1),
#     inpatient = c(F, F, F, T, T, T),
#     admission = as.POSIXct(replicate(6, 1), origin = "2020-01-01 12:00:00", tz = "UTC"),
#     time = c(as.POSIXct('2019-12-24 12:00:00'),
#              as.POSIXct('2019-12-25 12:00:00'),
#              as.POSIXct('2019-12-30 12:00:00'),
#              as.POSIXct('2020-01-01 12:00:00'),
#              as.POSIXct('2020-01-03 12:00:00'),
#              as.POSIXct('2020-01-11 12:00:00')),
#     creatinine = c(1, 1, 1, 1, 1.3, 1.3)
#   )
#   aki <- returnAKIpatients_HBT(testDATA.patientA)
#   expect_equal(aki$aki, c(0, 0, 0, 0, 1, 0))
# })

test_that("Test BCI (baseline creatinine imputation) on patient A; no ASR", {
  testDATA.patientA <- data.table::data.table(
    patient_id = replicate(6, 1),
    inpatient = c(F, F, F, T, T, T),
    admission = as.POSIXct(replicate(6, 1), origin = "2020-01-01 12:00:00", tz = "UTC"),
    time = c(as.POSIXct('2019-12-24 12:00:00'),
             as.POSIXct('2019-12-25 12:00:00'),
             as.POSIXct('2019-12-30 12:00:00'),
             as.POSIXct('2020-01-01 12:00:00'),
             as.POSIXct('2020-01-03 12:00:00'),
             as.POSIXct('2020-01-11 12:00:00')),
    creatinine = c(1, 1, 1, 1, 1.3, 1.3)
  )
 # aki <- returnAKIpatients_BCI(testDATA.patientA)
  expect_error(returnAKIpatients_BCI(testDATA.patientA), "Can't subset columns that don't exist.")
})

test_that("Test BCI (baseline creatinine imputation) on patient A; ", {
  testDATA.patientA <- data.table::data.table(
    patient_id = replicate(6, 1),
    inpatient = c(F, F, F, T, T, T),
    admission = as.POSIXct(replicate(6, 1), origin = "2020-01-01 12:00:00", tz = "UTC"),
    time = c(as.POSIXct('2019-12-24 12:00:00'),
             as.POSIXct('2019-12-25 12:00:00'),
             as.POSIXct('2019-12-30 12:00:00'),
             as.POSIXct('2020-01-01 12:00:00'),
             as.POSIXct('2020-01-03 12:00:00'),
             as.POSIXct('2020-01-11 12:00:00')),
    creatinine = c(1, 1, 1, 1, 1.3, 1.3),
    age = 26, sex = F, race = F # 26 yo white male
  )
  aki <- returnAKIpatients_BCI(testDATA.patientA)
  expect_equal(aki$aki, c(0, 0, 0, 0, 0, 0))
})
