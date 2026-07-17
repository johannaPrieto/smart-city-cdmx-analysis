"""
Normalización por Tasa por 1,000 Habitantes — Smart City CDMX  [A-3]
======================================================================
Elimina el sesgo de densidad poblacional usando datos del Censo INEGI 2020.
Recalcula las correlaciones Pearson/Spearman sobre tasas normalizadas
y compara con los coeficientes sobre conteos brutos.

Población hardcodeada de las 16 alcaldías (Censo INEGI 2020):
  https://www.inegi.org.mx/app/descarga/?ag=09

Salidas:
  datasets/processed/poblacion_inegi_alcaldias.csv
  resultados/tablas/correlacion_tasas_normalizadas.csv
  resultados/graficas/comparacion_bruto_vs_tasa.png
  resultados/graficas/barplot_tasas_alcaldias.png

Uso:
  python scripts/analisis/normalizacion_inegi.py
"""

import io, sys, warnings
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats

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

# ─── Población INEGI Censo 2020 — 16 Alcaldías CDMX ──────────────────────────
POBLACION_INEGI = {
    "Alvaro Obregon":          759_137,
    "Azcapotzalco":            432_205,
    "Benito Juarez":           434_153,
    "Coyoacan":                614_447,
    "Cuajimalpa De Morelos":   217_686,
    "Cuauhtemoc":              531_831,
    "Gustavo A. Madero":     1_173_351,
    "Iztacalco":               424_657,
    "Iztapalapa":            1_835_486,
    "La Magdalena Contreras":  247_622,
    "Miguel Hidalgo":          414_470,
    "Milpa Alta":              152_685,
    "Tlahuac":                 361_593,
    "Tlalpan":                 699_928,
    "Venustiano Carranza":     427_263,
    "Xochimilco":              442_178,
}


def normalizar_nombre(s: str) -> str:
    """Normaliza el nombre de alcaldía para hacer match con INEGI."""
    import unicodedata
    s = str(s).strip().title()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def main():
    print("=" * 70)
    print("  NORMALIZACIÓN INEGI — TASAS POR 1,000 HAB  [A-3]")
    print("=" * 70)

    # ── 1. Exportar tabla de población ───────────────────────────────────────
    print("\n[1/5] Exportando tabla de población INEGI 2020...")
    df_pob = pd.DataFrame(
        list(POBLACION_INEGI.items()), columns=["alcaldia", "poblacion_2020"]
    )
    ruta_pob = DATA_DIR / "poblacion_inegi_alcaldias.csv"
    df_pob.to_csv(ruta_pob, index=False, encoding="utf-8-sig")
    print(f"   [✓] {ruta_pob.name}  —  16 alcaldías registradas")

    # ── 2. Cargar y limpiar datasets ─────────────────────────────────────────
    print("[2/5] Cargando datasets limpios...")
    locatel  = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    for df in [locatel, carpetas]:
        df["alcaldia_norm"] = df["alcaldia_catalogo"].apply(normalizar_nombre)
        df["colonia_catalogo"] = df["colonia_catalogo"].astype(str).str.title().str.strip()

    locatel  = locatel[locatel["alcaldia_norm"].isin(POBLACION_INEGI)]
    carpetas = carpetas[carpetas["alcaldia_norm"].isin(POBLACION_INEGI)]

    # ── 3. Agregar por alcaldía ───────────────────────────────────────────────
    print("[3/5] Agregando conteos por alcaldía...")

    inc  = locatel.groupby("alcaldia_norm").size().reset_index(name="total_incidencias")
    del_ = carpetas.groupby("alcaldia_norm").size().reset_index(name="total_delitos")

    carpetas["hora"] = pd.to_datetime(
        carpetas["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    noc = carpetas[(carpetas["hora"] >= 20) | (carpetas["hora"] <= 5)]
    noc_ = noc.groupby("alcaldia_norm").size().reset_index(name="total_delitos_nocturnos")

    alumb = locatel[locatel["tema_solicitud"] == "ALUMBRADO"]
    alumb_ = alumb.groupby("alcaldia_norm").size().reset_index(name="total_alumbrado")

    k = "alcaldia_norm"
    agg = (inc.merge(del_, on=k, how="outer")
              .merge(alumb_, on=k, how="left")
              .merge(noc_,   on=k, how="left")
              .fillna(0))

    # Agregar población
    pob_dict = POBLACION_INEGI
    agg["poblacion_2020"] = agg[k].map(pob_dict)
    agg = agg.dropna(subset=["poblacion_2020"])
    agg["poblacion_2020"] = agg["poblacion_2020"].astype(int)

    # ── 4. Calcular tasas por 1,000 habitantes ────────────────────────────────
    print("[4/5] Calculando tasas por 1,000 habitantes y correlaciones...")

    VARS_BRUTO = ["total_incidencias", "total_delitos",
                  "total_alumbrado", "total_delitos_nocturnos"]
    VARS_TASA  = [f"tasa_{v.replace('total_','')}" for v in VARS_BRUTO]

    for var_b, var_t in zip(VARS_BRUTO, VARS_TASA):
        agg[var_t] = agg[var_b] / agg["poblacion_2020"] * 1000

    # ── Correlaciones bruto vs tasa ───────────────────────────────────────────
    resultados = []
    pares = [
        ("total_incidencias",       "total_delitos",           "Incidencias → Delitos (bruto)"),
        ("total_alumbrado",         "total_delitos_nocturnos", "Alumbrado → Del. Nocturnos (bruto)"),
        ("tasa_incidencias",        "tasa_delitos",            "Incidencias → Delitos (tasa)"),
        ("tasa_alumbrado",          "tasa_delitos_nocturnos",  "Alumbrado → Del. Nocturnos (tasa)"),
    ]

    for xv, yv, label in pares:
        r_p, p_p = stats.pearsonr(agg[xv], agg[yv])
        r_s, p_s = stats.spearmanr(agg[xv], agg[yv])
        resultados.append({
            "par": label, "xvar": xv, "yvar": yv,
            "pearson_r": round(r_p, 4), "pearson_p": round(p_p, 5),
            "spearman_r": round(r_s, 4), "spearman_p": round(p_s, 5),
            "significativo_p05": p_p < 0.05 and p_s < 0.05,
        })
        sig = "✓ sig." if p_p < 0.05 else "✗ no sig."
        print(f"   {label[:42]:<42}  Pearson r={r_p:+.3f} (p={p_p:.3f}) {sig}")

    df_res = pd.DataFrame(resultados)
    ruta_res = TABLAS_DIR / "correlacion_tasas_normalizadas.csv"
    df_res.to_csv(ruta_res, index=False, encoding="utf-8-sig")
    print(f"\n   [✓] Tabla exportada: {ruta_res.name}")

    ruta_agg = TABLAS_DIR / "agregado_por_alcaldia.csv"
    agg.to_csv(ruta_agg, index=False, encoding="utf-8-sig")

    # ── 5. Visualizaciones ────────────────────────────────────────────────────
    print("[5/5] Generando visualizaciones...")

    # Gráfica 1: Comparación Bruto vs Tasa (scatter 2x2)
    fig, axes = plt.subplots(2, 2, figsize=(15, 12), facecolor=DARK)
    fig.suptitle(
        "Impacto de la Normalización Poblacional (INEGI 2020)\n"
        "Bruto (conteos) vs Tasa (por 1,000 hab.)",
        fontsize=14, fontweight="bold", y=0.99)

    config = [
        (axes[0,0], "total_incidencias",  "total_delitos",           PURPLE, "Incidencias (bruto)"),
        (axes[0,1], "tasa_incidencias",   "tasa_delitos",            CYAN,   "Incidencias (tasa/1k hab)"),
        (axes[1,0], "total_alumbrado",    "total_delitos_nocturnos", RED,    "Alumbrado (bruto)"),
        (axes[1,1], "tasa_alumbrado",     "tasa_delitos_nocturnos",  ORANGE, "Alumbrado (tasa/1k hab)"),
    ]

    for ax, xv, yv, color, titulo in config:
        r_p, p_p = stats.pearsonr(agg[xv], agg[yv])
        ax.scatter(agg[xv], agg[yv], color=color, alpha=0.8, s=80, edgecolors="white",
                   linewidths=0.5, zorder=3)

        # Línea de regresión
        m, b = np.polyfit(agg[xv], agg[yv], 1)
        x_line = np.linspace(agg[xv].min(), agg[xv].max(), 100)
        ax.plot(x_line, m * x_line + b, color="white", lw=1.5, ls="--", alpha=0.7)

        # Etiquetas
        for _, row in agg.iterrows():
            ax.annotate(row[k][:12], (row[xv], row[yv]),
                        textcoords="offset points", xytext=(4, 3),
                        fontsize=7, color=MUTED, alpha=0.85)

        sig_txt = "✓ p<0.05" if p_p < 0.05 else "✗ p≥0.05"
        ax.set_title(f"{titulo}\nr = {r_p:+.3f}  {sig_txt}", fontsize=10, fontweight="bold", pad=8)
        ax.set_xlabel(xv, fontsize=8)
        ax.set_ylabel(yv, fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.25)
        ax.set_axisbelow(True)

    fig.tight_layout(pad=2.5)
    ruta_g1 = GRAFICAS_DIR / "comparacion_bruto_vs_tasa.png"
    fig.savefig(ruta_g1, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] Gráfica guardada: {ruta_g1.name}")

    # Gráfica 2: Ranking de alcaldías por tasa de delitos y alumbrado
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), facecolor=DARK)
    fig2.suptitle("Ranking de Alcaldías — Tasas por 1,000 Habitantes (INEGI 2020)",
                  fontsize=14, fontweight="bold", y=1.01)

    agg_sorted_del = agg.sort_values("tasa_delitos", ascending=True)
    ax1.barh(agg_sorted_del[k], agg_sorted_del["tasa_delitos"],
             color=RED, alpha=0.8, edgecolor=BORDER, height=0.6)
    ax1.set_title("Tasa de Delitos por 1,000 Hab.", fontweight="bold", pad=10)
    ax1.set_xlabel("Delitos / 1,000 habitantes")
    ax1.grid(axis="x", linestyle="--", alpha=0.3)

    for i, (_, row) in enumerate(agg_sorted_del.iterrows()):
        ax1.text(row["tasa_delitos"] + 0.1, i,
                 f"{row['tasa_delitos']:.1f}", va="center", fontsize=8, color=TEXT)

    agg_sorted_alumb = agg.sort_values("tasa_alumbrado", ascending=True)
    ax2.barh(agg_sorted_alumb[k], agg_sorted_alumb["tasa_alumbrado"],
             color=CYAN, alpha=0.8, edgecolor=BORDER, height=0.6)
    ax2.set_title("Tasa de Fallas de Alumbrado por 1,000 Hab.", fontweight="bold", pad=10)
    ax2.set_xlabel("Fallas Alumbrado / 1,000 habitantes")
    ax2.grid(axis="x", linestyle="--", alpha=0.3)

    for i, (_, row) in enumerate(agg_sorted_alumb.iterrows()):
        ax2.text(row["tasa_alumbrado"] + 0.05, i,
                 f"{row['tasa_alumbrado']:.2f}", va="center", fontsize=8, color=TEXT)

    fig2.tight_layout(pad=2.5)
    ruta_g2 = GRAFICAS_DIR / "barplot_tasas_alcaldias.png"
    fig2.savefig(ruta_g2, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig2)
    print(f"   [✓] Gráfica guardada: {ruta_g2.name}")

    print("\n" + "=" * 70)
    print("  NORMALIZACIÓN INEGI COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
