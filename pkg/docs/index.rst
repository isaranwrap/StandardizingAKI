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
   MoreInformation
   

Introduction
============

Acute Kidney Injury (AKI) is a sudden onset of kidney failure and damage marked by an increase in the serum creatinine levels
(amongst other biomarkers) of the patient. Kidney Disease Improving Global Outcomes (KDIGO) has a set of guidelines and standard definitions 
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

   pip install akiFlagger

To ensure that it is working properly, you can open a Python session and test it with.

.. code-block:: python

   import akiFlagger

   akiFlagger.__version__

   >> '0.1.3'

Alternatively, you can download the source and wheel files to build manually from https://pypi.org/project/akiFlagger/.


Methods of Calculating AKI
==========================

There are two methods to retroactively determine if a patient has developed AKI: ``rolling-window`` and ``back-calculation``. 

.. option:: Rolling Window 

   The rolling window definition of AKI is based on the change in creatinine in a 48 hour or 7 day `rolling window <https://www.mathworks.com/help/econ/rolling-window-estimation-of-state-space-models.html>`_ period.
   These are the stages mentioned in the KDIGO guidelines in the `Introduction`. 

.. option:: Back-calculation

   The back-calculated definition of AKI is based on retroactively imputing baseline creatinine values. This is done by taking the *median*
   of the patient's outpatient creatinine values from 365 to 7 days prior to admission and setting that as the baseline creatinine. Then, the 
   first KDIGO criterion for *Stage 1* is applied (the 50% increase in creatinine in < 7 days). If the condition is satisfied, the patient is considered to have AKI.

   If there are no outpatient creatinine values measured for the patient from 365 to 7 days prior to admission, it is possible to still impute a
   baseline creatinine value based on the patients demographics: namely their age, sex, and race. 

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
    
    >> '0.1.3'

Let's start off by creating some toy data.
------------------------------------------

The flagger comes with a built-in generator of a toy dataset to demonstrate how it works. Simply call the `generate_toy_data()` function. By default, the toy dataset has 100 patients, but let's initialize ours with 1000 patients.

.. code-block:: python

    toy = generate_toy_data(num_patients=100)

    print('Toy dataset shape: {}'.format(toy.shape))

    toy.head()

    >> Successfully generated toy data!


.. admonition:: Tip!

    In order to calculate AKI, the flagger expects a dataset with certain columns in it. Depending on the type of computation you are interested in, your dataset will need to have different columns. Here's a brief rundown of the necessary columns. 

    * *Rolling-window*: **patient_id**, **inpatient/outpatient**, **time**, and **creatinine** 

    * *Back-calculate*: **patient_id**, **inpatient/outpatient**, **time**, and **creatinine**

    * *eGFR-imputed baseline creatinine*: **age**, **sex** (female or not), and **race** (black or not).

    ------------

    By default, the naming system is as follows:

    **patient_id :raw-html:`&rarr;` 'mrn'** 
        
    **encounter_id |rarr| 'enc'** 

    **inpatient/outpatient |rarr| 'inpatient'** 
        
    **admission |rarr| 'admission'** 

    **creatinine |rarr| 'creatinine'** 
        
    **time |rarr| 'time'** 

    If you have different names for your columns, you **_must_ specify them.** The toy dataset's name for `creatinine` is *'creat'* so you can see where in the flagger the alternate name is specified.

Example: Rolling-window
-----------------------

The next code block runs the flagger and returns those patients who satisfy the AKI conditions according to the `KDIGO guidelines <https://kdigo.org/guidelines/>`_ for change in creatinine values by the rolling-window definition, categorized as follows:


*Stage 1:* $(1)$ $50\% \uparrow$ in creatinine in $ < 7 $ days OR $(2)$ $0.3 mg/dL \uparrow $  in creatinine in $ < 48$ hours

*Stage 2:* $100\% \uparrow$ (or doubling of) in creatinine in $ < 7 $ days

*Stage 3:* $200\% \uparrow$ (or tripling of) in creatinine in $ < 7 $ days

.. code-block:: python

    flagger = AKIFlagger(rolling_window = True, creatinine = 'creat')

    out = flagger.returnAKIpatients(toy)

    out = out[['mrn', 'enc', 'inpatient', 'admission', 'time', 'creat', 'rw']] # This just orders the columns to match the initial order
    
    out.head()

.. code-block:: python

    df = akiFlagger.generate_toy_data()

    >> Successfully generated toy data!

We can take a look at what our dataframe looks like. ``df.head()`` should yield this:

+-----+--------+--------+----------------------+---------------------+-------------+
|     |  mrn   |  enc   |      admission       |       time          |  creat      |
|     |        |        |                      |                     |             |
+=====+========+========+======================+=====================+=============+
| 0   | 12732  | 25741  | 2020-02-27 11:42:42  | 2020-02-29 05:42:42 | 1.116895    |
+-----+--------+--------+----------------------+---------------------+-------------+
| 1   | 19845  | 81382  | 2020-05-12 06:02:54  | 2020-05-09 12:02:54 | 0.390540    |
+-----+--------+--------+----------------------+---------------------+-------------+
| 2   | 13264  | 89464  | 2020-01-10 11:16:57  | 2020-01-10 17:16:57 | 1.353141    |
+-----+--------+--------+----------------------+---------------------+-------------+
| 3   | 14859  | 75180  | 2020-06-07 12:27:38  | 2020-06-09 18:27:38 | 1.182348    |
+-----+--------+--------+----------------------+---------------------+-------------+
| 4   | 19225  | 94917  | 2020-03-26 21:16:49  | 2020-03-23 21:16:49 | 1.232916    |
+-----+--------+--------+----------------------+---------------------+-------------+

.. warning::

    The column names should be named exactly as they are in the examples. The full list of acceptable names can be found
    in the *returnAKIpatients()* function in the :ref:`genindex` section.

Running the following should run the flagger for ``rolling-window`` AKI.

.. code-block:: python
    
    rw = akiFlagger.returnAKIpatients(df, aki_calc_type = 'rolling_window')

Now the data frame has increased in size by quite a bit! Let's check out whats been added:

+---------+--------------+----------------+----------------+---------------+-----------------+-------------------+-------------------+--------+--------+--------+
|         |              |      creat     | mincreat_48hr  | mincreat_7day | deltacreat_48hr |  deltacreat_7day  | rollingwindow_aki | stage1 | stage2 | stage3 |
+---------+--------------+----------------+----------------+---------------+-----------------+-------------------+-------------------+--------+--------+--------+
|  mrn    |     time     |                |                |               |                 |                   |                   |        |        |        |						
+=========+==============+================+================+===============+=================+===================+===================+========+========+========+
|**12732**|**2020-02-22**|                |                |               |                 |                   |                   |        |        |        |   
|         | **23:42:42** |   1.116895     |  1.116895      | 1.116895      | 0.00000         |  0.00000          |       False       |  False |  False |  False |										
+---------+--------------+----------------+----------------+---------------+-----------------+-------------------+-------------------+--------+--------+--------+
|         |**2020-02-25**|                |                |               |                 |                   |                   |        |        |        | 
|         | **05:42:42** |   0.842858     |  0.842858      | 0.842858      | 0.00000         | 0.00000           |       False       |  False |  False |  False |                                             
+---------+--------------+----------------+----------------+---------------+-----------------+-------------------+-------------------+--------+--------+--------+
|         |**2020-02-26**|                |                |               |                 |                   |                   |        |        |        | 
|         | **11:42:42** |   1.359735     |  0.842858      | 0.842858      | 0.51688         |  0.51688          |       True        |  True  |  False |  False |										
+---------+--------------+----------------+----------------+---------------+-----------------+-------------------+-------------------+--------+--------+--------+
|         |**2020-02-27**|                |                |               |                 |                   |                   |        |        |        |
|         | **05:42:42** |   1.275845     |  1.275845      | 1.275845      | 0.00000         |  0.43299          |       True        |  True  |  False |  False |											
+---------+--------------+----------------+----------------+---------------+-----------------+-------------------+-------------------+--------+--------+--------+
|         |**2020-02-28**|                |                |               |                 |                   |                   |        |        |        |
|         | **23:42:42** |   1.277589     |  1.277589      | 1.275845      | 0.00174         |  0.43473          |       True        |  True  |  False |  False |										
+---------+--------------+----------------+----------------+---------------+-----------------+-------------------+-------------------+--------+--------+--------+

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

Example: Back-calculation
-------------------------

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
