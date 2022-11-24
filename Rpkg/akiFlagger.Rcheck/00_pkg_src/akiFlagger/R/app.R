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
library(ggplot2)
library(zoo)
library(DT)

baseFolder <- file.path("/Users", "Praveens", "github", "StandardizingAKI")
dataFolder <- file.path(baseFolder, "data")
logoFolder <- file.path(baseFolder, "logos/hex")
scriptsFolder <- file.path(baseFolder, "scripts")
source(file.path(scriptsFolder, "plotAKIoverlap.R"))
source(file.path(scriptsFolder, "returnAKIpatients.R"))
#
#
#/Users/Praveens/github/StandardizingAKI/Rpkg/akiFlagger/www
ui <- fluidPage(theme = shinytheme("sandstone"),
                sidebarPanel(
                  headerPanel(paste("AKI Flagger", today())),
                  fileInput("file", "FILE",
                            accept = "text/csv"), # END FILE INPUT
                  img(src=file.path(logoFolder, "07hexlogo.png"), align = "right",
                      height = 64, width = 64), # Image Logo
                  checkboxGroupButtons("definitionSelector",
                                       "DEFINITION:",
                                       c("RMW", "HBT", "BCI"),
                                       selected = c("RMW")),
                  selectInput("happyIndex", label = "happyBoolean", choices = c("happy", "notHappy"), selected = "happy", multiple = T, selectize = T),
                  #inline = TRUE), # END CHECKBOX INPUT
                  sliderInput("padding", "PADDING",
                              value = 4, min = 0, max = 8), # END SLIDER INPUT
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

  definitionRMW <- reactive(tableIN() %>% returnAKIpatients(padding = c(input$padding, "hours")))
  definitionHBT <- reactive(
    tableIN() %>% returnAKIpatients(padding = c(input$padding, "hours"), HB_trumping = TRUE)
  )
  definitionBCI <- reactive(
    definitionBCI <- tableIN() %>% returnAKIpatients(padding = c(input$padding, "hours"), eGFR_impute = TRUE)
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
      tableReactive <- tableIN() %>% returnAKIpatients(padding = c(input$padding, "hours"), RM_window = T)
    } else if ("HBT" %in% input$definitionSelector) {
      tableReactive <- tableIN() %>% returnAKIpatients(padding = c(input$padding, "hours"), HB_trumping = T)
    } else if ("BCI" %in% input$definitionSelector) {
      tableReactive <- tableIN() %>% returnAKIpatients(padding = c(input$padding, "hours"), eGFR_impute = T)
                                                           #padding = c(input$padding, "hours"))
    }
    return(tableReactive)
  }
  )

  output$venn <- shiny::renderPlot({

    plotAKIoverlap(tableREACTIVE())
  })

  output$download <- shiny::downloadHandler(
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

