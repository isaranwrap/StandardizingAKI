library(shiny)
library(shinyWidgets)
library(shinythemes)

library(DT)

# Define UI ----
  ui <- fluidPage(shinythemes::themeSelector(), # Selector to iterate between themes
                  tags$head( # CSS styling via style.css in www/ folder - mainy for padding slider right now
                    tags$link(rel = "stylesheet", type = "text/css", href = "style.css")),
                  titlePanel("AKI Flagger GUI"), # Title panel
                  sidebarLayout(
                    sidebarPanel(
                      HTML('<style type="text/css">
                      .row-fluid { width: 50%; }
                      .well { background-color: #99CCFF; }
                      .shiny-html-output { font-size: 16px; line-height: 21px; }
                    </style>'),

                      # Read in file input
                      fileInput("file", h4("File input"),
                                accept = c(".csv")),

                      # Parameters
                      h4('Parameter options:'),
                      fluidRow(
                        column(1, actionLink("ab1", label = "", icon = icon("info-circle"),
                                               onclick ="window.open('https://akiflagger.readthedocs.io/en/latest/', '_blank')")),
                        column(12, materialSwitch(inputId = "HB_trumping", label = "Historical baseline trumping?",
                                                  status = "warning", value = FALSE))),

                      # Padding slider
                      sliderInput('padding', "Padding (in hours)", min=0, max=8, value = 4, step = 0.5),

                      # Calculate AKI button
                      div(
                        style = "display:inline-block;width:100%;text-align: right;",
                        actionButton("calcAKI", label = "Calculate AKI", icon = icon("calculator"))
                      ),
                    ),
                    mainPanel(
                      "File preview:",
                      DT::dataTableOutput("contents"),
                      br(),
                      "Returned output:",
                      DT::dataTableOutput("flagger_output"),

                      # Download data goes here
                      uiOutput("download")
                    )
                    ))
