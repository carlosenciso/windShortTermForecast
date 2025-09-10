# #-- Import modules --#
# import dash
# import pandas as pd
# from dash import Dash, html, dcc, Input, Output, State
# import dash_bootstrap_components as dbc
# import plotly.express as px
# #=======================
# #    Read Gen Dataset 
# #=======================
# dataset = pd.read_parquet('../dataset/currentGen.parquet')
# #========================
# # App & Theme Setup
# #========================
# app = Dash(
#     __name__,
#     external_stylesheets=[
#         # keep icons only; DO NOT preload a dbc theme here
#         "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
#     ],
#     assets_folder='/content/assets',
# )
# app.title = "ENGIE WindForecast Platform "

# # Choose distinct themes
# LIGHT_THEME = dbc.themes.CERULEAN
# DARK_THEME  = dbc.themes.SUPERHERO
# #========================
# # UI Bits
# #========================
# def create_metric_card(icon, title, value, change, color="primary"):
#     up = (str(change).startswith("+") or float(str(change).replace("+","").replace("%","")) >= 0)
#     trend_class = "text-success" if up else "text-danger"
#     change_txt  = f"{change}% from last month" if "%" not in str(change) else f"{change} from last month"
#     return dbc.Card([
#         dbc.CardBody([
#             html.Div([
#                 html.Div([html.I(className=f"fas {icon} fa-2x text-{color}")],
#                          className="col-3 d-flex align-items-center"),
#                 html.Div([
#                     html.H4(value, className="mb-0", style={'font-size': '32px','font-weight': 'bold'}),
#                     html.P(title, className="mb-0 text-muted"),
#                     html.Small(change_txt, className=trend_class)
#                 ], className="col-9")
#             ], className="row align-items-center")
#         ])
#     ], className="mb-3 shadow-sm")

# metric_cards = [
#     create_metric_card("fa-solid fa-wind", "m/s", "13.5", "+2.5", "primary"),
#     create_metric_card("fa-solid fa-bolt", "MW", "1,234", "+900.5", "info"),
#     create_metric_card("fa-solid fa-chart-line", "MAPE (%)", "20.2", "20", "warning"),
# ]

# color_mode_switch = html.Span(
#     [
#         dbc.Label(className="fa fa-sun", html_for="switch"),
#         dbc.Switch(id="switch", value=False, className="d-inline-block ms-1", persistence=True),
#         dbc.Label(className="fa fa-moon", html_for="switch"),
#     ],
#     className="my-2"
# )

# #========================
# # Layout
# #========================
# app.layout = dbc.Container([
#     # Theme link and state (this is what we toggle)
#     html.Link(rel="stylesheet", href=LIGHT_THEME, id="theme-link"),
#     dcc.Store(id="theme-store", data={"dark": False}),

#     dbc.Row([
#         # Left Panel
#         dbc.Col([
#             html.Div([
#                 html.Div(color_mode_switch, className='mb-3 text-end'),
#                 html.Img(
#                     src='https://upload.wikimedia.org/wikipedia/commons/8/8f/Logo-engie.svg',
#                     style={'width': '200px','margin-bottom': '20px','display': 'block','margin-left': 'auto','margin-right': 'auto'}
#                 ),
#                 html.H1([html.Span("Welcome"), html.Br(), html.Span("WindForecast Platform")],
#                         style={'color':'#00bdff'}, className="text-center mb-4"),
#                 html.P(
#                     "This platform provides accurate wind forecasts and energy generation "
#                     "insights for 10 wind farms and the SEIN system. It supports short and "
#                     "long-term planning with interactive tools and clear visualizations.",
#                     className="text-justify mb-4",
#                 ),
#                 html.H5("Forecast Range", className="mb-3"),
#                 dbc.RadioItems(
#                     id='top-buttons',
#                     className='btn-group-horizontal',
#                     inputClassName='btn-check',
#                     labelClassName="btn btn-outline-primary",
#                     labelCheckedClassName="btn btn-primary",
#                     options=[
#                         {"label": "Short Term (15 days)", "value":1},
#                         {"label": "Long  Term (07 months)", "value":2},
#                     ],
#                     value=1,
#                 ),
#                 html.Hr(),
#                 html.H5("WindFarms", className="mt-4", style={'color':'#00bdff'}),
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
#                         {"label": "W.F. Wayra Ext", "value": "9"},
#                         {"label": "W.F. Wayra I", "value": "10"},
#                     ],
#                     value="1",
#                     className="mb-3"
#                 ),
#             ])
#         ], width=4),

#         # Right Panel
#         dbc.Col([
#             html.Br(),
#             html.H4("Monitoring KPI", className="mt-4", style={'color':'#00bdff'}),
#             dbc.Row([dbc.Col(card, width=4) for card in metric_cards]),
#             html.H4("Forecast Wind Generation", className="mt-4", style={'color':'#00bdff'}),
#             dcc.Graph(id='genPlot', style={'height':'250px'}),
#             html.H4("Forecast Wind Resource", className="mt-4", style={'color':'#00bdff'}),
#             html.H4("Resume Forecast Skill", className="mt-4", style={'color':'#00bdff'}),
#         ], width=8)
#     ])
# ], fluid=True)

# #========================
# # Callbacks
# #========================
# @app.callback(
#     Output("theme-link", "href"),
#     Output("theme-store", "data"),
#     Input("switch", "value"),
#     State("theme-store", "data"),
# )
# def toggle_theme(switch_value, data):
#     dark = bool(switch_value)
#     theme_href = DARK_THEME if dark else LIGHT_THEME
#     return theme_href, {"dark": dark}

# @app.callback(
#     Output('genPlot', 'figure'),
#     Input('windfarm-buttons', 'value'),
#     Input("switch", "value"),
# )
# def updateGenPlot(windfarm_value, dark):
#     # Example data hook (replace 'dataset' with your actual DataFrame in scope)
#     windfarm_mapping = {
#         "0": "SEIN", "1": "W.F. Punta Lomitas", "2": "W.F. Cupisnique",
#         "3": "W.F. Duna", "4": "W.F. Huambos", "5": "W.F. Marcona",
#         "6": "W.F. San Juan", "7": "W.F. Talara", "8": "W.F. Tres Hermanas",
#         "9": "W.F. Wayra Ext", "10": "W.F. Wayra I"
#     }
#     windfarm_name = windfarm_mapping.get(windfarm_value, "SEIN")
#     subset = dataset.query("name==@windfarm_name").copy()  # <- ensure 'dataset' exists

#     colors = {
#         'background': '#0f2537' if dark else '#ffffff',
#         'text': '#ffffff' if dark else '#2c3e50',
#     }

#     fig = px.line(subset, x='date', y='power', line_shape='linear')
#     fig.update_traces(line=dict(width=1.2))
#     fig.update_layout(
#         template="plotly_dark" if dark else "plotly_white",
#         xaxis=dict(
#             tickfont_size=9,
#             showgrid=True, gridcolor='lightgrey', gridwidth=0.01, tickangle=0,
#             tickformat="%d-%b\n%H:%M hrs.", dtick=18*3600000, griddash='solid'
#         ),
#         yaxis=dict(showgrid=True, gridcolor='lightgrey', tickfont_size=10,
#                    gridwidth=0.01, griddash='solid', 
#                    title=dict(text='Wind Generation (MW)', font=dict(size=12))
#                    ),
#         plot_bgcolor=colors['background'],
#         paper_bgcolor=colors['background'],
#         font=dict(color=colors['text']),
#         xaxis_title='',
#         # yaxis_title='Wind Generation (MW)',
#         # width=1000, height=300,
#         legend=dict(
#             orientation='h', yanchor='bottom', y=1.05, xanchor='right', x=.8,
#             tracegroupgap=5, itemclick='toggle', itemdoubleclick='toggle'
#         ),
#         hovermode="x unified",
#         margin=dict(t=10, b=5),
#         # margin=dict(l=10, r=10, t=10, b=30),
#         autosize=True,
#     )
#     # --- range selector styles based on theme ---
#     rs_style = dict(
#         bgcolor="#000000" if dark else "#ffffff",
#         activecolor="#4169e1" if dark else "#00bdff",  # royalblue / dodgerblue
#         font=dict(color="#ffffff" if dark else "#000000"),
#     )
#     fig.update_xaxes(
#         rangeslider_visible=True,
#         rangeselector=dict(
#             buttons=[
#                 dict(count=1, label="1D", step="day", stepmode="backward"),
#                 dict(count=5, label="5D", step="day", stepmode="backward"),
#                 dict(step="all")
#             ],
#             **rs_style
#         )
#     )
#     return fig
# if __name__ == '__main__':
#     # If you're in a notebook, use JupyterDash. Otherwise:
#     app.run(host="0.0.0.0", port=8053, debug=False)


#-- Import modules --#
import dash
import pandas as pd
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import os

#=======================
#    Read Gen Dataset 
#=======================
# Ruta corregida para Render - desde la raíz del proyecto
try:
    dataset = pd.read_parquet('dataset/currentGen.parquet')
    print("Parquet file loaded successfully")
except FileNotFoundError:
    print("Parquet file not found. Creating empty dataset for testing.")
    # Dataset vacío para que no falle la app
    dataset = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=24, freq='H'),
        'name': ['W.F. Punta Lomitas'] * 24,
        'power': range(24)
    })

#========================
# App & Theme Setup
#========================
app = Dash(
    __name__,
    external_stylesheets=[
        # keep icons only; DO NOT preload a dbc theme here
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ]
    # Removido: assets_folder (Render lo maneja automáticamente)
)
app.title = "ENGIE WindForecast Platform"

# Choose distinct themes
LIGHT_THEME = dbc.themes.CERULEAN
DARK_THEME  = dbc.themes.SUPERHERO

# Server configuration for Render
server = app.server

#========================
# UI Bits
#========================
def create_metric_card(icon, title, value, change, color="primary"):
    up = (str(change).startswith("+") or float(str(change).replace("+","").replace("%","")) >= 0)
    trend_class = "text-success" if up else "text-danger"
    change_txt  = f"{change}% from last month" if "%" not in str(change) else f"{change} from last month"
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([html.I(className=f"fas {icon} fa-2x text-{color}")],
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

#========================
# Layout
#========================
app.layout = dbc.Container([
    # Theme link and state (this is what we toggle)
    html.Link(rel="stylesheet", href=LIGHT_THEME, id="theme-link"),
    dcc.Store(id="theme-store", data={"dark": False}),

    dbc.Row([
        # Left Panel
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
                    "This platform provides accurate wind forecasts and energy generation "
                    "insights for 10 wind farms and the SEIN system. It supports short and "
                    "long-term planning with interactive tools and clear visualizations.",
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
                        {"label": "Short Term (15 days)", "value":1},
                        {"label": "Long  Term (07 months)", "value":2},
                    ],
                    value=1,
                ),
                html.Hr(),
                html.H5("WindFarms", className="mt-4", style={'color':'#00bdff'}),
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
                        {"label": "W.F. Wayra Ext", "value": "9"},
                        {"label": "W.F. Wayra I", "value": "10"},
                    ],
                    value="1",
                    className="mb-3"
                ),
            ])
        ], width=4),

        # Right Panel
        dbc.Col([
            html.Br(),
            html.H4("Monitoring KPI", className="mt-4", style={'color':'#00bdff'}),
            dbc.Row([dbc.Col(card, width=4) for card in metric_cards]),
            html.H4("Forecast Wind Generation", className="mt-4", style={'color':'#00bdff'}),
            dcc.Graph(id='genPlot', style={'height':'250px'}),
            html.H4("Forecast Wind Resource", className="mt-4", style={'color':'#00bdff'}),
            html.H4("Resume Forecast Skill", className="mt-4", style={'color':'#00bdff'}),
        ], width=8)
    ])
], fluid=True)

#========================
# Callbacks
#========================
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
def updateGenPlot(windfarm_value, dark):
    # Example data hook (replace 'dataset' with your actual DataFrame in scope)
    windfarm_mapping = {
        "0": "SEIN", "1": "W.F. Punta Lomitas", "2": "W.F. Cupisnique",
        "3": "W.F. Duna", "4": "W.F. Huambos", "5": "W.F. Marcona",
        "6": "W.F. San Juan", "7": "W.F. Talara", "8": "W.F. Tres Hermanas",
        "9": "W.F. Wayra Ext", "10": "W.F. Wayra I"
    }
    windfarm_name = windfarm_mapping.get(windfarm_value, "SEIN")
    
    # Manejo seguro del dataset
    if not dataset.empty and 'name' in dataset.columns:
        subset = dataset.query("name==@windfarm_name").copy()
    else:
        # Dataset de prueba si hay problemas
        subset = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=24, freq='H'),
            'power': range(24)
        })

    colors = {
        'background': '#0f2537' if dark else '#ffffff',
        'text': '#ffffff' if dark else '#2c3e50',
    }

    fig = px.line(subset, x='date', y='power', line_shape='linear')
    fig.update_traces(line=dict(width=1.2))
    fig.update_layout(
        template="plotly_dark" if dark else "plotly_white",
        xaxis=dict(
            tickfont_size=9,
            showgrid=True, gridcolor='lightgrey', gridwidth=0.01, tickangle=0,
            tickformat="%d-%b\n%H:%M hrs.", dtick=18*3600000, griddash='solid'
        ),
        yaxis=dict(showgrid=True, gridcolor='lightgrey', tickfont_size=10,
                   gridwidth=0.01, griddash='solid', 
                   title=dict(text='Wind Generation (MW)', font=dict(size=12))
                   ),
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font=dict(color=colors['text']),
        xaxis_title='',
        hovermode="x unified",
        margin=dict(t=10, b=5),
        autosize=True,
    )
    # --- range selector styles based on theme ---
    rs_style = dict(
        bgcolor="#000000" if dark else "#ffffff",
        activecolor="#4169e1" if dark else "#00bdff",
        font=dict(color="#ffffff" if dark else "#000000"),
    )
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1D", step="day", stepmode="backward"),
                dict(count=5, label="5D", step="day", stepmode="backward"),
                dict(step="all")
            ],
            **rs_style
        )
    )
    return fig

if __name__ == '__main__':
    # Render automáticamente usa el puerto de la variable de entorno PORT
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)