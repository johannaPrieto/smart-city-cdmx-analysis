"""
Análisis de Correlación Temporal — Smart City CDMX
==================================================
Analiza las series de tiempo de incidentes y delitos para calcular
correlación cruzada (lags) y detectar si las fallas preceden a los delitos.

Uso:
  python scripts/analisis/correlacion_temporal.py
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
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "datasets" / "processed"
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

def crosscorr(datax, datay, lag=0):
    """Calcula la correlación cruzada con un rezago (lag) determinado."""
    return datax.corr(datay.shift(lag))

def main():
    print("=" * 70)
    print("  CORRELACION TEMPORAL -- SMART CITY CDMX")
    print("=" * 70)

    print("[1/3] Cargando datasets limpios...")
    locatel = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    locatel["fecha"] = pd.to_datetime(locatel["datetime_solicitud"]).dt.date
    carpetas["fecha"] = pd.to_datetime(carpetas["datetime_hecho"]).dt.date

    # Filtrar solo temas clave (alumbrado) vs delitos
    alumbrado = locatel[locatel["tema_solicitud"] == "ALUMBRADO"]

    print("[2/3] Agrupando por semana...")
    # Agrupar por semana (resample)
    alumbrado_diario = alumbrado.groupby("fecha").size().reset_index(name="alumbrado")
    delitos_diario = carpetas.groupby("fecha").size().reset_index(name="delitos")

    alumbrado_diario["fecha"] = pd.to_datetime(alumbrado_diario["fecha"])
    delitos_diario["fecha"] = pd.to_datetime(delitos_diario["fecha"])

    alumbrado_semanal = alumbrado_diario.set_index("fecha").resample("W").sum()
    delitos_semanal = delitos_diario.set_index("fecha").resample("W").sum()

    df_ts = pd.merge(alumbrado_semanal, delitos_semanal, left_index=True, right_index=True, how="inner")
    
    # Calcular cross-correlation para lags -4 a 4 semanas
    print("[3/3] Calculando Lags y graficando...")
    lags = range(-4, 5)
    rs = [crosscorr(df_ts["alumbrado"], df_ts["delitos"], lag) for lag in lags]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot 1: Series de tiempo normalizadas (para comparar tendencias)
    df_norm = (df_ts - df_ts.mean()) / df_ts.std()
    ax1.plot(df_norm.index, df_norm["alumbrado"], label="Reportes de Alumbrado", color="#7C5CFC", linewidth=2, marker='o')
    ax1.plot(df_norm.index, df_norm["delitos"], label="Delitos", color="#FF6B6B", linewidth=2, marker='s')
    ax1.set_title("Evolución Semanal (Normalizada): Alumbrado vs Delitos", fontweight="bold", pad=15)
    ax1.legend(framealpha=0.7, edgecolor="#2E3347")
    ax1.grid(True, linestyle="--", alpha=0.3)

    # Plot 2: Cross Correlation
    colors = ["#00D9A3" if lag == 0 else "#7C5CFC" if lag < 0 else "#FF6B6B" for lag in lags]
    ax2.bar(lags, rs, color=colors, alpha=0.8, width=0.6)
    
    # Añadir valores
    for i, v in enumerate(rs):
        ax2.text(lags[i], v + (0.01 if v > 0 else -0.02), f"{v:.2f}", ha='center', va='bottom' if v > 0 else 'top', fontsize=9)

    ax2.set_title("Correlación Cruzada (Lags en Semanas)", fontweight="bold", pad=15)
    ax2.set_xlabel("Semanas de Rezago (Lag)\\nNegativo = Alumbrado precede a Delito | Positivo = Delito precede a Alumbrado")
    ax2.set_ylabel("Coeficiente de Correlación")
    ax2.axhline(0, color="#E0E0E0", linewidth=1)
    ax2.grid(axis="y", linestyle="--", alpha=0.3)
    ax2.set_xticks(lags)

    fig.tight_layout(pad=3.0)
    ruta_grafica = GRAFICAS_DIR / "correlacion_temporal_lags.png"
    fig.savefig(ruta_grafica, dpi=200, bbox_inches="tight", facecolor="#0F1117")
    plt.close(fig)

    print(f"   [✓] Gráfica guardada: {ruta_grafica.name}")
    print("\\n" + "=" * 70)
    print("  ANÁLISIS TEMPORAL COMPLETADO")
    print("=" * 70)

if __name__ == "__main__":
    main()
