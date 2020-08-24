import pandas as pd
import numpy as np
import datetime, random

class AKIFlagger:
    def __init__(self, patient_id = 'mrn', creatinine='creatinine', time = 'time', inpatient = 'inpatient', 
                 aki_calc_type=None, keep_extra_cols = False, eGFR_impute = False, add_stages = False,
                 cond1time = '48hours', cond2time = '168hours', pad1time = '0hours', pad2time = '0hours', 
                 rolling_window = False, back_calculate = False,
                 admission = 'admission', age = 'age', sex = 'sex', race = 'race', encounter_id = 'enc',
                 baseline_creat = 'baseline_creat', sort_values = True, remove_bc_na = True, add_baseline_creat = False):
        
        self.aki_calc_type = aki_calc_type
        self.patient_id = patient_id
        self.creatinine = creatinine
        self.time = time
        self.inpatient = inpatient
        
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
        self.cond1time = pd.Timedelta(cond1time) + pd.Timedelta(pad1time)
        self.cond2time = pd.Timedelta(cond2time) + pd.Timedelta(pad2time)
        
        #Back-calculate variables
        self.baseline_creat = baseline_creat
        
        #Extra options to specify what is included in the output
        self.eGFR_impute = eGFR_impute
        self.add_stages = add_stages
        self.keep_extra_cols = keep_extra_cols
        self.remove_bc_na = remove_bc_na
        self.add_baseline_creat = add_baseline_creat
        
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
        
        ## Step 1: Set the index to encounter & time variables
        
        #First, check if enc in cols or indx
        if self.encounter_id not in dataframe.columns and self.encounter_id not in dataframe.index.names:
            #If no, check if admission in cols or indx
            if self.admission not in dataframe.columns and self.admission not in dataframe.index.names:
                df = self.addAdmissionColumn(dataframe, add_encounter_col = True)
                
            #Otherwise, add encounters based on the unique admissions
            elif self.admission in dataframe.index.names and self.admission in dataframe.columns:
                df = dataframe.copy()
                
                mask = df.groupby(self.admission).head(1).index
                df.loc[mask, self.encounter_id] = np.arange(df[self.admission].unique().shape[0])
                df[self.encounter_id] = df[self.encounter_id].ffill()
        
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
            return pd.concat([df, rw, bc], axis=1).reset_index()
        elif self.rolling_window:
            return pd.concat([df, rw], axis=1).reset_index()
        elif self.back_calculate:
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
        
        #Set the index to just time 
        tmp = df[self.creatinine].reset_index(self.encounter_id) 
        #Groupby on encounter then apply conditions for rolling-window AKI
        gb = tmp.groupby(self.encounter_id, as_index = True, sort = False)
        gb_indx = gb[self.creatinine].rolling(self.cond1time).min().index
        c1 = tmp.set_index([self.encounter_id, tmp.index.get_level_values(level=self.time)]).loc[gb_indx][self.creatinine] >= 0.3 + gb[self.creatinine].rolling(self.cond1time).min()
        c2 = tmp.set_index([self.encounter_id, tmp.index.get_level_values(level=self.time)]).loc[gb_indx][self.creatinine] >= 1.5*gb[self.creatinine].rolling(self.cond2time).min()
        
        stage1 = np.logical_or(c1, c2)
        stage2 = tmp.set_index([self.encounter_id, tmp.index.get_level_values(level=self.time)]).loc[gb_indx][self.creatinine].values >= 2*gb[self.creatinine].rolling(self.cond2time).min()
        stage3 = tmp.set_index([self.encounter_id, tmp.index.get_level_values(level=self.time)]).loc[gb_indx][self.creatinine].values >= 3*gb[self.creatinine].rolling(self.cond2time).min()
        
        if self.add_stages:
            assert (np.all(stage1.index == df.index))
            return pd.Series(stage3.add(stage2.add(stage1*1)), name = 'rw')
        
        #assert (np.all(stage1.index == df.index)), 'Index mismatch! Something went wrong...'
        rw = pd.Series(np.logical_or.reduce((stage1, stage2, stage3)), index = stage1.index,
                         name = 'rw')
        rw = rw.reindex(df.index)
        assert (np.all(rw.index == df.index)), 'Index mismatch! Something went wrong...'
        return rw
    
    def addBaselineCreat(self, df):
    
        #Baseline creatinine is defined as the MEDIAN of the OUTPATIENT values from 365 to 7 days prior to admission

        #First, subset on columns necessary for calculation: creatinine, admission & inpatient/outpatient
        tmp = df.loc[:,[self.creatinine, self.admission, self.inpatient]]

        #Next, create a T/F mask for the times between 365 & 7 days prior to admission AND outpatient vals 
        bc_tz = np.logical_and(tmp[self.admission] - pd.Timedelta(days=365) <= tmp.index.get_level_values(level=self.time),
                           tmp[self.admission] - pd.Timedelta(days=7) >= tmp.index.get_level_values(level=self.time))
        mask = np.logical_and(bc_tz, ~tmp[self.inpatient])
        
        #Finally, add the median creat values to the dataframe, forward-fill, and return
        tmp.loc[mask, self.baseline_creat] = tmp[mask].groupby(self.encounter_id, as_index=True).creat.transform('median')
        tmp[self.baseline_creat] = tmp.groupby(self.encounter_id)[self.baseline_creat].ffill()
        
        #Still need to figure out the eGFR_impute conditional ~ ~ ~ ~ ~ that will go here ~ ~ ~ ~ ~ ~ ~ ~
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~I was up at 2am when I did this~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
        return tmp.baseline_creat
    
    def addBackCalcAKI(self, df, baseline_creat=None):
        
        #Subset on necessary cols: creat + admn
        tmp = df.loc[:, [self.creatinine, self.admission]]
        
        #Look back 6 hours prior to admission until cond2time from admission
        mask = np.logical_and(tmp[self.admission] - pd.Timedelta(hours=6) <= tmp.index.get_level_values(level = self.time),
                              tmp[self.admission] + self.cond2time >= tmp.index.get_level_values(level = self.time))
        
        #Apply aki definition & return the resulting series (the reason we add it to the data frame is so we can get
        # the NaNs in the right place without doing much work as a "freebie")
        tmp.loc[mask, 'bc'] = tmp[mask][self.creatinine] >= 1.5*baseline_creat[mask]
        
        #And by default, I'll replace the null values with False's 
        if self.remove_bc_na:
            tmp.loc[tmp.bc.isnull(), 'bc'] = False
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


        Returns:
            df (pd.DataFrame): dataframe with toy numbers to work with.

        '''
        np.random.seed(0) #seed for reproducibility

        #To explicitly demonstrate that race and sex variables only care about black/female distinction
        race = 'black'
        sex = 'female'
        age = 'age'
        
        #pick admission dates from Jan 1, 2020 to July 1, 2020 (6 month period) and generate time deltas from +- 5 days
        if date_range is None:
            date_range = (pd.to_datetime('2020-01-01').value // 10**9, pd.to_datetime('2020-07-01').value // 10**9) 
        if time_delta_range is None:
            time_delta_range = pd.timedelta_range(start='-5 days', end='5 days', freq='6H')

        #Generate random MRN #s, admission dates, and encounters
        #Generate between 3 and 10 encounters for each patient
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
            d1.columns = [patient_id, admission, baseline_creat, age, 'black', 'female']

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
            df = df.loc[:,[patient_id, encounter_id, age, race, sex, inpatient, admission, time, creatinine]]
            print('Successfully generated toy data!')
            return df
        
        df = df.loc[:,[patient_id, encounter_id, inpatient, admission, time, creatinine]]
        print('Successfully generated toy data!')
        return df