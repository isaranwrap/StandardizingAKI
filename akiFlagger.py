import pandas as pd
import numpy as np
import random 

__version__ = '0.0.3'

def returnAKIpatients(df, 
                      aki_calc_type = 'both', keep_extra_cols = True, 
                      cond1time = '48hours', cond2time = '168hours', eGFR_impute = False, add_stages=True):
    '''
    Returns patients with AKI according to the KDIGO guidelines. The KDIGO guidelines are as follows:

    * *Stage 1:* 0.3 increase in serum creatinine in < 48 hours OR 50% increase in serum creatinine in < 7 days (168 hours)
    * *Stage 2:* 100% increase in (or doubling of) serum creatinine in < 48 hours
    * *Stage 3:* 200% increase in (our tripling of) serum creatinine in < 48 hours

    Args: 

        df (pd.DataFrame): Patient dataframe, should include some sort of patient and encounter identifier(s) and age, sex, race, serum creatinine and timestamps.
        aki_calc_type (str): string, "rolling_window", "back_calculate", and "both" are the acceptable values, corresponding to the desired AKI calculation type to be returned.
        keep_extra_cols (bool): boolean, default True. 
            Choose whether or not to keep the extra columns added in the calculation process. The extra columns added throughout the process are:
            (1) the minimum creatinine in the 48 hour rolling window period
            (2) the minimum creatinine in the 7 day rolling window period
            (3) the change in creatinine between the creatinine at the given timestamp and the minimum of the previous 48 hours
            (4) the change in creatinine between the creatinine at the given timestamp and the minimum of the previous 7 days
            (5) The imputed baseline creatinine value

        cond1time (str): string, default '48hours'. 
            The amount of time for the rolling-window according to the first criterion; i.e. 0.3 increase in creatinine in *cond1time* hours. 
        cond2time (str): string, default '168hours'. 
            The amount of time for the rolling-window according to the second criterion; i.e. 50% increase in creatinine in *cond2time* hours.
        eGFR_impute (bool): boolean, default False. 
            Choose whether or not to impute baseline creatinine values for those who have no outpatient creatinine values from 365 - 7 days prior to admission.
        add_stages (bool): boolean, default True. 
            Choose whether or not to break the rolling-window AKI into the three stages as defined above.

    Returns:
        df (pd.DataFrame): Patient dataframe with AKI patients identified. 

    Raises:
        AssertionError: If the dataframe is missing an expected column; e.g. if there is no age/sex/race and eGFR_impute is True.

    '''
    
    #First, check if column names (mrn, enc, creatinine, admission & time) are as we want it
    assert ('mrn' or 'MRN' or 'pat_mrn_id' or 'PAT_MRN_ID') in df.columns
    assert ('enc' or 'ENC' or 'pat_enc_csn_id' or 'PAT_ENC_CSN_ID') in df.columns

    assert ('creat' or 'creatinine') in df.columns
    assert 'time' in df.columns
    assert 'admission' in df.columns

    #Also, if eGFR_impute is True, then we need sex age and race
    if eGFR_impute:
        assert ('age' and 'race' and 'sex') in df.columns
    
    
    if aki_calc_type == 'both': 
        df = df.groupby('mrn', sort=False).apply(lambda d: addRollingWindowAKI(d,
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
    
    Args: 
        df (pd.DataFrame): dataframe, typically of a single patient.
        eGFR_impute (bool): boolean, whether or not to impute the null baseline creatinines with the age/sex/race and eGFR of 75
        
    Returns: 
        df (pd.DataFrame): dataframe with baseline creatinine values added in

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
    i.e. a 50% increase from baseline creatinine in <7 days. Back-calculated AKI is based on the baseline creatinine, defined in the addBaselineCreat() function.
    
    Args: 
        df (pd.DataFrame): dataframe, typically of a single encounter. 

    Returns: 
        df (pd.DataFrame): dataframe with back-calculated aki values added in
    '''
    
    df = df.reset_index(drop=True).set_index('time')
    df = df[~df.index.duplicated()]
    df_lf = df.loc[(df.admission - datetime.timedelta(hours=6)).values[0]:(df.admission + pd.Timedelta(cond2time)).values[0]]
    df.loc[df_lf.index, 'backcalc_aki'] = df_lf.creat >= np.round(1.5*df_lf.baseline_creat, decimals=5)
    
    return df 

def addRollingWindowAKI(df, add_stages = True,
                        cond1time = '48hours', cond2time = '168hours'):
    '''
    Adds the AKI conditions based on rolling window definition: 

    * *Stage 1:* 0.3 increase in serum creatinine in < 48 hours OR 50% increase in serum creatinine in < 7 days (168 hours)
    * *Stage 2:* 100% increase in (or doubling of) serum creatinine in < 48 hours
    * *Stage 3:* 200% increase in (our tripling of) serum creatinine in < 48 hours
    
    Args: 
        df (pd.DataFrame): dataframe, typically of a single encounter.
        add_stages (bool): boolean, default **True**. 
            Choose whether or not to delineate the rolling-window AKI into the three stages (if False it will just lump Stage 1/2/3 into a boolean True/False)
        cond1time (str): string, default **'48hours'**. 
            The amount of time for the rolling-window according to the first criterion; i.e. 0.3 increase in creatinine in ``cond1time`` hours. 
        cond2time (str): string, default **'168hours'**. 
            The amount of time for the rolling-window according to the second criterion; i.e. 50% increase in creatinine in ``cond2time`` hours.
            
    Returns: 
        df (pd.DataFrame): dataframe with rolling-window aki values added in
    '''
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
        df['stage2'] = df.deltacreat_48hr >= 2*df.mincreat_48hr
        df['stage3'] = df.deltacreat_48hr >= 3*df.mincreat_48hr
    return df

def eGFRbasedCreatImputation(age, sex, race):
    '''
    Imputes the baseline creatinine values for those patients missing outpatient creatinine measurements from 365 to 7 days prior to admisison.
    The imputation is based on the `CKD-EPI equation <https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating>`_ 
    from the paper *A New Equation to Estimate Glomerular Filtration Rate (Levey et. Al, 2009)* linked below. 

    We assume a GFR of 75 (mL/min/1.73 m^2) and then estimate a creatinine value based on the patient demographics.

    Equation: https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating
    
    Full paper: https://pubmed.ncbi.nlm.nih.gov/19414839/

    Args:
        age (float or array of floats): the age(s) of the patient(s).
        sex (bool or array of bools): whether or not the patient is female (female is True).
        race (bool or array of bools): whether or not the patient is black (black is True).

    Returns:
        creat (float or array of floats): the imputed creatinine value(s) of the patient(s).
    '''
    #The constants kappa and alpha correspond to those used by the authors and the CKD-EPI equation, linked in the docstrings
    kappa  = (0.9 - 0.2*sex)
    alpha  = (-0.411+0.082*sex)
    creat_over_kappa = 75/(141*(1 + 0.018*sex)*(1 + 0.159*race)*0.993**age)
    
    #Note that if creat/kappa is < 1 then the equation simplifies to creat_over_kappa = (creat/kappa)**(-1.209)
    # and if creat/kappa is > 1 then the equation simplifies to (creat/kappa)**alpha. Thus, we can replace the min(~)max(~)
    #statements with the following check to define the creatinine.
    if creat_over_kappa < 1:
        creat = kappa*creat_over_kappa**(-1/1.209)
    elif creat_over_kappa >= 1:
        creat = kappa*creat_over_kappa**(1/alpha)
    return creat

def eGFR(creat, age, female, black): 
    '''
    Calculates the estimated glomerular filtration rate based on the serum creatinine levels, age, sex, and race.
    Based on the formula in the paper A New Equation to Estimate Glomerular Filtration Rate (Levey et. Al, 2009) linked below.
    
    Equation: https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating
    
    Full paper: https://pubmed.ncbi.nlm.nih.gov/19414839/
    
    Args:
        creat (float or array of floats): the creatinine value(s) of the patient(s).
        age (float or array of floats): the age(s) of the patient(s).
        female (bool or array of bools): whether or not the patient is female (female is True).
        black (bool or array of bools): whether or not the patient is black (black is True).

    Returns:
        egfr (float or array of floats): the estimated glomerular filtration rate based on the CKD-EPI equation.
    '''
    
    min_ck = np.clip(creat/(0.9-0.2*female), a_min=None, a_max=1) #Equivalent to min(cr/k, 1)
    max_ck = np.clip(creat/(0.9-0.2*female), a_min=1, a_max=None) #Equivalent to max(cr/k, 1)
    
    alpha = (-0.411+0.082*female)
    
    egfr = 141*(0.993**age)*(min_ck**alpha)*(max_ck**-1.209)*(1+female*0.018)*(1+black*0.159)
    
    return np.round(egfr, decimals=5) 

def generate_toy_data(num_patients = 100, num_encounters_range = (3, 10), include_demographic_info = False):
    '''
    Generates toy data for demonstrating how the flagger works.

    Args:
        num_patients (int): integer, default 100.
            Number of patients to generate
        num_encounters_range (tuple): tuple, default (3, 10).
            Number of encounters per patient will be randomly selected from a range between this tuple.
        include_demographic_info (bool): boolean, default False. 
            Whether or not to include the demographic information in the generated dataset


    Returns:
        df (pd.DataFrame): dataframe with toy numbers to work with.

    '''
    np.random.seed(0) #seed for reproducibility

    #pick admission dates from Jan 1, 2020 to July 1, 2020 (6 month period) and generate time deltas from +- 5 days
    date_range = (pd.to_datetime('2020-01-01').value // 10**9, pd.to_datetime('2020-07-01').value // 10**9) 
    time_deltas = pd.timedelta_range(start='-5 days', end='5 days', freq='6H')

    #Generate random MRN #s, admission dates, and encounters
    #Generate between 3 and 10 encounters for each patient
    mrns = np.random.randint(10000, 20000, num_patients)
    admns = pd.to_datetime(np.random.randint(date_range[0], date_range[1], num_patients), unit = 's')
    encs = [np.random.randint(10000, 99999, np.random.randint(num_encounters_range[0],num_encounters_range[1])) for mrn, admn in zip(mrns, admns)]
    creats = np.clip(np.random.normal(loc = 1, scale = 0.3, size=num_patients), a_min = 0, a_max = None)

        
    #Combine the two dataframes
    d1 = pd.DataFrame([mrns, admns, creats]).T
    d2 = pd.DataFrame(encs)
    
    d1.columns = ['mrn', 'admission', 'base_creat']
    d2 = d2.add_prefix('enc_')
    
    if include_demographic_info:
        ages = np.random.normal(loc = 60, scale = 5, size=num_patients)
        race = np.random.rand(num_patients) > 0.85
        sex = np.random.rand(num_patients) > 0.5
    
        d1 = pd.DataFrame([mrns, admns, creats, ages, race, sex]).T
        d1.columns = ['mrn', 'admission', 'base_creat', 'age', 'black', 'female']

    df = pd.concat([d1, d2], axis=1)
    df = pd.melt(df, id_vars = d1.columns, value_name = 'enc').drop('variable', axis=1)

    #Remove the duplicated & null values and reset the index
    df = df[np.logical_and(~df.enc.isnull(), ~df.enc.duplicated())].reset_index(drop=True) 

    df['creat'] = np.clip(df.base_creat + np.random.normal(loc = 0, scale = 0.25, size = df.shape[0]), a_min = 0.1, a_max = None).astype('float')
    df['time'] = df.admission + np.array([random.choice(time_deltas) for i in range(df.shape[0])])
    
    df['mrn'] = df.mrn.astype('int')
    df['enc'] = df.enc.astype('int')
    
    if include_demographic_info:
        df = df[['mrn', 'enc', 'age', 'black', 'female', 'admission', 'time', 'creat']]
        print('Successfully generated toy data!')
        return df
    df = df[['mrn', 'enc', 'admission', 'time', 'creat']]
    print('Successfully generated toy data!')
    return df