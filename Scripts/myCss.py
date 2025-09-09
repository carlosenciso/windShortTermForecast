#!/home/cenciso/miniconda3/envs/py37/bin/python
# -*- coding:utf-8 -*-
#---------------------------------------------------------------------------
# @Project: /home/cenciso/Documents/WORK/ENGIE/DashBoard/windShortTermForecast/Scripts
# @File: /home/cenciso/Documents/WORK/ENGIE/DashBoard/windShortTermForecast/Scripts/myCss.py
# @Author: Carlos Enciso Ojeda
# @Email: carlos.enciso.o@gmail.com
# @Created Date: Monday, September 1st 2025, 11:29:15 pm
# -----
# @Last Modified: Monday, 1st September 2025 11:29:15 pm
# @Modified By: Carlos Enciso Ojeda at <carlos.enciso.o@gmail.com>
# -----
# @Copyright (c) 2025 Peruvian Geophysical Institute
# @License: MIT
# -----
# @HISTORY:
# Date                   	By   	Comments
# ----                   	----   	----------
#---------------------------------------------------------------------------
#!/home/cenciso/anaconda3/envs/dash/bin/python
#-- Write CSS --#
#-- Create the assets folder and CSS file --#
import os
os.makedirs('./assets', exist_ok=True)
#-- Write the CSS file --#
css_content = """
body {
    # background-color: #708090;
}

.dashboard-container {
    width: 1400px;
    height: 1200px;
    margin-left: auto;
    margin-right: auto;
    margin-top: 50px;
    margin-bottom: 50px;
    # background-color: #010103;
    border: 1px solid #cccccc;
    border-radius: 10px;
}

h1 {
    # font-family: 'Poppins';
    color: #00bdff;
    margin: 15px,
    font-size: 20px;
    text-align: justify;
}

h2 {
    # font-family: 'Poppins';
    color: #00bdff;
    margin: 12px,
    font-size: 10px;
    text-align: justify;
    # font-weight: bold;
}

h3 {
    # font-family: 'Poppins';
    color: #00bdff;
    margin: 12px,
    font-size: 10px;
    text-align: justify;
    # font-weight: bold;
}

h3 {
    # font-family: 'Poppins';
    color: #00bdff;
    margin: 12px,
    font-size: 10px;
    text-align: justify;
    # font-weight: bold;
}

P {
    # font-family: 'Poppins';
    # color: #ffffff;
    margin: 15px,
    font-size: 16px;
    text-align: justify;
}

.mb-3 {
    # font-family: 'Poppins';
    color: #00bdff;
    margin: 12px,
    font-size: 10px;
    text-align: justify;
    # font-weight: bold;
}


"""
with open('./assets/style.css', 'w') as f:
    f.write(css_content)