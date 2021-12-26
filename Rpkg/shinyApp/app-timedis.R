library(shiny)
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
    DT::dataTableOutput("datasetInput"),
    verbatimTextOutput("status"),
    plotOutput("histogram")

  )
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

  output$histogram <- renderPlot({
    hist(datasetInput()$time, breaks = 55L)
  })

  output$datasetInput <- DT::renderDataTable(
    datasetInput()
  )

}

shinyApp(ui, server)
