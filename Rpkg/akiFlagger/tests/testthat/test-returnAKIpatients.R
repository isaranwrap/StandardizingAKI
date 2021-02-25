### Test the toy dataset initialization
test_that("Toy loads properly", {
  toy <- toy %>% dplyr::rename(patient_id = mrn, encounter_id = enc)
  aki <- returnAKIpatients(toy)
  expect_equal(aki$aki[1:5], c(0,1,0,0,0))
})

### TESTING PATIENT A: RM & HB should both flag ###
test_that("Patient A - rolling minimum", {
  df <- data.table::data.table(patient_id = replicate(6, 1234),
                   encounter_id = replicate(6, 12345),
                   inpatient = c(F, T, T, T, T, T),
                   admission = c(as.POSIXct('2020-05-24 12:00:00'),
                                 as.POSIXct('2020-05-24 12:00:00'),
                                 as.POSIXct('2020-05-24 12:00:00'),
                                 as.POSIXct('2020-05-24 12:00:00'),
                                 as.POSIXct('2020-05-24 12:00:00'),
                                 as.POSIXct('2020-05-24 12:00:00')),
                   time = c(as.POSIXct('2020-01-01 12:00:00'),
                            as.POSIXct('2020-05-24 12:00:00'),
                            as.POSIXct('2020-05-24 12:00:00'),
                            as.POSIXct('2020-05-25 12:00:00'),
                            as.POSIXct('2020-05-28 12:00:00'),
                            as.POSIXct('2020-05-30 12:00:00')),
                   creatinine = c(1.0, 1.0, 1.29, 1.3, 2, 3))
  aki <- returnAKIpatients(df)
  expect_equal(aki$aki, c(0, 0, 0, 1, 2, 3))
})

test_that("Patient A - historical baseline", {
  df <- data.table::data.table(patient_id = replicate(6, 1234),
                               encounter_id = replicate(6, 12345),
                               inpatient = c(F, T, T, T, T, T),
                               admission = c(as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00')),
                               time = c(as.POSIXct('2020-01-01 12:00:00'),
                                        as.POSIXct('2020-05-24 12:00:00'),
                                        as.POSIXct('2020-05-24 12:00:00'),
                                        as.POSIXct('2020-05-25 12:00:00'),
                                        as.POSIXct('2020-05-28 12:00:00'),
                                        as.POSIXct('2020-05-30 12:00:00')),
                               creatinine = c(1.0, 1.0, 1.29, 1.3, 2, 3))
  aki <- returnAKIpatients(df, HB_trumping = T)
  expect_equal(aki$aki, c(0, 0, 0, 1, 2, 3))
})

### TESTING PATIENT B: RM flags; HB doesn't ###
test_that("Patient B - rolling minimum", {
  df <- data.table::data.table(patient_id = replicate(8, 1234),
                               encounter_id = replicate(8, 12345),
                               inpatient = c(F, T, T, T, T, T, T, T),
                               admission = c(as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00')),
                               time = c(as.POSIXct('2020-01-01 12:00:00'),
                                        as.POSIXct('2020-05-24 12:00:00'),
                                        as.POSIXct('2020-05-25 12:00:01'),
                                        as.POSIXct('2020-05-25 12:00:02'),
                                        as.POSIXct('2020-05-28 12:00:00'), # 5
                                        as.POSIXct('2020-05-29 12:00:00'),
                                        as.POSIXct('2020-05-30 12:00:01'),
                                        as.POSIXct('2020-05-30 12:00:02')), # 8
                               creatinine = c(1.1, 1.0, 1.29, 1.3, 2, 2.2, 3, 3.3))
  aki <- returnAKIpatients(df, HB_trumping = F)
  expect_equal(aki$aki[1:8], c(0, 0, 0, 1, 2, 2, 3, 3))
})

test_that("Patient B - historical baseline", {
  df <- data.table::data.table(patient_id = replicate(8, 1234),
                               encounter_id = replicate(8, 12345),
                               inpatient = c(F, T, T, T, T, T, T, T),
                               admission = c(as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00'),
                                             as.POSIXct('2020-05-24 12:00:00')),
                               time = c(as.POSIXct('2020-01-01 12:00:00'),
                                        as.POSIXct('2020-05-24 12:00:00'),
                                        as.POSIXct('2020-05-25 12:00:01'),
                                        as.POSIXct('2020-05-25 12:00:02'),
                                        as.POSIXct('2020-05-28 12:00:00'), # 5
                                        as.POSIXct('2020-05-29 12:00:00'),
                                        as.POSIXct('2020-05-30 12:00:01'),
                                        as.POSIXct('2020-05-30 12:00:02')), # 8
                               creatinine = c(1.1, 1.0, 1.29, 1.3, 2, 2.2, 3, 3.3))
  aki <- returnAKIpatients(df, HB_trumping = T)
  expect_equal(aki$aki, c(0, 0, 0, 0, 1, 2, 2, 3))
})
