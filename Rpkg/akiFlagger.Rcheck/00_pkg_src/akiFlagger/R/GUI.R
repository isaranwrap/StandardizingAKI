#' GUI Shiny App
#' @export
runGUI <- function() {
  shiny::runApp(appDir = system.file("shinyApp", package = "akiFlagger"))
}
