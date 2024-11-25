#!/home/cenciso/miniconda3/envs/pangeo/bin/python
# -*- coding:utf-8 -*-
#---------------------------------------------------------------------------
# @Project: /home/cenciso/Documents/WORK/ENGIE/DashBoard/windShortTermForecast/Scripts
# @File: /home/cenciso/Documents/WORK/ENGIE/DashBoard/windShortTermForecast/Scripts/preProcessing.py
# @Author: Carlos Enciso Ojeda
# @Email: carlos.enciso.o@gmail.com
# @Created Date: Monday, November 25th 2024, 1:17:57 pm
# -----
# @Last Modified: Monday, 25th November 2024 1:17:57 pm
# @Modified By: Carlos Enciso Ojeda at <carlos.enciso.o@gmail.com>
# -----
# @Copyright (c) 2024 Peruvian Geophysical Institute
# @License: MIT
# -----
# @HISTORY:
# Date                   	By   	Comments
# ----                   	----   	----------
#---------------------------------------------------------------------------
#-- Import module --#
import os
import pandas as pd
import numpy as np
#-------------------
# Printer decorator
#-------------------
def _decorator(func):
    def wrap(*args, **kwargs):
        print('#'+'-'*(len(*args)+2))
        func(*args)
        print('#'+'-'*(len(*args)+2))
    return wrap
@_decorator
def printing(msg):
    print('# '+msg)
#-- Reading all Files --#
mainDir = '../Dataset/Darwin/'
listFiles = sorted([os.path.join(root,x) for root,subdir,fili in os.walk(mainDir) for x in fili if x.endswith('.xlsx') and 'Plantilla' in x])
#-- PreProcessing --#
from tqdm.notebook import tqdm
def preProcessing(oBj, kind='fc'):
  idxCol = [1,3] if kind=='fc' else [8,10]
  varname = f'ws_{kind}'
  dfObj = pd.read_excel(oBj, sheet_name='Plantilla Datos').iloc[7:,idxCol]
  dfObj.columns = ['date', varname]
  dfObj.dropna(axis=0, inplace=True)
  dfObj['date'] = pd.to_datetime(dfObj['date'])
  dfObj = dfObj.apply(lambda x: pd.to_numeric(x, errors='coerce') if x.name == varname else x)
  #-- Adding Lead and initDate --#
  if kind=='fc':
    dfObj['lead_hour'] = range(1, len(dfObj)+1)
    dfObj['initDate'] = dfObj['date'].min().strftime('%Y-%m-%d')
  return dfObj
#-- Call Function --#
if __name__ == '__main__':
  #-- Iteration through files --#
  containerFc = []
  containerObs = []
  printing('PreProcessing Datasets')
  for n,f in tqdm(enumerate(listFiles), desc='Extracting data', total=len(listFiles)):
    try:
      containerFc.append(preProcessing(f))
      containerObs.append(preProcessing(f, kind='obs'))
    except:
      print(f"Error in {f} file")
  #-- Concating all Fc --#
  dfDarwinFc = pd.concat(containerFc, axis=0, ignore_index=True)
  dfwinObs = pd.concat(containerObs, ignore_index=True).drop_duplicates(subset='date')
#-- Merging and Categorize --#
dfWindExecu = dfwinObs.rename({'ws_obs':'ws_execute'},axis=1).copy()
dfMergedFcObs = pd.merge(dfDarwinFc, dfWindExecu, on='date', how='outer')
dfMergedFcObs['lead_days'] = pd.cut(dfMergedFcObs['lead_hour'], bins=list(range(0,241,24)), labels=[f'Day {x+1:02d}' for x in range(10)])
dfMergedFcObs.sort_values(['initDate', 'date', 'lead_hour'], inplace=True)
dfMergedFcObs = dfMergedFcObs.rename({'ws_fc':'Darwin'},axis=1)
#-- Reading webScrapping --#
mainDir = '../Dataset/Scraped_Data/'
sScrapped = sorted([os.path.join(root, x) for root,subdir,files in os.walk(mainDir) for x in files if x.endswith('.xlsx')])
#-- Reading all books --#
dfWindGuru = [pd.read_excel(x, sheet_name='WINDGURU') for x in sScrapped]
dfWindy = [pd.read_excel(x, sheet_name='WINDY') for x in sScrapped]
#-- Concating DataFrame --#
dfWindGuru = pd.concat(dfWindGuru, ignore_index=True)
dfWindy = pd.concat(dfWindy, ignore_index=True)
#-- Convert to Datetime --#
windGuruCols = ['initDate', 'fcDate', 'model', 'wSpeed', 'wGusts', 'Wd']
dfWindGuru.columns = windGuruCols
dfWindGuru['initDate'] = pd.to_datetime(dfWindGuru['initDate'])
dfWindGuru['fcDate'] = pd.to_datetime(dfWindGuru['fcDate'])
#-- Convert to Datime --#
windyCols = ['initDate', 'fcDate', 'model', 'temp', 'wSpeed', 'Wd']
dfWindy.columns = windyCols
dfWindy['initDate'] = pd.to_datetime(dfWindy['initDate'])
dfWindy['fcDate'] = pd.to_datetime(dfWindy['fcDate'])
#-- Convert to float --#
dfWindGuru = dfWindGuru.apply(lambda x: pd.to_numeric(x, errors='coerce') if x.name=='wSpeed' else x)
dfWindy = dfWindy.apply(lambda x: pd.to_numeric(x, errors='coerce') if x.name=='wSpeed' else x)
#-- Get ride of duplicates --#
dfWindGuru = dfWindGuru.groupby(['initDate', 'model'], group_keys=False).apply(lambda x: x.drop_duplicates(subset='fcDate', keep='first'))
dfWindy = dfWindy.groupby(['initDate', 'model'], group_keys=False).apply(lambda x: x.drop_duplicates(subset='fcDate', keep='first'))
#-- Get ride the f** off --#
dfWindGuru['initDateFixed'] = dfWindGuru['initDate'].apply(lambda x: x.strftime('%Y-%m-%d'))
dfWindy['initDateFixed'] = dfWindy['initDate'].apply(lambda x: x.strftime('%Y-%m-%d'))
dfWindGurup = dfWindGuru.pivot_table(index=['initDateFixed', 'fcDate'], columns='model', values='wSpeed', aggfunc=np.nanmean).reset_index()
dfWindyp = dfWindy.pivot_table(index=['initDateFixed', 'fcDate'], columns='model', values='wSpeed', aggfunc=np.nanmean).reset_index()
#-- Merge with Observation --#
dfWindGuruObs = pd.merge(dfMergedFcObs, dfWindGurup.rename({'fcDate':'date', 'initDateFixed':'initDate'}, axis=1), on=['date', 'initDate'], how='outer')
dfWindyObs = pd.merge(dfMergedFcObs, dfWindyp.rename({'fcDate':'date', 'initDateFixed':'initDate'}, axis=1), on=['date', 'initDate'], how='outer')
#-- Save PreoProcessing --#
outDir='../Outputs/PreProcessing'
dfWindGuruObs.to_pickle(f'{outDir}/preProWindGuru.pkl')
dfWindyObs.to_pickle(f'{outDir}/preProWindy.pkl')