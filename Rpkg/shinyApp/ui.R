library(shiny)
library(shinyWidgets)
library(shinythemes)

library(DT)

# Define UI ----
ui <- fluidPage(shinythemes::themeSelector(),
  
  # Title
  titlePanel(h2('AKI Flagger GUI')),
  
  # Sidebar panel for inputs
  sidebarPanel(
    
    # Read in file input
    fileInput("file", h4("File input"),
              accept = c(".csv")),
    
    # Parameter options title:
    tags$h3("Flagger parameters:"),
    
    # Link to documentation
    tags$div(class="header", checked=NA,
             tags$p("Not sure what the flagger parameters are? If so, ", style = "display: inline;"),
             tags$a(href="https://akiflagger.readthedocs.io", "click here!")
    ),
    
    br(),
    br(),
    
    # Parameter options:
    materialSwitch(inputId = "HB_trumping", 
                   label = HTML("<b>Historical baseline trumping</b>"),
                   status = 'primary'),
    
    materialSwitch(inputId = "eGFR_impute", 
                   label = HTML("<b>CKD-EPI based creatinine imputation</b>"), 
                   status = "primary"),
    
    # Padding slider
    sliderInput('padding', "Padding (in hours)", min=0, max=8, value = 4, step = 0.5),
    
    # Calculate AKI button
    div(
      style = "display:inline-block;width:100%;text-align: center;",
      actionButton("calcAKI", label = "Calculate AKI", icon = icon("calculator"))
    ),
    
    br(),
    br(),
    
    div(
      style = "display:inline-block;width:100%;text-align: center;",
      uiOutput("download")
    )
  ), # End of sidebar panel
  
  # Main panel
  mainPanel(
    "File preview:",
    DT::dataTableOutput("previewTable"),
    br(),
    
    textOutput("aki_preview_text"),
    DT::dataTableOutput("aki")
  )
  
)