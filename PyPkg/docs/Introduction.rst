============
Introduction
============

Acute Kidney Injury (AKI) is a sudden onset of kidney failure and damage marked by an increase in the serum creatinine levels
(amongst other biomarkers) of the patient. Kidney Disease Improving Global Outcomes (KDIGO) has a set of guidelines and standard definitions 
of AKI:

* *Stage 1:* 50% increase in creatinine in < 7 days or 0.3 increase in creatinine in < 48 hours
* *Stage 2:* 100% increase in (or doubling of) creatinine in < 48 hours
* *Stage 3:* 200% increase in (or tripling of) creatinine in < 48 hours

This package contains a flagger to determine if a patient has developed AKI based on longitudinal data of serum creatinine measurements.
More information about the specific data input format can be found in the `Getting started` section. 

Methods of calculating AKI
==========================

.. role:: bolditalic
  :class: bolditalic

There are two frameworks for retroactively determining if a patient has developed AKI: ``rolling-window`` and ``back-calculation``. 

.. option:: Rolling Window (default)

   The rolling window definition of AKI is based on the change in creatinine in a 48 hour or 7 day `rolling window <https://www.mathworks.com/help/econ/rolling-window-estimation-of-state-space-models.html>`_ period.
   These are the stages mentioned in the KDIGO guidelines in the `Introduction` above. 

.. option:: Back Calculation (2)
.. option:: Historical baseline trumping 

   The idea with :bolditalic:`Historical baseline trumping` is to use the historical baseline creatinine value as the value to compare the current creatinine to when runnning the KDIGO criterion 
   *instead of* the rolling window value; i.e. the historical baseline *trumps* the rolling minimum value. 
   
   :bolditalic:`Definition:` The historical baseline is defined as the :bolditalic:`median` of the patient's :bolditalic:`outpatient` creatinine values from 365 to 7 days prior to admission. 

   :bolditalic:`Reasoning:` Right when a patient is admitted to the hospital, their creatinine might not be representative of what their true, stable creatinine values
   normally are. As such, you might want to use the *historical baseline value*. This historical baseline value, calculated retroactively, is only used around the time of admission -
   specifically from the time of admission to 7 days (+ padding) out. For any time outside of this, the rolling window is still in effect... but this allows you to capture patients
   whose hemodynamic balance might be messed up at the time of admission. 

.. option:: Baseline creatinine imputation

   If there are no outpatient creatinine values measured for the patient from 365 to 7 days prior to admission, it is possible to still impute a
   baseline creatinine value based on the patients demographics: namely their age and sex. This is what the ``eGFR_impute`` option in the flagger does:
   *eGFR imputation* because it assumes an eGFR of 75 mL/min/1.73m^2 and estimates the creatinine from that. 

   
