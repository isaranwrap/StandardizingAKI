#!/usr/bin/env python
# coding: utf-8

# ## Imports

# In[1]:


import pandas as pd
import numpy as np
import datetime, random

from multiprocessing import Pool
import time
import os


# ## Reading in both dataframes; modifying Yu's dataframe to match mine and subsetting my dataframe on Yu's mrn/enc/time patients

# In[2]:


yu = pd.read_csv(r'H:\Data\Standardized AKI definition\dataset\new aki flagger 1.csv')


# In[3]:


get_ipython().run_cell_magic('time', '', "df = pd.read_csv(r'H:\\Data\\Standardized AKI definition\\dataset\\output2.csv')\ndf['time'] = pd.to_datetime(df.time)\ndf = df.drop(['Unnamed: 0'], axis=1)\n\nyu = pd.read_csv(r'H:\\Data\\Standardized AKI definition\\dataset\\new aki flagger 1.csv')\nyu['mrn'] = yu.pat_mrn_id.str.strip('MR').astype('int') #indexing with integers is quicker\nyu['enc'] = yu.enc_id\nyu['time'] = pd.to_datetime(yu.time)\n\n# yu.columns = ['mrn', #Renaming columns for ease\n#              'pat_enc_id',\n#              'time',\n#              'creat',\n#              'enc',\n#              'running_aki_stage',\n#              'historical_aki_stage',\n#              'covid'] \n\nyu['running_aki'] = yu.running_aki_stage > 0 \nyu['historical_aki'] = yu.historical_aki_stage > 0\n\nyu = yu.groupby('enc').apply(lambda d: d[~d.time.duplicated()])\nyu = yu.reset_index(drop=True)\n\nprint(yu.shape)")


# In[4]:


get_ipython().run_cell_magic('time', '', "df_subset = df.set_index(['mrn', 'enc', 'time']).loc[yu.set_index(['mrn','enc','time']).index]\ndf_subset = df_subset.reset_index().groupby('enc').apply(lambda d: d[~d.time.duplicated()])\ndf_subset = df_subset.reset_index(drop=True)\nprint(np.all(df_subset.time == yu.time))\nprint(np.all(df_subset.enc == yu.enc))\nprint(np.all(df_subset.mrn == yu.mrn))\nprint('Subset shape:',df_subset.shape, 'Yu\\'s df shape:',yu.shape)\ndf_subset.loc[df_subset.rollingwindow_aki.isnull(), 'rollingwindow_aki'] = 0\ndf_subset.loc[df_subset.backcalc_aki.isnull(), 'backcalc_aki'] = 0")


# ## Check mismatch 
# -------
# 
#     (Reloading dataframes on Aug 4, 2020 - number of rows changed from 127254 to 169243 hmm.... still 100% match though)
# ###### Back-calc match: 169243 / 169243 ; 100% Match 
# 
# ###### Rolling-window match: 169242 / 169234; 100% Match

# In[5]:


print('Back-calc match:', (df_subset.backcalc_aki == yu.historical_aki).sum(), '/', df_subset.shape[0],
      ';',(df_subset.backcalc_aki == yu.historical_aki).sum() / df_subset.shape[0])

print('Rolling-window match:', (df_subset.rollingwindow_aki == yu.running_aki).sum(), '/', yu.shape[0],
      ';', (df_subset.rollingwindow_aki == yu.running_aki).sum() / yu.shape[0])


# ### Back-calc mismatch - FULLY MATCHED NOW
# 
# ~~1248799, 4488514~~

# In[6]:


yu_mismatch = yu.iloc[np.where(df_subset.backcalc_aki != yu.historical_aki)[0]] #we don't match on 75 patients
print(yu_mismatch.shape)
print(yu_mismatch.historical_aki.sum()) # He says they're all false


# In[7]:


df_mismatch = df_subset.iloc[np.where(df_subset.backcalc_aki != yu.historical_aki)[0]]


# ### Rolling-window mismatch - FULLY MATCHED NOW
# 
# ~~We mismatch on mrn: 2258332, 6492074, ...~~

# In[8]:


yu_mismatch = yu.iloc[np.where(df_subset.rollingwindow_aki != yu.running_aki)[0]]
print(yu_mismatch.shape)
print(yu_mismatch.running_aki.sum()) #Again, he says all false


# In[9]:


#np.where(df_subset.loc[df_subset.mrn == 503537].rollingwindow_aki != yu.loc[yu.mrn == 503537].running_aki)


# 

# 

# 

# In[ ]:




