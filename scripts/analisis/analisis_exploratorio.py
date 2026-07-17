"""
Análisis Exploratorio — Smart City CDMX
=========================================
Genera tablas resumen (CSV) y gráficas (PNG) a partir de los datasets limpios.

Salidas:
  - resultados/tablas/  → 13 archivos CSV
  - resultados/graficas/ → 12 archivos PNG

Uso:
  python scripts/analisis/analisis_exploratorio.py
"""

import io
import os
import sys
import warnings

# Forzar UTF-8 en stdout para Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Backend no-interactivo para generar PNGs

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore", category=FutureWarning)

# ─── Configuración de rutas ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]  # d:/cdmx-analysis
DATA_DIR = ROOT / "datasets" / "processed"
TABLAS_DIR = ROOT / "resultados" / "tablas"
GRAFICAS_DIR = ROOT / "resultados" / "graficas"

TABLAS_DIR.mkdir(parents=True, exist_ok=True)
GRAFICAS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Estilo visual ───────────────────────────────────────────────────────────
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
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "figure.titlesize": 16,
    "figure.titleweight": "bold",
    "savefig.dpi": 180,
    "savefig.bbox": "tight",
    "savefig.facecolor": "#0F1117",
    "savefig.pad_inches": 0.3,
})

# Paleta personalizada
PAL_MAIN = "#7C5CFC"       # Morado vibrante
PAL_SECONDARY = "#00D9A3"  # Verde turquesa
PAL_ACCENT = "#FF6B6B"     # Coral
PAL_WARM = "#FFB347"        # Naranja cálido
GRADIENT_BLUES = sns.color_palette("mako", 16)
GRADIENT_REDS = sns.color_palette("rocket", 16)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════
def cargar_datos():
    """Carga los 3 datasets principales y parsea fechas."""
    print("[CARGA] Cargando datos limpios...")

    locatel = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")
    victimas = pd.read_csv(DATA_DIR / "victimasFGJ_2024_limpio.csv")

    # Parsear fechas
    locatel["datetime_solicitud"] = pd.to_datetime(locatel["datetime_solicitud"], errors="coerce")
    carpetas["datetime_hecho"] = pd.to_datetime(carpetas["datetime_hecho"], errors="coerce")
    victimas["datetime_hecho"] = pd.to_datetime(victimas["datetime_hecho"], errors="coerce")

    # Extraer componentes temporales — Locatel
    locatel["mes"] = locatel["datetime_solicitud"].dt.month
    locatel["nombre_mes"] = locatel["datetime_solicitud"].dt.month_name(locale=None)
    locatel["dia_semana"] = locatel["datetime_solicitud"].dt.day_name()
    locatel["hora"] = pd.to_datetime(locatel["hora_solicitud"], format="%H:%M:%S", errors="coerce").dt.hour

    # Extraer componentes temporales — Carpetas FGJ
    carpetas["mes"] = carpetas["datetime_hecho"].dt.month
    carpetas["nombre_mes"] = carpetas["datetime_hecho"].dt.month_name(locale=None)
    carpetas["dia_semana"] = carpetas["datetime_hecho"].dt.day_name()
    carpetas["hora"] = pd.to_datetime(carpetas["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour

    # Normalizar alcaldía a formato título para consistencia entre datasets
    for df in [locatel, carpetas, victimas]:
        if "alcaldia_catalogo" in df.columns:
            df["alcaldia_catalogo"] = df["alcaldia_catalogo"].str.title()
        if "colonia_catalogo" in df.columns:
            df["colonia_catalogo"] = df["colonia_catalogo"].str.title()

    print(f"   Locatel:  {len(locatel):>10,} filas")
    print(f"   Carpetas: {len(carpetas):>10,} filas")
    print(f"   Victimas: {len(victimas):>10,} filas")

    return locatel, carpetas, victimas


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GENERACIÓN DE TABLAS RESUMEN
# ═══════════════════════════════════════════════════════════════════════════════
def generar_tablas(locatel: pd.DataFrame, carpetas: pd.DataFrame):
    """Genera 13 tablas resumen y las guarda como CSV."""
    print("\n[TABLAS] Generando tablas resumen...")
    tablas = {}

    # --- LOCATEL (Incidencias urbanas) ---

    # 1. Incidencias por alcaldía
    t = (locatel["alcaldia_catalogo"]
         .value_counts()
         .reset_index()
         .rename(columns={"alcaldia_catalogo": "alcaldia", "count": "total_incidencias"}))
    t = t[t["alcaldia"] != "DESCONOCIDA"]
    tablas["incidencias_por_alcaldia"] = t

    # 2. Incidencias por tema
    t = (locatel["tema_solicitud"]
         .value_counts()
         .reset_index()
         .rename(columns={"tema_solicitud": "tema", "count": "total_incidencias"}))
    tablas["incidencias_por_tema"] = t

    # 3. Incidencias por mes
    meses_orden = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                   5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                   9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    t = (locatel.groupby("mes").size().reset_index(name="total_incidencias"))
    t["nombre_mes"] = t["mes"].map(meses_orden)
    t = t.sort_values("mes")
    tablas["incidencias_por_mes"] = t

    # 4. Incidencias por día de semana
    dias_orden = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dias_es = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
               "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}
    t = (locatel["dia_semana"]
         .value_counts()
         .reindex(dias_orden)
         .reset_index()
         .rename(columns={"dia_semana": "dia_semana", "count": "total_incidencias"}))
    t["dia_es"] = t["dia_semana"].map(dias_es)
    tablas["incidencias_por_dia_semana"] = t

    # 5. Incidencias por hora
    t = (locatel.groupby("hora").size().reset_index(name="total_incidencias").sort_values("hora"))
    tablas["incidencias_por_hora"] = t

    # 6. Top 50 colonias incidencias
    t = (locatel[locatel["colonia_catalogo"] != "DESCONOCIDA"]
         .groupby(["alcaldia_catalogo", "colonia_catalogo"])
         .size()
         .reset_index(name="total_incidencias")
         .sort_values("total_incidencias", ascending=False)
         .head(50)
         .rename(columns={"alcaldia_catalogo": "alcaldia", "colonia_catalogo": "colonia"}))
    tablas["top_colonias_incidencias"] = t

    # --- CARPETAS FGJ (Delitos) ---

    # 7. Delitos por alcaldía
    t = (carpetas["alcaldia_catalogo"]
         .value_counts()
         .reset_index()
         .rename(columns={"alcaldia_catalogo": "alcaldia", "count": "total_delitos"}))
    t = t[t["alcaldia"].notna()]
    tablas["delitos_por_alcaldia"] = t

    # 8. Delitos por categoría
    t = (carpetas["categoria_delito"]
         .value_counts()
         .reset_index()
         .rename(columns={"categoria_delito": "categoria", "count": "total_delitos"}))
    tablas["delitos_por_categoria"] = t

    # 9. Delitos por tipo (top 30)
    t = (carpetas["delito"]
         .value_counts()
         .head(30)
         .reset_index()
         .rename(columns={"delito": "delito", "count": "total_delitos"}))
    tablas["delitos_por_delito"] = t

    # 10. Delitos por mes
    t = (carpetas.groupby("mes").size().reset_index(name="total_delitos"))
    t["nombre_mes"] = t["mes"].map(meses_orden)
    t = t.sort_values("mes")
    tablas["delitos_por_mes"] = t

    # 11. Delitos por día de semana
    t = (carpetas["dia_semana"]
         .value_counts()
         .reindex(dias_orden)
         .reset_index()
         .rename(columns={"dia_semana": "dia_semana", "count": "total_delitos"}))
    t["dia_es"] = t["dia_semana"].map(dias_es)
    tablas["delitos_por_dia_semana"] = t

    # 12. Delitos por hora
    t = (carpetas.groupby("hora").size().reset_index(name="total_delitos").sort_values("hora"))
    tablas["delitos_por_hora"] = t

    # 13. Top 50 colonias delitos
    t = (carpetas[carpetas["colonia_catalogo"].notna()]
         .groupby(["alcaldia_catalogo", "colonia_catalogo"])
         .size()
         .reset_index(name="total_delitos")
         .sort_values("total_delitos", ascending=False)
         .head(50)
         .rename(columns={"alcaldia_catalogo": "alcaldia", "colonia_catalogo": "colonia"}))
    tablas["top_colonias_delitos"] = t

    # Guardar todas
    for nombre, df in tablas.items():
        ruta = TABLAS_DIR / f"{nombre}.csv"
        df.to_csv(ruta, index=False, encoding="utf-8-sig")
        print(f"   OK: {ruta.name} ({len(df)} filas)")

    return tablas


# ═══════════════════════════════════════════════════════════════════════════════
# 3. GENERACIÓN DE GRÁFICAS
# ═══════════════════════════════════════════════════════════════════════════════
def _guardar(fig, nombre):
    """Guarda figura y cierra."""
    ruta = GRAFICAS_DIR / nombre
    fig.savefig(ruta)
    plt.close(fig)
    print(f"   OK: {nombre}")


def grafica_barras_h(data, x_col, y_col, titulo, color, nombre_archivo, xlabel=""):
    """Barras horizontales estilizadas."""
    fig, ax = plt.subplots(figsize=(12, max(6, len(data) * 0.4)))

    bars = ax.barh(data[y_col], data[x_col], color=color, edgecolor="none", height=0.65)

    # Etiquetas de valor
    max_val = data[x_col].max()
    for bar in bars:
        w = bar.get_width()
        ax.text(w + max_val * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{int(w):,}", va="center", fontsize=9, color="#B0B0B0")

    ax.set_title(titulo, pad=15)
    ax.set_xlabel(xlabel)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    fig.tight_layout()
    _guardar(fig, nombre_archivo)


def grafica_lineas(data, x_col, y_col, titulo, color, nombre_archivo, ylabel=""):
    """Líneas con marcadores y relleno."""
    fig, ax = plt.subplots(figsize=(12, 5.5))

    ax.fill_between(data[x_col], data[y_col], alpha=0.15, color=color)
    ax.plot(data[x_col], data[y_col], marker="o", markersize=7,
            linewidth=2.5, color=color, markeredgecolor="white", markeredgewidth=1.5)

    # Etiquetas en cada punto
    for _, row in data.iterrows():
        ax.annotate(f"{int(row[y_col]):,}",
                     (row[x_col], row[y_col]),
                     textcoords="offset points", xytext=(0, 12),
                     ha="center", fontsize=8, color="#B0B0B0")

    ax.set_title(titulo, pad=15)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    plt.xticks(rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    fig.tight_layout()
    _guardar(fig, nombre_archivo)


def grafica_barras_v(data, x_col, y_col, titulo, color, nombre_archivo, ylabel=""):
    """Barras verticales estilizadas."""
    fig, ax = plt.subplots(figsize=(12, 5.5))

    bars = ax.bar(data[x_col].astype(str), data[y_col], color=color,
                  edgecolor="none", width=0.7)

    max_val = data[y_col].max()
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + max_val * 0.01,
                f"{int(h):,}", ha="center", fontsize=8, color="#B0B0B0")

    ax.set_title(titulo, pad=15)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    plt.xticks(rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    fig.tight_layout()
    _guardar(fig, nombre_archivo)


def generar_graficas(tablas: dict, locatel: pd.DataFrame, carpetas: pd.DataFrame):
    """Genera las 12 gráficas del análisis exploratorio."""
    print("\n[GRAFICAS] Generando graficas...")

    # 1. Incidencias por alcaldía
    d = tablas["incidencias_por_alcaldia"].sort_values("total_incidencias")
    grafica_barras_h(d, "total_incidencias", "alcaldia",
                     "Incidencias Urbanas por Alcaldía (Locatel 0311 — 2024)",
                     PAL_MAIN, "incidencias_por_alcaldia.png",
                     xlabel="Total de incidencias")

    # 2. Delitos por alcaldía
    d = tablas["delitos_por_alcaldia"].sort_values("total_delitos")
    grafica_barras_h(d, "total_delitos", "alcaldia",
                     "Carpetas de Investigación por Alcaldía (FGJ — 2024)",
                     PAL_ACCENT, "delitos_por_alcaldia.png",
                     xlabel="Total de carpetas")

    # 3. Incidencias por mes
    d = tablas["incidencias_por_mes"].copy()
    grafica_lineas(d, "nombre_mes", "total_incidencias",
                   "Incidencias Urbanas por Mes (Locatel 0311 — 2024)",
                   PAL_MAIN, "incidencias_por_mes.png",
                   ylabel="Total de incidencias")

    # 4. Delitos por mes
    d = tablas["delitos_por_mes"].copy()
    grafica_lineas(d, "nombre_mes", "total_delitos",
                   "Carpetas de Investigación por Mes (FGJ — 2024)",
                   PAL_ACCENT, "delitos_por_mes.png",
                   ylabel="Total de carpetas")

    # 5. Incidencias por hora
    d = tablas["incidencias_por_hora"].copy()
    # Generar gradiente de colores por hora
    n = len(d)
    colores_hora = [plt.cm.cool(i / n) for i in range(n)]
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.bar(d["hora"].astype(str), d["total_incidencias"], color=colores_hora,
           edgecolor="none", width=0.75)
    ax.set_title("Incidencias Urbanas por Hora del Día (Locatel 0311 — 2024)", pad=15)
    ax.set_xlabel("Hora")
    ax.set_ylabel("Total de incidencias")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    fig.tight_layout()
    _guardar(fig, "incidencias_por_hora.png")

    # 6. Delitos por hora
    d = tablas["delitos_por_hora"].copy()
    colores_hora2 = [plt.cm.hot(0.3 + 0.5 * i / max(1, n - 1)) for i in range(len(d))]
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.bar(d["hora"].astype(str), d["total_delitos"], color=colores_hora2,
           edgecolor="none", width=0.75)
    ax.set_title("Carpetas de Investigación por Hora del Día (FGJ — 2024)", pad=15)
    ax.set_xlabel("Hora")
    ax.set_ylabel("Total de carpetas")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    fig.tight_layout()
    _guardar(fig, "delitos_por_hora.png")

    # 7. Top 15 temas incidencias
    d = tablas["incidencias_por_tema"].head(15).sort_values("total_incidencias")
    grafica_barras_h(d, "total_incidencias", "tema",
                     "Top 15 Temas de Incidencias Urbanas (Locatel 0311 — 2024)",
                     PAL_SECONDARY, "top_temas_incidencias.png",
                     xlabel="Total de incidencias")

    # 8. Top 15 delitos
    d = tablas["delitos_por_delito"].head(15).copy()
    # Acortar nombres largos
    d["delito_corto"] = d["delito"].str[:55].where(
        d["delito"].str.len() <= 55,
        d["delito"].str[:52] + "..."
    )
    d = d.sort_values("total_delitos")
    grafica_barras_h(d, "total_delitos", "delito_corto",
                     "Top 15 Delitos Más Frecuentes (FGJ — 2024)",
                     PAL_WARM, "top_delitos.png",
                     xlabel="Total de carpetas")

    # 9. Incidencias por día de semana
    d = tablas["incidencias_por_dia_semana"].copy()
    dias_es_orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    d = d.set_index("dia_es").reindex(dias_es_orden).reset_index()
    grafica_barras_v(d, "dia_es", "total_incidencias",
                     "Incidencias Urbanas por Día de la Semana (Locatel 0311 — 2024)",
                     PAL_MAIN, "incidencias_por_dia_semana.png",
                     ylabel="Total de incidencias")

    # 10. Delitos por día de semana
    d = tablas["delitos_por_dia_semana"].copy()
    d = d.set_index("dia_es").reindex(dias_es_orden).reset_index()
    grafica_barras_v(d, "dia_es", "total_delitos",
                     "Carpetas de Investigación por Día de la Semana (FGJ — 2024)",
                     PAL_ACCENT, "delitos_por_dia_semana.png",
                     ylabel="Total de carpetas")

    # 11. Comparativo alcaldías: incidencias vs delitos
    inc = tablas["incidencias_por_alcaldia"].rename(columns={"total_incidencias": "incidencias"})
    deli = tablas["delitos_por_alcaldia"].rename(columns={"total_delitos": "delitos"})
    comp = inc.merge(deli, on="alcaldia", how="outer").fillna(0)
    comp = comp.sort_values("delitos", ascending=True)

    fig, ax = plt.subplots(figsize=(13, 8))
    y_pos = np.arange(len(comp))
    bar_h = 0.35
    ax.barh(y_pos - bar_h / 2, comp["incidencias"], bar_h, label="Incidencias (Locatel)",
            color=PAL_MAIN, edgecolor="none")
    ax.barh(y_pos + bar_h / 2, comp["delitos"], bar_h, label="Delitos (FGJ)",
            color=PAL_ACCENT, edgecolor="none")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(comp["alcaldia"])
    ax.set_title("Comparativo: Incidencias Urbanas vs Delitos por Alcaldía (2024)", pad=15)
    ax.set_xlabel("Total de registros")
    ax.legend(loc="lower right", framealpha=0.7, edgecolor="#2E3347")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    fig.tight_layout()
    _guardar(fig, "comparativo_alcaldias.png")

    # 12. Comparativo mensual: incidencias vs delitos
    inc_m = tablas["incidencias_por_mes"][["mes", "nombre_mes", "total_incidencias"]].copy()
    del_m = tablas["delitos_por_mes"][["mes", "nombre_mes", "total_delitos"]].copy()
    comp_m = inc_m.merge(del_m, on=["mes", "nombre_mes"], how="outer").sort_values("mes")

    fig, ax1 = plt.subplots(figsize=(13, 5.5))
    x_labels = comp_m["nombre_mes"].values

    ax1.fill_between(range(len(comp_m)), comp_m["total_incidencias"], alpha=0.12, color=PAL_MAIN)
    l1, = ax1.plot(range(len(comp_m)), comp_m["total_incidencias"], marker="o", markersize=7,
                   linewidth=2.5, color=PAL_MAIN, markeredgecolor="white", markeredgewidth=1.5,
                   label="Incidencias (Locatel)")
    ax1.set_ylabel("Incidencias", color=PAL_MAIN)
    ax1.tick_params(axis="y", labelcolor=PAL_MAIN)

    ax2 = ax1.twinx()
    ax2.fill_between(range(len(comp_m)), comp_m["total_delitos"], alpha=0.12, color=PAL_ACCENT)
    l2, = ax2.plot(range(len(comp_m)), comp_m["total_delitos"], marker="s", markersize=7,
                   linewidth=2.5, color=PAL_ACCENT, markeredgecolor="white", markeredgewidth=1.5,
                   label="Delitos (FGJ)")
    ax2.set_ylabel("Delitos", color=PAL_ACCENT)
    ax2.tick_params(axis="y", labelcolor=PAL_ACCENT)

    ax1.set_xticks(range(len(x_labels)))
    ax1.set_xticklabels(x_labels, rotation=45, ha="right")
    ax1.set_title("Comparativo Mensual: Incidencias Urbanas vs Delitos (2024)", pad=15)
    ax1.legend(handles=[l1, l2], loc="upper left", framealpha=0.7, edgecolor="#2E3347")
    ax1.grid(axis="y", linestyle="--", alpha=0.2)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    fig.tight_layout()
    _guardar(fig, "comparativo_mensual.png")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("  ANALISIS EXPLORATORIO -- SMART CITY CDMX")
    print("=" * 70)

    locatel, carpetas, victimas = cargar_datos()
    tablas = generar_tablas(locatel, carpetas)
    generar_graficas(tablas, locatel, carpetas)

    print("\n" + "=" * 70)
    print("  ANALISIS COMPLETADO")
    print(f"  Tablas:   {TABLAS_DIR}")
    print(f"  Graficas: {GRAFICAS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
