# # -*- coding:utf-8 -*-
# #-----------------------------------------------------
# # @Project: ./windShortTermForecast/app/
# # @File: ./windShortTermForecast/app/app.py
# # @Author: Carlos Enciso Ojeda
# # @Email: carlos.enciso.o@gmail.com
# # @Created Date: Tuesday, Sept 09th 2025, 9:21:10 am
# #-----------------------------------------------------
# -*- coding:utf-8 -*-
#-----------------------------------------------------
# @Project: ./windShortTermForecast/app/
# @File:    ./windShortTermForecast/app/app.py
# @Author:  Carlos Enciso Ojeda
#-----------------------------------------------------
# -- Imports -- #
import os
import dash
import pandas as pd
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px

# -------- Global visual setting (both graphs share the same height) --------
GRAPH_HEIGHT = int(os.environ.get("GRAPH_HEIGHT_PX", "320"))  # change env var to adjust

# =======================
# Read Gen Dataset (Parquet)
# =======================
# Priority: ENV -> local repo -> Render path
PARQUET_CANDIDATES = [
    os.environ.get("DATASET_PATH"),
    "../dataset/currentGen.parquet",
    "./dataset/currentGen.parquet",
    "/opt/render/project/dataset/currentGen.parquet",
]
parquet_path = next((p for p in PARQUET_CANDIDATES if p and os.path.exists(p)), None)

if parquet_path:
    dataset = pd.read_parquet(parquet_path)
    print(f"[OK] Data loaded from: {parquet_path} | shape={dataset.shape}")
else:
    raise FileNotFoundError(
        "Missing 'currentGen.parquet'. Put it in ./dataset/ or ../dataset/ or set DATASET_PATH."
    )

required_cols = {"name", "date", "power"}
missing = required_cols - set(dataset.columns)
if missing:
    raise ValueError(f"'currentGen.parquet' lacks required columns {required_cols}. Missing: {missing}")
dataset = dataset.copy()
dataset["date"] = pd.to_datetime(dataset["date"])

# =======================
# Read Wind Forecast Dataset (Parquet)
# =======================
WIND_PARQUET_CANDIDATES = [
    os.environ.get("WIND_FCS_PATH"),
    "../dataset/windSpeedFcs.parquet",
    "./dataset/windSpeedFcs.parquet",
    "/opt/render/project/dataset/windSpeedFcs.parquet",
]
wind_parquet_path = next((p for p in WIND_PARQUET_CANDIDATES if p and os.path.exists(p)), None)

if wind_parquet_path:
    wind_dataset = pd.read_parquet(wind_parquet_path)
    print(f"[OK] Wind data loaded from: {wind_parquet_path} | shape={wind_dataset.shape}")
    wind_required = {"name", "date", "wwind100", "model"}
    wmissing = wind_required - set(wind_dataset.columns)
    if wmissing:
        for col in wmissing:
            wind_dataset[col] = pd.Series(dtype="float64" if col == "wwind100" else "object")
    wind_dataset = wind_dataset.copy()
    wind_dataset["date"] = pd.to_datetime(wind_dataset["date"], errors="coerce")
else:
    print("[WARN] Missing 'windSpeedFcs.parquet'; wind chart will be empty.")
    wind_dataset = pd.DataFrame(columns=["name", "date", "wwind100", "model"])
    wind_dataset["date"] = pd.to_datetime(wind_dataset["date"])

# =======================
# App & Theme
# =======================
app = Dash(
    __name__,
    external_stylesheets=[
        # do not preload dbc theme here; toggle with <link> below
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
)
app.title = "ENGIE WindForecast Platform"
server = app.server

LIGHT_THEME = dbc.themes.CERULEAN
DARK_THEME  = dbc.themes.SUPERHERO

# =======================
# Style helpers (same look & feel for both figures)
# =======================
def get_theme(dark: bool):
    colors = {
        "bg":   "#0f2537" if dark else "#ffffff",
        "text": "#ffffff" if dark else "#2c3e50",
    }
    template = "plotly_dark" if dark else "plotly_white"
    rs_style = dict(
        bgcolor="#000000" if dark else "#ffffff",
        activecolor="#4169e1" if dark else "#00bdff",
        font=dict(color=colors["text"]),
    )
    return colors, template, rs_style

def apply_common_layout(fig, *, dark: bool, ytitle: str, x_dtick_ms: int):
    colors, template, rs_style = get_theme(dark)
    fig.update_traces(line=dict(width=2))
    fig.update_layout(
        template=template,
        plot_bgcolor=colors["bg"],
        paper_bgcolor=colors["bg"],
        font=dict(color=colors["text"]),
        xaxis=dict(
            tickfont_size=10,
            showgrid=True, gridcolor="lightgrey", gridwidth=0.01, griddash="solid",
            tickangle=0, tickformat="%d-%b\n%H:%M", dtick=x_dtick_ms, title=""
        ),
        yaxis=dict(
            showgrid=True, gridcolor="lightgrey", gridwidth=0.01, griddash="solid",
            title=dict(text=ytitle, font=dict(size=12))
        ),
        hovermode="x unified",
        margin=dict(t=60, b=5, l=10, r=10),
        autosize=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title=None,
        height=GRAPH_HEIGHT,  # enforce same figure height internally
    )
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1D", step="day", stepmode="backward"),
                dict(count=5, label="5D", step="day", stepmode="backward"),
                dict(step="all"),
            ],
            **rs_style,
        ),
    )
    return fig

# =======================
# UI bits
# =======================
def create_metric_card(icon_classes: str, title: str, value: str, change, color: str = "primary"):
    try:
        up = (str(change).startswith("+") or float(str(change).replace("+","").replace("%","")) >= 0)
    except Exception:
        up = True
    trend_class = "text-success" if up else "text-danger"
    change_txt  = f"{change}% from last month" if "%" not in str(change) else f"{change} from last month"
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([html.I(className=f"{icon_classes} fa-2x text-{color}")],
                         className="col-3 d-flex align-items-center"),
                html.Div([
                    html.H4(value, className="mb-0", style={'font-size': '32px','font-weight': 'bold'}),
                    html.P(title, className="mb-0 text-muted"),
                    html.Small(change_txt, className=trend_class)
                ], className="col-9")
            ], className="row align-items-center")
        ])
    ], className="mb-3 shadow-sm")

metric_cards = [
    create_metric_card("fa-solid fa-wind", "m/s", "13.5", "+2.5", "primary"),
    create_metric_card("fa-solid fa-bolt", "MW", "1,234", "+900.5", "info"),
    create_metric_card("fa-solid fa-chart-line", "MAPE (%)", "20.2", "20", "warning"),
]

color_mode_switch = html.Span(
    [
        dbc.Label(className="fa fa-sun", html_for="switch"),
        dbc.Switch(id="switch", value=False, className="d-inline-block ms-1", persistence=True),
        dbc.Label(className="fa fa-moon", html_for="switch"),
    ],
    className="my-2"
)

WINDFARM_MAPPING = {
    "0": "SEIN", "1": "W.F. Punta Lomitas", "2": "W.F. Cupisnique",
    "3": "W.F. Duna", "4": "W.F. Huambos", "5": "W.F. Marcona",
    "6": "W.F. San Juan", "7": "W.F. Talara", "8": "W.F. Tres Hermanas",
    "9": "W.F. Wayra Ext", "10": "W.F. Wayra I"
}

# =======================
# Layout
# =======================
app.layout = dbc.Container([
    html.Link(rel="stylesheet", href=LIGHT_THEME, id="theme-link"),
    dcc.Store(id="theme-store", data={"dark": False}),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div(color_mode_switch, className='mb-3 text-end'),
                html.Img(
                    src='https://upload.wikimedia.org/wikipedia/commons/8/8f/Logo-engie.svg',
                    style={'width': '200px','margin-bottom': '20px','display': 'block','margin-left': 'auto','margin-right': 'auto'}
                ),
                html.H1([html.Span("Welcome"), html.Br(), html.Span("WindForecast Platform")],
                        style={'color':'#00bdff'}, className="text-center mb-4"),
                html.P(
                    "This platform provides wind forecasts and energy insights for 10 wind farms and SEIN.",
                    className="text-justify mb-4",
                ),
                html.H5("Forecast Range", className="mb-3"),
                dbc.RadioItems(
                    id='top-buttons',
                    className='btn-group-horizontal',
                    inputClassName='btn-check',
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="btn btn-primary",
                    options=[
                        {"label": "Short Term (15 days)", "value": 1},
                        {"label": "Long  Term (07 months)", "value": 2},
                    ],
                    value=1,
                ),
                html.Hr(),
                html.H5("WindFarms", className="mt-4", style={'color':'#00bdff'}),
                dbc.RadioItems(
                    id="windfarm-buttons",
                    options=[{"label": v, "value": k} for k, v in WINDFARM_MAPPING.items()],
                    value="1",
                    className="mb-3"
                ),
            ])
        ], width=4),

        dbc.Col([
            html.Br(),
            html.H4("Monitoring KPI", className="mt-4", style={'color':'#00bdff'}),
            dbc.Row([dbc.Col(card, width=4) for card in metric_cards]),
            html.H4("Forecast Wind Generation", className="mt-4", style={'color':'#00bdff'}),
            dcc.Graph(id='genPlot', style={'height': f'{GRAPH_HEIGHT}px'}),
            html.H4("Forecast Wind Resource", className="mt-4", style={'color':'#00bdff'}),
            dcc.Graph(id='windPlot', style={'height': f'{GRAPH_HEIGHT}px'}),
            html.H4("Resume Forecast Skill", className="mt-4", style={'color':'#00bdff'}),
        ], width=8)
    ])
],
style={'display':'flex', 'maxWidth':'1440px'},
fluid=True)

# =======================
# Callbacks
# =======================
@app.callback(
    Output("theme-link", "href"),
    Output("theme-store", "data"),
    Input("switch", "value"),
    State("theme-store", "data"),
)
def toggle_theme(switch_value, data):
    dark = bool(switch_value)
    theme_href = DARK_THEME if dark else LIGHT_THEME
    return theme_href, {"dark": dark}

@app.callback(
    Output('genPlot', 'figure'),
    Input('windfarm-buttons', 'value'),
    Input("switch", "value"),
)
def update_gen_plot(windfarm_value, dark):
    windfarm_name = WINDFARM_MAPPING.get(windfarm_value, "SEIN")
    subset = dataset.query("name == @windfarm_name").copy()
    if subset.empty:
        subset = pd.DataFrame({"date": pd.to_datetime([]), "power": []})

    fig = px.line(subset, x='date', y='power', line_shape='linear')
    fig = apply_common_layout(fig, dark=bool(dark), ytitle='Wind Generation (MW)',
                              x_dtick_ms=18*3600*1000)  # 18h
    return fig

@app.callback(
    Output('windPlot', 'figure'),
    Input('windfarm-buttons', 'value'),
    Input("switch", "value"),
)
def updateWindPlot(windfarm_value, dark):
    windfarm_name = WINDFARM_MAPPING.get(windfarm_value, "SEIN")
    if not wind_dataset.empty and 'name' in wind_dataset.columns:
        subset = wind_dataset.query("name == @windfarm_name").copy()
    else:
        subset = pd.DataFrame(columns=["date", "wwind100", "model"])
        subset["date"] = pd.to_datetime(subset["date"])

    # spline rendering for smoother visual
    fig = px.line(subset, x='date', y='wwind100', color='model', line_shape='spline')
    fig.update_traces(line=dict(smoothing=0.85))
    fig = apply_common_layout(fig, dark=bool(dark), ytitle='Wind Speed (m/s)',
                              x_dtick_ms=24*3600*1000)  # 24h
    return fig

# =======================
# Main
# =======================
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8060, debug=False)





# #-- Import modules --#
# import dash
# import time
# from dash import Dash, html, dcc, Input, Output, State
# import dash_bootstrap_components as dbc
# import plotly.graph_objects as go
# import plotly.express as px

# #-- Layout --#
# app = Dash(__name__,
#            external_stylesheets=[
#                dbc.themes.SUPERHERO,
#                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"],
#            assets_folder='/content/assets',
#            )
# #-- Tab Name --#
# app.title = "ENGIE WindForecast Platform "
# #-- Theme to Toggle --#
# # LIGHT_THEME = dbc.themes.CERULEAN
# LIGHT_THEME = dbc.themes.SUPERHERO
# # LIGHT_THEME = dbc.themes.CERULEAN
# DARK_THEME = dbc.themes.SUPERHERO
# #-- Cards --#
# def create_metric_card(icon, title, value, change, color="primary"):
#     return dbc.Card([
#         dbc.CardBody([
#             html.Div([
#                 html.Div([
#                     html.I(className=f"fas {icon} fa-2x text-{color}")
#                 ], className="col-3 d-flex align-items-center"),
#                 html.Div([
#                     html.H4(value, className="mb-0",
#                             style={
#                                 'font-size': '32px',
#                                 # 'font-family': 'DidoneRoomNumbers',
#                                 'font-weight': 'bold',
#                                 }),
#                     html.P(title, className="mb-0 text-muted"),
#                     html.Small(f"{change}% from last month",
#                               className=f"text-{'success' if '+' in change else 'danger'}")
#                 ], className="col-9")
#             ], className="row align-items-center")
#         ])
#     ], className="mb-3 shadow-sm")
# metric_cards = [
#                 create_metric_card("fa-solid fa-wind", "m/s", "13.5", "+2.5", "primary"),
#                 create_metric_card("fa-solid fa-bolt", "MW", "1,234", "+900.5", "info"),
#                 create_metric_card("fa-solid fa-chart-line", "MAPE (%)", "20.2", "20", "warning"),
#                 ]
# #-- Function to create sample figures --#
# """
#   All plots on the right panel
# """
# #-- UI Theme switch --#
# color_mode_switch = html.Span(
#     [
#         dbc.Label(className="fa fa-moon", html_for="switch"),
#         dbc.Switch(id="switch", value=False, className="d-inline-block ms-1", persistence=True),
#         dbc.Label(className="fa fa-sun", html_for="switch"),
#     ],
#     className="my-2"
# )
# #-- Main Layout --#
# app.layout = dbc.Container([
#     #-- Wait for the intro --#
#     #-- Theme link and store --#
#     # dbc.Label(className="fa fa-moon", html_for="switch"),
#     html.Link(rel="stylesheet", href=LIGHT_THEME, id="theme-link"),
#     dcc.Store(id="theme-store", data={"dark": False}),
#     #-- Left Panel --#
#     dbc.Row([
#         dbc.Col([
#             html.Div([
#                 #-- The switch --#
#                 html.Div(color_mode_switch, className='mb-3 text-end'),
#                 #-- Logo --#
#                 html.Img(
#                     src='https://upload.wikimedia.org/wikipedia/commons/8/8f/Logo-engie.svg',
#                     style={
#                         'width': '200px',
#                         'margin-bottom': '20px',
#                         'display': 'block',
#                         'margin-left': 'auto',
#                         'margin-right': 'auto'
#                     }
#                 ),
#                 #-- Title --#
#                 html.H1([
#                     html.Span("Welcome"),
#                     html.Br(),
#                     html.Span("WindForecast Platform")
#                 ],
#                         style={'color':'#00bdff'},
#                         className="text-center mb-4"),
#                 #-- Description --#
#                 html.P(
#                     "\
#                       This platform provides accurate wind forecasts and energy generation \
#                       insights for 10 wind farms and the SEIN system. It supports short and \
#                       long-term planning with interactive tools and clear visualizations. \
#                     ",
#                     className="text-justify mb-4",
#                 ),
#                 #-- Time range buttons --#
#                 html.H5("Forecast Range", className="mb-3"),
#                 dbc.RadioItems(
#                     id='top-buttons',
#                     className='btn-group-horizontal',
#                     inputClassName='btn-check',
#                     labelClassName="btn btn-outline-primary",
#                     labelCheckedClassName="btn btn-primary",
#                     options=[
#                         {"label": "Short Term (15 days)", "value":1,},
#                         {"label": "Long  Term (07 months)", "value":2},
#                     ],
#                     value=1,
#                 ),
#                 html.Hr(),
#                 #-- Wind Farms Section --#
#                 html.H5("WindFarms", className="mt-4", style={'color':'#00bdff'},),
#                 dbc.RadioItems(
#                     id="windfarm-buttons",
#                     options=[
#                         {"label": "SEIN", "value": "0"},
#                         {"label": "W.F. Punta Lomitas", "value": "1"},
#                         {"label": "W.F. Cupisnique", "value": "2"},
#                         {"label": "W.F. Duna", "value": "3"},
#                         {"label": "W.F. Huambos", "value": "4"},
#                         {"label": "W.F. Marcona", "value": "5"},
#                         {"label": "W.F. San Juan", "value": "6"},
#                         {"label": "W.F. Talara", "value": "7"},
#                         {"label": "W.F. Tres Hermanas", "value": "8"},
#                         {"label": "W.F. Wayra Ext.", "value": "9"},
#                         {"label": "W.F. Wayra I", "value": "10"},
#                     ],
#                     value="0",
#                     className="mb-3"
#                 ),
#             ])
#         #-- Set the width left panel --#
#         ], width=4),
#         #-- Right Panel --#
#         dbc.Col([
#             html.Br(),
#             html.H4("Monitoring KPI", className="mt-4", style={'color':'#00bdff'},),
#             dbc.Row([
#                 dbc.Col(card, width=4) for card in metric_cards
#                 ]),
#             html.H4("Forecast Wind Generation", className="mt-4", style={'color':'#00bdff'},),
#             html.H4("Forecast Wind Resource", className="mt-4", style={'color':'#00bdff'},),
#             html.H4("Resume Forecast Skill", className="mt-4", style={'color':'#00bdff'},),
#         ], width=8)
#     ])
# ],
#   # fluid=True,
#   # className='dashboard-container',

#   # style={
#   #     'width':'1400px',
#   #     'height':'2200px',
#   #     'display': 'flex',

#   #     }
# )

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=8050, debug=False)