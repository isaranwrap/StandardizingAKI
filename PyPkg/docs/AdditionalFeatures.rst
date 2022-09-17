========================================
Additional Features and Common Use Cases
========================================

For most use cases, you will just need to specify the AKI definition methodology (i.e. `rolling minimum window`, `historical baseline trumping`, or `baseline creatinine imputation`) and the AKI-column will be returned. There are a slew of other features, some of which are listed below. For a full listing of the features and appropriate use cases, see the `Documentation` at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.


**→ Adding padding to the rolling window**
==========================================


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
=========================================

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

**→ Adding in rolling window minimum creatinines**
==================================================

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

    # Example 2: Adding in rolling window minima

    example2 <- returnAKIpatients(toy, add_min_creat = T)

    head(example2)

.. csv-table:: 
    :file: ../doc_csvs/r/example2.csv

**→ Adding in baseline creatinine**
===================================

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
