Additional Features / Common Use Cases
========================================

For most use cases, you will just need to specify `rolling-window` or `back-calculate` and the AKI-column will be returned. There are a slew of other features, some of which are listed below. For a full listing of the features and appropriate use cases, see the `Documentation` at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.


**→ Adding padding to the rolling window** (52 hour & 172 hour windows, instead, for example)

It's often the case that you want to add some padding to the window to account for variations occurring on the floor. If the amount of padding you would like to add is the same for both the smaller and larger window, simply pass ``padding='_hours'`` filling the blank with the number of hours to add to the windows.
If the pad times are different between windows, the parameters ``pad1time`` and ``pad2time`` allow you to add just this padding to the initial windows of 48 and 172 hours. In fact, if you wanted a window of 36 hours, you could even set `pad1time = '-12hours'`; this is one way in which you could modify the rolling window. 

.. code-block:: python

    # Example 0: Adding 4-hour padding to windows

    flagger = AKIFlagger(rolling_window = True, padding = '4hours', creatinine = 'creat')

    example0 = flagger.returnAKIpatients(toy)

    example0[example0.rw > 0].head(3)

.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/example0.csv

**→ Working with different column names**

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

**→ Adding in rolling-window minimum creatinines**

To add in the baseline creatinine, simply pass the flag ``add_min_creat = True`` to the flagger. This will add in two columns which contain the minimum values in the rolling window, which is an intermediate column generated to calculate AKI; the flag adds in the column which the current creatinine is checked against.

.. code-block:: python

    # Example 2: Adding in rolling-window minima
    
    flagger = AKIFlagger(rolling_window = True, creatinine = 'creat', add_min_creat = True)
    
    example2 = flagger.returnAKIpatients(toy)
    
    example2.head(3)
    
.. csv-table::
    :file: /Users/Praveens/Desktop/ishan/StandardizingAKI/pkg/doc_csvs/example2.csv

**→ Adding in baseline creatinine**

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

**→ Bare-bones dataset**

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