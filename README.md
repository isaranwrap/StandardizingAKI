# AKI Flagger <img src="https://github.com/isaranwrap/StandardizingAKI/blob/master/logos/hex/07hexlogo.png?raw=true" alt="hex-AKI FlaggeR_github" width="200" align = "right"/>

<img src="https://insights.som.yale.edu/sites/default/files/styles/square_xl/public/2023-10/F._Perry_Wilson_thumb.webp?h=8a7fc05e&itok=gDP0OqlB" width="300">

#### [Advisor](https://medicine.yale.edu/intmed/ctra/profile/francis_p_wilson/): Dr. Francis Perry Wilson, MD MSCE 

<img src="https://github.com/isaranwrap/StandardizingAKI/blob/master/logos/ysm/02ctra_logo.png?raw=true" alt="CTRA" width="300" align = "center"/>

### Yale School of Medicine, Section of Nephrology, [Clinical and Translational Research Accelerator](https://medicine.yale.edu/intmed/ctra/)

<br>


---

## Getting started

There is a [walk-through notebook](https://colab.research.google.com/github/isaranwrap/StandardizingAKI/blob/master/notebooks/GettingStarted.ipynb) available on Github to introduce the necessary components and parameters of the flagger. The notebook can be accessed via Google Colab notebooks. The notebook has also been adapted in the [documentation](https://akiflagger.readthedocs.io/en/latest/). 

---

### Introduction

Acute Kidney Injury (AKI) is a sudden often reversible decline in kidney function and damage marked by an increase in the serum creatinine levels (amongst other biomarkers) of the patient. Kidney Disease Improving Global Outcomes (KDIGO) has a set of guidelines and standard definitions of AKI:

* *Stage 1*: 50% increase in creatinine within 7 days or 0.3 mg/dL increase in creatinine in within 48 hours

* *Stage 2*: 100% increase in (or doubling of) creatinine within 7 days

* *Stage 3*: 200% increase in (or tripling of) creatinine within 7 days

This package contains a flagger to determine if a patient has developed AKI based on longitudinal data of serum creatinine measurements. More information about the specific data input format can be found in the documentation under the *Getting Started* section.

## Installation

You can install the flagger with ``pip``. Simply type the following into command line and the 
package should install properly.

```python 
pip install akiFlagger
```

To ensure that it is working properly, you can open a Python session and test it with.

```python
import akiFlagger

print(akiFlagger.__version__)

>> '1.0.8'
```

Alternatively, you can download the source and wheel files to build manually from https://pypi.org/project/akiFlagger/.


