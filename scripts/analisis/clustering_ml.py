"""
Clustering y Detección de Hotspots con Machine Learning — Smart City CDMX
===========================================================================
Aplica algoritmos de Clustering (MiniBatchKMeans) para encontrar las
5 macro-zonas más críticas donde coexisten fallas de alumbrado y delitos nocturnos.

Salidas:
  - resultados/tablas/zonas_criticas_ml.csv
  - resultados/mapas/mapa_clusters_criticos.html

Uso:
  python scripts/analisis/clustering_ml.py
"""

import io
import sys
from pathlib import Path
import warnings

# Forzar UTF-8 en stdout para Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import folium
from sklearn.cluster import MiniBatchKMeans

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "datasets" / "processed"
MAPAS_DIR = ROOT / "resultados" / "mapas"
TABLAS_DIR = ROOT / "resultados" / "tablas"

CDMX_CENTER = [19.38, -99.14]

# CSS Global similar al Dashboard
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
body { font-family: 'Inter', sans-serif !important; background-color: #0f1117; }
.modern-title {
    position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999;
    background: rgba(20, 22, 30, 0.8); backdrop-filter: blur(12px);
    padding: 15px 35px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1);
    color: #ffffff; text-align: center; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}
.modern-title h1 { margin: 0; font-size: 20px; font-weight: 700; }
.modern-title p { margin: 4px 0 0 0; font-size: 12px; color: #FF4B4B; font-weight: 600; }
.stat-cards-container { position: fixed; top: 20px; left: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 12px; }
.stat-card {
    background: rgba(20, 22, 30, 0.8); backdrop-filter: blur(12px);
    padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1);
    color: white; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); display: flex; align-items: center; gap: 15px; min-width: 180px;
}
.stat-icon { font-size: 22px; }
.stat-info h4 { margin: 0; font-size: 10px; color: #A0AABF; text-transform: uppercase; }
.stat-info p { margin: 2px 0 0 0; font-size: 18px; font-weight: 700; }
</style>
"""

def filtrar_coords_validas(df, lat_col="latitud", lon_col="longitud"):
    mask = (df[lat_col].notna() & df[lon_col].notna() & 
            (df[lat_col] > 19.0) & (df[lat_col] < 19.8) & 
            (df[lon_col] > -99.5) & (df[lon_col] < -98.8))
    return df[mask]

def main():
    print("=" * 70)
    print("  CLUSTERING Y ML -- SMART CITY CDMX")
    print("=" * 70)

    print("[1/4] Preparando datos para Machine Learning...")
    locatel = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    locatel = filtrar_coords_validas(locatel)
    carpetas = filtrar_coords_validas(carpetas)

    # Filtrar solo "Falta de Alumbrado" y "Delitos Nocturnos" (20-05h)
    alumbrado = locatel[locatel["tema_solicitud"] == "ALUMBRADO"].copy()
    
    carpetas["hora"] = pd.to_datetime(carpetas["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    nocturnos = carpetas[(carpetas["hora"] >= 20) | (carpetas["hora"] <= 5)].copy()

    alumbrado["origen"] = "Alumbrado"
    nocturnos["origen"] = "Delito Nocturno"

    # Unir datos
    df_ml = pd.concat([
        alumbrado[["latitud", "longitud", "origen"]],
        nocturnos[["latitud", "longitud", "origen"]]
    ])

    print(f"      Total Puntos: {len(df_ml):,} (Alumbrado: {len(alumbrado):,} | Delitos: {len(nocturnos):,})")

    # 2. Aplicar Clustering (K-Means)
    print("[2/4] Entrenando modelo de KMeans (k=30 macro-zonas)...")
    coords = df_ml[["latitud", "longitud"]].values
    kmeans = MiniBatchKMeans(n_clusters=30, random_state=42, n_init="auto")
    df_ml["cluster_id"] = kmeans.fit_predict(coords)

    # 3. Evaluar y rankear clusters
    print("[3/4] Evaluando y rankeando hotspots...")
    eval_clusters = df_ml.groupby(["cluster_id", "origen"]).size().unstack(fill_value=0).reset_index()
    if "Alumbrado" not in eval_clusters: eval_clusters["Alumbrado"] = 0
    if "Delito Nocturno" not in eval_clusters: eval_clusters["Delito Nocturno"] = 0
    
    # Calcular un "Score de Riesgo" que premia zonas con ALTOS delitos Y ALTAS fallas de alumbrado
    eval_clusters["score_riesgo"] = eval_clusters["Alumbrado"] * eval_clusters["Delito Nocturno"]
    
    # Top 5
    top_5 = eval_clusters.sort_values("score_riesgo", ascending=False).head(5)
    
    # Obtener centroides del top 5
    centroides = kmeans.cluster_centers_
    top_5["lat_centroide"] = top_5["cluster_id"].apply(lambda x: centroides[x][0])
    top_5["lon_centroide"] = top_5["cluster_id"].apply(lambda x: centroides[x][1])
    
    top_5["rango"] = range(1, 6)
    
    ruta_csv = TABLAS_DIR / "zonas_criticas_ml.csv"
    top_5.to_csv(ruta_csv, index=False)
    print(f"      Top 5 Zonas exportadas a: {ruta_csv.name}")

    # 4. Generar Mapa
    print("[4/4] Generando mapa Dashboard de Clusters Críticos...")
    m = folium.Map(location=CDMX_CENTER, zoom_start=11.5, tiles="CartoDB dark_matter", control_scale=True, prefer_canvas=True)
    m.get_root().html.add_child(folium.Element(GLOBAL_CSS))

    titulo_html = f"""
    <div class="modern-title">
        <h1>Top 5 Macro-Zonas Críticas</h1>
        <p>Identificadas por Inteligencia Artificial (K-Means)</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(titulo_html))

    total_delitos_top5 = top_5["Delito Nocturno"].sum()
    total_alumbrado_top5 = top_5["Alumbrado"].sum()

    cards_html = f"""
    <div class="stat-cards-container">
        <div class="stat-card">
            <div class="stat-icon">⚠️</div>
            <div class="stat-info"><h4>Delitos en Zonas Críticas</h4><p>{total_delitos_top5:,}</p></div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">💡</div>
            <div class="stat-info"><h4>Fallas de Alumbrado (Top 5)</h4><p>{total_alumbrado_top5:,}</p></div>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(cards_html))

    colores = ["#FF1744", "#FF5252", "#FF8A80", "#FFB74D", "#FFD54F"]
    
    for _, row in top_5.iterrows():
        color = colores[int(row['rango'])-1]
        
        # Círculo grande de área (aprox 1500m de radio para macro-zonas)
        folium.Circle(
            location=[row["lat_centroide"], row["lon_centroide"]],
            radius=1500,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.15,
            weight=1
        ).add_to(m)

        # Marcador del centroide
        html_popup = f"""
        <div style="font-family: 'Inter', sans-serif; padding: 10px; min-width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">🔥 Hotspot #{int(row['rango'])}</h4>
            <div style="font-size: 13px; color: #555;">
                <b>Delitos Nocturnos:</b> {int(row['Delito Nocturno']):,}<br>
                <b>Fallas Alumbrado:</b> {int(row['Alumbrado']):,}
            </div>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat_centroide"], row["lon_centroide"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=1,
            popup=folium.Popup(html_popup, max_width=300)
        ).add_to(m)

    ruta_mapa = MAPAS_DIR / "mapa_clusters_criticos.html"
    m.save(str(ruta_mapa))
    print(f"      Mapa Dashboard guardado: {ruta_mapa.name}")

    print("\\n" + "=" * 70)
    print("  CLUSTERING Y ML COMPLETADO")
    print("=" * 70)

if __name__ == "__main__":
    main()
