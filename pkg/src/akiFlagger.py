import pandas as pd
import numpy as np

def returnAKIpatients(df, 
                      aki_calc_type = 'both', keep_extra_cols = True, 
                      cond1time = '48hours', cond2time = '168hours', eGFR_impute = False, add_stages=True):
    '''
    Returns patients with AKI according to the KDIGO guidelines. The KDIGO guidelines are as follows:

    ~KDIGO guidelines will go here~ & any additional information

    Args: 
        df (pd.DataFrame): Patient dataframe, should include some sort of patient and encounter identifier(s) and age, sex, race, serum creatinine and timestamps.
        aki_calc_type (str): string, "rolling_window", "back_calculate", and "both" are the acceptable values, corresponding to the desired AKI calculation type to be returned.
        keep_extra_cols (bool): boolean, default True. Choose whether or not to keep the extra columns added in the calculation process. The extra columns added throughout the process are:
            Rolling-window AKI
            ------------------
            (1) the minimum creatinine in the two specified rolling-window periods (48 hours and 7 days, by default)
            (2) the change in creatinine between the creatinine at the given timestamp and the minimum of the previous 48 hours and 7 days
            
            Back-calculated
            ---------------
            (1) The imputed baseline creatinine value
        cond1time (str): string, default '48hours'. The amount of time for the rolling-window according to the first criterion; i.e. 0.3 increase in creatinine in *cond1time* hours. 
        cond2time (str): string, default '168hours'. The amount of time for the rolling-window according to the second criterion; i.e. 50% increase in creatinine in *cond2time* hours.
        eGFR_impute (bool): boolean, default False. Choose whether or not to impute baseline creatinine values for those who have no outpatient creatinine values from 365 - 7 days prior to admission.
        add_stages (bool): boolean, default True. Choose whether or not to break the rolling-window AKI into the three stages as defined above.

    Returns:
        df (pd.DataFrame): Patient dataframe with AKI patients identified. 

    Raises:
        AssertionError: If the dataframe is missing an expected column; e.g. if there is no age/sex/race and eGFR_impute is True.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/


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
        df (pd.DataFrame): dataframe, typically of a single patient)
        eGFR_impute (bool): boolean, whether or not to impute the null baseline creaitnines with the age/sex/race and eGFR of 75
        
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