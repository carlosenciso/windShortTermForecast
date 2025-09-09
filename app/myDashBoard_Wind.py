#!/home/cenciso/anaconda3/envs/dash/bin/python
#-- Main Code --#
#-- Import modules --#
import dash
import time
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

#-- Layout --#
app = Dash(__name__,
           external_stylesheets=[
               dbc.themes.SUPERHERO,
               "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"],
           assets_folder='/content/assets',
           )
#-- Tab Name --#
app.title = "ENGIE WindForecast Platform "
#-- Theme to Toggle --#
# LIGHT_THEME = dbc.themes.CERULEAN
LIGHT_THEME = dbc.themes.SUPERHERO
# LIGHT_THEME = dbc.themes.CERULEAN
DARK_THEME = dbc.themes.SUPERHERO
#-- Cards --#
def create_metric_card(icon, title, value, change, color="primary"):
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color}")
                ], className="col-3 d-flex align-items-center"),
                html.Div([
                    html.H4(value, className="mb-0",
                            style={
                                'font-size': '32px',
                                # 'font-family': 'DidoneRoomNumbers',
                                'font-weight': 'bold',
                                }),
                    html.P(title, className="mb-0 text-muted"),
                    html.Small(f"{change}% from last month",
                              className=f"text-{'success' if '+' in change else 'danger'}")
                ], className="col-9")
            ], className="row align-items-center")
        ])
    ], className="mb-3 shadow-sm")
metric_cards = [
                create_metric_card("fa-solid fa-wind", "m/s", "13.5", "+2.5", "primary"),
                create_metric_card("fa-solid fa-bolt", "MW", "1,234", "+900.5", "info"),
                create_metric_card("fa-solid fa-chart-line", "MAPE (%)", "20.2", "20", "warning"),
                ]
#-- Function to create sample figures --#
"""
  All plots on the right panel
"""
#-- UI Theme switch --#
color_mode_switch = html.Span(
    [
        dbc.Label(className="fa fa-moon", html_for="switch"),
        dbc.Switch(id="switch", value=False, className="d-inline-block ms-1", persistence=True),
        dbc.Label(className="fa fa-sun", html_for="switch"),
    ],
    className="my-2"
)
#-- Main Layout --#
app.layout = dbc.Container([
    #-- Wait for the intro --#
    #-- Theme link and store --#
    # dbc.Label(className="fa fa-moon", html_for="switch"),
    html.Link(rel="stylesheet", href=LIGHT_THEME, id="theme-link"),
    dcc.Store(id="theme-store", data={"dark": False}),
    #-- Left Panel --#
    dbc.Row([
        dbc.Col([
            html.Div([
                #-- The switch --#
                html.Div(color_mode_switch, className='mb-3 text-end'),
                #-- Logo --#
                html.Img(
                    src='https://upload.wikimedia.org/wikipedia/commons/8/8f/Logo-engie.svg',
                    style={
                        'width': '200px',
                        'margin-bottom': '20px',
                        'display': 'block',
                        'margin-left': 'auto',
                        'margin-right': 'auto'
                    }
                ),
                #-- Title --#
                html.H1([
                    html.Span("Welcome"),
                    html.Br(),
                    html.Span("WindForecast Platform")
                ],
                        style={'color':'#00bdff'},
                        className="text-center mb-4"),
                #-- Description --#
                html.P(
                    "\
                      This platform provides accurate wind forecasts and energy generation \
                      insights for 10 wind farms and the SEIN system. It supports short and \
                      long-term planning with interactive tools and clear visualizations. \
                    ",
                    className="text-justify mb-4",
                ),
                #-- Time range buttons --#
                html.H5("Forecast Range", className="mb-3"),
                dbc.RadioItems(
                    id='top-buttons',
                    className='btn-group-horizontal',
                    inputClassName='btn-check',
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="btn btn-primary",
                    options=[
                        {"label": "Short Term (15 days)", "value":1,},
                        {"label": "Long  Term (07 months)", "value":2},
                    ],
                    value=1,
                ),
                html.Hr(),
                #-- Wind Farms Section --#
                html.H5("WindFarms", className="mt-4", style={'color':'#00bdff'},),
                dbc.RadioItems(
                    id="windfarm-buttons",
                    options=[
                        {"label": "SEIN", "value": "0"},
                        {"label": "W.F. Punta Lomitas", "value": "1"},
                        {"label": "W.F. Cupisnique", "value": "2"},
                        {"label": "W.F. Duna", "value": "3"},
                        {"label": "W.F. Huambos", "value": "4"},
                        {"label": "W.F. Marcona", "value": "5"},
                        {"label": "W.F. San Juan", "value": "6"},
                        {"label": "W.F. Talara", "value": "7"},
                        {"label": "W.F. Tres Hermanas", "value": "8"},
                        {"label": "W.F. Wayra Ext.", "value": "9"},
                        {"label": "W.F. Wayra I", "value": "10"},
                    ],
                    value="0",
                    className="mb-3"
                ),
            ])
        #-- Set the width left panel --#
        ], width=4),
        #-- Right Panel --#
        dbc.Col([
            html.Br(),
            html.H4("Monitoring KPI", className="mt-4", style={'color':'#00bdff'},),
            dbc.Row([
                dbc.Col(card, width=4) for card in metric_cards
                ]),
            html.H4("Forecast Wind Generation", className="mt-4", style={'color':'#00bdff'},),
            html.H4("Forecast Wind Resource", className="mt-4", style={'color':'#00bdff'},),
            html.H4("Resume Forecast Skill", className="mt-4", style={'color':'#00bdff'},),
        ], width=8)
    ])
],
  # fluid=True,
  # className='dashboard-container',

  # style={
  #     'width':'1400px',
  #     'height':'2200px',
  #     'display': 'flex',

  #     }
)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=False)