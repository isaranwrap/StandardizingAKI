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

That about does it for the basics! There are a slew of other features, some of which are listed in the `Additional Features` section. For a full listing of the features and appropriate use cases, see the `Documentation` at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.