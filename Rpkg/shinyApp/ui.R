library(DT)
library(shiny)
library(shinyWidgets)
library(shinythemes)

# Define UI ----
  ui <- fluidPage(shinythemes::themeSelector(), # Selector to iterate between themes
                  tags$head(
                    tags$link(rel = "stylesheet", type = "text/css", href = "style.css")
                  ),
                  titlePanel("AKI Flagger GUI"),
                  sidebarLayout(
                    sidebarPanel(
                      HTML('<style type="text/css">
                      .row-fluid { width: 50%; }
                      .well { background-color: #99CCFF; }
                      .shiny-html-output { font-size: 16px; line-height: 21px; }
                    </style>'),
                      fileInput("file", h4("File input"),
                                accept = c("text/csv",
                                           "text/comma-separated-values,text/plain",
                                           ".csv")),
                      h4('Column identifier information'),
                      textInput("patient_id", "Patient identifier",
                                value = "Enter the name for your patient id column"),
                      textInput("encounter_id", "Encounter identifier (optional)",
                                value = "Enter the name for your encounter id column"),
                      textInput("inpatient_id", "Inpatient identifier",
                                value = "Enter the name for your inpatient column"),
                      textInput("admission_id", "Admission identifier (optional)",
                                value = "Enter the name for your admission column"),
                      textInput("creat_id", "Creatinine identifier",
                                value = "Enter the name for your creatinine column"),
                      textInput("time_id", "Time identifier",
                                value = "Enter the name for your time column"),
                      # textInput("patient_id", "Patient identifier",
                      #           value = "mrn"),
                      # textInput("encounter_id", "Encounter identifier (optional)",
                      #           value = "enc"),
                      # textInput("inpatient_id", "Inpatient identifier",
                      #           value = "inpatient"),
                      # textInput("admission_id", "Admission identifier (optional)",
                      #           value = "admission"),
                      # textInput("creat_id", "Creatinine identifier",
                      #           value = "creatinine"),
                      # textInput("time_id", "Time identifier",
                      #           value = "time"),
                      materialSwitch(inputId = "HB_trumping", label = "Historical baseline trumping?", status = "warning", value = FALSE),
                      #materialSwitch(inputId = "eGFR_impute", label = "eGFR-based imputation?", status = "warning", value = FALSE),
                      sliderInput('padding', "Padding (in hours)", min=0, max=8, value = 4, step = 0.5),
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
