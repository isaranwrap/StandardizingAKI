# akiFlagger

## Introduction

Acute Kidney Injury (AKI) is a sudden onset of kidney failure and damage marked by an increase in the serum creatinine levels (amongst other biomarkers) of the patient. Kidney Disease Improving Global Outcomes (KDIGO) has a set of guidelines and standard definitions of AKI:

* *Stage 1*: 50% increase in creatinine in < 7 days or 0.3 increase in creatinine in < 48 hours

* *Stage 2*: 100% increase in (or doubling of) creatinine in < 48 hours

* *Stage 3*: 200% increase in (or tripling of) creatinine in < 48 hours

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

akiFlagger.__version__

>> '0.0.4'
```

Alternatively, you can download the source and wheel files to build manually from https://pypi.org/project/akiFlagger/.


## Getting started

This package is meant to handle patient data. Let's walk through an example of how to use this package
with some toy data since real patient data is probably protected health information.

Once you've installed the package following the instructions in `Installation`, you're ready to get started.
To begin with, we'll import the ``akiFlagger`` module as well as the trifecta ``pandas``, ``numpy``, and ``matplotlib``.


```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as pyplot

import akiFlagger
print(akiFlagger.__version__)
>> '0.0.4'
```

The input dataframe needs to contain the correct columns in order for the flagger to recognize and deal with the proper variables.
Some pre-processing may be necessary. Here are the required columns depending on which calculation methods
you are interested in:

* *Rolling-window*: **mrn**, **enc**, **admission**, **creatinine**, and **time**. 
* *Back-calculation*: **mrn**, **enc**, **admission**, and **time**. 
* *eGFR-imputed baseline creatinine*: **age**, **sex** (female or not), and **race** (black or not).

### Example: Rolling-window

Generally speaking, real patient data will be protected health information, so this walkthrough will use toy data. 
The flagger comes with a built-in generator for toy data, which we can call with the following command.

```python
df = akiFlagger.generate_toy_data()

>> Successfully generated toy data!
```



We can take a look at what our dataframe looks like. ``df.head()`` should yield this:


The column names should be named exactly as they are in the examples. The full list of acceptable names can be found in the *returnAKIpatients()* function in the :ref:`genindex` section.

Running the following should run the flagger for ``rolling-window`` AKI.

```python
rw = akiFlagger.returnAKIpatients(df, aki_calc_type = 'rolling_window')
```

Now the data frame has increased in size by quite a bit! Let's check out whats been added:

The **mincreat_48hr** and **mincreat_7day** give us the running minimum for the selected window. Note that
*returnAKIpatients()* takes ``cond1time`` and ``cond2time`` as optional arguments. By default, these values are set to 
'48hours' and '168hours', which correspond to the 2-day and 7-day rolling window time periods. However, often some researchers
like to put a padding of some sort on the windows to account for logging lag. In this case, we would modify the ``cond1time`` and
``cond2time`` variables to have the padding, for 4 hours, say, you would have '52hours' and '172hours'.

The **deltacreat_48hrs** and **deltacreat_7day** give us the change in creatinine from the corresponding minimum values.
This is where the check occurs to qualify as stage 1, 2, or 3 AKI. 

The **stage 1, stage 2**, and **stage3** columns are the AKI stages as per the KDIGO standards and if any of them are *True*,
then the **rollingwindow_aki** column will be *True*. Otherwise, **rollingwindow_aki** will be *False*.

I encourage you to play around more with the dataframe to get an idea for how the data should be shaped and how the flagger works.

## Example: Back-calculation

Say we wanted to see who has AKI according to the back-calculation method. Now, we need to have information about the
age, sex, and race of the patient. The built-in generator has an option to include patient demographics:

.. code-block:: python

    df = akiFlagger.generate_toy_data(include_demographic_info = True)

    >> Successfully generated toy data!
    
Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

