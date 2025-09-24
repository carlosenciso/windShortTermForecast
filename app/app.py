# -*- coding:utf-8 -*-
#-----------------------------------------------------
# @Project: windShortTermForecast
# @File:    app.py
# @Author:  Carlos Enciso Ojeda
#-----------------------------------------------------
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

# =======================
# Config de pesos y grupos
# =======================
WEIGHTS_FARMS = {
    "W.F. Cupisnique": 83.15, "W.F. Duna": 18.37, "W.F. Huambos": 18.37, "W.F. Marcona": 32.0,
    "W.F. Punta Lomitas": 296.4, "W.F. San Juan": 135.7, "W.F. Talara": 30.86,
    "W.F. Tres Hermanas": 97.15, "W.F. Wayra Ext": 177.0, "W.F. Wayra I": 132.30
}
GROUPS = {
    "Costa Norte (11%)": ["W.F. Cupisnique", "W.F. Talara"],
    "Costa Sur (85%)": ["W.F. Punta Lomitas", "W.F. Marcona", "W.F. San Juan", "W.F. Tres Hermanas", "W.F. Wayra Ext", "W.F. Wayra I"],
    "Sierra Norte (4%)": ["W.F. Huambos", "W.F. Duna"],
}

# =======================
# Load Generation Dataset
# =======================
PARQUET_CANDIDATES = [
    os.environ.get("DATASET_PATH"),
    "../dataset/currentGen.parquet",
    "./dataset/currentGen.parquet",
    "/opt/render/project/dataset/currentGen.parquet",
]
parquet_path = next((p for p in PARQUET_CANDIDATES if p and os.path.exists(p)), None)
if not parquet_path:
    raise FileNotFoundError("currentGen.parquet not found")

dataset = pd.read_parquet(parquet_path)
print(f"[OK] Data loaded from: {parquet_path} | shape={dataset.shape}")

# Validaciones mínimas
expected_cols = {"name", "date", "power"}
missing = expected_cols - set(dataset.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")
dataset = dataset.copy()
dataset["date"] = pd.to_datetime(dataset["date"])

# =======================
# Load Wind Forecast Dataset
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
    if "initDate" in wind_dataset.columns:
        wind_dataset["initDate"] = pd.to_datetime(wind_dataset["initDate"], errors="coerce")
        max_initDate_por_modelo = wind_dataset.groupby('model')['initDate'].transform('max')
        wind_dataset = wind_dataset[wind_dataset['initDate'] == max_initDate_por_modelo].copy()
    wind_expected = {"name", "date", "wwind100", "model"}
    for col in wind_expected - set(wind_dataset.columns):
        wind_dataset[col] = pd.Series(dtype="float64" if col == "wwind100" else "object")
else:
    print("[WARN] windSpeedFcs.parquet not found; wind chart will be empty")
    wind_dataset = pd.DataFrame(columns=["name", "date", "wwind100", "model"])

wind_dataset = wind_dataset.copy()
wind_dataset["date"] = pd.to_datetime(wind_dataset["date"], errors="coerce")

# =======================
# App Configuration
# =======================
app = Dash(
    __name__,
    external_stylesheets=[
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
)
app.title = "ENGIE WindForecast Platform"
server = app.server

# === Mantén tus temas Bootstrap favoritos ===
LIGHT_THEME = dbc.themes.CERULEAN
DARK_THEME  = dbc.themes.SUPERHERO

# === SOLO paletas para las líneas (armonizadas con cada tema) ===
LIGHT_COLORWAY = [
    "#0d6efd",  # Azul (Costa Norte)
    "#e83e8c",  # Rosa/coral (Costa Sur)
    "#20c997",  # Verde-azulado (Sierra Centro)
    "#6f42c1",  # Púrpura (SEIN Total)
    "#fd7e14",  # Ámbar
    "#198754",  # Verde
    "#495057",  # Slate
]
DARK_COLORWAY = [
    "#7ab8ff",  # Azul claro
    "#ff8fa3",  # Rosa claro
    "#34d0ba",  # Teal claro
    "#c29ffa",  # Púrpura claro
    "#f8b26a",  # Ámbar
    "#8ce99a",  # Verde
    "#cbd5e1",  # Slate claro
]

def get_theme(dark: bool):
    colors = {
        "bg":   "#0f2537" if dark else "#ffffff",
        "text": "#ffffff" if dark else "#2c3e50",
        "grid": "#90a4b4" if dark else "#e5e7eb",
        "accent": "#00bdff" if not dark else "#8dd3ff",
    }
    template = "plotly_dark" if dark else "plotly_white"
    colorway = DARK_COLORWAY if dark else LIGHT_COLORWAY
    rs_style = dict(
        bgcolor=colors["bg"],
        activecolor=colors["accent"],
        font=dict(color=colors["text"]),
    )
    return colors, template, rs_style, colorway

# =======================
# Styling Helpers
# =======================
def apply_common_layout(fig, *, dark: bool, ytitle: str, x_dtick_ms: int, step='backward'):
    colors, template, rs_style, colorway = get_theme(dark)
    fig.update_traces(line=dict(width=2))
    fig.update_layout(
        template=template,
        colorway=colorway,             # líneas armonizadas
        plot_bgcolor=colors["bg"],
        paper_bgcolor=colors["bg"],
        font=dict(color=colors["text"]),
        xaxis=dict(
            tickfont_size=10,
            showgrid=True, gridcolor=colors["grid"], gridwidth=0.6,
            tickangle=0, tickformat="%d-%b\n%H:%M", dtick=x_dtick_ms, title=""
        ),
        yaxis=dict(
            showgrid=True, gridcolor=colors["grid"], gridwidth=0.6,
            title=dict(text=ytitle, font=dict(size=12))
        ),
        hovermode="x unified",
        margin=dict(t=5, b=50, l=10, r=10),
        autosize=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=.75),
        title=None,
        height=320
    )
    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1D", step="day", stepmode=step),
                dict(count=5, label="5D", step="day", stepmode=step),
                dict(step="all", label="all"),
            ],
            **rs_style,
        ),
    )
    return fig

# =======================
# UI Components
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

# Windfarm mapping
WINDFARM_MAPPING = {
    "0": "SEIN", "1": "W.F. Punta Lomitas", "2": "W.F. Cupisnique",
    "3": "W.F. Duna", "4": "W.F. Huambos", "5": "W.F. Marcona",
    "6": "W.F. San Juan", "7": "W.F. Talara", "8": "W.F. Tres Hermanas",
    "9": "W.F. Wayra Ext", "10": "W.F. Wayra I"
}

# =======================
# Helpers para series ponderadas por grupos
# =======================
def _weighted_series(df, names, value_col, weights):
    tmp = (df[df["name"].isin(names)]
           .assign(w=lambda x: x["name"].map(weights))
           .dropna(subset=["w"]))
    if tmp.empty:
        return pd.Series(dtype="float64")
    s = tmp.groupby("date").apply(lambda g: np.average(g[value_col], weights=g["w"]))
    s.index = pd.to_datetime(s.index)
    return s.sort_index()

def _build_group_figure(df, value_col, ytitle, dark, weights, x_dtick_ms):
    traces = []
    for gname, names in GROUPS.items():
        s = _weighted_series(df, names, value_col=value_col, weights=weights)
        traces.append(go.Scatter(x=s.index, y=s.values, mode="lines", name=gname))
    all_names = list(weights.keys())
    s_all = _weighted_series(df, all_names, value_col=value_col, weights=weights)
    traces.append(go.Scatter(x=s_all.index, y=s_all.values, mode="lines",
                             name="SEIN (Total)", line=dict(width=3)))
    fig = go.Figure(data=traces)
    fig = apply_common_layout(fig, dark=bool(dark), ytitle=ytitle, x_dtick_ms=x_dtick_ms)
    return fig

# =======================
# App Layout
# =======================
app.layout = dbc.Container([
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

        # Right Panel
        dbc.Col([
            html.Br(),
            html.H4("Monitoring KPI", className="mt-4", style={'color':'#00bdff'}),
            dbc.Row([dbc.Col(card, width=4) for card in metric_cards]),
            html.H4("Forecast Wind Generation", className="mt-4", style={'color':'#00bdff'}),
            dcc.Graph(id='genPlot', style={'height': '350px'}),
            html.H4("Forecast Wind Resource", className="mt-4", style={'color':'#00bdff'}),
            dcc.Graph(id='windPlot', style={'height': '350px'}),
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

    if windfarm_name == "SEIN":
        return _build_group_figure(dataset, value_col="power",
                                   ytitle="Wind Generation (MW)",
                                   dark=bool(dark), weights=WEIGHTS_FARMS,
                                   x_dtick_ms=18*3600*1000)

    subset = dataset.query("name == @windfarm_name").copy()
    if subset.empty:
        subset = pd.DataFrame({"date": pd.to_datetime([]), "power": []})

    fig = px.line(subset, x='date', y='power', line_shape='linear')
    fig = apply_common_layout(fig, dark=bool(dark), ytitle='Wind Generation (MW)',
                              x_dtick_ms=18*3600*1000)
    return fig

@app.callback(
    Output('windPlot', 'figure'),
    Input('windfarm-buttons', 'value'),
    Input("switch", "value"),
)
def update_wind_plot(windfarm_value, dark):
    windfarm_name = WINDFARM_MAPPING.get(windfarm_value, "SEIN")

    if windfarm_name == "SEIN":
        def _weighted_series_wind(df, names, weights):
            tmp = (df[df["name"].isin(names)]
                   .assign(w=lambda x: x["name"].map(weights))
                   .dropna(subset=["w"]))
            if tmp.empty:
                return pd.Series(dtype="float64")
            per_model = tmp.groupby(["date", "model"]).apply(
                lambda g: np.average(g["wwind100"], weights=g["w"])
            ).reset_index(name="v")
            s = per_model.groupby("date")["v"].mean()
            s.index = pd.to_datetime(s.index)
            return s.sort_index()

        traces = []
        for gname, names in GROUPS.items():
            s = _weighted_series_wind(wind_dataset, names, WEIGHTS_FARMS)
            traces.append(go.Scatter(x=s.index, y=s.values, mode="lines", name=gname))

        all_names = list(WEIGHTS_FARMS.keys())
        s_all = _weighted_series_wind(wind_dataset, all_names, WEIGHTS_FARMS)
        traces.append(go.Scatter(x=s_all.index, y=s_all.values, mode="lines",
                                 name="SEIN (Total)", line=dict(width=3)))

        fig = go.Figure(traces)
        fig = apply_common_layout(fig, dark=bool(dark), ytitle='Wind Speed (m/s)',
                                  x_dtick_ms=24*3600*1000, step='todate')
        return fig

    if not wind_dataset.empty and 'name' in wind_dataset.columns:
        subset = wind_dataset.query("name == @windfarm_name").copy()
    else:
        subset = pd.DataFrame(columns=["date", "wwind100", "model"])
        subset["date"] = pd.to_datetime(subset["date"])

    fig = px.line(subset, x='date', y='wwind100', color='model', line_shape='spline')
    fig = apply_common_layout(fig, dark=bool(dark), ytitle='Wind Speed (m/s)',
                              x_dtick_ms=24*3600*1000, step='todate')
    return fig

# =======================
# Main Execution
# =======================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
