"""
Índice de Riesgo Urbano Compuesto — Smart City CDMX  [A-6]
============================================================
Sintetiza hallazgos de infraestructura y criminalidad en un
indicador normalizado (0-100) por alcaldía.

Componentes del índice:
  1. Tasa de delitos / 1,000 hab
  2. Tasa de fallas de alumbrado / 1,000 hab
  3. Tasa de delitos nocturnos / 1,000 hab
  4. Proporción de delitos nocturnos sobre total
  5. Clasificación LISA (hot spot = penalización)

Salidas:
  resultados/tablas/indice_riesgo_urbano.csv
  resultados/graficas/ranking_riesgo_alcaldias.png
  resultados/graficas/radar_riesgo_top5.png
  resultados/mapas/mapa_riesgo_coropletico.html

Uso:
  python scripts/analisis/indice_riesgo_urbano.py
"""

import io, sys, warnings
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import folium

warnings.filterwarnings("ignore")

ROOT         = Path(__file__).resolve().parents[2]
DATA_DIR     = ROOT / "datasets" / "processed"
TABLAS_DIR   = ROOT / "resultados" / "tablas"
GRAFICAS_DIR = ROOT / "resultados" / "graficas"
MAPAS_DIR    = ROOT / "resultados" / "mapas"

for d in [TABLAS_DIR, GRAFICAS_DIR, MAPAS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DARK, PANEL, BORDER = "#0F1117", "#1A1D27", "#2E3347"
TEXT, MUTED = "#E0E0E0", "#A0AABF"
PURPLE, CYAN, RED, ORANGE, GREEN = "#7C5CFC", "#00D9A3", "#FF6B6B", "#FFB347", "#4CAF50"
CDMX_CENTER = [19.38, -99.14]

plt.rcParams.update({
    "figure.facecolor": DARK, "axes.facecolor": PANEL,
    "axes.edgecolor": BORDER, "axes.labelcolor": TEXT,
    "text.color": TEXT, "xtick.color": MUTED, "ytick.color": MUTED,
    "grid.color": BORDER, "grid.alpha": 0.5, "font.family": "sans-serif",
})

# ── Población INEGI Censo 2020 ───────────────────────────────────────────────
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

# Coordenadas centroides aproximados por alcaldía (para mapa)
COORDS_ALCALDIA = {
    "Alvaro Obregon":         (19.3580, -99.2280),
    "Azcapotzalco":           (19.4870, -99.1840),
    "Benito Juarez":          (19.3720, -99.1630),
    "Coyoacan":               (19.3350, -99.1620),
    "Cuajimalpa De Morelos":  (19.3590, -99.2910),
    "Cuauhtemoc":             (19.4280, -99.1530),
    "Gustavo A. Madero":      (19.4830, -99.1130),
    "Iztacalco":              (19.3960, -99.0970),
    "Iztapalapa":             (19.3550, -99.0530),
    "La Magdalena Contreras": (19.3150, -99.2530),
    "Miguel Hidalgo":         (19.4150, -99.2000),
    "Milpa Alta":             (19.1920, -99.0230),
    "Tlahuac":                (19.2710, -99.0040),
    "Tlalpan":                (19.2710, -99.1690),
    "Venustiano Carranza":    (19.4380, -99.1050),
    "Xochimilco":             (19.2580, -99.1040),
}

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
body { font-family: 'Inter', sans-serif !important; background-color: #f8f9fa; }
.modern-title {
    position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999;
    background: rgba(20,22,30,0.85); backdrop-filter: blur(12px);
    padding: 14px 32px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
    color: #fff; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}
.modern-title h1 { margin: 0; font-size: 19px; font-weight: 700; }
.modern-title p  { margin: 3px 0 0 0; font-size: 11px; color: #FF6B6B; font-weight: 600; }
.risk-legend {
    position: fixed; bottom: 40px; right: 20px; z-index: 9999;
    background: rgba(20,22,30,0.85); backdrop-filter: blur(12px);
    padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
    color: #fff; min-width: 180px;
}
.risk-legend h4 { margin: 0 0 10px 0; font-size: 12px; color: #A0AABF; text-transform: uppercase; }
.risk-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:12px; }
.rdot { width:14px; height:14px; border-radius:50%; flex-shrink:0; border: 1px solid rgba(255,255,255,0.2); }
.stat-cards {
    position: fixed; top: 20px; left: 20px; z-index: 9999;
    display: flex; flex-direction: column; gap: 10px;
}
.stat-card {
    background: rgba(20,22,30,0.85); backdrop-filter: blur(12px);
    padding: 10px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
    color: white; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    display: flex; align-items: center; gap: 12px; min-width: 170px;
}
.stat-card .icon { font-size: 20px; }
.stat-card h4 { margin: 0; font-size: 9px; color: #A0AABF; text-transform: uppercase; }
.stat-card p { margin: 2px 0 0 0; font-size: 16px; font-weight: 700; }
</style>
"""


def normalizar_nombre(s):
    import unicodedata
    s = str(s).strip().title()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def construir_datos(locatel, carpetas):
    """Agrega conteos por alcaldía y calcula tasas."""
    for df in [locatel, carpetas]:
        df["alcaldia_norm"] = df["alcaldia_catalogo"].apply(normalizar_nombre)

    locatel  = locatel[locatel["alcaldia_norm"].isin(POBLACION_INEGI)]
    carpetas = carpetas[carpetas["alcaldia_norm"].isin(POBLACION_INEGI)]

    k = "alcaldia_norm"
    inc  = locatel.groupby(k).size().reset_index(name="total_incidencias")
    del_ = carpetas.groupby(k).size().reset_index(name="total_delitos")

    carpetas["hora"] = pd.to_datetime(
        carpetas["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    noc = carpetas[(carpetas["hora"] >= 20) | (carpetas["hora"] <= 5)]
    noc_ = noc.groupby(k).size().reset_index(name="total_delitos_nocturnos")

    alumb = locatel[locatel["tema_solicitud"] == "ALUMBRADO"]
    alumb_ = alumb.groupby(k).size().reset_index(name="total_alumbrado")

    agg = (inc.merge(del_, on=k, how="outer")
              .merge(alumb_, on=k, how="left")
              .merge(noc_,   on=k, how="left")
              .fillna(0))

    agg["poblacion"] = agg[k].map(POBLACION_INEGI)
    agg = agg.dropna(subset=["poblacion"])
    agg["poblacion"] = agg["poblacion"].astype(int)

    # Tasas por 1,000 hab
    for col in ["total_incidencias", "total_delitos", "total_alumbrado", "total_delitos_nocturnos"]:
        tasa_col = col.replace("total_", "tasa_")
        agg[tasa_col] = agg[col] / agg["poblacion"] * 1000

    # Proporción nocturnos
    agg["prop_nocturnos"] = np.where(
        agg["total_delitos"] > 0,
        agg["total_delitos_nocturnos"] / agg["total_delitos"] * 100, 0)

    # Coordenadas
    agg["lat"] = agg[k].map(lambda x: COORDS_ALCALDIA.get(x, (np.nan, np.nan))[0])
    agg["lon"] = agg[k].map(lambda x: COORDS_ALCALDIA.get(x, (np.nan, np.nan))[1])

    return agg


def cargar_lisa():
    """Intenta cargar resultados LISA si existen."""
    ruta = TABLAS_DIR / "lisa_por_alcaldia.csv"
    if ruta.exists():
        df = pd.read_csv(ruta)
        if "lisa_total_delitos" in df.columns and "alcaldia_catalogo" in df.columns:
            df["alcaldia_norm"] = df["alcaldia_catalogo"].apply(normalizar_nombre)
            return df[["alcaldia_norm", "lisa_total_delitos"]].copy()
    return None


def calcular_indice(agg):
    """Calcula el Índice de Riesgo Urbano (IRU) ponderado y normalizado 0-100."""
    # Componentes del índice y sus pesos
    componentes = {
        "tasa_delitos":           0.30,  # Peso principal: tasa delictiva general
        "tasa_alumbrado":         0.20,  # Infraestructura: fallas de alumbrado
        "tasa_delitos_nocturnos": 0.20,  # Delitos en horario vulnerable
        "prop_nocturnos":         0.15,  # Proporción de delitos nocturnos (intensidad)
        "tasa_incidencias":       0.15,  # Volumen total de fallas urbanas
    }

    print("\n   Componentes del IRU y pesos:")
    for comp, peso in componentes.items():
        print(f"      {comp:<30} → peso = {peso:.2f}")

    # Estandarización Z-Score de cada componente
    for comp in componentes:
        col_z = f"z_{comp}"
        mean_val = agg[comp].mean()
        std_val  = agg[comp].std()
        if std_val > 0:
            agg[col_z] = (agg[comp] - mean_val) / std_val
        else:
            agg[col_z] = 0.0

    # Bonificación LISA: penalizar +0.5σ si la alcaldía es Hot Spot (HH)
    lisa_df = cargar_lisa()
    agg["bonus_lisa"] = 0.0
    if lisa_df is not None:
        agg = agg.merge(lisa_df, on="alcaldia_norm", how="left")
        agg["lisa_total_delitos"] = agg["lisa_total_delitos"].fillna("NS")
        agg.loc[agg["lisa_total_delitos"] == "HH", "bonus_lisa"] = 0.5
        agg.loc[agg["lisa_total_delitos"] == "LL", "bonus_lisa"] = -0.3
        print("\n   [✓] Bonificación LISA aplicada (HH: +0.5σ, LL: -0.3σ)")
    else:
        print("\n   [!] Archivo LISA no encontrado — IRU sin bonificación espacial")

    # Suma ponderada
    agg["iru_raw"] = sum(
        agg[f"z_{comp}"] * peso for comp, peso in componentes.items()
    ) + agg["bonus_lisa"]

    # Normalización Min-Max → escala 0-100
    iru_min = agg["iru_raw"].min()
    iru_max = agg["iru_raw"].max()
    if iru_max > iru_min:
        agg["IRU"] = ((agg["iru_raw"] - iru_min) / (iru_max - iru_min)) * 100
    else:
        agg["IRU"] = 50.0

    agg["IRU"] = agg["IRU"].round(1)

    # Clasificación de riesgo
    agg["nivel_riesgo"] = pd.cut(
        agg["IRU"],
        bins=[-1, 25, 50, 75, 100],
        labels=["Bajo", "Medio", "Alto", "Muy Alto"]
    )

    return agg


RISK_COLORS = {
    "Muy Alto": "#D32F2F",
    "Alto":     "#FF6B6B",
    "Medio":    "#FFB347",
    "Bajo":     "#4CAF50",
}


def plot_ranking(agg):
    """Gráfico de barras horizontal del ranking IRU."""
    df_sorted = agg.sort_values("IRU", ascending=True).copy()

    fig, ax = plt.subplots(figsize=(14, 9), facecolor=DARK)
    fig.suptitle(
        "Índice de Riesgo Urbano (IRU) por Alcaldía — CDMX\n"
        "Escala 0–100 | Ponderado por tasas de delitos, alumbrado y LISA",
        fontsize=14, fontweight="bold", y=0.98)

    colors = [RISK_COLORS.get(str(n), MUTED) for n in df_sorted["nivel_riesgo"]]
    bars = ax.barh(
        range(len(df_sorted)), df_sorted["IRU"],
        color=colors, alpha=0.85, edgecolor=BORDER, height=0.65)

    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted["alcaldia_norm"], fontsize=9)
    ax.set_xlabel("Índice de Riesgo Urbano (IRU)", fontweight="bold")
    ax.set_xlim(0, 105)
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.set_axisbelow(True)

    # Etiquetas de valor + nivel
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        nivel = str(row["nivel_riesgo"])
        ax.text(row["IRU"] + 1.2, i,
                f'{row["IRU"]:.1f}  [{nivel}]',
                va="center", fontsize=8.5, color=TEXT, fontweight="bold")

    # Leyenda de niveles
    import matplotlib.patches as mpatches
    patches = [mpatches.Patch(color=c, label=k) for k, c in RISK_COLORS.items()]
    ax.legend(handles=patches, loc="lower right", fontsize=9,
              framealpha=0.6, edgecolor=BORDER, title="Nivel de Riesgo")

    fig.tight_layout(pad=2.0)
    ruta = GRAFICAS_DIR / "ranking_riesgo_alcaldias.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] {ruta.name}")


def plot_radar_top5(agg):
    """Gráfico radar de las 5 alcaldías con mayor IRU."""
    top5 = agg.nlargest(5, "IRU").copy()
    categorias = ["Tasa\nDelitos", "Tasa\nAlumbrado", "Tasa Del.\nNocturnos",
                  "Prop.\nNocturnos", "Tasa\nIncidencias"]
    z_cols = ["z_tasa_delitos", "z_tasa_alumbrado", "z_tasa_delitos_nocturnos",
              "z_prop_nocturnos", "z_tasa_incidencias"]

    N = len(categorias)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True), facecolor=DARK)
    ax.set_facecolor(PANEL)
    fig.suptitle("Perfil de Riesgo — Top 5 Alcaldías con Mayor IRU",
                 fontsize=14, fontweight="bold", y=0.98, color=TEXT)

    radar_colors = [RED, ORANGE, PURPLE, CYAN, "#FF85A1"]
    for i, (_, row) in enumerate(top5.iterrows()):
        values = [max(row[c], -2) for c in z_cols]
        values += values[:1]
        ax.plot(angles, values, linewidth=2, label=f'{row["alcaldia_norm"][:18]} (IRU={row["IRU"]:.0f})',
                color=radar_colors[i % len(radar_colors)])
        ax.fill(angles, values, alpha=0.08, color=radar_colors[i % len(radar_colors)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categorias, fontsize=9, color=TEXT)
    ax.tick_params(axis='y', colors=MUTED)
    ax.spines['polar'].set_color(BORDER)
    ax.grid(color=BORDER, alpha=0.4)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.05), fontsize=8.5,
              framealpha=0.6, edgecolor=BORDER)

    fig.tight_layout(pad=2.5)
    ruta = GRAFICAS_DIR / "radar_riesgo_top5.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] {ruta.name}")


def generar_mapa_riesgo(agg):
    """Mapa Folium con círculos proporcionales al IRU."""
    m = folium.Map(location=CDMX_CENTER, zoom_start=11,
                   tiles="CartoDB positron", control_scale=True)
    m.get_root().html.add_child(folium.Element(GLOBAL_CSS))

    m.get_root().html.add_child(folium.Element("""
    <div class="modern-title">
        <h1>Índice de Riesgo Urbano — CDMX</h1>
        <p>IRU Compuesto · Escala 0–100 · Ponderado por Infraestructura y Criminalidad</p>
    </div>"""))

    # Leyenda
    legend_rows = ""
    for nivel, color in RISK_COLORS.items():
        legend_rows += f'<div class="risk-row"><div class="rdot" style="background:{color}"></div>{nivel}</div>'
    m.get_root().html.add_child(folium.Element(f"""
    <div class="risk-legend">
        <h4>Nivel de Riesgo</h4>
        {legend_rows}
    </div>"""))

    # Stat cards
    top1 = agg.nlargest(1, "IRU").iloc[0]
    n_alto = len(agg[agg["nivel_riesgo"].isin(["Alto", "Muy Alto"])])
    m.get_root().html.add_child(folium.Element(f"""
    <div class="stat-cards">
        <div class="stat-card">
            <div class="icon">🔴</div>
            <div><h4>Mayor Riesgo</h4><p>{top1['alcaldia_norm']}</p></div>
        </div>
        <div class="stat-card">
            <div class="icon">⚠️</div>
            <div><h4>Alcaldías Alto/Muy Alto</h4><p>{n_alto} de 16</p></div>
        </div>
        <div class="stat-card">
            <div class="icon">📊</div>
            <div><h4>IRU Máximo</h4><p>{top1['IRU']:.1f}</p></div>
        </div>
    </div>"""))

    for _, row in agg.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            continue

        nivel = str(row["nivel_riesgo"])
        color = RISK_COLORS.get(nivel, MUTED)
        radius = 800 + row["IRU"] * 25  # Radio proporcional al IRU

        popup_html = f"""
        <div style='font-family:Inter,sans-serif;padding:12px;min-width:220px;'>
        <h4 style='margin:0 0 10px 0;color:#333;'>{row['alcaldia_norm']}</h4>
        <div style='font-size:28px;font-weight:800;color:{color};margin-bottom:8px;'>
            IRU: {row['IRU']:.1f}
        </div>
        <div style='font-size:11px;color:#555;line-height:1.7;'>
            <b>Nivel:</b> <span style='color:{color};font-weight:700;'>{nivel}</span><br>
            <b>Tasa Delitos:</b> {row['tasa_delitos']:.1f} / 1,000 hab<br>
            <b>Tasa Alumbrado:</b> {row['tasa_alumbrado']:.2f} / 1,000 hab<br>
            <b>Delitos Nocturnos:</b> {row['prop_nocturnos']:.1f}% del total<br>
            <b>Población:</b> {int(row['poblacion']):,}
        </div></div>"""

        folium.Circle(
            [row["lat"], row["lon"]], radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.25, weight=2,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

        folium.CircleMarker(
            [row["lat"], row["lon"]], radius=7,
            color="white", fill=True, fill_color=color,
            fill_opacity=1, weight=1.5,
            tooltip=f'{row["alcaldia_norm"]}: IRU {row["IRU"]:.0f}'
        ).add_to(m)

    ruta = MAPAS_DIR / "mapa_riesgo_coropletico.html"
    m.save(str(ruta))
    print(f"   [✓] {ruta.name}")


def main():
    print("=" * 70)
    print("  ÍNDICE DE RIESGO URBANO COMPUESTO  [A-6]")
    print("=" * 70)

    print("\n[1/4] Cargando y preparando datos...")
    locatel  = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    agg = construir_datos(locatel, carpetas)
    print(f"   Alcaldías procesadas: {len(agg)}")

    print("\n[2/4] Calculando Índice de Riesgo Urbano (IRU)...")
    agg = calcular_indice(agg)

    # Mostrar ranking
    ranking = agg[["alcaldia_norm", "IRU", "nivel_riesgo",
                    "tasa_delitos", "tasa_alumbrado", "prop_nocturnos"]
                  ].sort_values("IRU", ascending=False)
    print(f"\n   {'Alcaldía':<28} {'IRU':>6}  {'Nivel':<10} {'Tasa Del.':>10} {'Tasa Alum.':>11}")
    print(f"   {'-'*70}")
    for _, row in ranking.iterrows():
        print(f"   {row['alcaldia_norm']:<28} {row['IRU']:>6.1f}  "
              f"{str(row['nivel_riesgo']):<10} {row['tasa_delitos']:>10.1f} "
              f"{row['tasa_alumbrado']:>11.2f}")

    # Exportar tabla
    cols_export = ["alcaldia_norm", "poblacion",
                   "total_delitos", "total_alumbrado", "total_delitos_nocturnos",
                   "tasa_delitos", "tasa_alumbrado", "tasa_delitos_nocturnos",
                   "prop_nocturnos", "IRU", "nivel_riesgo", "lat", "lon"]
    cols_export = [c for c in cols_export if c in agg.columns]
    ruta_csv = TABLAS_DIR / "indice_riesgo_urbano.csv"
    agg[cols_export].sort_values("IRU", ascending=False).to_csv(
        ruta_csv, index=False, encoding="utf-8-sig")
    print(f"\n   [✓] Tabla exportada: {ruta_csv.name}")

    print("\n[3/4] Generando visualizaciones...")
    plot_ranking(agg)
    plot_radar_top5(agg)

    print("\n[4/4] Generando mapa interactivo...")
    generar_mapa_riesgo(agg)

    # Resumen final
    top = agg.nlargest(3, "IRU")
    print("\n" + "=" * 70)
    print("  ÍNDICE DE RIESGO URBANO COMPLETADO")
    print(f"  Top 3 alcaldías de mayor riesgo:")
    for i, (_, r) in enumerate(top.iterrows(), 1):
        print(f"    {i}. {r['alcaldia_norm']} — IRU: {r['IRU']:.1f} [{r['nivel_riesgo']}]")
    print("=" * 70)


if __name__ == "__main__":
    main()
