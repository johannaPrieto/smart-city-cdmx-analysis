"""
Autocorrelación Espacial: Moran's I + LISA — Smart City CDMX  [A-4]
=====================================================================
Cuantifica si la distribución espacial de delitos e incidencias
presenta clustering estadísticamente significativo (no aleatorio).

Análisis:
  1. Global Moran's I  — clustering espacial de toda la ciudad
  2. Local Moran's I (LISA) — identificar HH/LL/HL/LH por colonia
  3. Moran Scatter Plot
  4. Mapa Folium interactivo con clusters LISA

Requisitos adicionales:
  pip install esda libpysal

Salidas:
  resultados/tablas/moran_I_resultados.csv
  resultados/graficas/moran_scatterplot.png
  resultados/mapas/mapa_lisa_clusters.html

Uso:
  python scripts/analisis/moran_I.py
"""

import io, sys, warnings
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import folium

warnings.filterwarnings("ignore")

# Importaciones espaciales con mensaje amigable si faltan
try:
    import libpysal
    from libpysal.weights import KNN
    from libpysal.weights.spatial_lag import lag_spatial
    import esda
    from esda.moran import Moran, Moran_Local
    HAS_ESDA = True
except ImportError:
    HAS_ESDA = False
    print("=" * 70)
    print("  ERROR: Faltan librerías espaciales.")
    print("  Ejecuta: pip install esda libpysal")
    print("=" * 70)
    sys.exit(1)

ROOT        = Path(__file__).resolve().parents[2]
DATA_DIR    = ROOT / "datasets" / "processed"
TABLAS_DIR  = ROOT / "resultados" / "tablas"
GRAFICAS_DIR = ROOT / "resultados" / "graficas"
MAPAS_DIR   = ROOT / "resultados" / "mapas"

DARK, PANEL, BORDER = "#0F1117", "#1A1D27", "#2E3347"
TEXT, MUTED = "#E0E0E0", "#A0AABF"
PURPLE, CYAN, RED, ORANGE = "#7C5CFC", "#00D9A3", "#FF6B6B", "#FFB347"
CDMX_CENTER = [19.38, -99.14]

# Colores LISA: HH=rojo, LL=azul, HL=naranja claro, LH=azul claro, NS=gris
LISA_COLORS = {
    "HH": "#D7191C",   # Hot spot (alto rodeado de alto)
    "LL": "#2C7BB6",   # Cold spot (bajo rodeado de bajo)
    "HL": "#FDAE61",   # Outlier (alto rodeado de bajo)
    "LH": "#ABD9E9",   # Outlier (bajo rodeado de alto)
    "NS": "#555566",   # No significativo
}

plt.rcParams.update({
    "figure.facecolor": DARK, "axes.facecolor": PANEL,
    "axes.edgecolor": BORDER, "axes.labelcolor": TEXT,
    "text.color": TEXT, "xtick.color": MUTED, "ytick.color": MUTED,
    "grid.color": BORDER, "grid.alpha": 0.5, "font.family": "sans-serif",
})

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
body { font-family: 'Inter', sans-serif !important; }
.modern-title {
    position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999;
    background: rgba(20,22,30,0.85); backdrop-filter: blur(12px);
    padding: 14px 32px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
    color: #fff; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}
.modern-title h1 { margin: 0; font-size: 19px; font-weight: 700; }
.modern-title p  { margin: 3px 0 0 0; font-size: 11px; color: #7C5CFC; }
.lisa-legend {
    position: fixed; bottom: 40px; right: 20px; z-index: 9999;
    background: rgba(20,22,30,0.85); backdrop-filter: blur(12px);
    padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
    color: #fff; min-width: 180px;
}
.lisa-legend h4 { margin: 0 0 8px 0; font-size: 12px; color: #A0AABF; text-transform: uppercase; }
.lisa-row { display:flex; align-items:center; gap:8px; margin-bottom:5px; font-size:12px; }
.dot { width:12px; height:12px; border-radius:50%; flex-shrink:0; }
</style>
"""


def build_alcaldia_df(locatel, carpetas):
    """Agrega conteos a nivel alcaldía con coordenadas promedio."""
    for df in [locatel, carpetas]:
        df["alcaldia_catalogo"] = df["alcaldia_catalogo"].astype(str).str.title().str.strip()

    locatel  = locatel[locatel["alcaldia_catalogo"].notna() &
                       (locatel["alcaldia_catalogo"] != "Desconocida")]
    carpetas = carpetas[carpetas["alcaldia_catalogo"].notna() &
                        (carpetas["alcaldia_catalogo"] != "Desconocida")]

    k = "alcaldia_catalogo"
    inc  = locatel.groupby(k).size().reset_index(name="total_incidencias")
    del_ = carpetas.groupby(k).size().reset_index(name="total_delitos")

    # Coordenada centroide aproximada de cada alcaldía
    lat_c = locatel.groupby(k)["latitud"].median().reset_index(name="lat")
    lon_c = locatel.groupby(k)["longitud"].median().reset_index(name="lon")

    carpetas["hora"] = pd.to_datetime(
        carpetas["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    noc = carpetas[(carpetas["hora"] >= 20) | (carpetas["hora"] <= 5)]
    noc_ = noc.groupby(k).size().reset_index(name="total_delitos_nocturnos")

    alumb = locatel[locatel["tema_solicitud"] == "ALUMBRADO"]
    alumb_ = alumb.groupby(k).size().reset_index(name="total_alumbrado")

    df_agg = (inc.merge(del_,   on=k, how="outer")
                 .merge(alumb_, on=k, how="left")
                 .merge(noc_,   on=k, how="left")
                 .merge(lat_c,  on=k, how="left")
                 .merge(lon_c,  on=k, how="left")
                 .fillna(0))

    return df_agg.dropna(subset=["lat", "lon"])


def calcular_moran_global(y, w, var_name):
    mi = Moran(y, w, permutations=999)
    print(f"\n   [{var_name}]")
    print(f"      Moran's I  = {mi.I:.4f}")
    print(f"      E[I]       = {mi.EI:.4f}  (esperado bajo aleatoriedad)")
    print(f"      Z-score    = {mi.z_norm:.4f}")
    print(f"      p-value    = {mi.p_norm:.4f}  {'✓ sig.' if mi.p_norm < 0.05 else '✗ no sig.'}")
    return mi


def clasificar_lisa(mi_local, alpha=0.05):
    """Clasifica cada unidad en HH/LL/HL/LH/NS."""
    z    = mi_local.z
    pval = mi_local.p_sim

    # z_lag no está disponible en todas las versiones de esda;
    # se calcula manualmente como el lag espacial estandarizado.
    if hasattr(mi_local, "z_lag"):
        z_lag = mi_local.z_lag
    else:
        z_lag = lag_spatial(mi_local.w, z)

    labels = []
    for zi, zli, pi in zip(z, z_lag, pval):
        if pi > alpha:
            labels.append("NS")
        elif zi > 0 and zli > 0:
            labels.append("HH")
        elif zi < 0 and zli < 0:
            labels.append("LL")
        elif zi > 0 and zli < 0:
            labels.append("HL")
        else:
            labels.append("LH")
    return labels


def plot_moran_scatter(df_agg, mi_del, mi_alumb, mi_local_del, mi_local_alumb):
    fig, axes = plt.subplots(1, 2, figsize=(16, 8), facecolor=DARK)
    fig.suptitle(
        "Moran Scatter Plot — Autocorrelación Espacial\n"
        "(cada punto = una alcaldía; pendiente = Moran's I)",
        fontsize=14, fontweight="bold", y=1.01)

    pairs = [
        (axes[0], mi_del,   mi_local_del,   "total_delitos",      "Total Delitos",     RED),
        (axes[1], mi_alumb, mi_local_alumb, "total_alumbrado",   "Fallas Alumbrado",  CYAN),
    ]

    for ax, mi, mi_loc, var, label, color in pairs:
        z     = mi_loc.z
        z_lag = mi_loc.z_lag if hasattr(mi_loc, "z_lag") else lag_spatial(mi_loc.w, z)
        lisa_labels = clasificar_lisa(mi_loc)

        colors_pt = [LISA_COLORS[l] for l in lisa_labels]
        ax.scatter(z, z_lag, c=colors_pt, alpha=0.85, s=80,
                   edgecolors="white", linewidths=0.5, zorder=3)

        # Línea de regresión (pendiente = Moran's I)
        x_line = np.linspace(min(z), max(z), 100)
        ax.plot(x_line, mi.I * x_line, color="white", lw=2, ls="--", alpha=0.8,
                label=f"I = {mi.I:.4f}  (p={mi.p_norm:.3f})")

        # Cuadrantes
        ax.axhline(0, color=MUTED, lw=0.8, ls="-", alpha=0.4)
        ax.axvline(0, color=MUTED, lw=0.8, ls="-", alpha=0.4)
        ax.text( 0.98, 0.98, "HH", transform=ax.transAxes, ha="right", va="top",
                 fontsize=10, color=LISA_COLORS["HH"], alpha=0.7, fontweight="bold")
        ax.text( 0.02, 0.02, "LL", transform=ax.transAxes, ha="left", va="bottom",
                 fontsize=10, color=LISA_COLORS["LL"], alpha=0.7, fontweight="bold")
        ax.text( 0.98, 0.02, "HL", transform=ax.transAxes, ha="right", va="bottom",
                 fontsize=10, color=LISA_COLORS["HL"], alpha=0.7, fontweight="bold")
        ax.text( 0.02, 0.98, "LH", transform=ax.transAxes, ha="left", va="top",
                 fontsize=10, color=LISA_COLORS["LH"], alpha=0.7, fontweight="bold")

        for i, (xi, yi, alc) in enumerate(
                zip(z, z_lag, df_agg["alcaldia_catalogo"])):
            ax.annotate(alc[:14], (xi, yi),
                        textcoords="offset points", xytext=(4, 3),
                        fontsize=7, color=MUTED, alpha=0.8)

        ax.set_title(f"{label}\nMoran's I = {mi.I:.4f}  p = {mi.p_norm:.3f}",
                     fontweight="bold", pad=10)
        ax.set_xlabel("Variable estandarizada (z)")
        ax.set_ylabel("Lag espacial (promedio de vecinos)")
        ax.legend(fontsize=9, framealpha=0.5, edgecolor=BORDER)
        ax.grid(True, linestyle="--", alpha=0.2)

    # Leyenda LISA
    patches = [mpatches.Patch(color=v, label=k) for k, v in LISA_COLORS.items()]
    fig.legend(handles=patches, loc="lower center", ncol=5, fontsize=9,
               framealpha=0.5, edgecolor=BORDER, title="Categoría LISA")

    fig.tight_layout(pad=2.5)
    ruta = GRAFICAS_DIR / "moran_scatterplot.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] {ruta.name}")


def generar_mapa_lisa(df_agg, lisa_labels_del, lisa_labels_alumb):
    m = folium.Map(location=CDMX_CENTER, zoom_start=11,
                   tiles="CartoDB dark_matter", control_scale=True)
    m.get_root().html.add_child(folium.Element(GLOBAL_CSS))
    m.get_root().html.add_child(folium.Element("""
    <div class="modern-title">
        <h1>Autocorrelación Espacial — LISA (Local Moran's I)</h1>
        <p>Análisis de Delitos · Hot Spots y Cold Spots estadísticamente significativos</p>
    </div>"""))

    # Leyenda
    legend_rows = "".join(
        f'<div class="lisa-row"><div class="dot" style="background:{c}"></div>{k}</div>'
        for k, c in LISA_COLORS.items()
        if k != "NS"
    )
    m.get_root().html.add_child(folium.Element(f"""
    <div class="lisa-legend">
        <h4>Clasificación LISA (Delitos)</h4>
        {legend_rows}
        <div class="lisa-row"><div class="dot" style="background:{LISA_COLORS['NS']}"></div>No Significativo</div>
    </div>"""))

    for _, row in df_agg.iterrows():
        idx = df_agg.index.get_loc(_)
        cat_del  = lisa_labels_del[idx]
        cat_alum = lisa_labels_alumb[idx]
        color    = LISA_COLORS.get(cat_del, LISA_COLORS["NS"])

        popup_html = f"""
        <div style='font-family:Inter,sans-serif;padding:10px;min-width:200px;'>
        <h4 style='margin:0 0 8px 0;color:#333;'>{row['alcaldia_catalogo']}</h4>
        <div style='font-size:12px;color:#555;'>
            <b>LISA Delitos:</b> <span style='color:{color};font-weight:700;'>{cat_del}</span><br>
            <b>LISA Alumbrado:</b> {cat_alum}<br>
            <b>Total Delitos:</b> {int(row['total_delitos']):,}<br>
            <b>Fallas Alumbrado:</b> {int(row['total_alumbrado']):,}
        </div></div>"""

        folium.Circle(
            [row["lat"], row["lon"]], radius=2500,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.45, weight=1.5,
            popup=folium.Popup(popup_html, max_width=280)
        ).add_to(m)
        folium.CircleMarker(
            [row["lat"], row["lon"]], radius=6,
            color="white", fill=True, fill_color=color,
            fill_opacity=1, weight=1
        ).add_to(m)

    ruta = MAPAS_DIR / "mapa_lisa_clusters.html"
    m.save(str(ruta))
    print(f"   [✓] {ruta.name}")


def main():
    print("=" * 70)
    print("  AUTOCORRELACIÓN ESPACIAL — MORAN'S I + LISA  [A-4]")
    print("=" * 70)

    print("\n[1/4] Cargando y agregando datos por alcaldía...")
    locatel  = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    locatel  = locatel[locatel["latitud"].notna() & locatel["longitud"].notna() &
                       (locatel["latitud"] > 19.0) & (locatel["latitud"] < 19.8) &
                       (locatel["longitud"] > -99.5) & (locatel["longitud"] < -98.8)]
    carpetas = carpetas[carpetas["latitud"].notna() & carpetas["longitud"].notna() &
                        (carpetas["latitud"] > 19.0) & (carpetas["latitud"] < 19.8) &
                        (carpetas["longitud"] > -99.5) & (carpetas["longitud"] < -98.8)]

    df_agg = build_alcaldia_df(locatel, carpetas)
    print(f"   Alcaldías con datos: {len(df_agg)}")

    # ── Matriz de pesos espaciales ────────────────────────────────────────────
    print("[2/4] Construyendo matriz de pesos espaciales (KNN k=5)...")
    coords_xy = df_agg[["lon", "lat"]].values.astype(float)

    # Con pocas unidades (16 alcaldías), usamos KNN k=4
    k_neighbors = min(4, len(df_agg) - 1)
    w = KNN.from_array(coords_xy, k=k_neighbors)
    w.transform = "R"   # Row-standardized

    # ── Moran's I Global ─────────────────────────────────────────────────────
    print("[3/4] Calculando Moran's I Global y LISA...")
    vars_analisis = {
        "total_delitos":           "Total Delitos",
        "total_alumbrado":         "Fallas Alumbrado",
        "total_delitos_nocturnos": "Delitos Nocturnos",
        "total_incidencias":       "Incidencias Locatel",
    }

    resultados = []
    mi_del, mi_alumb = None, None
    mi_local_del, mi_local_alumb = None, None

    for var, label in vars_analisis.items():
        y = df_agg[var].values.astype(float)
        mi = calcular_moran_global(y, w, label)
        mi_loc = Moran_Local(y, w, permutations=999, seed=42)
        lisa_labels = clasificar_lisa(mi_loc)

        if var == "total_delitos":
            mi_del, mi_local_del = mi, mi_loc
        elif var == "total_alumbrado":
            mi_alumb, mi_local_alumb = mi, mi_loc

        df_agg[f"lisa_{var}"] = lisa_labels
        df_agg[f"moran_local_{var}"] = mi_loc.Is

        # Conteo por categoría LISA
        cats = pd.Series(lisa_labels).value_counts().to_dict()
        resultados.append({
            "variable": label,
            "moran_I": round(mi.I, 5),
            "z_score": round(mi.z_norm, 4),
            "p_value": round(mi.p_norm, 5),
            "significativo": mi.p_norm < 0.05,
            "HH": cats.get("HH", 0),
            "LL": cats.get("LL", 0),
            "HL": cats.get("HL", 0),
            "LH": cats.get("LH", 0),
            "NS": cats.get("NS", 0),
        })

    df_res = pd.DataFrame(resultados)
    ruta_res = TABLAS_DIR / "moran_I_resultados.csv"
    df_res.to_csv(ruta_res, index=False, encoding="utf-8-sig")
    print(f"\n   [✓] Tabla exportada: {ruta_res.name}")

    df_agg.to_csv(TABLAS_DIR / "lisa_por_alcaldia.csv", index=False, encoding="utf-8-sig")

    # ── Visualizaciones ───────────────────────────────────────────────────────
    print("[4/4] Generando visualizaciones...")
    lisa_del  = df_agg["lisa_total_delitos"].tolist()
    lisa_alum = df_agg["lisa_total_alumbrado"].tolist()
    plot_moran_scatter(df_agg, mi_del, mi_alumb, mi_local_del, mi_local_alumb)
    generar_mapa_lisa(df_agg, lisa_del, lisa_alum)

    print("\n" + "=" * 70)
    print("  AUTOCORRELACIÓN ESPACIAL COMPLETADA")
    print(f"  Moran's I (Delitos): {mi_del.I:.4f}  p={mi_del.p_norm:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
