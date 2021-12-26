library(shiny)
#library(shinyWidgets)
library(data.table)
library(DT)

# Source the main function
message(list.files("../akiFlagger/R"))
source("../akiFlagger/R/returnAKIpatients.R")

ticker <- 0
message(ticker)
# Ideally,
# toy <- read.csv(text = getURL("htpps://raw.githubusercontent.com/isaranwrap / toy.csv )) # or some central repository

ui <- bootstrapPage(
  fluidRow(sidebarPanel(
    fileInput("file1", h4("File input"),
              accept = c(".csv")), # File input ends here

    checkboxGroupInput("definitions", "Select your definition(s):",
                       choices = c("RMW", "HBT", "BCI"), inline = TRUE), # Definition selection ends here

    actionButton("calcAKI", "Calculate AKI") # Calculate AKI button here

  ),
  mainPanel(
    verbatimTextOutput("status"),
    #DT::dataTableOutput("inputTable"),
    DT::dataTableOutput("outTable")
    )
  )
  #plotOutput()
)

server <- function(input, output, session) {

  datasetInput <- reactive({

    req(input$file1)

    df626 <- data.table::fread(input$file1$datapath)

    # Pre-process
    df626$time <- as.POSIXct(df626$time)
    #setDT(df626)
    df626
  })

  output$inputTable <- DT::renderDataTable({
    DT::datatable(datasetInput())
  })

  output$status <- renderPrint({
    if (input$calcAKI > 0) {
      isolate("Calculation complete.")
    } else {
      return(paste("akiflagger.readthedocs.io", as.character(typeof(datasetInput()$time))))
    }
  })

  output$outTable <- DT::renderDataTable({
    DT::datatable(
      datasetInput()
      )
  })
    #observeEvent(input$calcAKI, {
    #})

  output$outTable <- DT::renderDataTable({
    dInp <- datasetInput()

    dInp$time <- as.POSIXct(dInp$time)
    dInp <- dInp[order(time), .SD, by = patient_id]
    dInp[, min_creat48 := sapply(.SD[, time], function(x) min(creatinine[between(.SD[, time], x - as.difftime(2, units = "days"), x)])), by=patient_id]
  })

  # output$displayTable <- DT::renderDataTable({
  #   observeEvent(input$calAKI, {
  #   isolate()
  #   })
  # })
  # Bookmarking - save for now
  # observe({
  #   reactiveValuesToList(input)
  #   session$doBookmark()
  # })
  # onBookmarked(updateQueryString)
  # output$AKI <- eventReactive(input$calcAKI, {
  #   returnAKIpatients(setDT(isolate(datasetIntermediate())))
  # })
}

shinyApp(ui, server)
