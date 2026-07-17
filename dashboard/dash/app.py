"""
Dashboard Interactivo — UrbanSignal CDMX (Versión Académica)
============================================================
Prototipo minimalista y profesional de tablero interactivo usando Dash y Plotly.
Integra visualizaciones geoespaciales y estadísticas avanzadas.

Uso:
  python dashboard/dash/app.py
"""

import os
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# ─── CONFIGURACIÓN DE RUTAS ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
TABLAS_DIR = ROOT / "resultados" / "tablas"
MAPAS_DIR = ROOT / "resultados" / "mapas"

# ─── CARGA DE DATOS ──────────────────────────────────────────────────────────
try:
    df_iru = pd.read_csv(TABLAS_DIR / "indice_riesgo_urbano.csv")
    df_delitos = pd.read_csv(TABLAS_DIR / "delitos_por_alcaldia.csv")
    df_incidencias = pd.read_csv(TABLAS_DIR / "incidencias_por_alcaldia.csv")
    
    # Nuevos datasets para la versión expandida
    df_delitos_hora = pd.read_csv(TABLAS_DIR / "delitos_por_hora.csv")
    df_incidencias_hora = pd.read_csv(TABLAS_DIR / "incidencias_por_hora.csv")
    df_coeficientes = pd.read_csv(TABLAS_DIR / "coeficientes_modelo.csv")
    df_del_cat = pd.read_csv(TABLAS_DIR / "delitos_por_categoria.csv")
    df_inc_tema = pd.read_csv(TABLAS_DIR / "incidencias_por_tema.csv")
except Exception as e:
    print(f"Error cargando archivos CSV: {e}")
    print("Asegúrate de haber ejecutado todo el pipeline de análisis primero.")
    sys.exit(1)

# Limpieza básica para el dashboard
df_delitos = df_delitos[~df_delitos["alcaldia"].isin(["Desconocida", "Cdmx (Indeterminada)", "Fuera De Cdmx"])]
df_incidencias = df_incidencias[~df_incidencias["alcaldia"].isin(["Desconocida"])]
df_iru = df_iru.sort_values("IRU", ascending=False)

# ─── ESTILOS MINIMALISTAS Y ACADÉMICOS ───────────────────────────────────────
# Paleta de colores sobria y elegante
BG_COLOR = "#FAFAFA"
CARD_BG = "#FFFFFF"
TEXT_MAIN = "#2C3E50"
TEXT_MUTED = "#7F8C8D"
BORDER_COLOR = "#E0E0E0"

# Colores de acento discretos
ACCENT_BLUE = "#3498DB"
ACCENT_RED = "#E74C3C"
ACCENT_ORANGE = "#E67E22"
ACCENT_GREEN = "#2ECC71"

PLOTLY_TEMPLATE = "simple_white"

# Configuración de la App (Tema LUMEN es muy limpio y blanco)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUMEN])
app.title = "UrbanSignal CDMX"

# Estilos CSS reutilizables
card_style = {
    "backgroundColor": CARD_BG,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "24px",
    "marginBottom": "24px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.03)"
}

title_style = {"fontWeight": "700", "color": TEXT_MAIN, "fontSize": "1.1rem", "marginBottom": "5px"}
desc_style = {"color": TEXT_MUTED, "fontSize": "0.85rem", "marginBottom": "20px", "lineHeight": "1.4"}

def CardHeader(title, description):
    """Genera un encabezado consistente para cada gráfica con título y descripción."""
    return html.Div([
        html.H4(title, style=title_style),
        html.P(description, style=desc_style)
    ])

# ─── COMPONENTES DEL DASHBOARD ───────────────────────────────────────────────

navbar = dbc.NavbarSimple(
    brand=html.Span("UrbanSignal CDMX", style={"fontWeight": "bold", "letterSpacing": "1px"}),
    brand_href="#",
    color="#FFFFFF",
    dark=False,
    fluid=True,
    style={"borderBottom": f"1px solid {BORDER_COLOR}", "padding": "15px 40px", "boxShadow": "0 1px 4px rgba(0,0,0,0.02)"}
)

layout = html.Div(style={"backgroundColor": BG_COLOR, "minHeight": "100vh", "paddingBottom": "60px", "fontFamily": "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"}, children=[
    navbar,
    
    dbc.Container(fluid=True, style={"paddingX": "4%", "marginTop": "30px", "maxWidth": "1600px"}, children=[
        
        # ── TARJETAS DE RESUMEN ──
        dbc.Row([
            dbc.Col(html.Div(style=card_style, children=[
                html.H6("Total de Delitos (2024)", style={"color": TEXT_MUTED, "textTransform": "uppercase", "fontSize": "11px", "fontWeight": "bold"}),
                html.H2(f"{df_delitos['total_delitos'].sum():,}", style={"color": ACCENT_RED, "fontWeight": "bold", "margin": "0"})
            ]), xs=12, md=4),
            
            dbc.Col(html.Div(style=card_style, children=[
                html.H6("Total de Fallas Urbanas", style={"color": TEXT_MUTED, "textTransform": "uppercase", "fontSize": "11px", "fontWeight": "bold"}),
                html.H2(f"{df_incidencias['total_incidencias'].sum():,}", style={"color": ACCENT_BLUE, "fontWeight": "bold", "margin": "0"})
            ]), xs=12, md=4),
            
            dbc.Col(html.Div(style=card_style, children=[
                html.H6("Alcaldía con Mayor Riesgo (IRU)", style={"color": TEXT_MUTED, "textTransform": "uppercase", "fontSize": "11px", "fontWeight": "bold"}),
                html.H2(f"{df_iru.iloc[0]['alcaldia_norm']}", style={"color": ACCENT_ORANGE, "fontWeight": "bold", "margin": "0"}),
                html.P(f"Índice de Riesgo: {df_iru.iloc[0]['IRU']:.1f} / 100", style={"color": TEXT_MAIN, "margin": "0", "fontSize": "13px"})
            ]), xs=12, md=4),
        ]),

        # ── VISOR DE MAPAS (FOLIUM) ──
        dbc.Row([
            dbc.Col(html.Div(style=card_style, children=[
                CardHeader(
                    "Análisis Espacial (Visor Cartográfico)", 
                    "Explora interactivamente la distribución del riesgo, los clústers críticos y las áreas de calor en la ciudad."
                ),
                dcc.Dropdown(
                    id="dropdown-mapa",
                    options=[
                        {"label": "Índice de Riesgo Urbano (Coroplético)", "value": "mapa_riesgo_coropletico.html"},
                        {"label": "Zonas Críticas de Alta Densidad (DBSCAN)", "value": "mapa_clusters_dbscan.html"},
                        {"label": "Macro-Zonas Predictivas (K-Means)", "value": "mapa_clusters_criticos.html"},
                        {"label": "Clusters de Autocorrelación Espacial (LISA)", "value": "mapa_lisa_clusters.html"},
                        {"label": "Comparativo: Delitos vs Fallas (Heatmap)", "value": "mapa_comparativo_incidencias_delitos.html"}
                    ],
                    value="mapa_riesgo_coropletico.html",
                    clearable=False,
                    style={"marginBottom": "20px", "width": "50%"}
                ),
                html.Iframe(
                    id="iframe-mapa",
                    style={"width": "100%", "height": "600px", "border": f"1px solid {BORDER_COLOR}", "borderRadius": "4px"}
                )
            ]), xs=12, lg=12)
        ]),
        
        # ── TENDENCIA TEMPORAL Y CATEGORÍAS ──
        dbc.Row([
            dbc.Col(html.Div(style=card_style, children=[
                CardHeader(
                    "Distribución Temporal de la Demanda", 
                    "Muestra cómo los reportes de infraestructura y la incidencia delictiva fluctúan a lo largo del día. Destaca el solapamiento nocturno."
                ),
                dcc.Graph(id="grafica-tendencia-temporal")
            ]), xs=12, lg=7),
            
            dbc.Col(html.Div(style=card_style, children=[
                CardHeader(
                    "Top 5: Problemas Urbanos y Delitos", 
                    "Desglose de las principales quejas ciudadanas en Locatel frente a los delitos con mayor volumen en la FGJ."
                ),
                dcc.Graph(id="grafica-categorias")
            ]), xs=12, lg=5)
        ]),
        
        # ── MODELO PREDICTIVO E ÍNDICE DE RIESGO ──
        dbc.Row([
            dbc.Col(html.Div(style=card_style, children=[
                CardHeader(
                    "Impacto de la Infraestructura en el Crimen", 
                    "Coeficientes de Regresión Binomial Negativa (IRR). Valores positivos indican que dicha falla urbana aumenta el riesgo delictivo en la colonia."
                ),
                dcc.Graph(id="grafica-modelo")
            ]), xs=12, lg=6),
            
            dbc.Col(html.Div(style=card_style, children=[
                CardHeader(
                    "Desglose del Índice de Riesgo Urbano (IRU)", 
                    "Ranking de las 16 alcaldías según su vulnerabilidad combinada (escala 0-100), normalizada por población y autocorrelación."
                ),
                dcc.Graph(id="grafica-iru")
            ]), xs=12, lg=6)
        ]),
        
        # ── RELACIONES BIVARIADAS ──
        dbc.Row([
            dbc.Col(html.Div(style=card_style, children=[
                CardHeader(
                    "Correlación: Infraestructura vs Crimen", 
                    "Relación lineal positiva que sugiere una asociación directa entre las tasas de fallas reportadas y la actividad criminal."
                ),
                dcc.Dropdown(
                    id="dropdown-variable",
                    options=[
                        {"label": "Tasas por 1,000 habitantes (Normalizado)", "value": "tasas"},
                        {"label": "Totales absolutos", "value": "totales"}
                    ],
                    value="tasas",
                    clearable=False,
                    style={"marginBottom": "15px", "width": "60%"}
                ),
                dcc.Graph(id="grafica-dispersion")
            ]), xs=12, lg=6),
            
            dbc.Col(html.Div(style=card_style, children=[
                CardHeader(
                    "Incidencia Delictiva Nocturna (20:00 - 05:00 hrs)", 
                    "Proporción de delitos que ocurren en horarios de vulnerabilidad lumínica por cada 1,000 habitantes."
                ),
                dcc.Graph(id="grafica-nocturnos")
            ]), xs=12, lg=6)
        ]),
        
        # ── PIE DE PÁGINA ──
        html.Div(
            html.Small("Laboratorio de Inteligencia Geo-Espacial y Cómputo Móvil (GeoDataX) | Investigación DELFIN 2026"),
            style={"textAlign": "center", "color": TEXT_MUTED, "marginTop": "20px"}
        )
    ])
])

app.layout = layout

# ─── CALLBACKS PARA COMPONENTES DINÁMICOS ────────────────────────────────────

@app.callback(
    Output("iframe-mapa", "srcDoc"),
    Input("dropdown-mapa", "value")
)
def update_map(map_filename):
    """Carga el código HTML del mapa de Folium seleccionado."""
    map_path = MAPAS_DIR / map_filename
    if map_path.exists():
        with open(map_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"<h3 style='font-family:sans-serif; color:red; padding:20px;'>Error: No se encontró el mapa {map_filename}</h3>"


@app.callback(
    Output("grafica-tendencia-temporal", "figure"),
    Input("grafica-tendencia-temporal", "id")
)
def render_tendencia(_):
    """Genera la gráfica de líneas para tendencias por hora."""
    # Normalizar ambas series para poder compararlas en el mismo eje (Min-Max scaling)
    df_del_h = df_delitos_hora.copy()
    df_inc_h = df_incidencias_hora.copy()
    
    df_del_h["norm"] = df_del_h["total_delitos"] / df_del_h["total_delitos"].max()
    df_inc_h["norm"] = df_inc_h["total_incidencias"] / df_inc_h["total_incidencias"].max()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_del_h["hora"], y=df_del_h["norm"],
        mode="lines", name="Delitos (FGJ)", line=dict(color=ACCENT_RED, width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df_inc_h["hora"], y=df_inc_h["norm"],
        mode="lines", name="Fallas Urbanas (Locatel)", line=dict(color=ACCENT_BLUE, width=3)
    ))
    
    # Resaltar la franja nocturna
    fig.add_vrect(x0=20, x1=23, fillcolor="rgba(0,0,0,0.05)", layer="below", line_width=0)
    fig.add_vrect(x0=0, x1=5, fillcolor="rgba(0,0,0,0.05)", layer="below", line_width=0, annotation_text="Franja Nocturna", annotation_position="top left")

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=20, r=20, t=10, b=30),
        xaxis_title="Hora del día (0-23)",
        yaxis_title="Volumen (Normalizado)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    return fig


@app.callback(
    Output("grafica-categorias", "figure"),
    Input("grafica-categorias", "id")
)
def render_categorias(_):
    """Genera dos gráficas de dona mostrando top categorías."""
    top_del = df_del_cat.head(5)
    # Excluir 'OTRO' para tener una vista más representativa si existe
    top_inc = df_inc_tema[df_inc_tema["tema"] != "OTRO"].head(5)
    
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]], subplot_titles=["Delitos Frecuentes", "Reportes Urbanos"])
    
    fig.add_trace(go.Pie(labels=top_del["categoria"], values=top_del["total_delitos"], hole=.4, 
                         marker_colors=[ACCENT_RED, "#f1948a", "#f5b7b1", "#fadbd8", "#fdedec"],
                         textposition='inside', textinfo='percent'), 1, 1)
                         
    fig.add_trace(go.Pie(labels=top_inc["tema"], values=top_inc["total_incidencias"], hole=.4, 
                         marker_colors=[ACCENT_BLUE, "#85c1e9", "#aed6f1", "#d6eaf8", "#ebf5fb"],
                         textposition='inside', textinfo='percent'), 1, 2)

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        annotations=[dict(text="FGJ", x=0.22, y=0.5, font_size=12, showarrow=False),
                     dict(text="Locatel", x=0.78, y=0.5, font_size=12, showarrow=False)]
    )
    return fig


@app.callback(
    Output("grafica-modelo", "figure"),
    Input("grafica-modelo", "id")
)
def render_modelo(_):
    """Gráfico de barras horizontales divergente para los coeficientes IRR."""
    df_coef = df_coeficientes[~df_coeficientes["variable"].isin(["Intercept", "const", "alpha"])].copy()
    # Calcular IRR (Incidence Rate Ratio)
    if "exp_coef_IRR" in df_coef.columns:
        df_coef["IRR"] = df_coef["exp_coef_IRR"]
    elif "coeficiente" in df_coef.columns:
        df_coef["IRR"] = np.exp(df_coef["coeficiente"])
    else:
        df_coef["IRR"] = 1.0 # Fallback si falla la columna
        
    # Calcular % de cambio: (IRR - 1) * 100
    df_coef["impacto_pct"] = (df_coef["IRR"] - 1) * 100
    df_coef = df_coef.sort_values("impacto_pct", ascending=True)
    
    colors = [ACCENT_RED if val > 0 else ACCENT_GREEN for val in df_coef["impacto_pct"]]
    
    fig = px.bar(
        df_coef, 
        y="variable", 
        x="impacto_pct", 
        orientation="h",
        text="impacto_pct",
        color_discrete_sequence=[ACCENT_RED] # Fallback, se sobreescribe abajo
    )
    
    fig.update_traces(marker_color=colors, texttemplate='%{text:+.1f}%', textposition='outside')
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=20, r=40, t=10, b=40),
        xaxis_title="Efecto sobre Tasa Delictiva (%)",
        yaxis_title="",
        xaxis=dict(showgrid=True, gridcolor=BORDER_COLOR),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    # Agregar línea base (0%)
    fig.add_vline(x=0, line_width=1, line_color=TEXT_MAIN)
    return fig


@app.callback(
    Output("grafica-iru", "figure"),
    Input("grafica-iru", "id") 
)
def update_iru(_):
    color_map = {"Muy Alto": ACCENT_RED, "Alto": ACCENT_ORANGE, "Medio": "#F1C40F", "Bajo": ACCENT_GREEN}
    
    fig = px.bar(
        df_iru, 
        x="alcaldia_norm", 
        y="IRU", 
        color="nivel_riesgo",
        color_discrete_map=color_map,
        labels={"alcaldia_norm": "Alcaldía", "IRU": "Valor IRU", "nivel_riesgo": "Nivel"}
    )
    
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=20, r=20, t=10, b=40),
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


@app.callback(
    Output("grafica-dispersion", "figure"),
    Input("dropdown-variable", "value")
)
def update_scatter(tipo):
    if tipo == "tasas":
        x_col = "tasa_alumbrado"
        y_col = "tasa_delitos"
        x_label = "Fallas de Alumbrado (por 1k hab)"
        y_label = "Delitos Totales (por 1k hab)"
    else:
        x_col = "total_alumbrado"
        y_col = "total_delitos"
        x_label = "Total Fallas Alumbrado"
        y_label = "Total Delitos"
        
    fig = px.scatter(
        df_iru,
        x=x_col,
        y=y_col,
        text="alcaldia_norm",
        size="poblacion",
        color="IRU",
        color_continuous_scale="Reds",
        labels={x_col: x_label, y_col: y_label}
    )
    
    fig.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(showgrid=True, gridcolor=BORDER_COLOR),
        yaxis=dict(showgrid=True, gridcolor=BORDER_COLOR),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
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
        labels={"alcaldia_norm": "", "tasa_delitos_nocturnos": "Tasa (por 1k hab)", "prop_nocturnos": "% del Total"}
    )
    
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=20, r=20, t=10, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig

# ─── EJECUCIÓN ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Iniciando Dashboard Académico en: http://127.0.0.1:8050")
    app.run(debug=True, port=8050)
