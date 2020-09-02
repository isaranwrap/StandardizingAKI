import pandas as pd
import numpy as np
import datetime, random

__version__ = '0.1.0' 

class AKIFlagger:
    ''' Main flagger to detect patients with acute kidney injury (AKI).
    This flagger returns patients with AKI according to the KDIGO guidelines. The KDIGO guidelines are as follows:

        * *Stage 1:* 0.3 increase in serum creatinine in < 48 hours OR 50% increase in serum creatinine in < 7 days (168 hours)
        * *Stage 2:* 100% increase in (or doubling of) serum creatinine in < 7 days (168 hours)
        * *Stage 3:* 200% increase in (our tripling of) serum creatinine in < 7 days (168 hours)

        More information can be found in the documentation at akiflagger.readthedocs.io
        
    Attributes:
        patient_id (string): **default 'mrn'.** Name of the column used to identify patients; e.g. 'PAT_MRN_ID'
        encounter_id (string): **default 'enc'.** Name of the column used to identify encounters; e.g. 'PAT_ENC_CSN_ID'
        
        time (string): **default 'time'.** Name of the column containing time stamps; e.g. 'time'
        inpatient (string): **default 'inpatient'.** Name of the column containing inpatient/outpatient identifier; e.g. 'inpatient'
        admission (string): **default 'admission'.** Name of the column containing the admission dates; e.g. 'admission'
        creatinine (string): **default 'creatinine'.** Name of the column containing creatinine values; e.g. 'creatinine'
        baseline_creat (string): **default 'baseline_creat'.** Name of the column containint baseline creatinine values; e.g 'baseline_creat'
        
        age (string): **default 'age'.** Name of the column containing the age values; e.g. 'age'
        sex (string): **default 'sex'.** Name of the column containing the age values; e.g. 'age'
        race (string): **default 'race'.** Name of the column containing the age values; e.g. 'age'
        
        aki_calc_type (string): **defaults to None.** Name of the AKI-calculation method the flagger should perform.
            Possible values are "rolling_window", "back_calculate", or "both".
        rolling_window (boolean): **default True.** Whether to perform rolling-window AKI calculation.
        back_calculate (boolean): **default False.** Whether to perform back-calculate AKI calculation.
        
        eGFR_impute (boolean): **default False.** Whether or not to impute the missing baseline creatinine values with the
            eGFR-imputation method; i.e. assuming an eGFR of 75 estimate baseline creatinine based on age, sex, and race.
        add_stages (boolean): **default True.** Whether or not to have rolling-window AKI delineated into stages.
            If add_stages is True, the generated `rw` column dtype is *int64* otherwise the `rw` column dtypes is *bool*.
        
        cond1time (string): **default '48hours'.** The rolling-window time of the first KDIGO criterion condition.
            This string gets passed to pd.Timedelta(cond1time), so any acceptable time format for that function will work.
        cond2time (string): **default '168hours'.** The rolling-window time of the second KDIGO criterion condition.
            This string gets passed to pd.Timedelta(cond2time), so any acceptable time format for that function will work.
        pad1time (string): **default '0hours'.** Padding to add to the first KDIGO criterion condition.
            This string gets passed to pd.Timedelta(pad1time), so any acceptable time format for that function will work.
        pad2time (string): **default '0hours'.** Padding to add to the second KDIGO criterion condition.
            This string gets passed to pd.Timedelta(pad2time), so any acceptable time format for that function will work.
        
        sort_values (boolean): **default True.** Whether or not to sort the values within each encounter based on `time`.
        remove_bc_na (boolean): **default True.** Whether or not to convert the back-calculated NaNs to Falses.
        add_baseline_creat (boolean): **default False.** Whether or not to add the baseline creatinine column from back-calculate method.
        add_min_creat (boolean): **default False.** Whether or not to add the minimum creatinine column from rolling-window method.
        
    '''
    def __init__(self, patient_id = 'mrn', creatinine = 'creatinine', time = 'time', inpatient = 'inpatient', 
                 aki_calc_type = None, eGFR_impute = False, add_stages = True,
                 cond1time = '48hours', cond2time = '168hours', pad1time = '0hours', pad2time = '0hours', 
                 rolling_window = True, back_calculate = False,
                 admission = 'admission', age = 'age', sex = 'sex', race = 'race', encounter_id = 'enc',
                 baseline_creat = 'baseline_creat', sort_values = True, remove_bc_na = True, add_baseline_creat = False, add_min_creat = False):
        
        # Identifiers
        self.patient_id = patient_id
        self.encounter_id = encounter_id
        
        # Columns necessary for calculation (if admission not included it will be imputed)
        self.creatinine = creatinine
        self.time = time
        self.inpatient = inpatient
        self.admission = admission
        
        # Demographic variables
        self.age = age
        self.sex = sex
        self.race = race
        
        # Rolling-window variables
        self.cond1time = pd.Timedelta(cond1time) + pd.Timedelta(pad1time)
        self.cond2time = pd.Timedelta(cond2time) + pd.Timedelta(pad2time)
        
        # Back-calculate variables
        self.baseline_creat = baseline_creat
        
        # Extra options to specify what is included in the output
        self.eGFR_impute = eGFR_impute
        self.add_stages = add_stages
        self.remove_bc_na = remove_bc_na
        self.add_baseline_creat = add_baseline_creat
        self.add_min_creat = add_min_creat
        
        # Specifying the calculation type wanted in the flagger
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
        if self.rolling_window and self.back_calculate:
            self.aki_calc_type = 'both'
        elif self.rolling_window:
            self.aki_calc_type = 'rolling_window'
        elif self.back_calculate:
            self.aki_calc_type = 'back_calculate'
        
    def returnAKIpatients(self, dataframe, add_stages = None, 
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
        ## Checks: we need to make sure the required columns are in the dataframe
        assert (self.encounter_id in dataframe.columns or self.patient_id in dataframe.columns), "Patient identifier missing!"
        assert (self.creatinine in dataframe.columns), "Creatinine column missing!"
        assert (self.time in dataframe.columns), "Time column missing!"
        assert (self.inpatient in dataframe.columns), "Inpatient/outpatient column missing!"
        
        if self.eGFR_impute:
            assert (self.age in dataframe.columns), "If you are using the eGFR-based imputation method, you need to have an age, sex, and race column!"
            assert (self.sex in dataframe.columns), "If you are using the eGFR-based imputation method, you need to have an age, sex, and race column!"
            assert (self.race in dataframe.columns), "If you are using the eGFR-based imputation method, you need to have an age, sex, and race column!"
        ## Step 1: Set the index to encounter & time variables
        
        #First, check if enc in cols or indx
        if self.encounter_id not in dataframe.columns and self.encounter_id not in dataframe.index.names:
            
            #If no, check if admission in cols or indx
            if self.admission not in dataframe.columns and self.admission not in dataframe.index.names:
                df = self.addAdmissionColumn(dataframe, add_encounter_col = True)
                df = df.set_index([self.encounter_id, self.time])

            #Otherwise, add encounters based on the unique admissions
            elif self.admission in dataframe.index.names or self.admission in dataframe.columns:
                df = dataframe.copy()
                mask = df.groupby(self.admission).head(1).index
                df.loc[mask, self.encounter_id] = np.arange(df[self.admission].unique().shape[0])
                df[self.encounter_id] = df[self.encounter_id].ffill()
                df = df.set_index([self.encounter_id, self.time])
        
        #If encounter is in indx/col, of course, we have no problem
        elif self.encounter_id in dataframe.columns or self.encounter_id in dataframe.index.names:
            df = dataframe.set_index([self.encounter_id, self.time])
            
        ## Step 2: Sort based on time and also drop the duplicates
        df = df.groupby(self.encounter_id, sort=False, as_index = False).apply(lambda d: d.sort_index(level=self.time))
        df = df[~df.index.duplicated()]
        
        #Note that at this point we assume enc & time are indices NOT columns
        
        ## Step 3: Add rolling-window and/or back-calculate aki
        if self.rolling_window:
            rw = self.addRollingWindowAKI(df)
        if self.back_calculate:
            baseline_creat = self.addBaselineCreat(df)
            bc = self.addBackCalcAKI(df, baseline_creat = baseline_creat)
        
        if self.aki_calc_type == 'both':
            if self.add_baseline_creat and self.add_min_creat: 
                return pd.concat([df, rw[0], rw[1], bc[0], bc[1]], axis=1).reset_index()
            elif self.add_baseline_creat: 
                return pd.concat([df, rw, bc[0], bc[1]], axis=1).reset_index() 
            elif self.add_min_creat:
                return pd.concat([df, rw[0], rw[1], bc], axis=1).reset_index()
            return pd.concat([df, rw, bc], axis=1).reset_index()
        elif self.rolling_window:
            if self.add_min_creat:
                return pd.concat([df, rw[0], rw[1]], axis=1).reset_index()
            return pd.concat([df, rw], axis=1).reset_index()
        elif self.back_calculate:
            if self.add_baseline_creat:
                return pd.concat([df, bc[0], bc[1]], axis=1).reset_index()
            return pd.concat([df, bc], axis=1).reset_index()
    
    def addAdmissionColumn(self, df, add_encounter_col = None):

        pat_gb = df.groupby(self.patient_id, sort = False)

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
    
    def addRollingWindowAKI(self, df):
        
        # Set the index to just time 
        tmp = df[self.creatinine].reset_index(self.encounter_id) 
        
        # Groupby on encounter then apply conditions for rolling-window AKI
        gb = tmp.groupby(self.encounter_id, as_index = True, sort = False)
        gb_indx = gb[self.creatinine].rolling(self.cond1time).min().index
        c1 = tmp.set_index([self.encounter_id, tmp.index.get_level_values(level=self.time)]).loc[gb_indx][self.creatinine] >= 0.3 + gb[self.creatinine].rolling(self.cond1time).min()
        c2 = tmp.set_index([self.encounter_id, tmp.index.get_level_values(level=self.time)]).loc[gb_indx][self.creatinine] >= 1.5*gb[self.creatinine].rolling(self.cond2time).min()
        
        # Stage 1 suffices for rw if add_stages is False
        stage1 = np.logical_or(c1, c2)
        stage1 = stage1.reindex(df.index)

        # Otherwise, create the additional stages & return their row-wise sum
        if self.add_stages:
            stage2 = tmp.set_index([self.encounter_id, tmp.index.get_level_values(level=self.time)]).loc[gb_indx][self.creatinine] >= 2*gb[self.creatinine].rolling(self.cond2time).min()
            stage3 = tmp.set_index([self.encounter_id, tmp.index.get_level_values(level=self.time)]).loc[gb_indx][self.creatinine] >= 3*gb[self.creatinine].rolling(self.cond2time).min()
            
            stage2 = stage2.reindex(df.index)
            stage3 = stage3.reindex(df.index)

            # Last checks on the index before returning 
            assert (np.all(stage1.index == df.index)), 'Index mismatch!'
            assert (np.all(stage2.index == df.index)), 'Index mismatch!'
            assert (np.all(stage3.index == df.index)), 'Index mismatch!'
            
            if self.add_min_creat:
                min_creat = pd.Series(gb[self.creatinine].rolling(self.cond1time).min(), index = df.index, name = 'min_creat')
                assert (np.all(min_creat.index == df.index)), 'Index mismatch!'
                return pd.Series(stage3.add(stage2.add(stage1*1)), name = 'rw'), min_creat
            return pd.Series(stage3.add(stage2.add(stage1*1)), name = 'rw')

        # One last check on the index before returning 
        rw = pd.Series(stage1, index = df.index, name = 'rw')
        assert (np.all(rw.index == df.index)), 'Index mismatch! Something went wrong...'
        return rw
    
    def eGFRbasedCreatImputation(self, age, female, black):
        '''Imputes the baseline creatinine values for those patients missing outpatient creatinine measurements from 365 to 7 days prior to admission.
        The imputation is based on the `CKD-EPI equation <https://niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimateing>`_ from the paper
        *A New Equation to Estimate Glomerular Filtration Rate (Levey et. Al, 2009)* linked below.
        '''

        kappa = (0.9 - 0.2*female)
        alpha = (-0.411 + 0.082*female)
        creat_over_kappa = 75/(141*(1 + 0.018*female)*(1 + 0.159*black)*0.993**age)

        # Note that if creat/kappa is < 1 then the equation simplifies to creat_over_kappa = (creat/kappa)**(-1.209)
        # and if creat/kappa is > 1 then the equation simplifies to (creat/kappa)**alpha. Thus, we can replace the min(~)max(~)
        # statements with the following check:
        
        creat = kappa
        creat[creat_over_kappa < 1] = kappa*creat_over_kappa**(-1/1.209)
        creat[creat_over_kappa >=1] = kappa*creat_over_kappa**(1/alpha)

        return creat

    def addBaselineCreat(self, df):
    
        # Baseline creatinine is defined as the MEDIAN of the OUTPATIENT values from 365 to 7 days prior to admission

        # First, subset on columns necessary for calculation: creatinine, admission & inpatient/outpatient
        tmp = df.loc[:,[self.creatinine, self.admission, self.inpatient]]
        if self.eGFR_impute:
            tmp = df.loc[:, [self.creatinine, self.admission, self.inpatient, self.age, self.race, self.sex]]
        

        # Next, create a T/F mask for the times between 365 & 7 days prior to admission AND outpatient vals 
        bc_tz = np.logical_and(tmp[self.admission] - pd.Timedelta(days=365) <= tmp.index.get_level_values(level=self.time),
                           tmp[self.admission] - pd.Timedelta(days=7) >= tmp.index.get_level_values(level=self.time))
        mask = np.logical_and(bc_tz, ~tmp[self.inpatient])
        
        # Finally, add the median creat values to the dataframe, forward-fill, and return
        tmp.loc[mask, self.baseline_creat] = tmp[mask].groupby(self.encounter_id, as_index=True)[self.creatinine].transform('median')
        tmp[self.baseline_creat] = tmp.groupby(self.encounter_id)[self.baseline_creat].ffill()
        
        # If we'd like to perform the imputation based on the eGFR of 75
        if self.eGFR_impute:
            imp = df.loc[tmp[self.baseline_creat].isnull()]
            if self.sex == 'male':
                tmp.loc[tmp[self.baseline_creat].isnull(), self.baseline_creat] = self.eGFRbasedCreatImputation(imp[self.age], ~imp[self.sex], imp[self.race])
            elif self.sex == 'female':
                tmp.loc[tmp[self.baseline_creat].isnull(), self.baseline_creat] = self.eGFRbasedCreatImputation(imp[self.age], imp[self.sex], imp[self.race])
            else:
                tmp.loc[tmp[self.baseline_creat].isnull(), self.baseline_creat] = self.eGFRbasedCreatImputation(imp[self.age], imp[self.sex], imp[self.race])
        return tmp.baseline_creat
    
    def addBackCalcAKI(self, df, baseline_creat=None):
        
        # Subset on necessary cols: creat + admn
        tmp = df.loc[:, [self.creatinine, self.admission]]
        
        # Look back 6 hours prior to admission until cond2time from admission
        mask = np.logical_and(tmp[self.admission] - pd.Timedelta(hours=6) <= tmp.index.get_level_values(level = self.time),
                              tmp[self.admission] + self.cond2time >= tmp.index.get_level_values(level = self.time))
        
        # Apply aki definition & return the resulting series (the reason we add it to the data frame is so we can get
        # the NaNs in the right place without doing much work as a "freebie")
        tmp.loc[mask, 'bc'] = tmp[mask][self.creatinine] >= 1.5*baseline_creat[mask]
        
        # And by default, I'll replace the null values with False's 
        if self.remove_bc_na:
            tmp.loc[tmp.bc.isnull(), 'bc'] = False
        if self.add_baseline_creat:
            return tmp.bc, baseline_creat[mask]
        return tmp.bc
    
    
def generate_toy_data(num_patients = 100, num_encounters_range = (1, 3), num_time_range = (5,10),
                      include_demographic_info = False, date_range = None, time_delta_range = None, creat_scale = 0.3):
        '''
        Generates toy data for demonstrating how the flagger works.

        Args:
            num_patients (int): integer, default 100.
                Number of patients to generate
            num_encounters_range (tuple): tuple, default (3, 10).
                Number of encounters per patient will be randomly selected from a range between this tuple.
            include_demographic_info (bool): boolean, default False. 
                Whether or not to include the demographic information in the generated dataset


        Returns
            df (pd.DataFrame): dataframe with toy numbers to work with.

        '''
        np.random.seed(0) # seed for reproducibility

        # To explicitly demonstrate that race and sex variables only care about black/female distinction
        black = 'black'
        female = 'female'
        age = 'age'
        
         # pick admission dates from Jan 1, 2020 to July 1, 2020 (6 month period) and generate time deltas from +- 5 days
        if date_range is None:
            date_range = (pd.to_datetime('2020-01-01').value // 10**9, pd.to_datetime('2020-07-01').value // 10**9) 
        if time_delta_range is None:
            time_delta_range = pd.timedelta_range(start='-5 days', end='5 days', freq='6H')

        # Generate random MRN #s, admission dates, and encounters
        # Generate between 3 and 10 encounters for each patient
        mrns = np.random.randint(10000, 20000, num_patients)
        admns = pd.to_datetime(np.random.randint(date_range[0], date_range[1], num_patients), unit = 's')
        encs = [np.random.randint(10000, 99999, np.random.randint(num_encounters_range[0],num_encounters_range[1])) for mrn, admn in zip(mrns, admns)]
        creats = np.clip(np.random.normal(loc = 1, scale = creat_scale, size=num_patients), a_min = 0, a_max = None)

        #Combine the two dataframes
        d1 = pd.DataFrame([mrns, admns, creats]).T
        d2 = pd.DataFrame(encs)

        patient_id, encounter_id, time, admission, inpatient, creatinine, baseline_creat = 'mrn','enc','time','admission','inpatient', 'creat', 'baseline_creat'
        d1.columns = [patient_id, admission, baseline_creat]
        d2 = d2.add_prefix('enc_')

        if include_demographic_info:
            ages = np.random.normal(loc = 60, scale = 5, size=num_patients)
            race = np.random.rand(num_patients) > 0.85
            sex = np.random.rand(num_patients) > 0.5

            d1 = pd.DataFrame([mrns, admns, creats, ages, race, sex]).T
            d1.columns = [patient_id, admission, baseline_creat, age, black, female]

        df1 = pd.concat([d1, d2], axis=1)
        df1 = pd.melt(df1, id_vars = d1.columns, value_name = 'enc').drop('variable', axis=1)
        df1 = df1[np.logical_and(~df1[encounter_id].isnull(), ~df1[encounter_id].duplicated())].reset_index(drop=True)
        
        time_deltas = [random.choices(time_delta_range, k=np.random.randint(num_time_range[0],num_time_range[1])) for i in range(df1.shape[0])]
        d3 = pd.DataFrame(time_deltas).add_prefix('time_')
        df = pd.concat([df1, d3], axis=1)
        df = pd.melt(df, id_vars = df1.columns, value_name = 'time').drop('variable', axis=1).dropna().reset_index(drop=True)

        df[creatinine] = np.clip(df[baseline_creat] + np.random.normal(loc = 0, scale = 0.25, size = df.shape[0]), a_min = 0.1, a_max = None).astype('float')
        df[time] = df[time] + df[admission]
        df[inpatient] = df[time] > df[admission]
        
        df[patient_id] = df[patient_id].astype('int')
        df[encounter_id] = df[encounter_id].astype('int')
        
        df = df[~df.time.duplicated()]    
        df = df.groupby(patient_id, sort=False, as_index=False).apply(lambda d: d.sort_values(time))
        df = df.reset_index(drop=True)

        
        if include_demographic_info:
            df = df.loc[:,[patient_id, encounter_id, age, black, female, inpatient, admission, time, creatinine]]
            print('Successfully generated toy data!\n')
            return df
        
        df = df.loc[:,[patient_id, encounter_id, inpatient, admission, time, creatinine]]
        print('Successfully generated toy data!\n')
        return df