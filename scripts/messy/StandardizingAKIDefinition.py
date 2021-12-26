#!/usr/bin/env python
# coding: utf-8

# ## Imports

# In[1]:


import pandas as pd
import numpy as np
import datetime, random

from multiprocessing import Pool
import time


# ## Two criterion for rolling-window definition of AKI
# ____
# 
# Based on the measured creatinine time series
# 
# * *$creat \uparrow$ 0.3 in < 48 hrs* 
# * *$creat \uparrow$ of 50% in < 7 days*
# 
# ## Back-calculated definition of AKI
# _____
# 
# First, calculate the baseline creatinine which is the *median* of outpatient creatinine values from 365 - 7 days prior to admission. Based on the imputed baseline creatinine value, apply the second KDIGO guideline:
# 
# * *$creat \uparrow$ of 50% in < 7 days*
# 
# ## eGFR-imputation of baseline creatinine 
# _______
# 
# If there are no outpatient creatinine measurements in the 365 - 7 day time period prior to admission, impute a baseline creatinine value based on age, sex, and race. Using an eGFR of 75, impute the baseline creatinine value. 

# ## Functions

# In[2]:


def returnAKIpatients(df, 
                      aki_calc_type = 'both', keep_extra_cols = True, 
                      cond1time = '48hours', cond2time = '168hours', eGFR_impute = False, add_stages=True):
    '''
    Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Parameters
    ----------
    param1 : int
        The first parameter.
    param2 : str
        The second parameter.

    Returns
    -------
    df
        dataframe with AKI patients added in 

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/


    '''
    
    #First, check if column names (mrn, enc, creatinine, admission & time) are as we want it
    assert ('mrn' or 'MRN' or 'pat_mrn_id' or 'PAT_MRN_ID') in df.columns
    #assert ('enc' or 'ENC' or 'pat_enc_csn_id' or 'PAT_ENC_CSN_ID') in df.columns
    
    if aki_calc_type == 'both': 
        df = df.groupby('mrn', sort=False).apply(lambda d: addRollingWindowAKI(d,#enc vs mrn
                                                                              cond1time = cond1time,
                                                                              cond2time = cond2time))
        df = df.reset_index('mrn', drop=True).reset_index()
        
        df = df.groupby('mrn', sort=False).apply(lambda d: addBaselineCreat(d, 
                                                                            eGFR_impute=eGFR_impute))
        
        df = df.groupby('enc', sort=False).apply(lambda d: addBackCalcAKI(d,
                                                                         cond2time = cond2time))
        
        df = df.reset_index('enc', drop=True).reset_index()
        
    elif aki_calc_type == 'rolling_window':
        df = df.groupby('mrn', sort=False).apply(lambda d: addRollingWindowAKI(d,
                                                                              cond1time = cond1time,
                                                                              cond2time = cond2time))
        
    elif aki_calc_type == 'back_calculate':
        df = df.groupby('mrn', sort=False).apply(lambda d: addBaselineCreat(d,
                                                                           eGFR_impute = eGFR_impute))
        df = df.groupby('enc', sort=False).apply(lambda d: addBackCalcAKI(d,
                                                                        cond2time = cond2time)) 
    
    if not keep_extra_cols:
        df = df.drop(['mincreat_48hr', 'mincreat_7day',
                      'deltacreat_48hr', 'deltacreat_7day',
                      'baseline_creat'], axis=1)
    return df

def addBaselineCreat(df, eGFR_impute = False):
    '''
    Adds the baseline creatinine to a dataframe. The baseline creatinine is defined as the median of the outpatient 
     creatinine values from 365 to 7 days prior to admission.
    
    Input: dataframe (typically of a single patient)
    Output: dataframe with baseline creatinine column added in
    '''
    split_dfs = list()
    for adm in df.admission.unique():
        adm_df = df.loc[df.admission == adm]
        adm_df['baseline_creat'] = adm_df[~adm_df.inpatient].set_index('time').loc[adm - pd.Timedelta(days=365):adm - pd.Timedelta(days=7)].creat.median()
        split_dfs.append(adm_df)
    
    df = pd.concat(split_dfs)
    
    if eGFR_impute:
            df.loc[df.baseline_creat.isnull(), 'baseline_creat'] = df[df.baseline_creat.isnull()].apply(lambda d: eGFRbasedCreatImputation(d.age, d.sex, d.race), axis=1)
            
    return df

def addBackCalcAKI(df, 
                   cond2time = '168hours'):
    '''
    Adds the back-calculated AKI conditions, the KDIGO standards on the outpatient values;
    i.e. a 50% increase from baseline creatinine in <7 days
    
    Input: dataframe (typically of a single encounter)
    Output: dataframe with back-calculated aki values added in
    '''
    #backcalc_aki = np.empty(df.shape[0])
    #backcalc_aki[:] = np.nan
    
    df = df.reset_index(drop=True).set_index('time')
    df = df[~df.index.duplicated()]
    df_lf = df.loc[(df.admission - datetime.timedelta(hours=6)).values[0]:(df.admission + pd.Timedelta(cond2time)).values[0]]
    df.loc[df_lf.index, 'backcalc_aki'] = df_lf.creat >= np.round(1.5*df_lf.baseline_creat, decimals=5)
    
    return df 

def addRollingWindowAKI(df, add_stages = True,
                        cond1time = '48hours', cond2time = '168hours'):
    '''
    Adds the AKI conditions based on rolling window definition: 0.3 creat increase in < 48 hrs OR 50% increase in < 7 days
    
    Input: dataframe (typically of a single encounter)
    Output: dataframe with rolling-window aki values added in
    '''
    #df = df[~df.duplicated()]
    df = df.set_index('time').sort_index()
    #df = df[~df.duplicated()]
    df_rw = df.loc[df.admission[0] - pd.Timedelta(hours=172):]
    minc_48, minc_7d = np.empty(df.shape[0]), np.empty(df.shape[0])
    minc_48[:], minc_7d[:] = np.nan, np.nan
    minc_48[df.shape[0]-df_rw.shape[0]:] = df_rw.creat.rolling(pd.Timedelta(cond1time), min_periods=1).min().values
    minc_7d[df.shape[0]-df_rw.shape[0]:] = df_rw.creat.rolling(pd.Timedelta(cond2time), min_periods=1).min().values
    
    df['mincreat_48hr'] = minc_48
    df['mincreat_7day'] = minc_7d
    
    df['deltacreat_48hr'] = np.round(df.creat - df.mincreat_48hr, decimals = 5)
    df['deltacreat_7day'] = np.round(df.creat - df.mincreat_7day, decimals = 5)

    df['rollingwindow_aki'] = (df.deltacreat_48hr >= 0.3) | (df.deltacreat_7day >= 0.5*df.mincreat_7day)
    
    if add_stages:
        df['stage1'] = (df.deltacreat_48hr >= 0.3) | (df.deltacreat_7day >= 0.5*df.mincreat_7day)
        df['stage2'] = df.deltacreat_48hr >= 2*df.deltacreat_48hr
        df['stage3'] = df.deltacreat_48hr >= 3*df.deltacreat_48hr
    return df

def eGFRbasedCreatImputation(age, sex, race):
    kappa  = (0.9 - 0.2*sex)
    alpha  = (-0.411+0.082*sex)
    creat_over_kappa = 75/(141*(1 + 0.018*sex)*(1 + 0.159*race)*0.993**age)
    
    if creat_over_kappa < 1:
        creat = kappa*creat_over_kappa**(-1/1.209)
    elif creat_over_kappa >= 1:
        creat = kappa*creat_over_kappa**(1/alpha)
    return creat

def eGFR(creat, age, female, black):
    '''
    Calculates the estimated glomerular filtration rate based on the serum creatinine levels, age, sex, and race (black or not black);
    Based on the formula in the paper A New Equation to Estimate Glomerular Filtration Rate (Levey et. Al, 2009) linked below
    
    Equation: https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating
    Full paper: https://pubmed.ncbi.nlm.nih.gov/19414839/
    
    
    '''
    min_ck = np.clip(creat/(0.9-0.2*female), a_min=None, a_max=1) #Equivalent to min(cr/k, 1)
    max_ck = np.clip(creat/(0.9-0.2*female), a_min=1, a_max=None) #Equivalent to max(cr/k, 1)
    
    alpha = (-0.411+0.082*female)
    
    egfr = 141*(0.993**age)*(min_ck**alpha)*(max_ck**-1.209)*(1+female*0.018)*(1+black*0.159)
    
    return np.round(egfr, decimals=5) #Helper function to ensure eGFRBasedImputation() works as expected


# ## Reading in file; cleaning data frame for returnAKIpatients() input

# In[3]:


covid_df = pd.read_csv(r'H:\Data\Standardized AKI definition\dataset\covid creatinines.csv')
covid_df['mrn'] = covid_df.pat_mrn_id.str.strip('MR').astype('int')
covid_df['enc'] = covid_df.enc_id
covid_df['time'] = pd.to_datetime(covid_df.time)
covid_df['sex'] = covid_df.sex.astype('bool')
covid_df['race'] = covid_df.race.astype('bool')
covid_df['inpatient'] = covid_df.inpatient.astype('bool')
covid_df['creat'] = covid_df['creatinine']
covid_df['admission'] = pd.to_datetime(covid_df.admission)
covid_df['discharge'] = pd.to_datetime(covid_df.discharge)
print('Shape:', covid_df.shape)
print(covid_df.dtypes)


# In[4]:


get_ipython().run_cell_magic('time', '', "df = covid_df[['mrn', 'enc', 'time', 'creat', 'age', 'sex', 'race', 'inpatient', 'admission', 'discharge']]\ndf = df[~df.duplicated()] #The rows where the pat_enc_csn_id was lumped into enc_id become duplicates\ndf = df.groupby('enc', sort=False).apply(lambda d: d.sort_values('time'))\ndf = df.reset_index(drop=True)")


# ## Adding Rolling-window & Back-calculated AKI values

# In[6]:


get_ipython().run_cell_magic('time', '', "out_rw = returnAKIpatients(df, aki_calc_type = 'rolling_window')")


# In[6]:


get_ipython().run_cell_magic('time', '', "out_bc = returnAKIpatients(df, aki_calc_type = 'back_calculate')")


# In[455]:


get_ipython().run_cell_magic('time', '', "out2 = returnAKIpatients(df, cond1time='52hours', cond2time='172hours', eGFR_impute=True)")


# In[461]:


out2.to_csv(r'H:\Data\Standardized AKI definition\dataset\output2.csv')


# In[462]:


get_ipython().run_cell_magic('time', '', "out = returnAKIpatients(df, cond1time='52hours', cond2time='172hours')")


# ## Mismatch cases

# In[10]:


tmp = out.loc[out.enc == 205472336]
backcalc_aki = np.empty(tmp.shape[0])
backcalc_aki[:] = np.nan
tmp = tmp.sort_values('time')
tmp2 = tmp.set_index('time').sort_index().loc[tmp.admission.values[0]:(tmp.admission + datetime.timedelta(days=7)).values[0]]
backcalc_aki[:tmp2.shape[0]] = tmp2.creat > 1.5*tmp2.baseline_creat
tmp['backcalc_aki'] = backcalc_aki


# In[90]:


tmp = df[df.mrn == 2307280]
tmp = tmp.groupby('enc', sort=False).apply(lambda d: addRollingWindowAKI(d, cond1time='52hours', cond2time='172hours'))
tmp = tmp.reset_index('enc', drop=True).reset_index()

tmp = tmp.groupby('mrn', sort=False).apply(lambda d: addBaselineCreat(d))
tmp = tmp.groupby('enc', sort=False).apply(lambda d: addBackCalcAKI(d))
tmp        
tmp = tmp.reset_index(drop=True)


# In[12]:


tmp = df[375:475]
tmp = tmp.groupby('enc', sort=False).apply(lambda d: addRollingWindowAKI(d,
                                                                         cond1time = '52hours',
                                                                         cond2time = '172hours'))
tmp = tmp.reset_index('enc', drop=True).reset_index()

tmp = tmp.groupby('mrn', sort=False).apply(lambda d: addBaselineCreat(d))
tmp = tmp.groupby('enc', sort=False).apply(lambda d: addBackCalcAKI(d))


# In[92]:


t = df.loc[df.mrn == 3660621]
t = t.set_index('time')
t2 = t.loc[t.admission[0] - pd.Timedelta(hours=172):]
#t2.creat.rolling(pd.Timedelta('52hours'), min_periods=1).min().values.shape
minc_48 = np.empty(t.shape[0])
minc_48[:] = np.nan
minc_48[t.shape[0]-t2.shape[0]:] = t2.creat.rolling(pd.Timedelta('52hours'), min_periods=1).min().values
t['st'] = minc_48
t = addRollingWindowAKI(t)
#t['2020-01-29 08:14:00':]


# ## eGFR-based imputation of creatinine based on CKD-EPI equation - along with using eGFR() function and Yu's to validate results

# In[401]:


def eGFR_impute(age, sex, race):
    kappa  = (0.9 - 0.2*sex)
    alpha  = (-0.411+0.082*sex)
    creat_over_kappa = 75/(141*(1 + 0.018*sex)*(1 + 0.159*race)*0.993**age)
    
    if creat_over_kappa < 1:
        creat = kappa*creat_over_kappa**(-1/1.209)
    elif creat_over_kappa >= 1:
        creat = kappa*creat_over_kappa**(1/alpha)
    return creat

def eGFR(creat, age, female, black):
    '''
    Calculates the estimated glomerular filtration rate based on the serum creatinine levels, age, sex, and race (black or not black);
    Based on the formula in the paper A New Equation to Estimate Glomerular Filtration Rate (Levey et. Al, 2009) linked below
    
    Equation: https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating
    Full paper: https://pubmed.ncbi.nlm.nih.gov/19414839/
    
    
    '''
    min_ck = np.clip(creat/(0.9-0.2*female), a_min=None, a_max=1) #Equivalent to min(cr/k, 1)
    max_ck = np.clip(creat/(0.9-0.2*female), a_min=1, a_max=None) #Equivalent to max(cr/k, 1)
    
    alpha = (-0.411+0.082*female)
    
    egfr = 141*(0.993**age)*(min_ck**alpha)*(max_ck**-1.209)*(1+female*0.018)*(1+black*0.159)
    
    return np.round(egfr, decimals=5)


# In[478]:


get_ipython().run_cell_magic('time', '', "tmp = out[out.baseline_creat.isnull()]\ntmp = tmp[['mrn', 'enc', 'age', 'sex', 'race', 'baseline_creat']]\ntmp['imputed_creat'] = tmp.apply(lambda d: eGFRbasedCreatImputation(d.age, d.sex, d.race), axis=1)\ntmp['egfr'] = tmp.apply(lambda d: eGFR(d.imputed_creat, d.age, d.sex, d.race), axis=1)\nprint((tmp.egfr != 75).sum(), tmp.shape, (tmp.egfr != 75).sum()/tmp.shape[0])\n#tmp.head(20)")


# In[479]:


yu = pd.read_csv(r'H:\Data\Standardized AKI definition\dataset\new aki flagger 1.csv')
yu['mrn'] = yu.pat_mrn_id.str.strip('MR').astype('int')
yu['enc'] = yu.enc_id
yu = yu[['mrn', 'enc', 'imputed_baseline_creat', 'imputed_baseline']]
#yu[yu.imputed_baseline.astype('bool')].head(20)


# In[400]:


tmp = eGFR_impute_asr.iloc[7]

kappa  = (0.9 - 0.2*tmp.sex)
alpha  = (-0.411+0.082*tmp.sex)

print('female: {}, black: {}, kappa: {}, alpha: {}'.format(tmp.sex, tmp.race, kappa, alpha))

creat_over_kappa = 75/(141*(1 + 0.018*tmp.sex)*(1+0.159*tmp.race)*0.993**tmp.age)

print('calculated creat_over_kappa: {}'.format(creat_over_kappa))

if creat_over_kappa > 1:
    creat = kappa*creat_over_kappa**(-1/1.209)
    
elif creat_over_kappa < 1:
    creat = kappa*creat_over_kappa**alpha

c_gt1 = kappa*creat_over_kappa**(-1/1.209)
c_lt1 = kappa*creat_over_kappa**(1/alpha)

print('if c/k was > 1: {}'.format(c_gt1))
print('if c/k was < 1: {}'.format(c_lt1))

print('with creat > kappa: {}'.format(eGFR(c_gt1, tmp.age, tmp.sex, tmp.race)))
print('with creat < kappa: {}'.format(eGFR(c_lt1, tmp.age, tmp.sex, tmp.race)))


# In[376]:


print('c/k:', creat_over_kappa, c_gt1, c_lt1)
print('min(c/k, 1):', np.clip(c_gt1, a_min=None, a_max=1))
print('max(c/k, 1):', np.clip(c_gt1, a_min=1, a_max=None))
min_ck = np.clip(c_gt1, a_min=None, a_max=1)
max_ck = np.clip(c_gt1, a_min=1, a_max=None)
print(141*(min_ck**(-0.411+0.082*tmp.sex))*(max_ck**-1.209)*(0.993**tmp.age)*(1+tmp.sex*0.018)*(1+tmp.race*0.159))


# ## Validating Stages

# In[476]:


get_ipython().run_cell_magic('time', '', "out = returnAKIpatients(df, cond1time='52hours', cond2time='172hours')")


# In[ ]:


print('shape: {}\nstage1: {}\nstage2: {}\nstage3: {}\n{}rollingwindow: {}'.format(out.shape, out.stage1.sum(), out.stage2.sum(), out.stage3.sum(), out.rollingwindow_aki.sum()))
out.head()


# In[ ]:




