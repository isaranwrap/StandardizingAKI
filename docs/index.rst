.. akiFlagger documentation master file, created by
   Ishan Saran on Thu Aug  6 07:44:21 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

========================================
Welcome to the akiFlagger documentation!
========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   usage/installation
   usage/quickstart
   license
   help

Introduction
------------

Acute Kidney Injury (AKI) is a sudden onset of kidney failure and damage marked by an increase in the serum creatinine levels
(amongst other biomarkers) of the patient. Kidney Disease Improving Global Outcomes (KDIGO) has a set of guidelines and standard definitions 
of AKI:

* *Stage 1:* 50% increase in creatinine in < 7 days or 0.3 increase in creatinine in < 48 hours
* *Stage 2:* 100% increase in (or doubling of) creatinine in < 48 hours
* *Stage 3:* 200% increase in (or tripling of) creatinine in < 48 hours

This package contains a flagger to determine if a patient has developed AKI based on longitudinal data of serum creatinine measurements.
More information about the specific data input format can be found in the `Getting started` section. 

Methods of Calculating AKI
==========================

There are two methods to retroactively determine if a patient developed AKI: ``rolling-window`` and ``back-calculation``. 

.. option:: Rolling Window 

   The rolling window definition of AKI is based on the change in creatinine in a 48 hour or 7 day `rolling window <https://www.mathworks.com/help/econ/rolling-window-estimation-of-state-space-models.html>`_ period.
   These are the stages mentioned in the KDIGO guidelines in the `Introduction`. 

.. option:: Back-calculation

   The back-calculated definition of AKI is based on retroactively imputing baseline creatinine values. This is done by taking the *median*
   of the patient's outpatient creatinine values from 365 to 7 days prior to admission and setting that as the baseline creatinine. Then, the 
   first KDIGO criterion for *Stage 1* is applied (the 50% increase in creatinine in < 7 days). If the condition is satisfied, the patient is considered to have AKI.

   If there are no outpatient creatinine values measured for the patient from 365 to 7 days prior to admission, it is possible to still impute a
   baseline creatinine value based on the patients demographics: namely their age, sex, and race. 

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
