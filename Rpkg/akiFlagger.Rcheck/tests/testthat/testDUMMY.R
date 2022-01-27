# baseFolder <- file.path("/Users", "saranmedical-smile", "AKIFlagger")
#
# scriptsFolder <- file.path(baseFolder, "scripts")
# dataFolder <- file.path(baseFolder, "data")
#
# testDATA <- data.table::fread(file.path(dataFolder, "01test.csv"))
# View(testDATA)
#
# testDATA.patientA <- data.table::data.table(
#   patient_id = replicate(6, 1),
#   inpatient = c(F, F, F, T, T, T),
#   admission = c(as.POSIXct('2020-01-01 12:00:00'),
#                 as.POSIXct('2020-01-01 12:00:00'),
#                 as.POSIXct('2020-01-01 12:00:00'),
#                 as.POSIXct('2020-01-01 12:00:00'),
#                 as.POSIXct('2020-01-01 12:00:00'),
#                 as.POSIXct('2020-01-01 12:00:00')),
#   time = c(as.POSIXct('2019-12-24 12:00:00'),
#            as.POSIXct('2019-12-25 12:00:00'),
#            as.POSIXct('2019-12-30 12:00:00'),
#            as.POSIXct('2020-01-01 12:00:00'),
#            as.POSIXct('2020-01-03 12:00:00'),
#            as.POSIXct('2020-01-11 12:00:00')),
#   creatinine = c(1, 1, 1, 1, 1.3, 1.3)
# )
