import unittest
from akiFlagger import AKIFlagger, generate_toy_data

import pandas as pd
import numpy as np

import akiFlagger
print(akiFlagger.__version__)

toy = generate_toy_data(num_patients=10, printMsg=False)
class TestFlagger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.toy = generate_toy_data(printMsg=False)
    
    @classmethod
    def tearDownClass(cls):
        pass
        
    def test_toyInit(self):
        print('Testing toy initialization...')

        # Testing all the expected columns are in the generated data set
        self.assertTrue('patient_id' in toy.columns)
        self.assertTrue('encounter_id' in toy.columns)
        self.assertTrue('inpatient' in toy.columns)
        self.assertTrue('admission' in toy.columns)
        self.assertTrue('time' in toy.columns)
        self.assertTrue('creat' in toy.columns)
        print('Success!\n')
    
    def test_AssertionErrors(self):
        print('Testing Assertion Error checks...')

        # Set-up: dataframe + flagger
        cols= ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row = [1234, 12345, False, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-27 12:00:02'), 1.3]
        df = pd.DataFrame([row], columns=cols)
        flagger = AKIFlagger()

        # Now drop the necessary columns and ensure it throws an error
        with self.assertRaises(AssertionError):
            flagger.returnAKIpatients(df.drop(['patient_id', 'encounter_id'], axis = 1))
        with self.assertRaises(AssertionError):
            flagger.returnAKIpatients(df.drop('inpatient', axis = 1))
        with self.assertRaises(AssertionError):
            flagger.returnAKIpatients(df.drop('time', axis = 1))
        with self.assertRaises(AssertionError):
            flagger.returnAKIpatients(df.drop('creatinine', axis = 1))
        print('Success!\n')

    def test_differentNames(self):
        print('Testing different names for identifiers...')

        # Set-up
        cols = ['fish', 'dog', 'rabbit', 'snail', 'james', 'buffboys']
        row0 = [1234, 12345, False, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-26 12:00:02'), 1.2]
        row1 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-28 12:00:01'), 1.5]
        row2 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-29 12:00:01'), 1.6]
        row3 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-03-01 12:00:01'), 1.8]
        row4 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-03-03 12:00:01'), 1.8]
        df = pd.DataFrame([row0, row1, row2, row3, row4], columns = cols)
        flagger = AKIFlagger(patient_id = 'fish', encounter_id = 'dog',
                            inpatient = 'rabbit', admission = 'snail',
                            time = 'james', creatinine = 'buffboys')
        
        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])
        self.assertTrue(out.aki.iloc[1])
        self.assertFalse(out.aki.iloc[2])
        self.assertTrue(out.aki.iloc[3])
        self.assertTrue(out.aki.iloc[4])
        print('Success!\n')

    def test_eGFRimpute(self):
        print('Testing eGFR-based imputation...')
        
    def test_patientA_RM(self): # Simplest case - both 
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-01-01 12:00:01'), 1.0] # Baseline creatinine
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1.0] # Admission creatinine
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:01'), 1.29]
        row3 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:02'), 1.3]
        row4 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-28 12:00:02'), 2]
        row5 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-30 12:00:02'), 3]

        df = pd.DataFrame([row0, row1, row2, row3, row4, row5], columns = cols)
        flagger = AKIFlagger()
        
        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])    # 1.0
        self.assertFalse(out.aki.iloc[1])    # 1.0
        self.assertFalse(out.aki.iloc[2])    # 1.29
        self.assertTrue(out.aki.iloc[3])     # 1.3
        self.assertEqual(out.aki.iloc[4], 2) # 2
        self.assertEqual(out.aki.iloc[5], 3) # 3

        print('Sucess!\n')
    
    def test_patientA_HB(self):
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-01-01 12:00:01'), 1.0] # Baseline creatinine
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1.0] # Admission creatinine
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:01'), 1.29]
        row3 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:02'), 1.3]
        row4 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-28 12:00:02'), 2]
        row5 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-30 12:00:02'), 3]

        df = pd.DataFrame([row0, row1, row2, row3, row4, row5], columns = cols)
        flagger = AKIFlagger(HB_trumping = True)

        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])    # 1.0
        self.assertFalse(out.aki.iloc[1])    # 1.0
        self.assertFalse(out.aki.iloc[2])    # 1.29
        self.assertTrue(out.aki.iloc[3])     # 1.3 --> UPDATED Version 0.3.5+: 0.3 condition is counted in HB_trumping now. 
        self.assertEqual(out.aki.iloc[4], 2) # 2
        self.assertEqual(out.aki.iloc[5], 3) # 3

        print('Sucess!\n')
    
    
    def test_patientB_HB(self): # Patient B: 
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-01-01 12:00:01'), 1.1] # Baseline creatinine
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1.0] # Admission creatinine
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:01'), 1.29]
        row3 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:02'), 1.3]
        row4 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-28 12:00:02'), 2]
        row5 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-29 12:00:02'), 2.2]
        row6 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-30 12:00:02'), 3]
        row7 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-30 12:00:03'), 3.3]

        df = pd.DataFrame([row0, row1, row2, row3, row4, row5, row6, row7], columns = cols)
        flagger = AKIFlagger(HB_trumping=True, add_baseline_creat=True)

        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])    # 1.1
        self.assertFalse(out.aki.iloc[1])    # 1.0
        self.assertFalse(out.aki.iloc[2])    # 1.29
        self.assertFalse(out.aki.iloc[3])    # 1.3  ---> This is the criterion that meets RM but not HB 
        self.assertEqual(out.aki.iloc[4], 1) # 2 
        self.assertEqual(out.aki.iloc[5], 2) # 2.2
        self.assertEqual(out.aki.iloc[6], 2) # 3
        self.assertEqual(out.aki.iloc[7], 3) # 3.3 (and it's not until 3.3 that HB should trigger stage3)

    def test_patientB_RM(self): # Identical to patientA, except their baseline is now 1.1 instead of 1.0
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-01-01 12:00:01'), 1.1] # Baseline creatinine
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1.0] # Admission creatinine
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:01'), 1.29]
        row3 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:02'), 1.3]
        row4 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-28 12:00:02'), 2]
        row5 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-29 12:00:02'), 2.2]
        row6 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-30 12:00:02'), 3]
        row7 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-30 12:00:03'), 3.3]

        df = pd.DataFrame([row0, row1, row2, row3, row4, row5, row6, row7], columns = cols)
        flagger = AKIFlagger(HB_trumping=False)

        #Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])    # 1.1
        self.assertFalse(out.aki.iloc[1])    # 1.0
        self.assertFalse(out.aki.iloc[2])    # 1.29
        self.assertTrue(out.aki.iloc[3])     # 1.3  ---> This is the criterion that meets RM but not HB 
        self.assertEqual(out.aki.iloc[4], 2) # 2 
        self.assertEqual(out.aki.iloc[5], 2) # 2.2
        self.assertEqual(out.aki.iloc[6], 3) # 3
        self.assertEqual(out.aki.iloc[7], 3) # 3.3

    def test_patientC_RM(self): # Patient C doesn't meet the rolling minimum criterion
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-01-01 12:00:01'), 1.0] # Baseline creatinine
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1.1] # Admission creatinine
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:01'), 1.1]
        row3 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-26 12:00:02'), 1.3]
        row4 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-28 12:00:02'), 1.5]
        df = pd.DataFrame([row0, row1, row2, row3, row4], columns = cols)
        flagger = AKIFlagger()

        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])
        self.assertFalse(out.aki.iloc[1])
        self.assertFalse(out.aki.iloc[2])
        self.assertFalse(out.aki.iloc[3])
        self.assertFalse(out.aki.iloc[4])

    def test_patientC_HB(self): # Patient C doesn't meet the rolling minimum criterion
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-01-01 12:00:01'), 1.0] # Baseline creatinine
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1.1] # Admission creatinine
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-25 12:00:01'), 1.1]
        row3 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-26 12:00:04'), 1.3]
        row4 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-28 12:00:02'), 1.5]
        df = pd.DataFrame([row0, row1, row2, row3, row4], columns = cols)
        flagger = AKIFlagger(HB_trumping=True)

        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])
        self.assertFalse(out.aki.iloc[1])
        self.assertFalse(out.aki.iloc[2])
        self.assertTrue(out.aki.iloc[3])
        self.assertTrue(out.aki.iloc[4]) # But on the last one, RM should trigger

    def test_PatientX_RM(self):
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-01-01 12:00:01'), 2.0] # Patient X has a baseline creatinine of 2 
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1] # Admission creatinine
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-26 12:00:02'), 1.3]
        row3 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-28 12:00:02'), 1.6]
        df = pd.DataFrame([row0, row1, row2, row3], columns = cols)
        flagger = AKIFlagger(HB_trumping=False)

        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])
        self.assertFalse(out.aki.iloc[1])
        self.assertTrue(out.aki.iloc[2])
        self.assertTrue(out.aki.iloc[3])

    def test_PatientX_HB(self):
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-01-01 12:00:01'), 2.0] # Patient X has a baseline creatinine of 2 
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1] # Admission creatinine
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-26 12:00:02'), 1.3]
        row3 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-28 12:00:02'), 1.6]
        df = pd.DataFrame([row0, row1, row2, row3], columns = cols)
        flagger = AKIFlagger(HB_trumping=True)

        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.aki.iloc[0])
        self.assertFalse(out.aki.iloc[1])
        self.assertFalse(out.aki.iloc[2])
        self.assertTrue(out.aki.iloc[3])

    def test_HB_notrump(self):
        cols = ['patient_id', 'encounter_id', 'inpatient', 'admission', 'time', 'creatinine']
        row0 = [1234, 12345, False, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-22 12:00:01'), 2.0]
        row1 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:02'), 1.0]
        row2 = [1234, 12345, True, pd.Timestamp('2020-05-24 12:00:02'), pd.Timestamp('2020-05-24 12:00:03'), 1.3]
        df = pd.DataFrame([row0, row1, row2], columns = cols)
        flagger = AKIFlagger(HB_trumping=True, add_baseline_creat = True) #HB_trumping is set to True but there is no baseline value... so it should switch to RM then
        
        # Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertTrue(np.all(out.baseline_creat.isnull()))
        self.assertEqual(out.aki.iloc[0], 0)
        self.assertEqual(out.aki.iloc[1], 0)
        self.assertEqual(out.aki.iloc[2], 1)

    def test_imputeAdmissionandEncounter(self):
        cols = ['patient_id', 'inpatient', 'time', 'creatinine']
        row0 = [1234, False, pd.Timestamp('2020-01-24 12:00:02'), 1.0]
        row1 = [1234, False, pd.Timestamp('2020-02-24 12:00:02'), 1.0]
        row2 = [1234, False, pd.Timestamp('2020-03-24 12:00:02'), 1.0]
        row3 = [1234, True, pd.Timestamp('2020-05-24 12:00:02'), 1.5]
        df = pd.DataFrame([row0, row1, row2, row3], columns = cols)
        flagger = AKIFlagger(HB_trumping=True)
        out = flagger.returnAKIpatients(df)
        self.assertTrue('imputed_admission' in out.columns.values)
        self.assertTrue('imputed_encounter_id' in out.columns.values)


        
if __name__ == '__main__':
    unittest.main()


