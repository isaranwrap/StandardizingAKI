Getting started
===============

This package is meant to handle patient data. Let's walk through an example of how to use this package
with some toy data since real patient data is probably protected health information.

Once you've installed the package following the instructions in `Installation`, you're ready to get started.
To begin with, we'll import the ``akiFlagger`` module as well as the trifecta ``pandas``, ``numpy``, and ``matplotlib``.


.. code-block:: python

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as pyplot

    import akiFlagger
    print(akiFlagger.__version__)
    >> '0.0.4'

.. admonition:: Tip!

    The input dataframe needs to contain the correct columns in order for the flagger to recognize and deal with the proper variables.
    Some pre-processing may be necessary. Here are the required columns depending on which calculation methods
    you are interested in:
    
    * *Rolling-window*: **mrn**, **enc**, **admission**, **creatinine**, and **time**. 
    * *Back-calculation*: **mrn**, **enc**, **admission**, and **time**. 
    * *eGFR-imputed baseline creatinine*: **age**, **sex** (female or not), and **race** (black or not).

Example: Rolling-window
-----------------------

Generally speaking, real patient data will be protected health information, so this walkthrough will use toy data. 
The flagger comes with a built-in generator for toy data, which we can call with the following command.

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