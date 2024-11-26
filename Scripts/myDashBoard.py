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
import pandas as pd
import os
import panel as pn
import panel.widgets as pnw
import holoviews as hv
import bokeh
from scipy import stats
from holoviews import opts
from holoviews.plotting.links import RangeToolLink
from bokeh.plotting import figure, show
from bokeh.models import CustomJSTickFormatter
from bokeh.models import DatetimeTickFormatter
import hvplot.pandas
import hvplot.dask
from bokeh.plotting import show
#-- Reading Pickled --#
outDir = '../Outputs/PreProcessing'
dfWindGuruObs = pd.read_pickle(f'{outDir}/preProWindGuru.pkl')
dfWindyObs = pd.read_pickle(f'{outDir}/preProWindy.pkl')
def addMinMaxMean(arg, *args, **kwargs):
  oBj = arg.copy()
  scolumns = oBj.columns[-4:]
  oBj = oBj.dropna(subset=scolumns, how='all')
  oBj[['min', 'max', kwargs.get('name', 'mean')]] = oBj[scolumns].agg(['min', 'max', 'mean'], axis=1)
  return oBj
#-- Apply Function --#
dfWindGuruObsp = addMinMaxMean(dfWindGuruObs, name='WindGuru Mean Model')
dfWindyObsp = addMinMaxMean(dfWindyObs, name='Windy Mean Model')

#-- Main Code --#

def myDashBoard(*args, **kwargs):
  #-- Copy DataFrame --#
  dataWindy = dfWindyObs.query("date>=20241101").copy()
  dataWindG = dfWindGuruObs.query("date>=20241101").copy()
  #-- Grid Style --#
  grid={'grid_line_color': 'gray', 'grid_line_width': .8, 'grid_line_dash': 'dotted'}
  #-- Logo --#
  logoUrl = 'https://hamed.energy/wp-content/uploads/2018/12/engie-copy.png'
  logo = pn.pane.PNG(logoUrl, width=200, height=150, align=('center','center'))
  wFarms = ['Punta Lomitas', 'Waira I', 'Cupisnique', 'Talara', 'Huambos', 'Tres Hermanas']
  windFarms = pn.widgets.RadioButtonGroup(name='name', options=wFarms, button_type='success')
  windyModels = ['Windy Mean Model','ECMWF 9km', 'GFS 22km', 'ICON 13km', 'METEOBLUE']
  windyModel = pn.widgets.Select(name='Model', options=windyModels)
  windGModels = ['WindGuru Mean Model', ' WG', 'GDPS 15 km', 'GFS 13 km', 'ICON 13 km']
  windGModel = pn.widgets.Select(name='Model', options=windGModels)
  #-- Principal Panel --#
  @pn.depends(model=windyModel.param.value)
  def get_plot_windy(model):
    #-- Parameters --#
    if model=='Windy Mean Model':
      #- Forecast -#
      hvArea = dfWindyObsp.hvplot.area(x='date', y='min', y2='max', alpha=.1, color='#0E62CB', label='MinMax Model')
    #- Observations -#
    hvMean = dfWindyObsp.hvplot(x='date', y=model, line_width=1.2, color='#0E62CB',
                                grid=True, alpha=.55, label=model)
    hvObs = dataWindy.hvplot(x='date', y='ws_execute', line_width=1.2, color='#c00585',
                              grid=True, alpha=.55, label='Executed')
    hvDarwin = dataWindy.hvplot(x='date', y='Darwin', line_width=1.2, color='green',
                              grid=True, alpha=.55, label='Darwin')

    mainPlot = hvMean * hvObs * hvDarwin if model!='Windy Mean Model' else hvArea * hvMean * hvObs * hvDarwin
    mainPlot = mainPlot.opts(legend_position='top_left', legend_cols=4, legend_offset=(800, 0),
                             fontscale=.95, toolbar='above', ylim=(0, 25), gridstyle=grid, show_grid=True,
                             xlabel="", ylabel="Wind Speed (m/s)")
    return mainPlot
  #-- Principal Panel --#
  @pn.depends(model=windGModel.param.value)
  def get_plot_windg(model):
    #-- Parameters --#
    if model=='WindGuru Mean Model':
      #- Forecast -#
      hvArea = dfWindGuruObsp.hvplot.area(x='date', y='min', y2='max', alpha=.2, color='#0E62CB', label='MinMax Model')
    #- Observations -#
    hvMean = dfWindGuruObsp.hvplot(x='date', y=model, line_width=1.2, color='#0E62CB',
                                   grid=True, alpha=.55, label=model)
    hvObs = dfWindGuruObsp.hvplot(x='date', y='ws_execute', line_width=1.2, color='#c00585',
                                  grid=True, alpha=.55, label='Executed')
    hvDarwin = dfWindGuruObsp.hvplot(x='date', y='Darwin', line_width=1.2, color='green',
                              grid=True, alpha=.55, label='Darwin')

    mainPlot = hvMean * hvObs * hvDarwin if model!='WindGuru Mean Model' else hvArea * hvMean * hvObs * hvDarwin
    mainPlot = mainPlot.opts(legend_position='top_left', legend_cols=4, legend_offset=(800, 0),
                             fontscale=.95, toolbar='above', ylim=(0, 25), gridstyle=grid, show_grid=True,
                             xlabel="", ylabel="Wind Speed (m/s)")
    return mainPlot
  #-- As Block --#
  appRow = pn.WidgetBox(
      pn.Row(logo, pn.WidgetBox('# Short-Term WindSpeed Forecast', windFarms, width=740), sizing_mode='scale_width', styles=dict(background='White')),
      '## Windy Forecast ', pn.Column(windyModel, hv.DynamicMap(get_plot_windy).opts(width=940, height=250, framewise=True)),
      '## WindGuru Forecast ', pn.Column(windGModel, hv.DynamicMap(get_plot_windg).opts(width=940, height=250, framewise=True)),
      )
  return appRow
myDash = myDashBoard()
#-- Save Dashboard --#
# from bokeh.resources import INLINE
# myDash.save('test.html', resources=INLINE)
myDash.save('../index.html', embed=True)