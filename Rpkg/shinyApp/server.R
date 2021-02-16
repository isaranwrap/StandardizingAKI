library(DT)
#library(akiFlagger)
library(data.table)
library(tidyverse)
library(zoo)

# Define server logic ----
server <- function(input, output) {
  output$contents <- DT::renderDataTable({
    file <- input$file # Input file will initially be NULL

    # Ensure the user uploads a .csv file
    ext <- tools::file_ext(file$datapath)
    validate(need(ext == "csv", "Please upload a csv file"))

    df <- fread(file$datapath)
    return(df)
  }, # Options for rendering table
  options = list(
    pageLength = 5,
    searching = F
    ))

  data <- eventReactive(input$calcAKI, {
    file <- input$file

    dt <- fread(input$file$datapath)
    dt <-
      dt %>% rename(
        'patient_id' = input$patient_id,
        'encounter_id' = input$encounter_id,
        'inpatient' = input$inpatient_id,
        'creatinine' = input$creat_id,
        'admission' = input$admission_id,
        'time' = input$time_id
      )

    dt <- transform(dt,
        time = as.POSIXct(time, format = '%Y-%m-%d %H:%M:%S'),
        admission = as.POSIXct(admission, format = '%Y-%m-%d %H:%M:%S')
      )

    aki <- returnAKIpatients(dt, HB_trumping = input$HB_trumping, add_baseline_creat = T)
    aki <- transform(aki,
                     time = as.character(time),
                     admission = as.character(admission))
    aki <- setnames(aki, old = c('patient_id', 'encounter_id',
                                 'inpatient', 'creatinine',
                                 'admission', 'time'), new = c(input$patient_id, input$encounter_id,
                                                               input$inpatient_id, input$creat_id,
                                                               input$admission_id, input$time_id))
    return(aki)
  }) # eventReactive's closing brackets

  output$flagger_output <- DT::renderDataTable(
    data(),
    options = list(
      pageLength = 5
    )
  )

  output$downloadData <- downloadHandler(
    filename = function() {
      paste(input$file, "-aki.csv", sep = "")
    },
    content = function(file) {
      write.csv(data(), file, row.names = FALSE)
    }
  )

  output$download <- renderUI({
    if(!is.null(input$file) & input$calcAKI) {
      downloadButton('downloadData', 'Download')
    }
  })

}
