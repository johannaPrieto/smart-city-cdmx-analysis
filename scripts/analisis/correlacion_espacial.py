"""
Análisis de Correlación Espacial — Smart City CDMX
==================================================
Cruza incidentes urbanos (Locatel) con delitos (FGJ) a nivel Colonia
para calcular la correlación espacial de Pearson y Spearman.

Uso:
  python scripts/analisis/correlacion_espacial.py
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
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

# ─── Configuración ───────────────────────────────────────────────────────────
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

def main():
    print("=" * 70)
    print("  CORRELACION ESPACIAL -- SMART CITY CDMX")
    print("=" * 70)

    # 1. Cargar datos
    print("[1/4] Cargando datasets limpios...")
    locatel = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    # Limpiar columnas clave
    for df in [locatel, carpetas]:
        df["alcaldia_catalogo"] = df["alcaldia_catalogo"].astype(str).str.title().str.strip()
        df["colonia_catalogo"] = df["colonia_catalogo"].astype(str).str.title().str.strip()

    # Filtramos valores "Desconocida" o "Nan"
    locatel = locatel[(locatel["alcaldia_catalogo"] != "Desconocida") & (locatel["colonia_catalogo"] != "Desconocida")]
    carpetas = carpetas[(carpetas["alcaldia_catalogo"] != "Desconocida") & (carpetas["colonia_catalogo"] != "Desconocida")]
    locatel = locatel.dropna(subset=["alcaldia_catalogo", "colonia_catalogo"])
    carpetas = carpetas.dropna(subset=["alcaldia_catalogo", "colonia_catalogo"])

    # 2. Agregar por Alcaldía y Colonia
    print("[2/4] Agregando datos a nivel colonia...")
    
    # 2.1 Todas las incidencias vs Todos los delitos
    incidencias_por_colonia = locatel.groupby(["alcaldia_catalogo", "colonia_catalogo"]).size().reset_index(name="total_incidencias")
    delitos_por_colonia = carpetas.groupby(["alcaldia_catalogo", "colonia_catalogo"]).size().reset_index(name="total_delitos")
    
    # 2.2 Específico: Alumbrado vs Delitos Nocturnos (20-05h)
    alumbrado = locatel[locatel["tema_solicitud"] == "ALUMBRADO"]
    alumbrado_colonia = alumbrado.groupby(["alcaldia_catalogo", "colonia_catalogo"]).size().reset_index(name="total_falla_alumbrado")
    
    carpetas_noche = carpetas.copy()
    carpetas_noche["hora"] = pd.to_datetime(carpetas_noche["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    delitos_nocturnos = carpetas_noche[(carpetas_noche["hora"] >= 20) | (carpetas_noche["hora"] <= 5)]
    delitos_nocturnos_colonia = delitos_nocturnos.groupby(["alcaldia_catalogo", "colonia_catalogo"]).size().reset_index(name="total_delitos_nocturnos")

    # 3. Cruzar datasets (Merge)
    print("[3/4] Cruzando datasets y calculando correlación...")
    cruce = pd.merge(incidencias_por_colonia, delitos_por_colonia, on=["alcaldia_catalogo", "colonia_catalogo"], how="inner")
    cruce = cruce.merge(alumbrado_colonia, on=["alcaldia_catalogo", "colonia_catalogo"], how="left").fillna(0)
    cruce = cruce.merge(delitos_nocturnos_colonia, on=["alcaldia_catalogo", "colonia_catalogo"], how="left").fillna(0)

    # Calcular correlaciones
    pearson_global, p_val_g = stats.pearsonr(cruce["total_incidencias"], cruce["total_delitos"])
    spearman_global, p_val_sg = stats.spearmanr(cruce["total_incidencias"], cruce["total_delitos"])
    
    pearson_alumbrado, p_val_a = stats.pearsonr(cruce["total_falla_alumbrado"], cruce["total_delitos_nocturnos"])
    spearman_alumbrado, p_val_sa = stats.spearmanr(cruce["total_falla_alumbrado"], cruce["total_delitos_nocturnos"])

    print(f"\\n   RESULTADOS DE CORRELACION (por Colonia, n={len(cruce)}):")
    print(f"   ► Global (Todas las incidencias vs Todos los delitos):")
    print(f"      Pearson:  {pearson_global:.3f} (p-value: {p_val_g:.2e})")
    print(f"      Spearman: {spearman_global:.3f} (p-value: {p_val_sg:.2e})")
    
    print(f"\\n   ► Específica (Falta de Alumbrado vs Delitos Nocturnos):")
    print(f"      Pearson:  {pearson_alumbrado:.3f} (p-value: {p_val_a:.2e})")
    print(f"      Spearman: {spearman_alumbrado:.3f} (p-value: {p_val_sa:.2e})")

    # Guardar tabla de cruce
    ruta_csv = TABLAS_DIR / "correlacion_espacial.csv"
    cruce.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    print(f"\\n   [✓] Datos cruzados exportados a: {ruta_csv.name}")

    # 4. Generar Gráficas de Dispersión
    print("[4/4] Generando gráficas de dispersión...")
    
    # Gráfica Alumbrado vs Delitos Nocturnos
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.regplot(
        x="total_falla_alumbrado", 
        y="total_delitos_nocturnos", 
        data=cruce, 
        scatter_kws={"color": "#7C5CFC", "alpha": 0.5, "s": 30, "edgecolor": "none"},
        line_kws={"color": "#FF6B6B", "linewidth": 2.5},
        ax=ax
    )
    
    ax.set_title(f"Correlación: Falta de Alumbrado vs Delitos Nocturnos\\n(Por Colonia, Pearson r = {pearson_alumbrado:.2f})", pad=20, fontweight="bold", fontsize=14)
    ax.set_xlabel("Fallas de Alumbrado Público (Reportes)", fontweight="bold")
    ax.set_ylabel("Delitos Nocturnos (Carpetas)", fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    
    # Anotación para casos atípicos
    outliers = cruce[(cruce["total_falla_alumbrado"] > cruce["total_falla_alumbrado"].quantile(0.99)) | 
                     (cruce["total_delitos_nocturnos"] > cruce["total_delitos_nocturnos"].quantile(0.99))]
    for _, row in outliers.iterrows():
        ax.annotate(row["colonia_catalogo"][:15], 
                    (row["total_falla_alumbrado"], row["total_delitos_nocturnos"]),
                    textcoords="offset points", xytext=(0, 5), ha="center", fontsize=8, color="#A0AABF")

    fig.tight_layout()
    ruta_grafica = GRAFICAS_DIR / "dispersion_alumbrado_delitos.png"
    fig.savefig(ruta_grafica, dpi=200, bbox_inches="tight", facecolor="#0F1117")
    plt.close(fig)
    print(f"   [✓] Gráfica guardada: {ruta_grafica.name}")
    print("\\n" + "=" * 70)
    print("  ANÁLISIS DE CORRELACIÓN COMPLETADO")
    print("=" * 70)

if __name__ == "__main__":
    main()
