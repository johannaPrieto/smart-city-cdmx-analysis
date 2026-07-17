"""
Generación de Mapas Interactivos — Smart City CDMX
====================================================
Genera mapas de calor con Folium a partir de coordenadas georreferenciadas.

Salidas:
  - resultados/mapas/mapa_incidencias_locatel.html
  - resultados/mapas/mapa_delitos_fgj.html
  - resultados/mapas/mapa_comparativo_incidencias_delitos.html

Uso:
  python scripts/visualizacion/generar_mapas.py
"""

import io
import sys
from pathlib import Path

# Forzar UTF-8 en stdout para Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import folium
from folium.plugins import HeatMap
import pandas as pd

# ─── Configuración ───────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "datasets" / "processed"
MAPAS_DIR = ROOT / "resultados" / "mapas"
MAPAS_DIR.mkdir(parents=True, exist_ok=True)

# Centro de CDMX (Ajustado para mejor encuadre)
CDMX_CENTER = [19.38, -99.14]
ZOOM_DEFAULT = 11

# Temas urbanos clave (fallas de infraestructura)
TEMAS_URBANOS = [
    "ALUMBRADO",
    "FALTA DE AGUA",
    "FUGA DE AGUA",
    "BACHEO",
    "DESAZOLVE",
    "MANTENIMIENTO VÍA PÚBLICA",
    "MANTENIMIENTO DE COLADERA / ALCANTARILLA",
    "PODA / RETIRO ARBOL",
    "RETIRO CASCAJO, ESCOMBRO, AZOLVE, RAMAS",
    "BARBECHO / CHAPONEO",
    "MANTENIMIENTO PARQUE / AREA VERDE",
    "LIMPIEZA VIA PUBLICA",
    "RECOLECCIÓN BASURA",
    "VEHÍCULO ABANDONADO / CHATARRIZACION",
]

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

body {
    font-family: 'Inter', sans-serif !important;
    background-color: #0f1117;
}

/* Glassmorphism Title */
.modern-title {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    background: rgba(20, 22, 30, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 15px 35px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #ffffff;
    text-align: center;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    animation: fadeInDown 0.8s ease-out;
}
.modern-title h1 {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.modern-title p {
    margin: 4px 0 0 0;
    font-size: 12px;
    color: #A0AABF;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Stat Cards */
.stat-cards-container {
    position: fixed;
    top: 20px;
    left: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 12px;
    animation: fadeInLeft 0.8s ease-out;
}
.stat-card {
    background: rgba(20, 22, 30, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 12px 18px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: white;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    gap: 15px;
    transition: transform 0.2s ease, background 0.2s ease;
    min-width: 180px;
}
.stat-card:hover {
    transform: translateX(5px);
    background: rgba(30, 33, 45, 0.85);
}
.stat-icon {
    font-size: 22px;
    opacity: 0.9;
}
.stat-info h4 {
    margin: 0;
    font-size: 10px;
    color: #A0AABF;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}
.stat-info p {
    margin: 2px 0 0 0;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.5px;
}

/* Layer Control Overrides */
.leaflet-control-layers {
    background: rgba(20, 22, 30, 0.85) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    color: #E0E0E0 !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    padding: 10px !important;
    animation: fadeInRight 0.8s ease-out;
}
.leaflet-control-layers-expanded {
    padding: 16px 20px !important;
    min-width: 220px;
}
.leaflet-control-layers-overlays label {
    margin-bottom: 10px !important;
    display: flex !important;
    align-items: center !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    cursor: pointer !important;
    transition: color 0.2s;
}
.leaflet-control-layers-overlays label:hover {
    color: #ffffff !important;
}
.leaflet-control-layers input[type="checkbox"] {
    appearance: none;
    background-color: rgba(255,255,255,0.05);
    margin: 0 12px 0 0 !important;
    font: inherit;
    color: currentColor;
    width: 18px;
    height: 18px;
    border-radius: 5px;
    display: grid;
    place-content: center;
    border: 1px solid rgba(255, 255, 255, 0.2);
    cursor: pointer;
    transition: all 0.2s;
}
.leaflet-control-layers input[type="checkbox"]::before {
    content: "";
    width: 10px;
    height: 10px;
    transform: scale(0);
    transition: 120ms transform ease-in-out;
    box-shadow: inset 1em 1em white;
    background-color: white;
    transform-origin: center;
    clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
}
.leaflet-control-layers input[type="checkbox"]:checked {
    background-color: #3b82f6; /* Default blue, can be overridden */
    border-color: #3b82f6;
}
.leaflet-control-layers input[type="checkbox"]:checked::before {
    transform: scale(1);
}
.leaflet-control-layers-separator {
    border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
    margin: 12px 0 !important;
}

/* Custom Legend & Info Cards */
.modern-legend {
    position: fixed;
    bottom: 30px;
    right: 20px;
    z-index: 9999;
    background: rgba(20, 22, 30, 0.85);
    backdrop-filter: blur(12px);
    padding: 15px 20px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #E0E0E0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    font-family: 'Inter', sans-serif;
    animation: fadeInUp 0.8s ease-out;
    width: 220px;
    transition: transform 0.2s;
}
.modern-legend:hover {
    transform: translateY(-5px);
}
.modern-legend h4 {
    margin: 0 0 12px 0;
    font-size: 12px;
    color: #ffffff;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.legend-gradient {
    height: 6px;
    border-radius: 3px;
    margin-bottom: 8px;
    width: 100%;
}
.legend-labels {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #A0AABF;
    font-weight: 600;
}

.modern-guide {
    position: fixed;
    bottom: 30px;
    left: 20px;
    z-index: 9999;
    background: rgba(20, 22, 30, 0.85);
    backdrop-filter: blur(12px);
    padding: 18px 22px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #A0AABF;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    line-height: 1.6;
    animation: fadeInUp 0.8s ease-out;
    max-width: 280px;
    transition: transform 0.2s;
}
.modern-guide:hover {
    transform: translateY(-5px);
}
.modern-guide h4 {
    margin: 0 0 10px 0;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
}
.modern-guide p {
    margin: 0;
}

/* Animations */
@keyframes fadeInDown {
    from { opacity: 0; transform: translate(-50%, -20px); }
    to { opacity: 1; transform: translate(-50%, 0); }
}
@keyframes fadeInLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes fadeInRight {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
"""

def crear_mapa_base(titulo="", subtitulo="", stats=None):
    """Crea un mapa base con estilo oscuro centrado en CDMX."""
    m = folium.Map(
        location=CDMX_CENTER,
        zoom_start=ZOOM_DEFAULT,
        tiles="CartoDB dark_matter",
        control_scale=True,
        prefer_canvas=True,
    )

    m.get_root().html.add_child(folium.Element(GLOBAL_CSS))

    if titulo:
        titulo_html = f"""
        <div class="modern-title">
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(titulo_html))

    if stats:
        cards_html = '<div class="stat-cards-container">'
        for stat in stats:
            val = f"{stat['value']:,}" if isinstance(stat['value'], (int, float)) else stat['value']
            cards_html += f"""
            <div class="stat-card">
                <div class="stat-icon">{stat['icon']}</div>
                <div class="stat-info">
                    <h4>{stat['label']}</h4>
                    <p>{val}</p>
                </div>
            </div>
            """
        cards_html += '</div>'
        m.get_root().html.add_child(folium.Element(cards_html))

    return m

def filtrar_coords_validas(df, lat_col="latitud", lon_col="longitud"):
    """Filtra registros con coordenadas válidas dentro del valle de México."""
    mask = (
        df[lat_col].notna()
        & df[lon_col].notna()
        & (df[lat_col] > 19.0) & (df[lat_col] < 19.8)
        & (df[lon_col] > -99.5) & (df[lon_col] < -98.8)
    )
    return df[mask]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. MAPA DE INCIDENCIAS LOCATEL
# ═══════════════════════════════════════════════════════════════════════════════
def mapa_incidencias_locatel():
    """Mapa de calor de incidencias urbanas (Locatel 0311)."""
    print("[MAPA 1] Generando mapa de incidencias Locatel...")

    df = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")

    df_urbano = df[df["tema_solicitud"].isin(TEMAS_URBANOS)]
    df_geo = filtrar_coords_validas(df_urbano)
    total_geo = len(df_geo)
    print(f"   Registros urbanos con georeferencia: {total_geo:,}")

    m = crear_mapa_base(
        titulo="Incidencias Urbanas Locatel", 
        subtitulo="Ciudad de México • 2024",
        stats=[
            {"icon": "📍", "label": "Registros Geo", "value": total_geo},
            {"icon": "🚧", "label": "Temas Urbanos", "value": len(TEMAS_URBANOS)}
        ]
    )

    # Añadir CSS para color de checkboxes
    m.get_root().html.add_child(folium.Element("<style>.leaflet-control-layers input[type='checkbox']:checked { background-color: #00E676; border-color: #00E676; }</style>"))

    coords = df_geo[["latitud", "longitud"]].values.tolist()
    HeatMap(
        coords,
        name="Todas las incidencias urbanas",
        radius=7,
        blur=10,
        min_opacity=0.3,
        max_zoom=15,
        gradient={0.4: "#00E676", 0.7: "#69F0AE", 1.0: "#B9F6CA"},
    ).add_to(m)

    temas_principales = ["ALUMBRADO", "FALTA DE AGUA", "BACHEO", "FUGA DE AGUA"]
    colores_temas = {
        "ALUMBRADO": {0.4: "#F57F17", 0.7: "#FBC02D", 1.0: "#FFF59D"},
        "FALTA DE AGUA": {0.4: "#01579B", 0.7: "#0288D1", 1.0: "#81D4FA"},
        "BACHEO": {0.4: "#33691E", 0.7: "#558B2F", 1.0: "#AED581"},
        "FUGA DE AGUA": {0.4: "#006064", 0.7: "#0097A7", 1.0: "#80DEEA"},
    }
    for tema in temas_principales:
        sub = df_geo[df_geo["tema_solicitud"] == tema]
        if len(sub) > 0:
            fg = folium.FeatureGroup(name=f"{tema} ({len(sub):,})", show=False)
            HeatMap(
                sub[["latitud", "longitud"]].values.tolist(),
                radius=8,
                blur=12,
                min_opacity=0.3,
                max_zoom=15,
                gradient=colores_temas.get(tema, {0.4: "#7C5CFC", 1.0: "#E040FB"}),
            ).add_to(fg)
            fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    legend_html = """
    <div class="modern-legend">
        <h4>Densidad de Incidencias</h4>
        <div class="legend-gradient" style="background: linear-gradient(to right, rgba(0,230,118,0), #00E676, #69F0AE, #B9F6CA);"></div>
        <div class="legend-labels">
            <span>Baja</span>
            <span>Media</span>
            <span>Alta</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    ruta = MAPAS_DIR / "mapa_incidencias_locatel.html"
    m.save(str(ruta))
    print(f"   OK: {ruta.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MAPA DE DELITOS FGJ
# ═══════════════════════════════════════════════════════════════════════════════
def mapa_delitos_fgj():
    """Mapa de calor de carpetas de investigación (FGJ)."""
    print("[MAPA 2] Generando mapa de delitos FGJ...")

    df = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")
    df_geo = filtrar_coords_validas(df)
    total_geo = len(df_geo)
    print(f"   Registros con georeferencia: {total_geo:,}")

    m = crear_mapa_base(
        titulo="Carpetas de Investigación FGJ", 
        subtitulo="Ciudad de México • 2024",
        stats=[
            {"icon": "🚨", "label": "Total Delitos", "value": total_geo},
            {"icon": "📅", "label": "Periodo", "value": "2024"}
        ]
    )

    # Añadir CSS para color de checkboxes
    m.get_root().html.add_child(folium.Element("<style>.leaflet-control-layers input[type='checkbox']:checked { background-color: #FF5252; border-color: #FF5252; }</style>"))

    coords = df_geo[["latitud", "longitud"]].values.tolist()
    HeatMap(
        coords,
        name="Todos los delitos",
        radius=6,
        blur=9,
        min_opacity=0.3,
        max_zoom=15,
        gradient={0.4: "#D50000", 0.7: "#FF5252", 1.0: "#FF8A80"},
    ).add_to(m)

    categorias_clave = {
        "ROBO A TRANSEUNTE EN VÍA PÚBLICA CON Y SIN VIOLENCIA": "Robo a transeúnte",
        "ROBO DE VEHÍCULO CON Y SIN VIOLENCIA": "Robo de vehículo",
        "HOMICIDIO DOLOSO": "Homicidio doloso",
        "VIOLACIÓN": "Violación",
    }
    for cat_original, cat_label in categorias_clave.items():
        sub = df_geo[df_geo["categoria_delito"] == cat_original]
        if len(sub) > 0:
            fg = folium.FeatureGroup(name=f"{cat_label} ({len(sub):,})", show=False)
            HeatMap(
                sub[["latitud", "longitud"]].values.tolist(),
                radius=8,
                blur=12,
                min_opacity=0.3,
                max_zoom=15,
                gradient={0.4: "#D50000", 0.7: "#FF5252", 1.0: "#FF8A80"}
            ).add_to(fg)
            fg.add_to(m)

    df_geo["hora"] = pd.to_datetime(df_geo["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    nocturnos = df_geo[(df_geo["hora"] >= 20) | (df_geo["hora"] <= 5)]
    fg_noche = folium.FeatureGroup(name=f"Delitos nocturnos 20-05h ({len(nocturnos):,})", show=False)
    HeatMap(
        nocturnos[["latitud", "longitud"]].values.tolist(),
        radius=7,
        blur=10,
        min_opacity=0.3,
        max_zoom=15,
        gradient={0.4: "#4A148C", 0.7: "#7B1FA2", 1.0: "#E040FB"},
    ).add_to(fg_noche)
    fg_noche.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    legend_html = """
    <div class="modern-legend">
        <h4>Densidad de Delitos</h4>
        <div class="legend-gradient" style="background: linear-gradient(to right, rgba(213,0,0,0), #D50000, #FF5252, #FF8A80);"></div>
        <div class="legend-labels">
            <span>Baja</span>
            <span>Media</span>
            <span>Alta</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    ruta = MAPAS_DIR / "mapa_delitos_fgj.html"
    m.save(str(ruta))
    print(f"   OK: {ruta.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MAPA COMPARATIVO
# ═══════════════════════════════════════════════════════════════════════════════
def mapa_comparativo():
    """Mapa comparativo: incidencias urbanas vs delitos, con toggle de capas."""
    print("[MAPA 3] Generando mapa comparativo...")

    loc = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    fgj = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    loc_urbano = loc[loc["tema_solicitud"].isin(TEMAS_URBANOS)]
    loc_geo = filtrar_coords_validas(loc_urbano)
    fgj_geo = filtrar_coords_validas(fgj)

    print(f"   Incidencias urbanas con georef: {len(loc_geo):,}")
    print(f"   Delitos con georef:             {len(fgj_geo):,}")

    m = crear_mapa_base(
        titulo="Fallas Urbanas vs Delitos", 
        subtitulo="Comparativo Espacial CDMX • 2024",
        stats=[
            {"icon": "🚧", "label": "Fallas Urbanas", "value": len(loc_geo)},
            {"icon": "🚨", "label": "Delitos FGJ", "value": len(fgj_geo)}
        ]
    )

    # Añadir CSS para color de checkboxes
    m.get_root().html.add_child(folium.Element("<style>.leaflet-control-layers input[type='checkbox']:checked { background-color: #FF9800; border-color: #FF9800; }</style>"))

    fg_inc = folium.FeatureGroup(name=f"Incidencias urbanas ({len(loc_geo):,})", show=True)
    HeatMap(
        loc_geo[["latitud", "longitud"]].values.tolist(),
        radius=7,
        blur=10,
        min_opacity=0.3,
        max_zoom=15,
        gradient={0.4: "#00E676", 0.7: "#69F0AE", 1.0: "#B9F6CA"},
    ).add_to(fg_inc)
    fg_inc.add_to(m)

    fg_del = folium.FeatureGroup(name=f"Delitos FGJ ({len(fgj_geo):,})", show=False)
    HeatMap(
        fgj_geo[["latitud", "longitud"]].values.tolist(),
        radius=6,
        blur=9,
        min_opacity=0.3,
        max_zoom=15,
        gradient={0.4: "#D50000", 0.7: "#FF5252", 1.0: "#FF8A80"},
    ).add_to(fg_del)
    fg_del.add_to(m)

    alumbrado = loc_geo[loc_geo["tema_solicitud"] == "ALUMBRADO"]
    fg_alum = folium.FeatureGroup(name=f"Solo alumbrado ({len(alumbrado):,})", show=False)
    HeatMap(
        alumbrado[["latitud", "longitud"]].values.tolist(),
        radius=8,
        blur=12,
        min_opacity=0.3,
        max_zoom=15,
        gradient={0.4: "#F57F17", 0.7: "#FBC02D", 1.0: "#FFF59D"},
    ).add_to(fg_alum)
    fg_alum.add_to(m)

    fgj_geo = fgj_geo.copy()
    fgj_geo["hora"] = pd.to_datetime(fgj_geo["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    nocturnos = fgj_geo[(fgj_geo["hora"] >= 20) | (fgj_geo["hora"] <= 5)]
    fg_noche = folium.FeatureGroup(name=f"Delitos nocturnos 20-05h ({len(nocturnos):,})", show=False)
    HeatMap(
        nocturnos[["latitud", "longitud"]].values.tolist(),
        radius=7,
        blur=10,
        min_opacity=0.3,
        max_zoom=15,
        gradient={0.4: "#4A148C", 0.7: "#7B1FA2", 1.0: "#E040FB"},
    ).add_to(fg_noche)
    fg_noche.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    legend_html = """
    <div class="modern-legend" style="bottom: 120px;">
        <h4>Densidad (Incidencias)</h4>
        <div class="legend-gradient" style="background: linear-gradient(to right, rgba(0,230,118,0), #00E676, #69F0AE, #B9F6CA);"></div>
        <div class="legend-labels"><span>Baja</span><span>Media</span><span>Alta</span></div>
    </div>
    <div class="modern-legend">
        <h4>Densidad (Delitos)</h4>
        <div class="legend-gradient" style="background: linear-gradient(to right, rgba(213,0,0,0), #D50000, #FF5252, #FF8A80);"></div>
        <div class="legend-labels"><span>Baja</span><span>Media</span><span>Alta</span></div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    guide_html = """
    <div class="modern-guide">
        <h4><span style="font-size:18px">💡</span> Guía de uso</h4>
        <p>Alterna las capas desde el menú derecho. <b>Activa "Solo alumbrado" y "Delitos nocturnos"</b> para explorar coincidencias espaciales.</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(guide_html))

    ruta = MAPAS_DIR / "mapa_comparativo_incidencias_delitos.html"
    m.save(str(ruta))
    print(f"   OK: {ruta.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("  GENERACION DE MAPAS -- SMART CITY CDMX")
    print("=" * 70)

    mapa_incidencias_locatel()
    mapa_delitos_fgj()
    mapa_comparativo()

    print("\\n" + "=" * 70)
    print("  MAPAS GENERADOS")
    print(f"  Ruta: {MAPAS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
