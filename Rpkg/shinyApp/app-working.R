library(shiny)
library(tidyverse)
#library(shinyWidgets)
library(data.table)
library(DT)
library(akiFlagger)

# Source the main function
message(list.files("../akiFlagger/R"))
source("../akiFlagger/R/returnAKIpatients.R")

# Ideally,
# toy <- read.csv(text = getURL("htpps://raw.githubusercontent.com/isaranwrap / toy.csv )) # or some central repository
ui <- bootstrapPage(
  sidebarPanel(
    fileInput("file1", h4("File input"),
              accept = c(".csv")), # File input ends here
    radioButtons("sep", "Separator",
                 choices = c(Comma = ",",
                             Tab = "\t")), # Separator selector ends here
    checkboxGroupInput("definitions", "Select your definition(s):",
                       choices = c("RMW", "HBT", "BCI"), inline = TRUE), # Definition selection ends here
    actionButton("calcAKI", "Calculate AKI", class = "btn btn-primary") # Calculate AKI button here
  ),
  mainPanel(
    DT::dataTableOutput("context"),
    verbatimTextOutput("status"),
    #plotOutput(),
    DT::dataTableOutput("AKI")
  )
  #plotOutput()
)

server <- function(input, output, session) {

  #inputFile <- reactive(paste0(input$file1))

  output$definitions <- renderText({ input$definitions })

  inputTable <- reactive({
    req(input$file1)

    df <- data.frame(
      Name = c("patient_id", "inpatient", "time", "creatinine"),
      Value = as.character(),
      stringsAsFactors = FALSE
    )
  })

  datasetInput <- reactive({
    req(input$file1)

    df <- read.csv(input$file1$datapath)

    # Pre-process
    df
  })

  output$context <- renderDT({
    req(input$file)

    df <- read.csv(input$file$datapath)
  })
  datasetIntermediate <- reactive({

    intermediateData <- data.frame(matrix(nrow = dim(datasetInput())[1],
                                          ncol = dim(datasetInput())[2]))
    colnames(intermediateData) <- c("patient_id", "inpatient", "time", "creatinine")
    intermediateData$patient_id <- datasetInput()$patient_id
    intermediateData$inpatient <- datasetInput()$inpatient
    intermediateData$creatinine <- datasetInput()$creatinine

    intermediateData$time <- as.POSIXct(datasetInput()$time)

    data.frame(intermediateData)
  })
  #inputTable()

  output$status <- renderPrint({
    if (input$calcAKI > 0) {
      isolate("Calculation complete.")
    } else {
      return("akiflagger.readthedocs.io")
    }
  })

  output$AKI <- eventReactive(input$calcAKI, {
    returnAKIpatients(setDT(isolate(datasetIntermediate())))
  })

  aki <- eventReactive(input$calcAKI, {

    pad_val <- input$padding
    df <- inputFile()
    df <- transform(df, time = as.POSIXct(time, format = "%Y-%m-%d %H:%M:%S"))
    aki <- returnAKIpatients(df)#, HB_trumping = input$HB_trumping,
    #eGFR_impute = input$eGFR_impute, padding = as.difftime(input$padding, units = 'hours'))
    validate(
      need(class(aki) == c('data.table', 'data.frame'), aki)
    )
    return(aki)
  })

  #output$dataTableCap <- DT::renderDataTable(inputFile)

}

shinyApp(ui, server)
