import unittest
from akiFlagger import AKIFlagger, generate_toy_data

import pandas as pd
import numpy as np

import akiFlagger

toy = generate_toy_data(num_patients=10)
class TestFlagger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.toy = generate_toy_data()
    
    @classmethod
    def tearDownClass(cls):
        pass
        
    def test_toyInit(self):
        print('Testing toy initialization...')

        # Testing all the expected columns are in the generated data set
        self.assertTrue('mrn' in toy.columns)
        self.assertTrue('enc' in toy.columns)
        self.assertTrue('inpatient' in toy.columns)
        self.assertTrue('admission' in toy.columns)
        self.assertTrue('time' in toy.columns)
        self.assertTrue('creat' in toy.columns)
        print('Success!\n')
    
    def test_AssertionErrors(self):
        print('Testing Assertion Error checks...')

        #Set-up: dataframe + flagger
        cols= ['mrn', 'enc', 'inpatient', 'admission', 'time', 'creatinine']
        row = [1234, 12345, False, pd.Timestamp('20200227 12:00:01'), pd.Timestamp('20200227 12:00:02'), 1.3]
        df = pd.DataFrame([row], columns=cols)
        flagger = AKIFlagger()

        #Now drop the necessary columns and ensure it throws an error
        with self.assertRaises(AssertionError):
            flagger.returnAKIpatients(df.drop(['mrn', 'enc'], axis = 1))
        with self.assertRaises(AssertionError):
            flagger.returnAKIpatients(df.drop('inpatient', axis = 1))
        with self.assertRaises(AssertionError):
            flagger.returnAKIpatients(df.drop('time', axis = 1))
        with self.assertRaises(AssertionError):
            flagger.returnAKIpatients(df.drop('creatinine', axis = 1))
        print('Success!\n')

    def test_RollingWindow_main(self):
        print('Testing rolling-window calculations...')

        #Set-up
        cols = ['mrn', 'enc', 'inpatient', 'admission', 'time', 'creatinine']
        row1 = [1234, 12345, False, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-26 12:00:02'), 1.2]
        row2 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-28 12:00:01'), 1.5]
        row3 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-29 12:00:01'), 1.6]
        row4 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-03-01 12:00:01'), 1.8]
        row5 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-03-03 12:00:01'), 1.8]
        df = pd.DataFrame([row1, row2, row3, row4, row5], columns = cols)
        flagger = AKIFlagger(rolling_window = True)
        
        #Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.rw[0])
        self.assertTrue(out.rw[1])
        self.assertFalse(out.rw[2])
        self.assertTrue(out.rw[3])
        self.assertTrue(out.rw[4])
        print('Success!\n')

    def test_RollingWindow_edge(self):
        print('Testing rolling-window edge-cases...')

        #Set-up
        cols = ['mrn', 'enc', 'inpatient', 'admission', 'time', 'creatinine']
        row1 = [1234, 12345, False, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-26 12:00:02'), 1.3]
        row2 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-28 12:00:02'), 1.5999]
        row3 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-03-02 12:00:02'), 3.0]
        row4 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-03-10 12:00:02'), 400]
        df = pd.DataFrame([row1, row2, row3, row4], columns = cols)
        flagger = AKIFlagger(rolling_window = True)

        #Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.rw[0])
        self.assertFalse(out.rw[1])
        self.assertTrue(out.rw[2])
        self.assertFalse(out.rw[3])
        print('Success!\n')

    def test_BackCalculate_main(self):
        print('Testing back-calculate calculations...')

        #Set-up
        cols = ['mrn', 'enc', 'inpatient', 'admission', 'time', 'creatinine']
        row1 = [1234, 12345, False, pd.Timestamp('2020-02-24 14:37:34'), pd.Timestamp('2019-05-21 12:00:02'), 1.3]
        row2 = [1234, 12345, False, pd.Timestamp('2020-02-24 14:37:34'), pd.Timestamp('2020-01-01 12:00:02'), 1.5]
        row3 = [1234, 12345, True, pd.Timestamp('2020-02-24 14:37:34'), pd.Timestamp('2020-02-29 12:00:02'), 2.1]
        df = pd.DataFrame([row1, row2, row3], columns = cols)
        flagger = AKIFlagger(back_calculate=True)
        
        #Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.bc[0])
        self.assertFalse(out.bc[1])
        self.assertTrue(out.bc[2])
        print('Success!\n')
        
    def test_differentNames(self):
        print('Testing different names for identifiers...')

        #Set-up
        cols = ['fish', 'dog', 'rabbit', 'snail', 'james', 'buffboys']
        row1 = [1234, 12345, False, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-26 12:00:02'), 1.2]
        row2 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-28 12:00:01'), 1.5]
        row3 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-02-29 12:00:01'), 1.6]
        row4 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-03-01 12:00:01'), 1.8]
        row5 = [1234, 12345, True, pd.Timestamp('2020-02-27 12:00:01'), pd.Timestamp('2020-03-03 12:00:01'), 1.8]
        df = pd.DataFrame([row1, row2, row3, row4, row5], columns = cols)
        flagger = AKIFlagger(rolling_window = True, back_calculate = True,
                            patient_id = 'fish', encounter_id = 'dog',
                            inpatient = 'rabbit', admission = 'snail',
                            time = 'james', creatinine = 'buffboys')
        
        #Ensure proper output
        out = flagger.returnAKIpatients(df)
        self.assertFalse(out.rw[0])
        self.assertTrue(out.rw[1])
        self.assertFalse(out.rw[2])
        self.assertTrue(out.rw[3])
        self.assertTrue(out.rw[4])
        print('Success!\n')

    def test_eGFRimpute(self):
        print('Testing eGFR-based imputation...')
        
if __name__ == '__main__':
    unittest.main()


