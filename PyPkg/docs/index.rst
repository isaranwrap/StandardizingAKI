.. akiFlagger documentation master file, created by
   Ishan Saran on Thu Aug 6 07:44:21 2020.

.. role::  raw-html(raw)
    :format: html
    
========================================
Welcome to the AKIFlagger documentation!
========================================

.. image:: ../../logos/hex/04hexlogo.png
	:width: 200
	:alt: AKI Flagger logo
	:align: right

..
	_https://sublime-and-sphinx-guide.readthedocs.io/en/latest/images.html

.. toctree::
   :maxdepth: 2
   :caption: Contents

   Introduction
   Installation
   GettingStarted
   AdditionalFeatures
   MoreInformation


Introduction
============

Acute Kidney Injury (AKI) is a sudden onset of kidney failure and damage marked by an increase in the serum creatinine levels
(amongst other biomarkers) of the patient. Kidney Disease Improving Global Outcomes (KDIGO) has a set of guidelines and standard definitions 
of AKI:

* *Stage 1:* 50% increase in creatinine in <= 7 days or 0.3 increase in creatinine in <= 48 hours
* *Stage 2:* 100% increase in (or doubling of) creatinine in <= 48 hours
* *Stage 3:* 200% increase in (or tripling of) creatinine in <= 48 hours

This package contains a flagger to determine if a patient has developed AKI based on the criterion above.
More information about the specific data input format can be found in the `Getting started` section. 

Installation
============

.. option:: Python

You can install the flagger with ``pip``. Simply type the following into command line and the 
package should install properly.

.. code-block:: python

   pip install akiFlagger

To ensure that it is working properly, you can open a Python session and test it with

.. code-block:: python

   import akiFlagger

   akiFlagger.__version__

   >> '1.0.10'

.. option:: R

You can install the flagger through `CRAN <https://cran.r-project.org/>`_. Simply type the following into an RStudio terminal and the package should install properly.

.. code-block:: R

   install.packages('akiFlagger')

To ensure that it is working properly, you can open an RStudio session and test it with

.. code-block:: R

    library(akiFlagger)

Getting started
===============

This package is meant to handle patient data. Let's walk through an example of how to use this package
with some toy data since real patient data is probably protected health information.

Once you've installed the package following the instructions in `Installation`, you're ready to get started.
To begin with, we'll import the ``akiFlagger`` module.

.. option:: Python
.. code-block:: python

    import akiFlagger

    print(akiFlagger.__version__)

    from akiFlagger import AKIFlagger, generate_toy_data
    
    >> '1.0.10'

.. option:: R
.. code-block:: R

    library(akiFlagger)

    ?returnAKIpatients

    > ℹ Rendering development documentation for 'returnAKIpatients'

Let's start off by generating some toy data.
--------------------------------------------

.. option:: Python
The flagger comes with a built-in generator of a toy dataset to demonstrate how it works. Simply call the `generate_toy_data()` function. By default, the toy dataset has 100 patients, but let's initialize ours with 1000 patients.

.. code-block:: python

    toy = generate_toy_data(num_patients=1000)

    print('Toy dataset shape: {}'.format(toy.shape))

    >> Successfully generated toy data!
    
       Toy dataset shape: (9094, 6)

The toy dataset comes with columns for the patient identifier, whether the measurement was taken in an inpatient or outpatient setting, the creatinine measurement and time at which the measurement was taken. ``toy.head()`` should yield something like this:

.. csv-table::
    :file: ../doc_csvs/python/toy_head.csv

.. option:: R

The R package comes with a built-in dataset, `toy`. The toy dataset comes with columns for the patient identifier, inpatient, the creatinine measurement and the time at which the measurement was taken. ``head(toy)`` should yield something like this:

.. csv-table::
    :file: ../doc_csvs/r/toy_headR.csv

.. admonition:: Tip!

    In order to calculate AKI, the flagger expects a dataset with certain columns in it. Depending on the type of computation you are interested in, your dataset will need to have different columns. Here's a brief rundown of the necessary columns. 

    * *Rolling Minimum Window*: **patient_id**, **inpatient**, **time**, and **creatinine** 

    * *Historical Baseline Trumping*: **patient_id**, **inpatient**, **time**, and **creatinine**

    * *Baseline Creatinine Imputation*: **age** and **sex** (which defaults to female).

    ------------

    By default, the naming system is as follows:

    **patient_id → 'patient_id'** 

    **inpatient/outpatient → 'inpatient'**

    **creatinine → 'creatinine'** 
        
    **time → 'time'** 

    If you have different names for your columns, you **must specify them.** 

Example: Rolling Minimum Window
-------------------------------

The next code block runs the flagger and returns those patients who satisfy the AKI conditions according to the `KDIGO guidelines <https://kdigo.org/guidelines/>`_ for change in creatinine values by the rolling-window definition, categorized as follows:

*Stage 1:* **(1)** 50% ↑ in creatinine in <= 7 days OR **(2)** 0.3 mg/dL ↑ in creatinine in  <= 48 hours

*Stage 2:* 100\% ↑ (or doubling of) in creatinine in <= 7 days

*Stage 3:* 200\% ↑ (or tripling of) in creatinine in <= 7 days

.. option:: Python

.. code-block:: python

    flagger = AKIFlagger()

    out = flagger.returnAKIpatients(toy)

    out = out.reset_index() # By default, the returned output has the patient_id and time as hierarchical indices

    out.head()


We can take a look at what our dataframe looks like. ``out.head()`` yields this:

.. csv-table::
    :file: ../doc_csvs/python/rw_out.csv

Notice that the dataframe looks exactly the same as we inputted into the flagger save an extra column added, `aki`. This column has values of either 0, 1, 2, or 3, depending on which stage AKI the flagger found.
The flagger runs on a row-wise basis, meaning that each row is checked for the increase in creatinine. Should, for example, a patient meet the criterion multiple times within a single encounter, the flagger will flag each measurement as a case of AKI.

.. warning::

    The column names specified within the flagger should match the dataset exactly. The full list of acceptable names can be found
    in the *returnAKIpatients()* function in the :ref:`genindex` section. For certain cases, the flagger understands special names. For example, 
    `sex = 'male'` will autoconvert the sex column from female to male. But you still need to have a column named `male` in your data frame, otherwise an error will occur.

We can take a look at what the flagger flagged as AKI. ``out[out.aki > 0].head()`` should give a list of some patients which were flagged. From that, we can subset the dataset on any given patient:

.. code-block:: python
    
    out[out.aki > 0].head() # this will give the rows which were marked as AKI by the flagger
    out[out.patient_id == 19845] # from that, we can find which patients were flagged with AKI

.. csv-table::
    :file: ../doc_csvs/python/rw_flagged.csv

Notice how as we would expect, when the creatinine more than tripled from 0.34 to 1.12, the flagger correctly identified it as Stage 3 AKI. 

You can even look at aggregate counts if you wanted as follows (but don't take the numbers too seriously, of course, because this is toy data):

.. code-block:: python
    
    aki_counts = out.aki.value_counts()
    print('AKI counts')
    print('----------')
    print('No AKI: {}\nStage 1: {}\nStage 2: {}\nStage 3: {}'.format(aki_counts[0], aki_counts[1], aki_counts[2], aki_counts[3]))

    >>  AKI counts
        ----------
        No AKI: 571
        Stage 1: 211
        Stage 2: 99
        Stage 3: 70

You can play around with the output of the ``returnAKIpatients()`` function in-depth to get a better understanding of how the flagger is operating. There are even optional parameters such as ``add_min_creat = True`` within the flagger which includes some of the intermediate steps the flagger is generating along to calculate AKI. 
Next, we'll take a look at an example of the other AKI-calculation method, the back-calculation method.

.. option:: R

.. code-block:: R

    library(akiFlagger)
    
    out <- returnAKIpatients(toy)

    head(out)

We can take a look at what the flagger returns. ``head(out)`` should return:

.. csv-table::
    :file: ../doc_csvs/r/rw_out.csv

Notice that the dataframe looks exactly the same as we inputted into the flagger save an extra column added, `aki`. This column has values of either 0, 1, 2, or 3, depending on which stage AKI the flagger found.
The flagger runs on a row-wise basis, meaning that each row is checked for the increase in creatinine. Should, for example, a patient meet the criterion multiple times within a single encounter, the flagger will flag each measurement as a case of AKI.

.. warning::

    The patient dataset you input should have minimally these columns: ``patient_id``, ``inpatient``, ``time``, and ``creatinine``. If you are interested in demographic-based imputation, 
    you'll also want to include the ``age`` and ``sex`` columns. 

We can take a look at what the flagger flagged as AKI. ``head(out[out$aki > 0])`` should give a list of some patients which were flagged. From that, we can subset the dataset on any given patient:

.. code-block:: R

    head(out[out$aki > 0])
    
    out[out$patient_id == 13264]

.. csv-table::
    :file: ../doc_csvs/r/rw_flagged.csv

Notice how as we would expect, when the creatinine more than tripled from 0.1 to 0.72, the flagger correctly identified it as Stage 3 AKI. Additionally,
row 11 was flagged as stage 1 because that was a greater than 50% increase from 0.27 and row 12 was flagged because it was a greater than 100% increase from 0.27. Even though
the flagger is performing a row-wise computation, it is comparing the current creatinine value with the minimum in the past ``window1`` hours (defaults to 48 hours).


You can look at aggregate counts if you wanted as follows (but don't take the numbers too seriously, of course, because this is toy data):

.. code-block:: R

    table(out$aki)

    >>    0    1    2    3 
        1001   44   19   14 

Example: Historical Baseline Trumping 
-------------------------------------

Next, we'll run the flagger to "back-calculate" AKI; that is, using the **median outpatient creatinine values from 365 to 7 days prior to admission** to impute a baseline creatinine value. Then, we'll run the same KDIGO criterion (except for the 0.3 increase) comparing the creatinine value to baseline creatinine.

.. option:: Python
.. code-block:: python

    flagger = AKIFlagger(HB_trumping = True, add_baseline_creat = True)

    out = flagger.returnAKIpatients(toy)
    
    out.head()

.. csv-table::
    :file: ../doc_csvs/python/bc_out.csv

.. option:: R

.. code-block:: R

    out <- returnAKIpatients(toy, HB_trumping = T, add_baseline_creat = T)

    head(out)

.. csv-table::
    :file: ../doc_csvs/r/bc_out.csv

Actually, by default the toy dataset only has patient values :math:`\pm` 5 days from the admission date, and because the baseline creatinine value calculates using values from 365 to 7 days prior, you'll notice that the flagger reverts to the rolling window definition. 
This is important: in the absence of available baseline creatinine values, the flagger defaults to a rolling minimum comparison. Indeed, most of the checking for AKI occurs outside of period of hospitalization.
Normally, of course, patients won't have times restricted to just :math:`\pm` 5 days, but this is a good opportunity to showcase one of the flagger features: the **eGFR-based imputation of baseline creatinine**.

The following equation is known as the `CKD-EPI equation <https://www.kidney.org/content/ckd-epi-creatinine-equation-2021>`_  .

.. math::
    \begin{equation}
    GFR = 142 \times min(S_{cr} / \kappa, 1)^{\alpha} \times max(S_{cr} / \kappa, 1)^{-1.200} \times 0.9938^{Age} \times (1 + 0.012 f)
    \end{equation}

where:

- :math:`GFR`  :math:`(\frac{mL/min}{1.73m^2})` is the glomerular filtration rate
- :math:`S_{cr}`  :math:`(\frac{mg}{dL})` is the serum creatinine
- :math:`\kappa` (unitless) is 0.7 for females and 0.9 for males
- :math:`\alpha` (unitless) is -0.241 for females and -0.302 for males
- :math:`f` is 1 if female, 0 if male

The idea is as follows: based on the above equation, we assume a GFR of 75 and then use the age and sex of the patient to determine an estimate for the baseline creatinine. Theory aside, simply pass ``eGFR_impute = True`` into the flagger and this will add values where the patient was missing outpatient values 365 to 7 days prior to admission.

.. option:: Python
**Note:** The toy dataset doesn't come with demographic information by default, but simply passing ``include_demographic_info = True`` adds in a column for the age and sex variables. 

.. code-block:: python

    toy = generate_toy_data(num_patients=100, include_demographic_info = True)

    toy.head()

.. csv-table::
    :file: ../doc_csvs/python/toy_demo.csv

.. code-block:: python

    flagger = AKIFlagger(HB_trumping = True, eGFR_impute = True, add_baseline_creat = True,
                         sex = 'female')

    out = flagger.returnAKIpatients(toy)

    out.head()

.. csv-table::
    :file: ../doc_csvs/python/egfr_out.csv

.. option:: R

There are actually two toy datasets that come with the packages: ``toy`` and ``toy.demo``. ``toy.demo`` is the toy dataframe with columns for age, sex, and race. As such, all we have to do is run

.. code-block:: R

    out <- returnAKIpatients(toy.demo, HB_trumping = T, eGFR_impute = T)

    head(out)

.. csv-table::
    :file: ../doc_csvs/r/egfr_out.csv

Example: Baseline Creatinine Imputation
---------------------------------------

.. option:: Python

.. code-block:: python
    
    flagger = AKIFlagger(HB_trumping = True, eGFR_impute = True, add_baseline_creat = True)

    out = flagger.returnAKIpatients(toy)


.. option:: R

.. code-block:: R

    out <- returnAKIpatients(toy.demo, HB_trumping = T, eGFR_impute = T)

That about does it for the basics! There are a slew of other features, some of which are listed in the `Additional Features` section. For a full listing of the features and appropriate use cases, see the `Documentation` at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.

=============
Using the GUI
=============




========================================
Additional Features and Common Use Cases
========================================

For most use cases, you will just need to specify the AKI definition methodology (i.e. `rolling minimum window`, `historical baseline trumping`, or `baseline creatinine imputation`) and the AKI-column will be returned. There are a slew of other features, some of which are listed below. For a full listing of the features and appropriate use cases, see the `Documentation` at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.


**→ Adding padding to the rolling window**

It's often the case that you want to add some padding to the window to account for variations occurring on the floor (52 hour & 172 hour windows instead, for example). If the amount of padding you would like to add is the same for both the smaller and larger window, simply pass ``padding='_hours'`` filling the blank with the number of hours to add to the windows.
If the pad times are different between windows, the parameters ``pad1time`` and ``pad2time`` allow you to add just this padding to the initial windows of 48 and 172 hours. In fact, if you wanted a window of 36 hours, you could even set `pad1time = '-12hours'`; this is one way in which you could modify the rolling window. 

.. option:: Python

.. code-block:: python

    # Example 0: Adding 4-hour padding to windows

    flagger = AKIFlagger(padding = '4hours')

    example0 = flagger.returnAKIpatients(toy)

    example0[example0.aki > 0].head(3)

.. csv-table::
    :file: ../doc_csvs/python/example0.csv

.. option:: R

.. code-block:: R

    # Example 0: Adding 4-hour padding to windows

    example0 <- returnAKIpatients(toy, padding = as.difftime(4, units = 'hours'))

    head(example0[example0$aki > 0])

.. csv-table::
    :file: ../doc_csvs/r/example0.csv

**→ Working with different column names**

.. option:: Python
As an additional example, the patient identifier will often come in as *'PAT_MRN_ID'* or *'PAT_ENC_CSN_ID'* (or something of the sort) if it is coming from a typical clinical data warehouse/repository. Accordingly, these should be passed in as options to the flagger. 

.. code-block:: python

    # Example 1: Working with different column names 

    dataframe = toy.rename(columns = {'patient_id': 'PAT_MRN_ID', 'creatinine':'CREATININE', 'inpatient': 'INPATIENT', 'time': 'TIME'
                                      'age': 'AGE', 'female': 'SEX'})

    flagger = AKIFlagger(patient_id = 'PAT_MRN_ID', inpatient = 'INPATIENT', time = 'TIME', creatinine = 'CREATININE', age = 'AGE', sex = 'SEX')

    example1 = flagger.returnAKIpatients(dataframe)

    example1.head(3)

.. csv-table::
    :file: ../doc_csvs/python/example1.csv

.. option:: R

Say we had a dataframe which looked like this: 

.. csv-table::
    :file: ../doc_csvs/r/df_example1.csv

In order to pass it to the flagger, we need to shape our data in a way that the flagger will understand. This means converting the outpatient columns to inpatient, and specifying the names of the columns as follows

.. code-block:: R

    # Example 1: Working with different column names

    library(dplyr) # rename function from dplyr library 
    
    dataframe$OUTPATIENT <- !dataframe$OUTPATIENT # turn the dataframe into inpatient instead of outpatient by logically inverting it

    dataframe <- dataframe %>% rename('patient_id' = 'PAT_MRN_ID', 'inpatient' = 'OUTPATIENT', 'time' = 'TIME', 'creatinine' = 'CREATININE')
    
    head(returnAKIpatients(dataframe), n = 3L)

.. csv-table::
    :file: ../doc_csvs/r/example1.csv

**→ Adding in rolling-window minimum creatinines**

To add in the baseline creatinine, simply pass the flag ``add_min_creat = True`` to the flagger. This will add in two columns which contain the minimum values in the rolling window, which is an intermediate column generated to calculate AKI; the flag adds in the column which the current creatinine is checked against.

.. option:: Python
.. code-block:: python

    # Example 2: Adding in rolling-window minima
    
    flagger = AKIFlagger(add_min_creat = True)
    
    example2 = flagger.returnAKIpatients(toy)
    
    example2.head(3)
    
.. csv-table::
    :file: ../doc_csvs/python/example2.csv

.. option:: R
.. code-block:: R

    # Example 2: Adding in rolling-window minima

    example2 <- returnAKIpatients(toy, add_min_creat = T)

    head(example2)

.. csv-table:: 
    :file: ../doc_csvs/r/example2.csv

**→ Adding in baseline creatinine**

To add in the baseline creatinine, simply pass the flag ``add_baseline_creat = True`` to the flagger. Note that the baseline creatinine is not defined for outpatient measurements. Baseline creatinine can be thought of as the "resting" creatinine before coming into the hospital, so it doesn't make much sense to define the baseline creatinine outside of a hospital visit. 

.. option:: Python
.. code-block:: python

    # Example 3: Adding in baseline creatinine 

    toy = generate_toy_data(include_demographic_info = True)

    flagger = AKIFlagger(HB_trumping = True, eGFR_impute = True, #Specifying both calculation methods
                         add_baseline_creat = True, # Additional parameter to add in baseline creatinine values
                         age = 'age', sex = 'female')

    example3 = flagger.returnAKIpatients(toy)

    example3[~example3.baseline_creat.isnull()].head(3)

.. csv-table::
    :file: ../doc_csvs/python/example3.csv

.. option:: R
.. code-block:: R

    # Example 3: Adding in baseline creatinine

    example3 <- returnAKIpatients(toy, add_baseline_creat = T)

    head(example3)
    
.. csv-table:: 
    :file: ../doc_csvs/r/example3.csv

================
More information
================

For more information on the package, feel free to contact francis.p.wilson@yale.edu, abinet.aklilu@yale.edu or is439@yale.edu.

Useful guides exist for more information about AKI, rolling windows, the back-calculation imputation method.

* `AKI <https://www.kidney.org/atoz/content/AcuteKidneyInjury>`_
* `KDIGO guidelines <https://kdigo.org/guidelines/acute-kidney-injury/>`__
* `KDIGO standard definitions <http://www.european-renal-best-practice.org/sites/default/files/u33/ndt.gfs375.full_.pdf>`_
* `Rolling-window method <https://www.mathworks.com/help/econ/rolling-window-estimation-of-state-space-models.html>`_
* `Back-calculation method <https://cjasn.asnjournals.org/content/5/7/1165>`_
* `CKD-EPI equation <https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating>`_

The source code for the package can be found on `GitHub <https://github.com/isaranwrap/StandardizingAKI>`_. 

* :ref:`genindex`




