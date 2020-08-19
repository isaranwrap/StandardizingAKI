class AKIFlagger:
    '''Flagger to detect patients with acute kidney injury (AKI).
    '''
    def __init__(self, patient_id = 'mrn', creatinine='creatinine', time = 'time', inpatient = 'inpatient', 
                 aki_calc_type=None, keep_extra_cols = False, eGFR_impute = False, add_stages = None,
                 cond1time = '48hours', cond2time = '168hours', pad1time = '0hours', pad2time = '0hours', 
                 rolling_window = False, back_calculate = False,
                 admission = 'admission', age = 'age', sex = 'sex', race = 'race', encounter_id = 'enc',
                 baseline_creat = 'baseline_creat'):
        
        #Identifiers
        self.patient_id = patient_id
        self.encounter_id = encounter_id
        
        #Columns necessary for calculation (if admission not included it will be imputed)
        self.creatinine = creatinine
        self.time = time
        self.inpatient = inpatient
        self.admission = admission
        
        #Demographic variables
        self.age = age
        self.sex = sex
        self.race = race
        
        #Rolling-window variables
        self.cond1time = cond1time
        self.cond2time = cond2time
        self.pad1time = pad1time
        self.pad2time = pad2time
        
        #Back-calculate variables
        self.baseline_creat = baseline_creat
        
        #Extra options to specify what is included in the output
        self.eGFR_impute = eGFR_impute
        self.add_stages = add_stages
        self.keep_extra_cols = keep_extra_cols
        
        #Specifying the calculation type wanted in the flagger
        self.aki_calc_type = aki_calc_type
        self.rolling_window = rolling_window
        self.back_calculate = back_calculate
        
        if self.aki_calc_type is not None:
            if self.aki_calc_type == 'rolling_window':
                self.rolling_window = True
            elif self.aki_calc_type == 'back_calculate':
                self.back_calculate = True
            elif self.aki_calc_type == 'both':
                self.rolling_window = True
                self.back_calculate = True
            
    def returnAKIpatients(self, df, add_stages = None, 
                          cond1time = None, cond2time = None, pad1time = None, pad2time = None):
        '''
        Returns patients with AKI according to the KDIGO guidelines. The KDIGO guidelines are as follows:

        * *Stage 1:* 0.3 increase in serum creatinine in < 48 hours OR 50% increase in serum creatinine in < 7 days (168 hours)
        * *Stage 2:* 100% increase in (or doubling of) serum creatinine in < 7 days (168 hours)
        * *Stage 3:* 200% increase in (our tripling of) serum creatinine in < 7 days (168 hours)

        More information can be found in the documentation at akiflagger.readthedocs.io
        Args: 
            df (pd.DataFrame): Patient dataframe, should include some sort of patient and encounter identifier(s) and age, sex, race, serum creatinine and timestamps.
        Returns:
            df (pd.DataFrame): Patient dataframe with AKI patients identified. 

        Raises:
            AssertionError: If the dataframe is missing an expected column; e.g. if there is no age/sex/race and eGFR_impute is True.

        '''
        if add_stages is None:
            add_stages = self.add_stages
        self.add_stages = add_stages
        
        if cond1time is None:
            cond1time = self.cond1time
        self.cond1time = cond1time
        
        if cond2time is None:
            cond2time = self.cond2time
        self.cond2time = cond2time
        
        if pad1time is None:
            pad1time = self.pad1time
        self.pad1time = pad1time
        
        if pad2time is None:
            pad2time = self.pad2time
        self.pad2time = pad2time
        
        if self.admission not in df.columns:
            df = self.addAdmissionColumn(df, add_encounter_col = self.encounter_id not in df.columns)
            df = df[~df[self.admission].isnull()]
            
        if self.rolling_window: 
            df = df.groupby(self.patient_id, sort=False, as_index=False).apply(lambda d: self.addRollingWindowAKI(d))
            df = df.reset_index(level=0, drop=True).reset_index() #this will leave time as the index
            
        if self.back_calculate:
            df = df.groupby(self.patient_id, sort=False, as_index=False).apply(lambda d: d.sort_values(self.time)).reset_index(drop=True)
            df = df.groupby(self.patient_id, sort=False).apply(lambda d: self.addBaselineCreat(d, 
                                                                                               eGFR_impute=self.eGFR_impute))

            df = df.groupby(self.encounter_id, sort=False, as_index=False).apply(lambda d: self.addBackCalcAKI(d))
            df = df.reset_index(level=0, drop=True).reset_index()
            
        if not self.keep_extra_cols:
            if self.rolling_window or self.aki_calc_type == 'both' or self.aki_calc_type == 'rolling_window':
                df = df.drop([self.mint1_colname, self.mint2_colname, self.delt1_colname, self.delt2_colname], axis=1)
            if self.back_calculate or self.aki_calc_type == 'both' or self.aki_calc_type == 'back_calculate':
                df = df.drop([self.baseline_creat], axis = 1)
        return df
    
    def addRollingWindowAKI(self, df):
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
        df = df.set_index(self.time).sort_index()
        df_rw = df.loc[df.admission[0] - pd.Timedelta(hours=172):]
        
        t1 = pd.Timedelta(self.cond1time) + pd.Timedelta(self.pad1time)
        t2 = pd.Timedelta(self.cond2time) + pd.Timedelta(self.pad2time)
        
        minc_t1, minc_t2 = np.empty(df.shape[0]), np.empty(df.shape[0])
        minc_t1[:], minc_t2[:] = np.nan, np.nan 
        minc_t1[df.shape[0]-df_rw.shape[0]:] = df_rw[self.creatinine].rolling(t1, min_periods=1).min().values
        minc_t2[df.shape[0]-df_rw.shape[0]:] = df_rw[self.creatinine].rolling(t2, min_periods=1).min().values

        self.mint1_colname = 'mincreat_{}'.format(t1.days*24 + t1.seconds // 3600)
        self.mint2_colname = 'mincreat_{}'.format(t2.days*24 + t2.seconds // 3600)
        self.delt1_colname = 'deltacreat_{}'.format(t1.days*24 + t1.seconds // 3600)
        self.delt2_colname = 'deltacreat_{}'.format(t2.days*24 + t2.seconds // 3600)
        
        df[self.mint1_colname] = minc_t1
        df[self.mint2_colname] = minc_t2

        df[self.delt1_colname] = np.round(df.creat - df[self.mint1_colname], decimals = 5)
        df[self.delt2_colname] = np.round(df.creat - df[self.mint2_colname], decimals = 5)

        if self.add_stages:
            df['stage1'] = (df[self.delt1_colname] >= 0.3) | (df[self.delt2_colname] >= 0.5*df[self.mint2_colname])
            df['stage2'] = df[self.delt2_colname] >= 2*df[self.mint2_colname]
            df['stage3'] = df[self.delt2_colname] >= 3*df[self.mint2_colname]
            
        df['rollingwindow_aki'] = 1*df.stage1 + 1*df.stage2 + 1*df.stage3 if self.add_stages else (df[self.delt1_colname] >= 0.3) | (df[self.delt2_colname] >= 0.5*df[self.mint2_colname])
  
        return df
    
    def addAdmissionColumn(self, df, add_encounter_col = None):

        pat_gb = df.groupby(self.patient_id)

        #Check for those rows which are all inpatient; e.g. a hospital visit
        df.loc[:, 'all_inp'] = pat_gb.inpatient.transform(lambda d: np.all(d))
        df.loc[:, 'all_inp'] = df.all_inp & ~pat_gb.all_inp.shift(1, fill_value=False)

        df.loc[:, self.admission] = df.inpatient & ~pat_gb.inpatient.shift(1, fill_value=False)
        df.loc[:, self.admission] = df[np.logical_or(df.admission, df.all_inp)].time
        df.loc[:, self.admission] = pat_gb.admission.apply(lambda s: s.bfill().ffill())

        if add_encounter_col:
            df.loc[:, self.encounter_id] = df.inpatient & ~pat_gb.inpatient.shift(1, fill_value=False)
            df.loc[df[self.encounter_id], self.encounter_id] = np.arange(1, df.enc.sum()+1)
            df.loc[df[self.encounter_id] == False, self.encounter_id] = np.nan
            df.loc[:,self.encounter_id] = pat_gb[self.encounter_id].apply(lambda s: s.bfill().ffill())
        df = df.drop(['all_inp'], axis=1)
        
        return df

    def addBackCalcAKI(self, df):
        '''
        Adds the back-calculated AKI conditions, the KDIGO standards on the outpatient values;
        i.e. a 50% increase from baseline creatinine in <7 days. Back-calculated AKI is based on the baseline creatinine, defined in the addBaselineCreat() function.

        Args: 
            df (pd.DataFrame): dataframe, typically of a single encounter. 

        Returns: 
            df (pd.DataFrame): dataframe with back-calculated aki values added in
        '''

        df = df.reset_index(drop=True).set_index(self.time)
        df = df[~df.index.duplicated()]
        #Look back 6 hours prior to admission
        t_lf = pd.Timedelta(self.cond2time) + pd.Timedelta(self.pad2time) #Look forward time is cond2time + padding
        df_lf = df.loc[(df[self.admission] - datetime.timedelta(hours=6)).values[0]:(df[self.admission] + t_lf).values[0]]
        df.loc[df_lf.index, 'backcalc_aki'] = df_lf[self.creatinine] >= np.round(1.5*df_lf[self.baseline_creat], decimals=5)
        df.loc[df.backcalc_aki.isnull(), 'backcalc_aki'] = False

        return df
    
    def addBaselineCreat(self, df, eGFR_impute = None):
        '''
        Adds the baseline creatinine to a dataframe. The baseline creatinine is defined as the median of the outpatient 
        creatinine values from 365 to 7 days prior to admission.

        Args: 
            df (pd.DataFrame): dataframe, typically of a single patient.
            eGFR_impute (bool): boolean, whether or not to impute the null baseline creatinines with the age/sex/race and eGFR of 75

        Returns: 
            df (pd.DataFrame): dataframe with baseline creatinine values added in

        '''
        if eGFR_impute is None:
            eGFR_impute = self.eGFR_impute
        self.eGFR_impute = eGFR_impute

        split_dfs = list()
        unique_adms = df[self.admission].unique()
        for adm in unique_adms[~np.isnat(unique_adms)]:
            adm_df = df.loc[df[self.admission] == adm]
            adm_df.loc[:,self.baseline_creat] = adm_df[~adm_df[self.inpatient]].set_index(self.time).loc[adm - pd.Timedelta(days=365):adm - pd.Timedelta(days=7), self.creatinine].median()
            split_dfs.append(adm_df)
        
        df = pd.concat(split_dfs)

        if self.eGFR_impute:
                df.loc[df[self.baseline_creat].isnull(), self.baseline_creat] = df[df[self.baseline_creat].isnull()].apply(lambda d: self.eGFRbasedCreatImputation(d[self.age], d[self.sex], d[self.race]), axis=1)

        return df
    
    def eGFRbasedCreatImputation(self, age, sex, race):
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
        #The hard-coded constants, kappa, and alpha correspond to those used by the authors and the CKD-EPI equation, linked in the docstrings
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

    def eGFR(self, creat, age, female, black): 
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

    def generate_toy_data(self, num_patients = 100, 
                          num_encounters_range = (3, 10), include_demographic_info = False,
                          date_range = None, time_deltas = None, creat_scale = 0.3):
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

        #To explicitly demonstrate that race and sex variables only care about black/female distinction
        self.race = 'black'
        self.sex = 'female'
        
        #pick admission dates from Jan 1, 2020 to July 1, 2020 (6 month period) and generate time deltas from +- 5 days
        if date_range is None:
            date_range = (pd.to_datetime('2020-01-01').value // 10**9, pd.to_datetime('2020-07-01').value // 10**9) 
        if time_deltas is None:
            time_deltas = pd.timedelta_range(start='-5 days', end='5 days', freq='6H')

        #Generate random MRN #s, admission dates, and encounters
        #Generate between 3 and 10 encounters for each patient
        mrns = np.random.randint(10000, 20000, num_patients)
        admns = pd.to_datetime(np.random.randint(date_range[0], date_range[1], num_patients), unit = 's')
        encs = [np.random.randint(10000, 99999, np.random.randint(num_encounters_range[0],num_encounters_range[1])) for mrn, admn in zip(mrns, admns)]
        creats = np.clip(np.random.normal(loc = 1, scale = creat_scale, size=num_patients), a_min = 0, a_max = None)

        #Combine the two dataframes
        d1 = pd.DataFrame([mrns, admns, creats]).T
        d2 = pd.DataFrame(encs)

        d1.columns = [self.patient_id, self.admission, self.baseline_creat]
        d2 = d2.add_prefix('enc_')

        if include_demographic_info:
            ages = np.random.normal(loc = 60, scale = 5, size=num_patients)
            race = np.random.rand(num_patients) > 0.85
            sex = np.random.rand(num_patients) > 0.5

            d1 = pd.DataFrame([mrns, admns, creats, ages, race, sex]).T
            d1.columns = [self.patient_id, self.admission, self.baseline_creat, self.age, self.race, self.sex]

        df = pd.concat([d1, d2], axis=1)
        df = pd.melt(df, id_vars = d1.columns, value_name = self.encounter_id).drop('variable', axis=1)

        #Remove the duplicated & null values and reset the index
        df = df[np.logical_and(~df[self.encounter_id].isnull(), ~df[self.encounter_id].duplicated())].reset_index(drop=True) 

        df[self.creatinine] = np.clip(df[self.baseline_creat] + np.random.normal(loc = 0, scale = 0.25, size = df.shape[0]), a_min = 0.1, a_max = None).astype('float')
        df[self.time] = df[self.admission] + pd.to_timedelta([random.choice(time_deltas) for i in range(df.shape[0])])
        df[self.inpatient] = df[self.time] > df[self.admission]
        
        df[self.patient_id] = df[self.patient_id].astype('int')
        df[self.encounter_id] = df[self.encounter_id].astype('int')
        
            
        df = df.groupby(self.patient_id, sort=False, as_index=False).apply(lambda d: d.sort_values(self.time))
        df = df.reset_index(drop=True)
        
        if include_demographic_info:
            df = df[[self.patient_id, self.encounter_id, self.age, self.race, self.sex, self.inpatient, self.admission, self.time, self.creatinine]]
            print('Successfully generated toy data!')
            return df
        
        df = df[[self.patient_id, self.encounter_id, self.inpatient, self.admission, self.time, self.creatinine]]
        print('Successfully generated toy data!')
        return df