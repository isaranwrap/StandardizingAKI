library(shiny)
library(shinyWidgets)
library(shinydashboard)

# Define UI ----
if (interactive()) {
  ui <- fluidPage(titlePanel("AKI Flagger GUI"),

                  sidebarLayout(
                    sidebarPanel(
                      fileInput("file", h3("File input")),
                      h3('Column identifier information'),
                      textInput("pat_id", "Patient identifier",
                                value = "Enter the name for your patient id column"),
                      textInput("enc_id", "Encounter identifier (optional)",
                                value = "Enter the name for your encounter id column"),
                      textInput("enc_id", "Admission identifier (optional)",
                                value = "Enter the name for your admission column"),
                      textInput("inp_id", "Inpatient identifier",
                                value = "Enter the name for your inpatient column"),
                      textInput("creat_id", "Creatinine identifier",
                                value = "Enter the name for your creatinine column"),
                      textInput("time_id", "Time identifier",
                                value = "Enter the name for your time column"),
                      materialSwitch(inputId = "HB_trumping", label = "Historical baseline trumping?", status = "warning", value = FALSE),
                      div(
                        style = "display:inline-block;width:100%;text-align: right;",
                        actionButton("calcAKI", label = "Calculate AKI", icon = icon("calculator
"))
                      ),
                    ),
                    mainPanel(
                      "File preview:",
                      tableOutput("contents"),
                      br(),
                      "Returned output:",
                      tableOutput("flagger_output")
                    )
                  ))

  # Define server logic ----
  server <- function(input, output) {
    output$contents <- renderTable({
      file <- input$file
      ext <- tools::file_ext(file$datapath)

      req(file)
      validate(need(ext == "csv", "Please upload a csv file"))

      dt <- fread(file$datapath)
      head(dt)
    })

    data <- eventReactive(input$calcAKI, {
      dt <- fread(input$file$datapath)
      dt <-
        transform(
          dt,
          time = as.POSIXct(time, format = '%Y-%m-%d %H:%M:%S'),
          admission = as.POSIXct(admission, format = '%Y-%m-%d %H:%M:%S')
        )
      dt <-
        dt %>% rename(
          'patient_id' = patient_id,
          'encounter_id' = encounter_id,
          'inpatient' = inpatient,
          'creatinine' = creatinine,
          'admission' = admission,
          'time' = time
        )
      aki <- returnAKIpatients(dt)
      aki <- transform(aki,
                       time = as.character(time),
                       admission = as.character(admission))
      aki <-
        aki %>% rename(
          mrn = 'patient_id',
          enc = 'encounter_id')
      head(aki)
    }) # eventReactive's closing brackets

    output$flagger_output <- renderTable({
      print(data)
      data()
    })


  }

  # Run the app ----
  shinyApp(ui = ui, server = server)
}
