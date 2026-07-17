"""
Análisis Demográfico de Víctimas en Hotspots — Smart City CDMX
================================================================
Filtra el dataset de víctimas a las 5 macro-zonas críticas detectadas
por ML y genera un perfil demográfico (Edad y Sexo).

Salidas:
  - resultados/graficas/perfil_victimas_zonas_criticas.png

Uso:
  python scripts/analisis/analisis_victimas.py
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
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "datasets" / "processed"
TABLAS_DIR = ROOT / "resultados" / "tablas"
GRAFICAS_DIR = ROOT / "resultados" / "graficas"

plt.rcParams.update({
    "figure.facecolor": "#0F1117",
    "axes.facecolor": "#1A1D27",
    "axes.edgecolor": "#2E3347",
    "axes.labelcolor": "#E0E0E0",
    "text.color": "#E0E0E0",
    "xtick.color": "#B0B0B0",
    "ytick.color": "#B0B0B0",
    "grid.color": "#2E3347",
    "grid.alpha": 0.5,
    "font.family": "sans-serif",
})

def haversine_approx(lat1, lon1, lat2, lon2):
    """Aproximación simple de distancia en grados (1 grado ~ 111 km)."""
    return np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2) * 111.0

def main():
    print("=" * 70)
    print("  ANÁLISIS DE VÍCTIMAS EN HOTSPOTS -- SMART CITY CDMX")
    print("=" * 70)

    print("[1/3] Cargando datos de víctimas y zonas críticas...")
    try:
        victimas = pd.read_csv(DATA_DIR / "victimasFGJ_2024_limpio.csv")
        zonas_criticas = pd.read_csv(TABLAS_DIR / "zonas_criticas_ml.csv")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Por favor, ejecuta primero clustering_ml.py")
        sys.exit(1)

    # Filtrar coordenadas válidas
    victimas = victimas[victimas["latitud"].notna() & victimas["longitud"].notna()]
    victimas = victimas[(victimas["latitud"] > 19.0) & (victimas["latitud"] < 19.8) & 
                        (victimas["longitud"] > -99.5) & (victimas["longitud"] < -98.8)]

    print("[2/3] Filtrando víctimas a un radio de 1.5km de los hotspots...")
    
    # Etiquetar víctimas que caen en alguna de las 5 zonas críticas
    victimas["en_zona_critica"] = False
    
    for _, zona in zonas_criticas.iterrows():
        lat_c, lon_c = zona["lat_centroide"], zona["lon_centroide"]
        # Distancia en kilómetros
        distancias = haversine_approx(victimas["latitud"].values, victimas["longitud"].values, lat_c, lon_c)
        victimas.loc[distancias <= 1.5, "en_zona_critica"] = True

    vic_criticas = victimas[victimas["en_zona_critica"]].copy()
    print(f"      Víctimas totales: {len(victimas):,}")
    print(f"      Víctimas en Zonas Críticas (ML): {len(vic_criticas):,}")

    if len(vic_criticas) == 0:
        print("No hay víctimas en las zonas críticas identificadas. Abortando gráfica.")
        sys.exit(0)

    # Limpiar columnas de edad y sexo
    vic_criticas["sexo"] = vic_criticas["sexo"].fillna("Desconocido").astype(str).str.title()
    vic_criticas["edad"] = pd.to_numeric(vic_criticas["edad"], errors="coerce")

    print("[3/3] Generando gráficas de perfil demográfico...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Gráfica 1: Distribución de Sexo
    sexo_counts = vic_criticas["sexo"].value_counts()
    # Filtrar solo Femenino y Masculino para la visualización principal, agrupar resto
    sexo_counts = sexo_counts[sexo_counts.index.isin(["Femenino", "Masculino"])]
    
    ax1.pie(sexo_counts, labels=sexo_counts.index, autopct='%1.1f%%', startangle=90,
            colors=["#7C5CFC", "#00D9A3"], textprops={'color': "white", 'weight': 'bold'},
            wedgeprops={'edgecolor': '#0F1117', 'linewidth': 2})
    ax1.set_title("Distribución por Sexo en Zonas Críticas", fontweight="bold", pad=20)

    # Gráfica 2: Histograma de Edad por Sexo
    vic_edad = vic_criticas[vic_criticas["edad"].notna() & vic_criticas["sexo"].isin(["Femenino", "Masculino"])]
    sns.histplot(data=vic_edad, x="edad", hue="sexo", multiple="stack", bins=20,
                 palette={"Femenino": "#7C5CFC", "Masculino": "#00D9A3"}, ax=ax2, edgecolor="#0F1117")
    
    ax2.set_title("Distribución de Edad de Víctimas en Zonas Críticas", fontweight="bold", pad=20)
    ax2.set_xlabel("Edad", fontweight="bold")
    ax2.set_ylabel("Frecuencia", fontweight="bold")
    ax2.grid(True, axis="y", linestyle="--", alpha=0.3)
    ax2.set_axisbelow(True)

    fig.tight_layout(pad=3.0)
    ruta_grafica = GRAFICAS_DIR / "perfil_victimas_zonas_criticas.png"
    fig.savefig(ruta_grafica, dpi=200, bbox_inches="tight", facecolor="#0F1117")
    plt.close(fig)

    print(f"   [✓] Gráfica guardada: {ruta_grafica.name}")
    print("\\n" + "=" * 70)
    print("  ANÁLISIS DE VÍCTIMAS COMPLETADO")
    print("=" * 70)

if __name__ == "__main__":
    main()
