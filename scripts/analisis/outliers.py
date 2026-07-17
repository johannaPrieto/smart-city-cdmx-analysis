"""
Detección de Valores Atípicos — Smart City CDMX  [A-2]
=======================================================
IQR · Z-Score · Isolation Forest

Salidas:
  resultados/tablas/outliers_detectados.csv
  resultados/graficas/boxplot_outliers.png
  resultados/graficas/isolation_forest_scores.png

Uso:
  python scripts/analisis/outliers.py
"""

import io, sys, warnings
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from sklearn.ensemble import IsolationForest

warnings.filterwarnings("ignore")

ROOT        = Path(__file__).resolve().parents[2]
DATA_DIR    = ROOT / "datasets" / "processed"
TABLAS_DIR  = ROOT / "resultados" / "tablas"
GRAFICAS_DIR = ROOT / "resultados" / "graficas"

DARK, PANEL, BORDER = "#0F1117", "#1A1D27", "#2E3347"
TEXT, MUTED = "#E0E0E0", "#A0AABF"
PURPLE, CYAN, RED, ORANGE = "#7C5CFC", "#00D9A3", "#FF6B6B", "#FFB347"

plt.rcParams.update({
    "figure.facecolor": DARK, "axes.facecolor": PANEL,
    "axes.edgecolor": BORDER, "axes.labelcolor": TEXT,
    "text.color": TEXT, "xtick.color": MUTED, "ytick.color": MUTED,
    "grid.color": BORDER, "grid.alpha": 0.5, "font.family": "sans-serif",
})

VARS = ["total_incidencias", "total_delitos",
        "total_alumbrado", "total_delitos_nocturnos"]
LABELS = ["Incidencias Locatel", "Delitos Totales",
          "Fallas Alumbrado", "Delitos Nocturnos"]
COLORS_VAR = [PURPLE, RED, CYAN, ORANGE]


def flag_iqr(s):
    Q1, Q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = Q3 - Q1
    return (s < Q1 - 1.5 * iqr) | (s > Q3 + 1.5 * iqr)


def flag_z(s, thr=3.0):
    z = np.abs(stats.zscore(s.fillna(s.median())))
    return pd.Series(z > thr, index=s.index)


def build_colonia_df(locatel, carpetas):
    for df in [locatel, carpetas]:
        df["alcaldia_catalogo"] = df["alcaldia_catalogo"].astype(str).str.title().str.strip()
        df["colonia_catalogo"]  = df["colonia_catalogo"].astype(str).str.title().str.strip()

    locatel  = locatel[(locatel["alcaldia_catalogo"] != "Desconocida") &
                       (locatel["colonia_catalogo"]  != "Desconocida")]
    carpetas = carpetas[(carpetas["alcaldia_catalogo"] != "Desconocida") &
                        (carpetas["colonia_catalogo"]  != "Desconocida")]

    k = ["alcaldia_catalogo", "colonia_catalogo"]
    inc  = locatel.groupby(k).size().reset_index(name="total_incidencias")
    del_ = carpetas.groupby(k).size().reset_index(name="total_delitos")

    carpetas["hora"] = pd.to_datetime(
        carpetas["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    noc = carpetas[(carpetas["hora"] >= 20) | (carpetas["hora"] <= 5)]
    noc_ = noc.groupby(k).size().reset_index(name="total_delitos_nocturnos")

    alumb = locatel[locatel["tema_solicitud"] == "ALUMBRADO"]
    alumb_ = alumb.groupby(k).size().reset_index(name="total_alumbrado")

    return (inc.merge(del_, on=k, how="inner")
               .merge(alumb_, on=k, how="left")
               .merge(noc_,   on=k, how="left")
               .fillna(0))


def plot_boxplots(df):
    fig = plt.figure(figsize=(16, 10), facecolor=DARK)
    fig.suptitle("Detección de Valores Atípicos por Variable — Boxplot IQR",
                 fontsize=14, fontweight="bold", y=0.98)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.38)

    for idx, (var, label, color) in enumerate(zip(VARS, LABELS, COLORS_VAR)):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        data = df[var]
        bp = ax.boxplot(data, vert=True, patch_artist=True,
                        medianprops=dict(color="white", linewidth=2),
                        whiskerprops=dict(color=MUTED),
                        capprops=dict(color=MUTED),
                        flierprops=dict(marker="o", color=RED, alpha=0.5, markersize=4))
        bp["boxes"][0].set(facecolor=color, alpha=0.35, edgecolor=color)

        n_out = df[f"out_iqr_{var}"].sum()
        ax.set_title(label, fontsize=11, fontweight="bold", pad=8)
        ax.set_xticks([])
        ax.set_ylabel("Conteo por Colonia", fontsize=9)
        txt = (f"Mediana: {data.median():.0f}\n"
               f"P95: {data.quantile(0.95):.0f}\n"
               f"Máx: {data.max():.0f}\n"
               f"Outliers IQR: {n_out}")
        ax.text(1.28, data.median(), txt, transform=ax.get_yaxis_transform(),
                fontsize=8, color=MUTED, va="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor=PANEL, edgecolor=BORDER))
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)

    ruta = GRAFICAS_DIR / "boxplot_outliers.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] Gráfica guardada: {ruta.name}")


def plot_isoforest(df):
    out_rows = df[df["outlier_consenso"]]
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor=DARK)
    fig.suptitle(
        "Isolation Forest — Detección Multivariante de Anomalías\n"
        "(5 % de colonias marcadas | ⭕ = Outlier consenso ≥2 métodos)",
        fontsize=13, fontweight="bold", y=1.01)

    pairs = [
        ("total_incidencias", "total_delitos", "Incidencias Locatel", "Delitos Totales"),
        ("total_alumbrado", "total_delitos_nocturnos", "Fallas Alumbrado", "Delitos Nocturnos"),
    ]
    for ax, (xv, yv, xl, yl) in zip(axes, pairs):
        sc = ax.scatter(df[xv], df[yv], c=df["anomaly_score"],
                        cmap="RdYlGn", alpha=0.55, s=18, edgecolors="none")
        fig.colorbar(sc, ax=ax, label="Anomaly Score (+normal | −anómalo)")
        ax.scatter(out_rows[xv], out_rows[yv],
                   s=55, color=RED, edgecolors="white", linewidths=0.5, zorder=5)
        for _, row in out_rows.nlargest(6, yv).iterrows():
            ax.annotate(row["colonia_catalogo"][:14], (row[xv], row[yv]),
                        textcoords="offset points", xytext=(4, 4),
                        fontsize=7, color=ORANGE, alpha=0.9)
        ax.set_xlabel(xl, fontweight="bold")
        ax.set_ylabel(yl, fontweight="bold")
        ax.set_title(f"{xl} vs {yl}", fontweight="bold", pad=10)
        ax.grid(True, linestyle="--", alpha=0.22)

    fig.tight_layout(pad=2.5)
    ruta = GRAFICAS_DIR / "isolation_forest_scores.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] Gráfica guardada: {ruta.name}")


def main():
    print("=" * 70)
    print("  DETECCION DE OUTLIERS -- SMART CITY CDMX  [A-2]")
    print("=" * 70)

    print("\n[1/4] Cargando datasets...")
    locatel  = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    print("[2/4] Agregando por colonia...")
    df = build_colonia_df(locatel, carpetas)

    print("[3/4] Aplicando IQR, Z-Score e Isolation Forest...")
    for var in VARS:
        df[f"out_iqr_{var}"]    = flag_iqr(df[var])
        df[f"out_zscore_{var}"] = flag_z(df[var])

    iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    df["anomaly_score"]   = iso.fit(df[VARS]).decision_function(df[VARS])
    df["out_isoforest"]   = iso.predict(df[VARS]) == -1

    df["out_iqr_any"]    = df[[f"out_iqr_{v}" for v in VARS]].any(axis=1)
    df["out_zscore_any"] = df[[f"out_zscore_{v}" for v in VARS]].any(axis=1)
    df["outlier_consenso"] = (
        df["out_iqr_any"].astype(int) +
        df["out_zscore_any"].astype(int) +
        df["out_isoforest"].astype(int)) >= 2

    n = len(df)
    print(f"\n   Colonias analizadas       : {n:,}")
    print(f"   Outliers por IQR          : {df['out_iqr_any'].sum():,}  ({df['out_iqr_any'].mean()*100:.1f}%)")
    print(f"   Outliers por Z-Score      : {df['out_zscore_any'].sum():,}  ({df['out_zscore_any'].mean()*100:.1f}%)")
    print(f"   Outliers por IsoForest    : {df['out_isoforest'].sum():,}  ({df['out_isoforest'].mean()*100:.1f}%)")
    print(f"   Outlier consenso (≥2 mét.): {df['outlier_consenso'].sum():,}  ({df['outlier_consenso'].mean()*100:.1f}%)")

    ruta_csv = TABLAS_DIR / "outliers_detectados.csv"
    df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    print(f"\n   [✓] Tabla exportada: {ruta_csv.name}")

    print("\n[4/4] Generando visualizaciones...")
    plot_boxplots(df)
    plot_isoforest(df)

    print("\n" + "=" * 70)
    print("  DETECCIÓN DE OUTLIERS COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
