.. akiFlagger documentation master file, created by
   Ishan Saran on Thu Aug 6 07:44:21 2020.

.. role::  raw-html(raw)
    :format: html
    
========================================
Welcome to the akiFlagger documentation!
========================================

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
(amongst other biomarkers) of the patient. Kidney Disease Improving Global Outcomes (KDIGO) has a set of `guidelines <https://kdigo.org/guidelines/acute-kidney-injury/>`_ and `standard definitions <http://www.european-renal-best-practice.org/sites/default/files/u33/ndt.gfs375.full_.pdf>`_
of AKI:

* *Stage 1:* 50% increase in creatinine in < 7 days or 0.3 increase in creatinine in < 48 hours
* *Stage 2:* 100% increase in (or doubling of) creatinine in < 7 days
* *Stage 3:* 200% increase in (or tripling of) creatinine in < 7 days

This package contains a flagger to determine if a patient has developed AKI based on the criterion above.
More information about the specific data input format and examples can be found in the `Getting started` section. 

Installation
============

You can install the flagger with ``pip``. Simply type the following into command line and the 
package should install properly.

.. code-block:: python

   pip install akiflagger

To ensure that it is working properly, you can open a Python session and test it with.

.. code-block:: python

   import akiFlagger

   akiFlagger.__version__

   >> '1.0.0'

As long as the package is a stable version (1.0.0+), the flagger should be usable.

Alternatively, you can download the source and wheel files to build manually from https://pypi.org/project/akiFlagger/.


Getting started
===============

This package is meant to handle patient data. Let's walk through an example of how to use this package
with some toy data since real patient data is probably protected health information.

Once you've installed the package following the instructions in `Installation`, you're ready to get started.
To begin with, we'll import the ``akiFlagger`` module.


.. code-block:: python

    import akiFlagger

    print(akiFlagger.__version__)

    from akiFlagger import AKIFlagger, generate_toy_data
    
    >> '1.0.0'

Let's start off by creating some toy data.
------------------------------------------

The flagger comes with a built-in generator of a toy dataset to demonstrate how it works. Simply call the `generate_toy_data()` function. By default, the toy dataset has 100 patients, but let's initialize ours with 1000 patients.

.. code-block:: python

    toy = generate_toy_data(num_patients=1000)

    print('Toy dataset shape: {}'.format(toy.shape))

    >> Successfully generated toy data!
    
       Toy dataset shape: (9094, 6)

The toy dataset comes with columns for the patient identifier, the encounter identifier, whether the measurement was inpatient or outpatient, the creatinine measurement and time at which the measurement was taken. ``toy.head()`` should yield something like this:

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/toy_head.csv

.. admonition:: Tip!

    In order to calculate AKI, the flagger expects a dataset with certain columns in it. Depending on the type of computation you are interested in, your dataset will need to have different columns. Here's a brief rundown of the necessary columns. 

    * *Rolling-window*: **patient_id**, **inpatient/outpatient**, **time**, and **creatinine** 

    * *Back-calculate*: **patient_id**, **inpatient/outpatient**, **time**, and **creatinine**

    * *eGFR-imputed baseline creatinine*: **age**, **sex** (female or not), and **race** (black or not).

    ------------

    By default, the naming system is as follows:

    **patient_id → 'mrn'** 
        
    **encounter_id → 'enc'** 

    **inpatient/outpatient → 'inpatient'** 
        
    **admission → 'admission'** 

    **creatinine →'creatinine'** 
        
    **time → 'time'** 

    If you have different names for your columns, you **must specify them.** For example, in the toy dataset note that the creatinine column is not the literal string "creatinine" but rather "creat". The following examples show how to deal with a different naming system for creatinine; similar measures can be adapted for the other columns. 

Example: Rolling-window
-----------------------

The next code block runs the flagger and returns those patients who satisfy the AKI conditions according to the `KDIGO guidelines <https://kdigo.org/guidelines/>`_ for change in creatinine values by the rolling-window definition, categorized as follows:

*Stage 1:* **(1)** 50% ↑ in creatinine in < 7 days OR **(2)** 0.3 mg/dL ↑ in creatinine in  < 48 hours

*Stage 2:* 100\% ↑ (or doubling of) in creatinine in < 7 days

*Stage 3:* 200\% ↑ (or tripling of) in creatinine in < 7 days

.. code-block:: python

    flagger = AKIFlagger(rolling_window = True, creatinine = 'creat')

    out = flagger.returnAKIpatients(toy)

    out = out[['mrn', 'enc', 'inpatient', 'admission', 'time', 'creat', 'rw']] # This just orders the columns to match the initial order

    out.head()


We can take a look at what our dataframe looks like. ``out.head()`` yields this:

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/rw_out.csv

Notice that the dataframe looks exactly the same as we inputted into the flagger save an extra column added called `rw`. This column has values of either 0, 1, 2, or 3, depending on which stage AKI the flagger found.
The flagger runs on a row-wise basis, meaning that each row is checked for the increase in creatinine. Should, for example, a patient meet the criterion multiple times within a single encounter, the flagger will flag each measurement as a case of AKI.

.. warning::

    The column names specified within the flagger should match the dataset exactly. The full list of acceptable names can be found
    in the *returnAKIpatients()* function in the :ref:`genindex` section. For certain cases, the flagger understands 

We can take a look at what the flagger flagged as AKI. ``out[out.rw > 0].head()`` should give a list of some patients which were flagged. From that, we can subset the dataset on any given patient:

.. code-block:: python
    
    out[out.rw > 0].head() # this will give the rows which were marked as AKI by the flagger. We can take a look at the patients who were flagged. 
    out[out.mrn == 13264]

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/rw_flagged.csv

Notice how as we would expect, when the creatinine more than doubled from 0.22 to 0.49, the flagger correctly identified it as Stage 2 AKI. 

You can even look at aggregate counts if you wanted as follows (but don't take the numbers too seriously, because of course, this is toy data):

.. code-block:: python
    
    aki_counts = out.rw.value_counts()
    print('AKI counts')
    print('----------')
    print('No AKI: {}\nStage 1: {}\nStage 2: {}\nStage 3: {}'.format(aki_counts[0], aki_counts[1], aki_counts[2], aki_counts[3]))

    >>  AKI counts
        ----------
        No AKI: 658
        Stage 1: 181
        Stage 2: 69
        Stage 3: 34

You can play around with the output of the ``returnAKIpatients()`` function in-depth to get a better understanding of how the flagger is operating. There are even optional parameters such as ``add_min_creat = True`` within the flagger which includes some of the intermediate steps the flagger is generating along to calculate AKI. 
Next, we'll take a look at an example of the other AKI-calculation method, the back-calculation method.

Example: Back-calculation
-------------------------

Next, we'll run the flagger to "back-calculate" AKI; that is, using the **median outpatient creatinine values from 365 to 7 days prior to admission** to impute a baseline creatinine value. Then, we'll run the same KDIGO criterion (except for the 0.3 increase) comparing the creatinine value to baseline creatinine.

.. code-block:: python

    flagger = AKIFlagger(back_calculate = True, creatinine = 'creat')

    out = flagger.returnAKIpatients(toy)
    
    out.head()
    
.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/bc_out.csv

Actually, by default the toy dataset only has patient values :math:`\pm` 5 days from the admission date, and because the baseline creatinine value calculates using values from 365 to 7 days prior, you'll notice that it didn't flag a single row as having AKI. Normally, of course, patients won't have times restricted to just :math:`\pm` 5 days, but this is a good opportunity to showcase one of the flagger features: the **eGFR-based imputation of baseline creatinine**.

The following equation is known as the `CKD-EPI equation <https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating); developed via spline analysis by *Levey et. Al, 2009*. The full paper, along with the derived constants, can be found [here](https://pubmed.ncbi.nlm.nih.gov/19414839/>`_:

.. math::
    \begin{equation}
    GFR = 141 \times min(S_{cr} / \kappa, 1)^{\alpha} \times max(S_{cr} / \kappa, 1)^{-1.209} \times 0.993^{Age} \times (1 + 0.018 f) \times ( 1 + 0.159 b)
    \end{equation}

where

- :math:`GFR`  :math:`(\frac{mL/min}{1.73m^2})` is the glomerular filtration rate
- :math:`S_{cr}`  :math:`(\frac{mg}{dL})` is the serum creatinine
- :math:`\kappa` (unitless) is 0.7 for females and 0.9 for males
- :math:`\alpha` (unitless) is -0.329 for females and -0.411 for males
- :math:`f` is 1 if female, 0 if male
- :math:`b` is 1 if black, 0 if another race

The idea is as follows: based on the above equation, we assume a GFR of 75 and then use the age, sex, and race to determine an estimate for the baseline creatinine. Theory aside, simply pass ``eGFR_impute = True`` into the flagger and this will add values where the patient was missing outpatient values 365 to 7 days prior to admission.

**Note:** The toy dataset doesn't come with demographic information by default, but simply passing ``include_demographic_info=True`` adds in the age, race, and sex columns. We need to specify that sex is female & race is black in the flagger as well.

.. code-block:: python

    toy = generate_toy_data(num_patients=100, include_demographic_info = True)

    toy.head()

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/toy_demo.csv

.. code-block:: python

    flagger = AKIFlagger(back_calculate = True, creatinine = 'creat',
                        eGFR_impute = True, sex = 'female', race = 'black')

    out = flagger.returnAKIpatients(toy)

    out = out[['mrn', 'enc', 'inpatient', 'age', 'female', 'black', 'admission', 'time', 'creat', 'bc']] # This just orders the columns to match the initial order

    out.head()

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/egfr_out.csv

Additional Features and Common Use Cases
========================================

For most use cases, you will just need to specify `rolling-window` or `back-calculate` and the AKI-column will be returned. There are a slew of other features, some of which are listed below. For a full listing of the features and appropriate use cases, see the `Documentation` at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.


**Adding padding to the rolling window** (52 hour & 172 hour windows, instead, for example) 
---------------------------------------------------------------------------------------------

It's often the case that you want to add some padding to the window to account for variations occurring on the floor. If the amount of padding you would like to add is the same for both the smaller and larger window, simply pass ``padding='_hours'`` filling the blank with the number of hours to add to the windows.
If the pad times are different between windows, the parameters ``pad1time`` and ``pad2time`` allow you to add just this padding to the initial windows of 48 and 172 hours. In fact, if you wanted a window of 36 hours, you could even set `pad1time = '-12hours'`; this is one way in which you could modify the rolling window. 

.. code-block:: python

    # Example 0: Adding 4-hour padding to windows

    flagger = AKIFlagger(rolling_window = True, padding = '4hours', creatinine = 'creat')

    example0 = flagger.returnAKIpatients(toy)

    example0[example0.rw > 0].head(3)

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/example0.csv

**Working with different column names**
-----------------------------------------

As an additional example, the patient identifier will often come in as *'PAT_MRN_ID'* or *'PAT_ENC_CSN_ID'* (or something of the sort) if it is coming from a typical clinical data warehouse/repository. Accordingly, these should be passed in as options to the flagger. 

.. code-block:: python

    # Example 1: Working with different column names 

    dataframe = toy.rename(columns = {'mrn': 'PAT_MRN_ID', 'enc': 'PAT_ENC_CSN_ID', 'creat':'CREATININE',
                                    'age': 'AGE', 'female': 'SEX', 'black': 'RACE', 'inpatient': 'INPATIENT',
                                    'admission': 'ADMISSION', 'time': 'TIME'})

    flagger = AKIFlagger(rolling_window = True, patient_id = 'PAT_MRN_ID', encounter_id = 'PAT_ENC_CSN_ID', 
                        inpatient = 'INPATIENT', admission = 'ADMISSION', time = 'TIME', creatinine = 'CREATININE')

    example1 = flagger.returnAKIpatients(dataframe)

    example1.head(3)

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/example1.csv

**Adding in rolling-window minimum creatinines**
--------------------------------------------------

To add in the baseline creatinine, simply pass the flag ``add_min_creat = True`` to the flagger. This will add in two columns which contain the minimum values in the rolling window, which is an intermediate column generated to calculate AKI; the flag adds in the column which the current creatinine is checked against.

.. code-block:: python

    # Example 2: Adding in rolling-window minima
    
    flagger = AKIFlagger(rolling_window = True, creatinine = 'creat', add_min_creat = True)
    
    example2 = flagger.returnAKIpatients(toy)
    
    example2.head(3)
    
.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/example2.csv

**Adding in baseline creatinine**
-----------------------------------

To add in the baseline creatinine, simply pass the flag ``add_baseline_creat = True`` to the flagger. Note that the baseline creatinine is not defined for outpatient measurements. Baseline creatinine can be thought of as the "resting" creatinine before coming into the hospital, so it doesn't make much sense to define the baseline creatinine outside of a hospital visit. 

.. code-block:: python

    # Example 3: Adding in baseline creatinine 

    flagger = AKIFlagger(rolling_window = True, back_calculate = True, #Specifying both calculation methods
                        patient_id = 'PAT_MRN_ID', encounter_id = 'PAT_ENC_CSN_ID', inpatient = 'INPATIENT', #Specifying col names
                        age = 'AGE', sex = 'SEX', race = 'RACE', time = 'TIME', admission = 'ADMISSION', creatinine = 'CREATININE',#Specifying col names
                        eGFR_impute = True, add_baseline_creat = True) #Specifying additional columns to add

    example3 = flagger.returnAKIpatients(dataframe)

    example3 = example3[['PAT_MRN_ID', 'PAT_ENC_CSN_ID', 'INPATIENT', 'AGE', 'SEX', 'RACE', 'ADMISSION', 'TIME', 'CREATININE', 'baseline_creat', 'rw', 'bc']]

    example3[~example3.baseline_creat.isnull()].head(3)

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/example3.csv

**Bare-minimum input**
------------------------

As stated above, the bare minimum columns necessary for the flagger to run are the **patient_id, inpatient/outpatient, time,** and **creatinine**. In this case, any other columns used in intermediate steps will be imputed (admission, for example).

.. code-block:: python

    # Example 4: Bare-bones dataset

    barebones = toy.loc[:,['mrn', 'inpatient', 'time', 'creat']]

    print('Barebones head:')

    print(barebones.head())

    flagger = AKIFlagger(rolling_window = True, creatinine = 'creat')

    example4 = flagger.returnAKIpatients(barebones)

    example4[example4.rw > 0].head(3)

    >> Barebones head:
        mrn   inpatient                time   creat
    0  12732      False 2020-02-26 11:42:42   1.78
    1  12732      False 2020-02-26 23:42:42   1.46
    2  12732       True 2020-02-28 05:42:42   1.52
    3  12732       True 2020-02-28 11:42:42   1.62
    4  12732       True 2020-02-28 17:42:42   1.51

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/example4.csv

================
More information
================

For more information on the package, feel free to contact isaranwrap@gmail.com or is439@yale.edu.

Useful guides exist for more information about AKI, rolling windows, the back-calculation imputation method.

* `AKI <https://www.kidney.org/atoz/content/AcuteKidneyInjury>`_
* `KDIGO guidelines <https://kdigo.org/guidelines/acute-kidney-injury/>`_
* `KDIGO standard definitions <http://www.european-renal-best-practice.org/sites/default/files/u33/ndt.gfs375.full_.pdf>`_
* `Rolling-window method <https://www.mathworks.com/help/econ/rolling-window-estimation-of-state-space-models.html>`_
* `Back-calculation method <https://cjasn.asnjournals.org/content/5/7/1165>`_
* `CKD-EPI equation <https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating>`_

The source code for the package can be found on `GitHub <https://github.com/isaranwrap/StandardizingAKI>`_. 

* :ref:`genindex`




