# -*- coding:utf-8 -*-
#-----------------------------------------------------
# @Project: ./windShortTermForecast/src
# @File: ./windShortTermForecast/src/client_coes.py
# @Author: Carlos Enciso Ojeda
# @Email: carlos.enciso.o@gmail.com
# @Created Date: Tuesday, Sept 09th 2025, 9:21:10 am
#-----------------------------------------------------
#-- Modules --#
import pandas as pd
import requests
import datetime
import logging
import warnings
warnings.filterwarnings('ignore')
#-- logging --#
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('client_coes.log')
    ]
)
logger = logging.getLogger(__name__)
#-- Main code --#
def clientCoes(code:int, service, startDate, 
               endDate, *args, **kwargs):
    #-- Settings --#
    startDate = startDate.strftime("%Y-%m-%d")
    endDate = endDate.strftime("%Y-%m-%d")
    api = f'api/Mediciones?lectcodi={code}&fechaIni={startDate}&fechaFin={endDate}'
    url = f'{service}{api}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        obj = pd.DataFrame(response.json())
        if not obj.empty:
            queryList = ['Cupis', 'Dunas', 'Huambos', 'Marcona', 'Lomitas', 
                         'Talara', 'Hermanas', 'Wayra', 'C.E.' ]
            obj = obj[obj['NombreEquipo'].str.contains('|'.join(queryList), case=False, regex=True)].copy()
            queryList = ['TV', 'C.H.', 'C.S.']
            obj = obj[~obj['NombreEquipo'].str.contains('|'.join(queryList), case=False, regex=True)].copy()
        logger.info(f"Successfully retrieved data for code {code}")
        return obj.iloc[:,:-48]
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for code {code}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error processing code {code}: {e}")
        return pd.DataFrame()

def getFormatData(dataset: pd.DataFrame, *args, **kwargs):
    try:
        idxNames = [c for c in dataset.columns if not any(f'h{w}' in c for w in range(1,49))]
        data = dataset.melt(id_vars=idxNames, value_name='power', var_name='hour').sort_values(['NombreEquipo','Medifecha'])
        data['Medifecha'] = pd.to_datetime(data['Medifecha'], format="%Y-%m-%dT00:00:00")
        data['hour_timedelta'] = pd.to_timedelta(data['hour'].str.replace('h', '').astype(int) * 30, unit='m')
        data['date'] = data['Medifecha'] + data['hour_timedelta']
        data = data[['date']+idxNames+['power']]
        data = data.sort_values(['NombreEquipo','date'])
        #-- Punta Lomitas --#
        puntaLomitas = data[data['NombreEquipo'].str.contains('PUN', case=False, regex=True)]
        puntaLomitas = puntaLomitas.groupby(['date']).agg({'NombreEmpresa':'last', 'Tipoinfoabrev':'last', 'power':'sum'}).reset_index()
        puntaLomitas['name'] = 'W.F. Punta Lomitas'
        #-- All except Punta Lomitas --#
        epuntaLomitas = data[~data['NombreEquipo'].str.contains('|'.join(['PUN','paita']), 
                                                                case=False, regex=True)]
        repNames = {
            'C.E. CUPISNIQUE':'W.F. Cupisnique',
            'C.E. DUNA':'W.F. Duna',
            'C.E. HUAMBOS':'W.F. Huambos',
            'C.E. MARCONA':'W.F. Marcona',
            'C.E. SAN JUAN':'W.F. San Juan',
            'C.E. TALARA':'W.F. Talara',
            'C.E. TRES HERMANAS':'W.F. Tres Hermanas',
            'C.E. WAYRA EXTENSION':'W.F. Wayra Ext',
            'C.E. WAYRA I':'W.F. Wayra I'
        }
        epuntaLomitas.loc[:,'NombreEquipo'] = epuntaLomitas['NombreEquipo'].replace(repNames)
        epuntaLomitas = epuntaLomitas.rename({'NombreEquipo':'name'},axis=1)
        epuntaLomitas = epuntaLomitas[puntaLomitas.columns]
        #-- Merged Both Datasets --#
        data = pd.concat([puntaLomitas, epuntaLomitas], ignore_index=True)
        logger.info("Data formatting completed successfully")
        return data
    except Exception as e:
        logger.error(f"Error in data formatting: {e}")
        raise

#-- Run code --#
if __name__ == '__main__':
    try:
        service = 'https://appserver.coes.org.pe/waMediciones/'
        endDate = datetime.datetime.now()
        startDate = endDate - datetime.timedelta(days=1)
        logger.info(f"Starting data retrieval from {startDate.strftime('%Y-%b-%d')} to {endDate.strftime('%Y-%b-%d')}")
        #-- Iterations through codes --#
        container = []
        for code in range(0, 4):
            logger.debug(f"Processing code {code}")
            result = clientCoes(code, service, startDate, endDate)
            if not result.empty:
                container.append(result)
        if container:
            dataset = pd.concat(container, ignore_index=False)
            #-- Discard duplicates --#
            dataset = dataset.groupby("NombreEquipo", group_keys=False)\
                           .apply(lambda x: x.drop_duplicates(subset=['Medifecha'], keep='last'))\
                           .reset_index()
            dropColumns = ['TensionEquipo', 'CodigoUbicacion', 'NombreUbicacion', 'index', '$id']
            dataset = dataset.drop(dropColumns, axis=1, errors='ignore')
            #-- Set data format --#
            dataset = getFormatData(dataset)
            logger.info(f"Coes Dataset was retrieved! Shape: {dataset.shape}")
            #-- Export as parquet --#
            dataset.to_parquet('../../dataset/currentGen.parquet')
            logger.info(f"Coes Dataset was stored!")
        else:
            logger.warning("No data was retrieved from any of the codes")
    except Exception as e:
        logger.exception("An unexpected error occurred during execution")