"""
Dashboard Interactivo — UrbanSignal CDMX
========================================
Prototipo funcional de tablero interactivo usando Dash y Plotly.
Visualiza el Índice de Riesgo Urbano (IRU), delitos e incidencias por alcaldía.

Uso:
  python dashboard/dash/app.py
"""

import os
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# ─── CONFIGURACIÓN DE RUTAS ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
TABLAS_DIR = ROOT / "resultados" / "tablas"

# Verificar existencia de archivos
archivo_iru = TABLAS_DIR / "indice_riesgo_urbano.csv"
archivo_delitos = TABLAS_DIR / "delitos_por_alcaldia.csv"
archivo_incidencias = TABLAS_DIR / "incidencias_por_alcaldia.csv"

if not archivo_iru.exists() or not archivo_delitos.exists() or not archivo_incidencias.exists():
    print("Error: No se encontraron los archivos CSV en resultados/tablas/")
    print("Asegúrate de haber ejecutado los scripts de análisis exploratorio y del IRU.")
    sys.exit(1)

# ─── CARGA DE DATOS ──────────────────────────────────────────────────────────
df_iru = pd.read_csv(archivo_iru)
df_delitos = pd.read_csv(archivo_delitos)
df_incidencias = pd.read_csv(archivo_incidencias)

# Limpieza básica para el dashboard
df_delitos = df_delitos[~df_delitos["alcaldia"].isin(["Desconocida", "Cdmx (Indeterminada)", "Fuera De Cdmx"])]
df_incidencias = df_incidencias[~df_incidencias["alcaldia"].isin(["Desconocida"])]

# Ordenar IRU
df_iru = df_iru.sort_values("IRU", ascending=False)

# ─── ESTILOS (Dark Mode & Glassmorphism) ─────────────────────────────────────
DARK_BG = "#0F1117"
PANEL_BG = "#1A1D27"
BORDER = "#2E3347"
TEXT = "#E0E0E0"
MUTED = "#A0AABF"
PURPLE = "#7C5CFC"
CYAN = "#00D9A3"
RED = "#FF6B6B"
ORANGE = "#FFB347"

PLOTLY_TEMPLATE = "plotly_dark"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "UrbanSignal CDMX Dashboard"

# Estilos CSS en línea para tarjetas glassmorphism
card_style = {
    "backgroundColor": "rgba(26, 29, 39, 0.7)",
    "backdropFilter": "blur(10px)",
    "WebkitBackdropFilter": "blur(10px)",
    "border": f"1px solid {BORDER}",
    "borderRadius": "12px",
    "boxShadow": "0 8px 32px 0 rgba(0, 0, 0, 0.3)",
    "padding": "20px",
    "marginBottom": "20px",
    "color": TEXT
}

# ─── COMPONENTES DEL DASHBOARD ───────────────────────────────────────────────

navbar = dbc.NavbarSimple(
    brand="UrbanSignal CDMX: Infraestructura y Crimen",
    brand_href="#",
    color=PANEL_BG,
    dark=True,
    fluid=True,
    style={"borderBottom": f"1px solid {BORDER}", "padding": "10px 20px"}
)

layout = html.Div(style={"backgroundColor": DARK_BG, "minHeight": "100vh", "paddingBottom": "50px"}, children=[
    navbar,
    
    dbc.Container(fluid=True, style={"marginTop": "30px", "paddingX": "40px"}, children=[
        
        # Tarjetas de Resumen
        dbc.Row([
            dbc.Col(html.Div(style=card_style, children=[
                html.H6("Total de Delitos (2024)", style={"color": MUTED, "textTransform": "uppercase", "fontSize": "12px"}),
                html.H2(f"{df_delitos['total_delitos'].sum():,}", style={"color": RED, "fontWeight": "bold", "margin": "0"})
            ]), width=4),
            
            dbc.Col(html.Div(style=card_style, children=[
                html.H6("Total Incidencias Urbanas (Locatel)", style={"color": MUTED, "textTransform": "uppercase", "fontSize": "12px"}),
                html.H2(f"{df_incidencias['total_incidencias'].sum():,}", style={"color": PURPLE, "fontWeight": "bold", "margin": "0"})
            ]), width=4),
            
            dbc.Col(html.Div(style=card_style, children=[
                html.H6("Alcaldía Mayor Riesgo (IRU)", style={"color": MUTED, "textTransform": "uppercase", "fontSize": "12px"}),
                html.H2(f"{df_iru.iloc[0]['alcaldia_norm']}", style={"color": ORANGE, "fontWeight": "bold", "margin": "0"}),
                html.P(f"IRU: {df_iru.iloc[0]['IRU']:.1f}", style={"color": TEXT, "margin": "0", "fontSize": "14px"})
            ]), width=4),
        ]),
        
        # Gráficas Principales
        dbc.Row([
            dbc.Col(html.Div(style=card_style, children=[
                html.H5("Índice de Riesgo Urbano (IRU) por Alcaldía", style={"fontWeight": "bold", "marginBottom": "20px"}),
                dcc.Graph(id="grafica-iru")
            ]), width=12)
        ]),
        
        dbc.Row([
            dbc.Col(html.Div(style=card_style, children=[
                html.H5("Comparativo: Delitos vs Incidencias", style={"fontWeight": "bold", "marginBottom": "20px"}),
                dcc.Dropdown(
                    id="dropdown-variable",
                    options=[
                        {"label": "Tasas por 1,000 habitantes", "value": "tasas"},
                        {"label": "Totales absolutos", "value": "totales"}
                    ],
                    value="tasas",
                    clearable=False,
                    style={"color": "#000", "marginBottom": "20px"}
                ),
                dcc.Graph(id="grafica-dispersion")
            ]), width=6),
            
            dbc.Col(html.Div(style=card_style, children=[
                html.H5("Tasa de Delitos Nocturnos", style={"fontWeight": "bold", "marginBottom": "20px"}),
                dcc.Graph(id="grafica-nocturnos")
            ]), width=6)
        ]),
        
        # Pie de página
        html.Div(
            "Proyecto de Investigación DELFIN 2026 | Johanna Prieto | Laboratorio de Inteligencia Artificial Geoespacial",
            style={"textAlign": "center", "color": MUTED, "marginTop": "40px", "fontSize": "14px"}
        )
    ])
])

app.layout = layout

# ─── CALLBACKS ───────────────────────────────────────────────────────────────

@app.callback(
    Output("grafica-iru", "figure"),
    Input("grafica-iru", "id") # Dummy input
)
def update_iru(_):
    # Asignar color según nivel de riesgo
    color_map = {"Muy Alto": RED, "Alto": ORANGE, "Medio": "#F1C40F", "Bajo": CYAN}
    
    fig = px.bar(
        df_iru, 
        x="alcaldia_norm", 
        y="IRU", 
        color="nivel_riesgo",
        color_discrete_map=color_map,
        labels={"alcaldia_norm": "Alcaldía", "IRU": "Índice de Riesgo (0-100)", "nivel_riesgo": "Nivel"},
        hover_data={"alcaldia_norm": False, "IRU": ":.1f", "tasa_delitos": ":.1f"}
    )
    
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=80),
        xaxis_tickangle=-45,
        font_color=TEXT
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDER)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=BORDER)
    
    return fig


@app.callback(
    Output("grafica-dispersion", "figure"),
    Input("dropdown-variable", "value")
)
def update_scatter(tipo):
    if tipo == "tasas":
        x_col = "tasa_alumbrado"
        y_col = "tasa_delitos"
        x_label = "Tasa Fallas Alumbrado (por 1k hab)"
        y_label = "Tasa Delitos (por 1k hab)"
        title = "Tasa Alumbrado vs Tasa Delitos"
    else:
        x_col = "total_alumbrado"
        y_col = "total_delitos"
        x_label = "Total Fallas Alumbrado"
        y_label = "Total Delitos"
        title = "Total Alumbrado vs Total Delitos"
        
    fig = px.scatter(
        df_iru,
        x=x_col,
        y=y_col,
        text="alcaldia_norm",
        size="poblacion",
        color="IRU",
        color_continuous_scale="Viridis",
        labels={x_col: x_label, y_col: y_label}
    )
    
    fig.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='White')))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        font_color=TEXT
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=BORDER)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=BORDER)
    
    return fig


@app.callback(
    Output("grafica-nocturnos", "figure"),
    Input("grafica-nocturnos", "id")
)
def update_nocturnos(_):
    df_sorted = df_iru.sort_values("tasa_delitos_nocturnos", ascending=True)
    
    fig = px.bar(
        df_sorted,
        y="alcaldia_norm",
        x="tasa_delitos_nocturnos",
        orientation="h",
        color="prop_nocturnos",
        color_continuous_scale="Reds",
        labels={"alcaldia_norm": "Alcaldía", "tasa_delitos_nocturnos": "Delitos Nocturnos / 1k hab", "prop_nocturnos": "% Nocturnos"}
    )
    
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        font_color=TEXT
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=BORDER)
    fig.update_yaxes(showgrid=False)
    
    return fig

# ─── EJECUCIÓN ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Iniciando dashboard en: http://127.0.0.1:8050")
    app.run(debug=True, port=8050)
