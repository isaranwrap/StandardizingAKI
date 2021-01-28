import pandas as pd
import numpy as np
import datetime, random

__version__ = '0.3.2' # master file

class AKIFlagger:
    ''' Main flagger to detect patients with acute kidney injury (AKI).
    This flagger returns patients with AKI according to the `KDIGO guidelines <https://kdigo.org/guidelines/>`_ on changes in creatinine\*. The KDIGO guidelines are as follows:

        * *Stage 1:* 0.3 mg/dL increase in serum creatinine in < 48 hours OR 50% increase in serum creatinine in < 7 days (168 hours)
        * *Stage 2:* 100% increase in (or doubling of) serum creatinine in < 7 days (168 hours)
        * *Stage 3:* 200% increase in (our tripling of) serum creatinine in < 7 days (168 hours)

        \*Except for the stage 3 condition of a creatinine value larger than 4.0 mg/dL. This `paper <http://www.european-renal-best-practice.org/sites/default/files/u33/ndt.gfs375.full_.pdf>`_ has the full specifications including
        inclusion criterion based on urinary output and renal replacement therapy.

        More information can be found in the documentation at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.
        
    Attributes:
        patient_id (string): **default 'mrn'.** Name of the column used to identify patients; e.g. 'PAT_MRN_ID'
        encounter_id (string): **default 'enc'.** Name of the column used to identify encounters; e.g. 'PAT_ENC_CSN_ID'
        
        time (string): **default 'time'.** Name of the column containing time stamps; e.g. 'time'
        inpatient (string): **default 'inpatient'.** Name of the column containing inpatient/outpatient identifier; e.g. 'inpatient'
        admission (string): **default 'admission'.** Name of the column containing the admission dates; e.g. 'admission'
        creatinine (string): **default 'creatinine'.** Name of the column containing creatinine values; e.g. 'creatinine'
        
        age (string): **default 'age'.** Name of the column containing the age values; e.g. 'age'
        sex (string): **default 'sex'.** Name of the column containing the sex values; e.g. 'female'
        race (string): **default 'race'.** Name of the column containing the race values; e.g. 'black'
        
        HB_trumping (boolean): **default False.** Whether or not to have the historical baseline value trump the rolling 
            minimum value around admission time. 
        eGFR_impute (boolean): **default False.** Whether or not to impute the missing baseline creatinine values with the
            eGFR-imputation method; i.e. assuming an eGFR of 75 estimate baseline creatinine based on age, sex, and race.
        
        cond1time (string): **default '48hours'.** The rolling-window time of the first KDIGO criterion condition.
            This string gets passed to pd.Timedelta(cond1time), so any acceptable time format for that function will work.
        cond2time (string): **default '168hours'.** The rolling-window time of the second KDIGO criterion condition.
            This string gets passed to pd.Timedelta(cond2time), so any acceptable time format for that function will work.
        pad1time (string): **default '0hours'.** Padding to add to the first KDIGO criterion condition.
            This string gets passed to pd.Timedelta(pad1time), so any acceptable time format for that function will work.
        pad2time (string): **default '0hours'.** Padding to add to the second KDIGO criterion condition.
            This string gets passed to pd.Timedelta(pad2time), so any acceptable time format for that function will work.
        
        sort_values (boolean): **default True.** Whether or not to sort the values within each encounter based on `time`.
        add_baseline_creat (boolean): **default False.** Whether or not to add the baseline creatinine column from back-calculate method.
        add_min_creat (boolean): **default False.** Whether or not to add the minimum creatinine column from rolling-window method.
        
    '''
    def __init__(self, patient_id = 'mrn', creatinine = 'creatinine', time = 'time', inpatient = 'inpatient', # Required columns
                 encounter_id = 'enc', admission = 'admission', baseline_creat = 'baseline_creat', # Helpful columns, imputed otherwise
                 age = 'age', sex = 'sex', race = 'race',  # Required if CKD-EPI imputation is wanted
                 padding = None, HB_trumping = False, eGFR_impute = False, # Main parameters
                 cond1time = '48hours', cond2time = '168hours', pad1time = '0hours', pad2time = '0hours', # Rolling window sizes
                sort_values = True, add_baseline_creat = False, add_min_creat = False): # Ancillary optional parameters (include output for intermediate calculations)
        
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
        self.pad1time = pad1time
        self.pad2time = pad2time
        if padding is not None:
            self.pad1time = padding
            self.pad2time = padding

        self.cond1time = pd.Timedelta(cond1time) + pd.Timedelta(self.pad1time) + pd.Timedelta('1second') # Add one second to handle edge-cases (ex. exactly 48 hours)
        self.cond2time = pd.Timedelta(cond2time) + pd.Timedelta(self.pad2time) + pd.Timedelta('1second')
        
        # Historical baseline variables
        self.HB_trumping = HB_trumping
        self.baseline_creat = baseline_creat
        self.eGFR_impute = eGFR_impute
        
        # Extra options to specify what is included in the output
        self.add_baseline_creat = add_baseline_creat
        self.add_min_creat = add_min_creat

        # Sort values - if the dataframe is already pre-sorted, save time by setting sort_values to False
        self.sort_values = sort_values
        
        
    def returnAKIpatients(self, dataframe, cond1time = None, cond2time = None, pad1time = None, pad2time = None):
        '''
        Returns patients with AKI according to the `KDIGO guidelines <https://kdigo.org/guidelines/>`_ on changes in creatinine\*. The KDIGO guidelines are as follows:

        * *Stage 1:* 0.3 increase in serum creatinine in < 48 hours OR 50% increase in serum creatinine in < 7 days (168 hours)
        * *Stage 2:* 100% increase in (or doubling of) serum creatinine in < 7 days (168 hours)
        * *Stage 3:* 200% increase in (our tripling of) serum creatinine in < 7 days (168 hours)

        More information can be found in the documentation at `akiflagger.readthedocs.io <https://akiflagger.readthedocs.io/en/latest/>`_.
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
        
        assert not np.any(dataframe[self.creatinine].isnull()), "Get rid of any null creatinine values before running the flagger!"
        
        # Additional checks if we want to impute with eGFR ~ 75 method
        if self.eGFR_impute:
            assert (self.age in dataframe.columns), "If you are using the eGFR-based imputation method, you need to have an age, sex, and race column!"
            assert (self.sex in dataframe.columns), "If you are using the eGFR-based imputation method, you need to have an age, sex, and race column!"
            assert (self.race in dataframe.columns), "If you are using the eGFR-based imputation method, you need to have an age, sex, and race column!"

        # At this point, just want to make sure that the sex column is female. If sex is specified to be male, then change it 
        if self.sex == 'male' or self.sex == 'MALE': 
            df[self.sex] = ~df[self.sex].astype('bool')

        ## Step 1: Set the index to patient id & time variables
        df = dataframe.set_index([self.patient_id, self.time])

        ## Step 2: Sort based on time and drop any duplicates
        if self.sort_values:
            df = df.groupby(self.patient_id, sort=False, as_index = False).apply(lambda d: d.sort_index(level=self.time))
            if df.index.names != [self.patient_id, self.time]: # Occassionally, the index is kept s.t. the index is [None, patient_id, time]
                df = df.reset_index(level=0, drop=True) # This gets rid of the None index
            df = df[~df.index.duplicated()] # Drop any duplicates

        ## Step 3: Adding in AKI
        
        # Rolling minimum, first: 
        gb = df.loc[:, [self.creatinine]].reset_index(self.patient_id).groupby(self.patient_id, sort=False) # Groupby on patients
        min_creat48 = gb.rolling(self.cond1time).min().reindex(df.index)[self.creatinine] # Rolling 48hr minimum creatinine time series 
        min_creat7d = gb.rolling(self.cond2time).min().reindex(df.index)[self.creatinine] # Rolling 7day minimum creatinine time series

        if self.add_min_creat: # Add in min creat time series to the dataframe
            df['min_creat{}'.format(self.cond1time.days*24 + self.cond1time.seconds // 3600)] = min_creat48
            df['min_creat{}'.format(self.cond2time.days*24 + self.cond2time.seconds // 3600)] = min_creat7d
        
        if self.add_baseline_creat: # Add in baseline creatinine time series to the dataframe
            df[self.baseline_creat] = self.addBaselineCreat(df)

        if self.HB_trumping: # Historical baseline "trumping" local minimum values
            if self.baseline_creat not in df.columns:
                baseline_creat = self.addBaselineCreat(df)
            else:
                baseline_creat = df[self.baseline_creat]
                assert np.all(baseline_creat.index == min_creat48.index)
            
            # Create masks for selecting admission to +2 days and +7 days in advance, respectively
            mask2d = np.logical_and(df.index.get_level_values(level=self.time) >= df[self.admission], df.index.get_level_values(level=self.time) <= df[self.admission] + self.cond1time)
            mask7d = np.logical_and(df.index.get_level_values(level=self.time) >= df[self.admission], df.index.get_level_values(level=self.time) <= df[self.admission] + self.cond2time)
            mask_bc = ~baseline_creat.isnull() # Only have baseline TRUMP rolling minimum if it exists
            mask = np.logical_and(mask7d, mask_bc)

            # Calculate rolling minimum conditions 
            c1 = np.round(df[self.creatinine], decimals=4) >= np.round(0.3 + min_creat48, decimals=4) 
            c2 = np.round(df[self.creatinine], decimals=4) >= np.round(1.5*min_creat7d, decimals=4)
            
            stage1 = c2 # Notice now, stage1 is just condition2 ... we will add in condition 1 later so as not to have the HB double-trump
            stage2 = np.round(df[self.creatinine], decimals=4) >= np.round(2*min_creat7d, decimals=4)
            stage3 = np.round(df[self.creatinine], decimals=4) >= np.round(3*min_creat7d, decimals=4)
            aki = pd.Series(stage3.add(stage2.add(stage1*1)), name = 'aki')
            
            # Calculate historical baseline conditions
            stage1hb = np.round(df[mask][self.creatinine], decimals=4) >= np.round(1.5*baseline_creat[mask], decimals=4)
            stage2hb = np.round(df[mask][self.creatinine], decimals=4) >= np.round(2*baseline_creat[mask], decimals=4)
            stage3hb = np.round(df[mask][self.creatinine], decimals=4) >= np.round(3*baseline_creat[mask], decimals=4)
            aki[mask]= pd.Series(stage3hb.add(stage2hb.add(stage1hb*1)), name = 'aki')

            # Add back in the 0.3 bump criterion (separately since the rolling window is of a different size than the other checks)
            mask2d = np.logical_and(df.index.get_level_values(level=self.time) >= df[self.admission], df.index.get_level_values(level=self.time) <= df[self.admission] + self.cond1time)
            mask_empty = aki == 0 # Replace the current value only if the flagger didn't flag as baseline. If it was 1, same result. If it was 2 or 3, we would prioritize those over the 0.3 bump
            mask_rw = np.logical_or(np.logical_and(~mask2d, mask_empty), ~mask_bc) # The full mask is of all these conditions: admit to +2d, missed flagger, and non-null baseline creatinine values
            aki[mask_rw] = c1*1

        else: # Vanilla rolling minimum if no HB trumping

            # Calculate rolling minimum conditions 
            c1 = np.round(df[self.creatinine], decimals=4) >= np.round(0.3 + min_creat48, decimals=4)
            c2 = np.round(df[self.creatinine], decimals=4) >= np.round(1.5*min_creat7d, decimals=4)
            
            stage1 = np.logical_or(c1, c2)
            stage2 = np.round(df[self.creatinine], decimals=4) >= np.round(2*min_creat7d, decimals=4)
            stage3 = np.round(df[self.creatinine], decimals=4) >= np.round(3*min_creat7d, decimals=4)

            aki = pd.Series(stage3.add(stage2.add(stage1*1)), name = 'aki')
        
        # Concatenate and return output
        return pd.concat([df, aki], axis=1)
    
    def addAdmissionColumn(self, df, add_encounter_col = None):
        '''
        Returns the admission (and possible encounter) column(s) in case the patient data frame is missing the admission/enc column.
        '''
        pat_gb = df.groupby(self.patient_id, sort = False)

        #Check for those rows which are all inpatient; e.g. a hospital visit
        df.loc[:, 'all_inp'] = pat_gb[self.inpatient].transform(lambda d: np.all(d))
        df.loc[:, 'all_inp'] = df.all_inp & ~pat_gb.all_inp.shift(1, fill_value=False)

        df.loc[:, self.admission] = df.inpatient & ~pat_gb.inpatient.shift(1, fill_value=False)
        df.loc[np.logical_or(df[self.admission], df.all_inp), self.admission] = df[np.logical_or(df[self.admission], df.all_inp)].index.get_level_values(level=self.time)
        df.loc[:, self.admission] = pat_gb[self.admission].apply(lambda s: s.bfill().ffill())

        if add_encounter_col:
            df.loc[:, self.encounter_id] = df.inpatient & ~pat_gb.inpatient.shift(1, fill_value=False)
            df.loc[df[self.encounter_id], self.encounter_id] = np.arange(1, df.enc.sum()+1)
            df.loc[df[self.encounter_id] == False, self.encounter_id] = np.nan
            df.loc[:,self.encounter_id] = pat_gb[self.encounter_id].apply(lambda s: s.bfill().ffill())
        df = df.drop(['all_inp'], axis=1)
        
        return df   
    
    def eGFRbasedCreatImputation(self, age, female, black):
        '''Imputes the baseline creatinine values for those patients missing outpatient creatinine measurements from 365 to 7 days prior to admission.
        The imputation is based on the `CKD-EPI equation <https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/kidney-disease/laboratory-evaluation/glomerular-filtration-rate/estimating>`_ from the paper
        *A New Equation to Estimate Glomerular Filtration Rate (Levey et. Al, 2009)*.
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
        '''
        Returns baseline creatinine used in intermediate calculation for back-calculating AKI. Baseline creatinine is defined as the MEDIAN of OUTPATIENT creatinine values from 365 to 7 days prior to admission.
        '''
        # Baseline creatinine is defined as the MEDIAN of the OUTPATIENT creatinine values from 365 to 7 days prior to admission

        # If the admission column isn't present, impute it here
        if self.encounter_id not in df.columns or self.admission not in df.columns:
            df = self.addAdmissionColumn(df, add_encounter_col=True)

        # First, subset on columns necessary for calculation: creatinine, admission & inpatient/outpatient
        tmp = df.loc[:,[self.creatinine, self.admission, self.inpatient, self.encounter_id]]
        if self.eGFR_impute:
            tmp = df.loc[:, [self.creatinine, self.admission, self.inpatient, self.encounter_id, self.age, self.race, self.sex]]
        

        # Next, create a T/F mask for the times between 365 & 7 days prior to admission AND outpatient vals 
        bc_tz = np.logical_and(tmp[self.admission] - pd.Timedelta(days=365) <= tmp.index.get_level_values(level=self.time),
                           tmp[self.admission] - pd.Timedelta(days=7) >= tmp.index.get_level_values(level=self.time))
        mask = np.logical_and(bc_tz, ~tmp[self.inpatient])
        
        # Finally, add the median creat values to the dataframe, forward-fill, and return
        tmp.loc[mask, self.baseline_creat] = tmp[mask].groupby(self.encounter_id, as_index=True)[self.creatinine].transform('median')
        tmp[self.baseline_creat] = tmp.groupby(self.encounter_id)[self.baseline_creat].ffill().bfill()
        
        # If we'd like to perform the imputation based on the eGFR of 75
        if self.eGFR_impute:
            imp = df.loc[tmp[self.baseline_creat].isnull()]
            if self.sex == 'male':
                tmp.loc[tmp[self.baseline_creat].isnull(), self.baseline_creat] = self.eGFRbasedCreatImputation(imp[self.age], ~imp[self.sex], imp[self.race])
            elif self.sex == 'female':
                tmp.loc[tmp[self.baseline_creat].isnull(), self.baseline_creat] = self.eGFRbasedCreatImputation(imp[self.age], imp[self.sex], imp[self.race])
            else:
                tmp.loc[tmp[self.baseline_creat].isnull(), self.baseline_creat] = self.eGFRbasedCreatImputation(imp[self.age], imp[self.sex], imp[self.race])
        
        if self.add_baseline_creat:
            df[self.baseline_creat] = tmp.baseline_creat

        assert np.all(df.index == tmp.index)
        return tmp.baseline_creat
    
def generate_toy_data(num_patients = 100, num_encounters_range = (1, 3), num_time_range = (5,10), creat_scale = 0.3,
                      include_demographic_info = False, date_range = None, time_delta_range = None, set_index = False, printMsg=True):
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

        df[creatinine] = np.clip(df[baseline_creat] + np.random.normal(loc = 0, scale = 0.25, size = df.shape[0]), a_min = 0.1, a_max = None).astype('float').round(decimals=2)
        df[time] = df[time] + df[admission]
        df[inpatient] = df[time] >= df[admission]
        
        df[patient_id] = df[patient_id].astype('int')
        df[encounter_id] = df[encounter_id].astype('int')
        
        df = df[~df.time.duplicated()]    
        df = df.groupby(patient_id, sort=False, as_index=False).apply(lambda d: d.sort_values(time))
        df = df.reset_index(drop=True)

        if set_index:
            df = df.set_index([patient_id, time], drop=False)
            
        if include_demographic_info:
            df = df.loc[:,[patient_id, encounter_id, age, female, black, inpatient, admission, time, creatinine]]
            if printMsg:
                print('Successfully generated toy data!\n')
            return df
        
        df = df.loc[:,[patient_id, encounter_id, inpatient, admission, time, creatinine]]
        if printMsg:
            print('Successfully generated toy data!\n')
        return df
