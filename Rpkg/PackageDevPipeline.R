### This R file contains the list of commands I executed (in order, as much as I could)
##  for the development of the R package, including (most usefully) the use_this commands
#   I called to build all the directories and ancillary files. // I also use addRW as shorthand for addRollingWindowAKI

# Imports
library(devtools) # devtools is the main set of packages for pkg development
packageVersion("devtools") # needs to be version 2.3.1.x+
library(tidyverse) # for data wrangling
library(fs) # for managing file systems

# Step 1: Create package (w/ roxygen2)
create_package('~/Desktop/akiFlagger/Rpkg/akiFlagger')

# Step 2: Initialize git repository
# Use git creates the .git/ directory and adds .Rhistory, .RData, .gitignore, etc...
use_git() # I initialized a git repository (that I can hopefully link up with the Python project)
dir_info(all=T, regexp = '^[.]git$') %>% select(path, type, user) # Ensure .git exists

# Step 3: Create the functions you'd like to add in to your package
# After creating the addRollingWindowAKI.R in the R/ folder, the following command integrates the files with the package
#use_r("addRollingWindowAKI") # And I would do this for as many functions as I have (2 for the flagger)
#use_r("addBackCalcAKI") # And ONLY the definition (no library imports or nuthin') goes in the R file.
use_r("returnAKIpatients") # UPDATED Feb 3, 2021 --> single col output now

# Step 4: Load the package and test functionality (iteratively)
load_all() # load_all() is the best way to iteratively build, install, and test the package

addRollingWindowAKI(3) # I modified addRW.R to return the current working directory, dataframe=3 (first param) means nothing
# Correct output: "/Users/saranmedical-smile/Desktop/akiFlagger/Rpkg/akiFlagger"
# ... works! :)

# Note, though, that it doesn't exist in the global workspace
exists("returnAKIpatients", where = globalenv(), inherits=FALSE) # Outputs FALSE

# Step 5: Commit addRW --> I did this from terminal via:
>> cd Rpkg/akiFlagger # this code won't run bit it's how I committed
>> git add R/addRollingWindowAKI.R
>> git commit -m "Added first function addRollingWindowAKI.R to R/ functions folder." # associated commit message
# And, in general, we should be commiting after every step

# Step 6: Once we ensure that it's working overall (with load_all()), it's also useful to check each individual component
# check() achieves this.. Command + Shift + E is a shortcut
check() # 0 errors | 1 warning | 1 note ... always better to deal w/ problems earlier rather than later
# The warnings I'm getting right now are the bindings for the internal variables within the package.

# Step 7: Edit DESCRIPTION file, add license in (many of the following steps can be done in parallel/in a different order)
use_mit_license("Ishan Saran, Shivam Saran")

# Step 8: Document functions in R/
## Placing the cursor the function, Code > Insert Roxygen skeleton inserts the skeleton for documentation
document() # After filling in the barebones roxygen template, document() builds the documentation

# ---------- at this point, I stop following the tutorial walkthrough in R packages ------------ #
# But the next steps would be running check() again and then install() installs the
# package into your library and can be used w/ library(akiFlagger)
# This corresponds to sections 2.13 - 2.14 in the tutorial. I'll reconvene with the tutorial after I make the necessary accomodations to the package

# Resuming package development on Nov 11, 2020; Starting section 2.14 | install() now that I fixed the 1 warning
# which corresponded to the internal variables not being referenced

# document() --> check() --> install() # install() corresponds to Build > Install and Restart

# Once that's complete, I just need to develop a test suite for the package, and it's ready for deployment...

# Step 9: Write unit tests with use_testthat()
## which creates a folder called tests/ which contains the unit tests & testthat.R script for running those tests
## use_test() creates the file to write a single unit test into

# Step 10 (optional): Add data to package (for akiFlagger, toy.csv & out.csv)




