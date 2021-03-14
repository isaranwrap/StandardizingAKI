pkgname <- "akiFlagger"
source(file.path(R.home("share"), "R", "examples-header.R"))
options(warn = 1)
library('akiFlagger')

base::assign(".oldSearch", base::search(), pos = 'CheckExEnv')
base::assign(".old_wd", base::getwd(), pos = 'CheckExEnv')
cleanEx()
nameEx("returnAKIpatients")
### * returnAKIpatients

flush(stderr()); flush(stdout())

### Name: returnAKIpatients
### Title: Flag patients for AKI
### Aliases: returnAKIpatients

### ** Examples

returnAKIpatients(toy)



### * <FOOTER>
###
cleanEx()
options(digits = 7L)
base::cat("Time elapsed: ", proc.time() - base::get("ptime", pos = 'CheckExEnv'),"\n")
grDevices::dev.off()
###
### Local variables: ***
### mode: outline-minor ***
### outline-regexp: "\\(> \\)?### [*]+" ***
### End: ***
quit('no')
