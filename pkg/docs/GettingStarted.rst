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
    >> '0.0.3'

.. admonition:: Tip!

    The input dataframe needs to contain the correct columns in order for the flagger to recognize and deal with the proper variables.
    Some pre-processing may be necessary. Here are the required columns depending on which calculation methods
    you are interested in:
    
    * *Rolling-window*: **mrn**, **enc**, **admission**, **creatinine**, and **time**. 
    * *Back-calculation*: **mrn**, **enc**, **admission**, and **time**. 
    * *eGFR-imputed baseline creatinine*: **age**, **sex** (female or not), and **race** (black or not).