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