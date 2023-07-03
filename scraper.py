# %% [markdown]
# Script Name: scraper.py
# <br>Purpose: Scraping chinook data and orca for dashboard
# <br>Author: Zoe Liu
# <br>Date: Oct 12th 2022

# %% [markdown]
# #### 1 Setup

# %% [markdown]
# 1.1 Import libraries

# %%
import os
import re

import requests
import selenium
from selenium import webdriver 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

import chromedriver_autoinstaller

from datetime import date
from datetime import datetime
from time import strptime
import time
from time import sleep

import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment 

# %% [markdown]
# 1.2 Get today's date

# %%
today=date.today()
todaystr=str(today)
curyr=today.year
#curyr=2022
lastyr=curyr-1
twoyr=curyr-2
ayl=[y for y in range(1980, curyr+1)] #year list for Albion
byl=[y for y in range(1939, curyr+1)] #year list for Bonneville Dam

# %% [markdown]
# 1.3 Define data path

# %%
fos_path='./data/foschinook/'
bon_path='./data/bonchinook/'
acartia_path='./data/acartia/'
# %% [markdown]
# #### 2 Scap web data

# %% [markdown]
# 2.1 Scrap Chinook data by year
chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
                                      # and if it doesn't exist, download it automatically,
                                      # then add chromedriver to path

# %%
def scrap_fos(yrs='2022',spe='CHINOOK SALMON', fos_path=fos_path):
  #Set up chrome driver
  options = webdriver.ChromeOptions()
  options.add_argument('--headless')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  options.add_argument('--ignore-certificate-errors')
  driver=webdriver.Chrome(options=options)
  #landing page of fos data
  url = 'https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242'
  driver.get(url)
  sleep(3)
  #select year and species and generate report
  driver.find_element('id','lboYears').send_keys(yrs)
  driver.find_element('id','lboSpecies').send_keys(spe)
  driver.find_element('name','cmdRunReport').click()
  sleep(1)
  window_after = driver.window_handles[1] #Switch to the newly opened window
  driver.switch_to.window(window_after)
  #scrape data from the report table 
  table=driver.find_elements(By.XPATH,'.//tr')
  #process scrapped data and convert to pandas df
  tabls0=list(map(lambda x: x.text.split(sep=' '), table))
  tabls=[t for t in tabls0 if ((len(t)==12) & (t[0]!='Printed'))]
  dat=pd.DataFrame(tabls, columns=['day','mon','year','netlen','catch1','sets1','effort1','cpue1', 'catch2','sets2','effort2','cpue2'])
  #archive data to csv
  dat.to_csv(fos_path+'fos'+yrs+'.csv', index=False)

# %% [markdown]
# Use the following line to download the current year

# %%
scrap_fos(yrs=str(curyr),spe='CHINOOK SALMON', fos_path=fos_path)

# %% [markdown]
# Use the following lines to download all fos chinook data
# <br>Note: commented out after running it once

# %%
'''
for y in ayl:
  scrap_fos(yrs=str(y),spe='CHINOOK SALMON', fos_path=fos_path)
'''

# %% [markdown]
# 2.2 Scrap Bonneville Dam Chinook Daily count

# %%
def scrap_bon(yrs='2022', bon_path=bon_path):
  if os.path.exists(bon_path)==False:
    os.makedirs(bon_path)
  #Set up chrome driver
  options = webdriver.ChromeOptions()
  options.add_argument('--headless')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  options.add_argument('--ignore-certificate-errors')
  driver=webdriver.Chrome(options=options)
  #landing page of Columbia Basin Research 
  url = 'https://www.cbr.washington.edu/dart/query/adult_daily'
  driver.get(url)
  sleep(3)
  #select year and generate report
  site='BON'
  driver.find_element('id','daily').click()
  driver.find_element('id','outputFormat2').click()
  driver.find_element('id','year-select').send_keys(yrs)
  driver.find_element('id','proj-select').send_keys(site)
  if driver.find_element('id','calendar').is_selected()==False:
    print("click the calendar element")
    driver.find_element('id','calendar').submit()
  if driver.find_element('id','run1').is_selected()==False:
    print("click the run1 element")
    driver.find_element('id','run1').submit()  
  driver.find_element(By.XPATH, ".//input[@type='submit']").submit()
  sleep(3)
  dlf=[x for x in os.listdir("./") if x[-4:]=='.csv']
  filename=dlf[0]
  os.rename('./'+filename, bon_path+'bon'+yrs+'.csv')

# %% [markdown]
# Use the following line to download the current year

# %%
scrap_bon(yrs=str(curyr), bon_path=bon_path)

# %% [markdown]
# Use the following lines to download all fos chinook data
# <br>Note: commented out after running it once

# %%
'''
for y in byl:
  scrap_bon(yrs=str(y), bon_path=bon_path)
'''

# %% [markdown]
# 2.3 Scrap Acartia orca data

# %%
def scrap_acartia(acartia_path='./data/acartia/'):
  #Read Acartia token
  atoken = os.environ['ACARTIA_TOKEN']
  #Acartia webpages
  url='https://acartia.io/api/v1/sightings/'
  response = requests.get(url, headers={'Authorization': 'Bearer '+atoken, 
                                     'Content-Type': 'application/json'})
  acartia=pd.DataFrame(response.json(), 
                     columns=['type','created','profile','trusted','entry_id','latitude','longitude','photo_url','signature',
                              'ssemmi_id','no_sighted','submitter_did','data_source_id',
                              'data_source_name','ssemmi_date_added','data_source_entity', 'data_source_witness', 'data_source_comments'])
  acartia=acartia[['type','created','latitude','longitude','no_sighted','data_source_id','data_source_comments']]
  acartia=acartia.drop_duplicates()
  acartia=acartia.sort_values(by=['created'])
  #save acartia to the Colab local folder ***disappear after each session!!!
  acartia.to_csv(acartia_path+'acartia_'+todaystr+'.csv', index=False)
# %% [markdown]
# Run the following code to scrape Acartia data

# %%
scrap_acartia()

# %% [markdown]
# Processing Acartia Data
# Function to clean up dates format
def cleandates(s):
  if s.count('T')>0:
    s=s.replace('T',' ')
    s=s.replace('Z','')
    s=s.split('.')[0]
  return s
# %%
acartia=pd.read_csv(acartia_path+'acartia_'+todaystr+'.csv')
acartia=acartia[~acartia['created'].isnull()]
acartia['created']=acartia['created'].apply(lambda x: cleandates(x))
acartia['m']=pd.DatetimeIndex(acartia['created']).month
acartia['day']=pd.DatetimeIndex(acartia['created']).day
acartia['year']=pd.DatetimeIndex(acartia['created']).year
acartia['month']=acartia['m'].apply(lambda x: datetime.strptime(str(x), '%m').strftime('%b'))
acartia['date']=acartia[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
acartia['date_ymd']=acartia[['year','m','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
acartia['time']=pd.DatetimeIndex(acartia['created']).time

# Define keys to look up
srkw_keys=['SRKW', 'srkw', 'southern resident', 'Southern Resident', 'Southern resident', 'southern Resident']
jpod_keys=['J pod', 'Jpod', 'J ppd', 'J-pod', 'Js', 
           'j pod', 'jpod', 'j ppd', 'j-pod',  
           'j+k', 'k+j', 'j & k', 'k & j', 'j and k', 'k and j','jk pods', 'kj pods',
           'J+K', 'K+J', 'J & K', 'K & J', 'J and K', 'K and J','JK pods', 'KJ pods',
           'j+l', 'l+j', 'j & l', 'l & j', 'j and l', 'l and j', 'jl pods', 'lj pods',
           'J+L', 'L+J', 'J & L', 'L & J', 'J and L', 'L and J', 'JL pods', 'LJ pods',
           'j, k, l pod', 'j, k, and l pod','jkl', 
           'J, K, L pod', 'J, K, and L pod','JKL', 
           'j27', 'j38', 'j35','j40',
           'J27', 'J38', 'J35','J40',
           ]
kpod_keys=['K pod', 'Kpod', 'K-pod', 'Ks',
           'k pod', 'kpod', 'k-pod', 
           'j+k', 'k+j', 'j & k', 'k & j', 'j and k', 'k and j', 'jk pods', 'kj pods',
           'J+K', 'K+J', 'J & K', 'K & J', 'J and K', 'K and J', 'JK pods', 'KJ pods',
           'k+l', 'l+k', 'k & l','l & k', 'k and l', 'l and k', 'lk pods', 'kl pods',
           'K+L', 'L+K', 'K & L','L & K', 'K and L', 'L and K', 'LK pods', 'KL pods',
           'j, k, l pod', 'j, k, and l pod','jkl', 
           'J, K, L pod', 'J, K, and L pod','JKL', 
           'k37', 'K37',
]
lpod_keys=['L pod', 'Lpod', 'L-pod', 'Ls',
           'j+l', 'l+j', 'j & l', 'l & j', 'j and l', 'l and j', 'jl pods', 'lj pods',
           'J+L', 'L+J', 'J & L', 'L & J', 'J and L', 'L and J', 'JL pods', 'LJ pods',
           'k+l', 'l+k', 'k & l','l & k', 'k and l', 'l and k', 'lk pods', 'kl pods',
           'K+L', 'L+K', 'K & L','L & K', 'K and L', 'L and K', 'LK pods', 'KL pods',
           'j, k, l pod', 'j, k, and l pod','jkl', 
           'J, K, L pod', 'J, K, and L pod','JKL', 
           'l12','l54','l-12','l82','l85','l87', 
           'L12','L54','L-12','L82','L85','L87',
]
biggs_keys=['Bigg','bigg', 'Transient', 'transient', 'Ts',
            't99', 't137','t46','t10','t2c','t49',
            'T99','T137','T36','T10','T2C','T49',
            ]

# J pod
acartia['J']=acartia['data_source_comments'].apply(lambda x: 1 if any([k for k in jpod_keys if k in str(x)])
else 0)
# K pod
acartia['K']=acartia['data_source_comments'].apply(lambda x: 1 if any([k for k in kpod_keys if k in str(x)])
else 0)
# L pod
acartia['L']=acartia['data_source_comments'].apply(lambda x: 1 if any([k for k in lpod_keys if k in str(x)])
else 0)

# Southern Residents
acartia['sum_jkl']=acartia['J']+acartia['K']+acartia['L']
acartia['srkw_generic']=acartia['data_source_comments'].apply(lambda x: 1 if any([k for k in srkw_keys if k in str(x).lower()])
else 0)
acartia['srkw_type']=acartia['type'].apply(lambda x: 1 if isinstance(x, str) and ('Southern Resident') in x else 0)
acartia['srkw']=acartia[['J', 'K', 'L', 'srkw_generic', 'srkw_type']].values.max(axis=1)

# Biggs
acartia['biggs']=acartia['data_source_comments'].apply(lambda x: 1 if any([k for k in biggs_keys if k in str(x).lower()]) or ('Ts') in str(x) else 0)

acartia['sum_srkw_biggs']=acartia['srkw']+acartia['biggs']

# direction 
acartia['south']=acartia['data_source_comments'].apply(lambda x: 1 if ('southbound') in str(x).lower()
or ('heading south' in str(x).lower())
else 0)

acartia['southeast']=acartia['data_source_comments'].apply(lambda x: 1 if ('southeast') in str(x).lower()
or ('SE' in str(x))
else 0)

acartia['southwest']=acartia['data_source_comments'].apply(lambda x: 1 if ('southwest') in str(x).lower()
or ('SW' in str(x))
else 0)

acartia['north']=acartia['data_source_comments'].apply(lambda x: 1 if ('northbound') in str(x).lower()
or ('heading north' in str(x).lower())
else 0)

acartia['northeast']=acartia['data_source_comments'].apply(lambda x: 1 if ('northeast') in str(x).lower()
or ('NE' in str(x))
else 0)

acartia['northwest']=acartia['data_source_comments'].apply(lambda x: 1 if ('northwest') in str(x).lower()
or ('NW' in str(x))
else 0)

acartia['east']=acartia['data_source_comments'].apply(lambda x: 1 if (('eastbound') in str(x).lower() and ('southeastbound') not in str(x).lower())
or ('heading east' in str(x).lower())
else 0)

acartia['west']=acartia['data_source_comments'].apply(lambda x: 1 if (('westbound') in str(x).lower() and ('northwestbound' not in str(x).lower()))
or ('heading west' in str(x).lower())
else 0)

acartia['dir_sum']=acartia['south']+acartia['southeast']+acartia['southwest']+acartia['north']+acartia['northeast']+acartia['northwest']+acartia['east']+acartia['west']

for y in range(2018,curyr+1):
  act=acartia[acartia['year']==y]
  act=act[act['srkw']==1]
  act=act.drop_duplicates()
  act.to_csv(acartia_path+'srkw_'+str(y)+'.csv', index=False)
