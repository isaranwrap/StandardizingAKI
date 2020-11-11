
<!-- README.md is generated from README.Rmd. Please edit that file -->

# akiFlagger

<!-- badges: start -->

<!-- badges: end -->

Acute Kidney Injury (AKI) is a sudden onset of kidney failure and damage
marked by an increase in the serum creatinine levels (amongst other
biomarkers) of the patient. Kidney Disease Improving Global Outcomes
(KDIGO) has a set of
[guidelines](https://kdigo.org/guidelines/acute-kidney-injury/) and
[standard
definitions](http://www.european-renal-best-practice.org/sites/default/files/u33/ndt.gfs375.full_.pdf)
of AKI:

  - *Stage 1*: 50% increase in creatinine in \< 7 days or 0.3 increase
    in creatinine in \< 48 hours

  - *Stage 2*: 100% increase in (or doubling of) creatinine in \< 7 days

  - *Stage 3*: 200% increase in (or tripling of) creatinine in \< 7 days

This package contains a flagger to determine if a patient has developed
AKI based on longitudinal data of serum creatinine measurements.

## Installation

The package can be installed via [CRAN](https://CRAN.R-project.org).

``` r
install.packages("akiFlagger")
```

Alternatively, you can install the development version of the package
from [GitHub](https://github.com/isaranwrap) with:

``` r
# install.packages("devtools")
devtools::install_github("isaranwrap/akiFlagger")
```

## Getting Started

There is a [walk-through
vignette](https://colab.research.google.com/github/isaranwrap/StandardizingAKI/blob/master/GettingStarted.ipynb)
available on Github to introduce the necessary components and parameters
of the flagger. The notebook has also been adapted in the
[documentation](https://akiflagger.readthedocs.io/en/latest/).
