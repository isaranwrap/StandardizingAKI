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
    
    >> '1.0.0'

.. option:: R
.. code-block:: R

    library(akiFlagger)

    ?returnAKIpatients

    > ℹ Rendering development documentation for 'returnAKIpatients'

Let's start off by creating some toy data.
------------------------------------------

.. option:: Python
The flagger comes with a built-in generator of a toy dataset to demonstrate how it works. Simply call the `generate_toy_data()` function. By default, the toy dataset has 100 patients, but let's initialize ours with 1000 patients.

.. code-block:: python

    toy = generate_toy_data(num_patients=1000)

    print('Toy dataset shape: {}'.format(toy.shape))

    >> Successfully generated toy data!
    
       Toy dataset shape: (9094, 6)

The toy dataset comes with columns for the patient identifier, the encounter identifier, whether the measurement was inpatient or outpatient, the creatinine measurement and time at which the measurement was taken. ``toy.head()`` should yield something like this:

.. csv-table::
    :file: ../doc_csvs/python/toy_head.csv

.. option:: R

The R package comes with a built-in dataset, `toy`. The toy dataset comes with columns for the patient identifier, inpatient, the creatinine measurement and the time at which the measurement was taken. ``head(toy)`` should yield something like this:

.. csv-table::
    :file: ../doc_csvs/r/toy_headR.csv

.. admonition:: Tip!

    In order to calculate AKI, the flagger expects a dataset with certain columns in it. Depending on the type of computation you are interested in, your dataset will need to have different columns. Here's a brief rundown of the necessary columns. 

    * *Rolling-window*: **patient_id**, **inpatient**, **time**, and **creatinine** 

    * *Back-calculate*: **patient_id**, **inpatient**, **time**, and **creatinine**

    * *eGFR-imputed baseline creatinine*: **age**, **sex** (defaults to female), and **race** (defaults to black).

    ------------

    By default, the naming system is as follows:

    **patient_id → 'patient_id'** 

    **inpatient/outpatient → 'inpatient'**

    **creatinine →'creatinine'** 
        
    **time → 'time'** 

    If you have different names for your columns, you **must specify them.** 

Example: Rolling-window
-----------------------

The next code block runs the flagger and returns those patients who satisfy the AKI conditions according to the `KDIGO guidelines <https://kdigo.org/guidelines/>`_ for change in creatinine values by the rolling-window definition, categorized as follows:

*Stage 1:* **(1)** 50% ↑ in creatinine in < 7 days OR **(2)** 0.3 mg/dL ↑ in creatinine in  < 48 hours

*Stage 2:* 100\% ↑ (or doubling of) in creatinine in < 7 days

*Stage 3:* 200\% ↑ (or tripling of) in creatinine in < 7 days

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
    you'll also want to include the columns ``age``, ``sex``, and ``race``. 

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

Example: Back-calculation
-------------------------

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

The following equation is known as the `CKD-EPI equation <https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating); developed via spline analysis by *Levey et. Al, 2009*. The full paper, along with the derived constants, can be found [here](https://pubmed.ncbi.nlm.nih.gov/19414839/>`_.

.. math::
    \begin{equation}
    GFR = 141 \times min(S_{cr} / \kappa, 1)^{\alpha} \times max(S_{cr} / \kappa, 1)^{-1.209} \times 0.993^{Age} \times (1 + 0.018 f) \times ( 1 + 0.159 b)
    \end{equation}

where:

- :math:`GFR`  :math:`(\frac{mL/min}{1.73m^2})` is the glomerular filtration rate
- :math:`S_{cr}`  :math:`(\frac{mg}{dL})` is the serum creatinine
- :math:`\kappa` (unitless) is 0.7 for females and 0.9 for males
- :math:`\alpha` (unitless) is -0.329 for females and -0.411 for males
- :math:`f` is 1 if female, 0 if male
- :math:`b` is 1 if black, 0 if another race

The idea is as follows: based on the above equation, we assume a GFR of 75 and then use the age, sex, and race to determine an estimate for the baseline creatinine. Theory aside, simply pass ``eGFR_impute = True`` into the flagger and this will add values where the patient was missing outpatient values 365 to 7 days prior to admission.

.. option:: Python
**Note:** The toy dataset doesn't come with demographic information by default, but simply passing ``include_demographic_info = True`` adds in the age, race, and sex columns. We need to specify that sex is female & race is black in the flagger as well.

.. code-block:: python

    toy = generate_toy_data(num_patients=100, include_demographic_info = True)

    toy.head()

.. csv-table::
    :file: ../doc_csvs/python/toy_demo.csv

.. code-block:: python

    flagger = AKIFlagger(HB_trumping = True, eGFR_impute = True, add_baseline_creat = True,
                         sex = 'female', race = 'black')

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

That about does it for the basics! There are a slew of other features, some of which are listed in the `Additional Features` section. For a full listing of the features and appropriate use cases, see the `Documentation` at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.