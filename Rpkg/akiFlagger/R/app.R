## Ishan Saran, Yale School of Medicine
## Advisor: Dr. Francis Perry Wilson, Professor of Nephrology
##
##
## akiflagger.readthedocs.io
## pypi.com/project/akiFlagger
##
## | 二零二二年 |
## | 三月十四日 |

library(shiny)
library(shinythemes)
library(VennDiagram)
library(shinyWidgets)
library(data.table)
library(lubridate)
library(tidyverse)
library(zoo)
library(DT)

source("plotAKIoverlap.R")
source("returnAKIpatients.R")
baseFolder <- file.path("/Users", "saranmedical-smile", "AKIFlagger")
dataFolder <- file.path(baseFolder, "data")
imageFolder <- file.path(baseFolder, "images")

saveJSON <- function(dataframe, outFP = file.path(dataFolder, "appOUT.json")) {
  return(write(jsonlite::toJSON(dataframe), file = outFP))
}

ui <- fluidPage(theme = shinytheme("sandstone"),
  sidebarPanel(
    headerPanel(paste("AKI Flagger", today())),
    fileInput("file", "FILE",
              accept = "text/csv"), # END FILE INPUT
    img(src="hex-AKI FlaggeR_github.png", align = "right",
        height = 64, width = 64), # Image Logo
    checkboxGroupButtons("definitionSelector",
                       "DEFINITION:",
                       c("RMW", "HBT", "BCI"),
                       selected = c("RMW")),
                       #inline = TRUE), # END CHECKBOX INPUT
    sliderInput("padding", "PADDING",
                value = 4, min = -8, max = 8), # END SLIDER INPUT
    actionButton("go", "Compute AKI", icon("calculator")), # END ACTION BUTTON
    downloadButton('download',"Download the data"),
    uiOutput('downloadData') # END DOWNLOAD BUTTON
    ),
  mainPanel(
    DT::DTOutput("tableOUT")
  ),
  fluidRow(
    wellPanel(
      plotOutput("venn")
    )
    # wellPanel(img(src="hex-AKI FlaggeR_github.png",
    #               height = 46, width = 46),) # Image Logo)
  )
)


# Define server function
server <- function(input, output, session) {

  tableIN <- reactive({

    if (!is.null(input$file)) {
      dataframe <- data.table::fread(input$file$datapath)

      return(dataframe)
    } else {
      return()
    }
  })

  definitionRMW <- reactive(tableIN() %>% returnAKIpatients_RMW(padding = c(input$padding, "hours")))
  definitionHBT <- reactive(
    tableIN() %>% returnAKIpatients_HBT(padding = c(input$padding, "hours"))
  )
  definitionBCI <- reactive(
    definitionBCI <- tableIN() %>% returnAKIpatients_BCI(padding = c(input$padding, "hours"))
  )

  tableREACTIVE <- eventReactive(input$go, {
    message(length(input$definitionSelector))

    if (length(input$definitionSelector) == 3) {
      dataframe <- tableIN()
      dataframe$RMW <- definitionRMW()$aki
      dataframe$HBT <- definitionHBT()$aki
      dataframe$BCI <- definitionBCI()$aki
      return(dataframe)

    } else if (length(input$definitionSelector == 2)) {
      message("two of the 3 have been selected")

    }
    if ("RMW" %in% input$definitionSelector) {
      tableReactive <- tableIN() %>% returnAKIpatients_RMW(padding = c(input$padding, "hours"))
    } else if ("HBT" %in% input$definitionSelector) {
      tableReactive <- tableIN() %>% returnAKIpatients_HBT(padding = c(input$padding, "hours"))
    } else if ("BCI" %in% input$definitionSelector) {
      tableReactive <- tableIN() %>% returnAKIpatients_BCI(eGFR_impute = T,
                                        padding = c(input$padding, "hours"))
    }
    return(tableReactive)
  }
  )

  writeOut <- eventReactive(input$go, {
    saveJSON(tableREACTIVE())
    message(list.files(dataFolder))
  })

  output$venn <- renderPlot({
    plotAKIoverlap(tableREACTIVE())
  })

  output$download <- downloadHandler(
    filename = function() {
      if (input$file$name == "") {
        paste("Untitled_aki", "csv", sep=".")
      } else {
        paste(substr(input$file$name, 1, nchar(input$file$name) - 4), "_aki.csv", sep = "")
      }
    },
    content = function(file) {
      write.csv(tableREACTIVE(), file, row.names = FALSE)
    }
  )

  output$tableOUT <- DT::renderDT({
    tableREACTIVE()
  }, options = list(pageLength = 6))
} # server


# Create Shiny object
shinyApp(ui = ui, server = server)

## Back-up file; (local) master file located in:
## ~/AKIFlagger/scripts

