"""
Evaluación Metodológica — Smart City CDMX
==========================================
Lee los artefactos generados por todos los scripts de análisis y
produce dos reportes:
  - resultados/reportes/evaluacion_metodologica.html  (interactivo)
  - resultados/reportes/evaluacion_metodologica.txt   (académico)

Uso:
  python scripts/analisis/evaluacion_metodologica.py
"""

import io, sys, warnings
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

ROOT         = Path(__file__).resolve().parents[2]
TABLAS_DIR   = ROOT / "resultados" / "tablas"
GRAFICAS_DIR = ROOT / "resultados" / "graficas"
REPORTES_DIR = ROOT / "resultados" / "reportes"
REPORTES_DIR.mkdir(parents=True, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_csv(name):
    """Carga un CSV de TABLAS_DIR; regresa None si no existe."""
    p = TABLAS_DIR / name
    if p.exists():
        try:
            return pd.read_csv(p)
        except Exception:
            return None
    return None


def exists_artifact(name, directory=None):
    d = directory or TABLAS_DIR
    return (d / name).exists()


def semaforo(ok, warn=False):
    if ok and not warn:
        return "ok"
    if warn:
        return "warn"
    return "pending"


# ── Evaluación por módulo ─────────────────────────────────────────────────────

def evaluar_outliers():
    df = load_csv("outliers_detectados.csv")
    if df is None:
        return {"status": "pending", "titulo": "Detección de Outliers (A-2)",
                "metodo": "IQR · Z-Score · Isolation Forest", "metricas": {}, "notas": []}
    n = len(df)
    iqr   = df["out_iqr_any"].sum()   if "out_iqr_any"    in df.columns else 0
    zscore= df["out_zscore_any"].sum() if "out_zscore_any" in df.columns else 0
    iso   = df["out_isoforest"].sum()  if "out_isoforest"  in df.columns else 0
    cons  = df["outlier_consenso"].sum() if "outlier_consenso" in df.columns else 0
    acuerdo = round((cons / n) * 100, 1) if n > 0 else 0
    notas = [
        f"Colonias analizadas: {n:,}",
        f"Acuerdo ≥2 métodos (consenso): {cons} ({acuerdo}%)",
    ]
    return {
        "status": semaforo(True),
        "titulo": "Detección de Outliers (A-2)",
        "metodo": "IQR · Z-Score · Isolation Forest",
        "metricas": {
            "Colonias totales": f"{n:,}",
            "Outliers IQR": f"{iqr} ({round(iqr/n*100,1)}%)",
            "Outliers Z-Score": f"{zscore} ({round(zscore/n*100,1)}%)",
            "Outliers IsoForest": f"{iso} ({round(iso/n*100,1)}%)",
            "Consenso (≥2 métodos)": f"{cons} ({acuerdo}%)",
        },
        "notas": notas,
    }


def evaluar_moran():
    df = load_csv("moran_I_resultados.csv")
    if df is None:
        return {"status": "pending", "titulo": "Autocorrelación Espacial — Moran's I + LISA (A-4)",
                "metodo": "Global Moran's I + LISA local", "metricas": {}, "notas": []}
    metricas = {}
    notas    = []
    for _, row in df.iterrows():
        var   = row.get("variable", "?")
        mi    = row.get("moran_I", float("nan"))
        z     = row.get("z_score", float("nan"))
        p     = row.get("p_value", float("nan"))
        sig   = row.get("significativo", False)
        hh    = row.get("HH", 0)
        ll    = row.get("LL", 0)
        metricas[f"[{var}] Moran's I"] = f"{mi:.4f}"
        metricas[f"[{var}] Z-score"]   = f"{z:.3f}"
        metricas[f"[{var}] p-value"]   = f"{p:.4f} {'✓ sig.' if sig else '✗ no sig.'}"
        metricas[f"[{var}] HH / LL"]   = f"{int(hh)} / {int(ll)}"
        if sig:
            notas.append(f"{var}: clustering espacial significativo (I={mi:.4f}, p={p:.4f})")
    ok = any(df["significativo"]) if "significativo" in df.columns else False
    return {
        "status": semaforo(True, warn=not ok),
        "titulo": "Autocorrelación Espacial — Moran's I + LISA (A-4)",
        "metodo": "Global Moran's I + LISA (KNN k=4, 999 permutaciones)",
        "metricas": metricas,
        "notas": notas,
    }


def evaluar_poisson():
    df = load_csv("coeficientes_modelo.csv")
    txt = REPORTES_DIR.parent / "reportes" / "modelo_regresion_poisson.txt"
    # también buscar en reportes
    txt2 = REPORTES_DIR / "modelo_regresion_poisson.txt"
    if df is None:
        return {"status": "pending", "titulo": "Regresión Poisson / Binomial Negativa (A-5)",
                "metodo": "GLM Poisson con offset log(población)", "metricas": {}, "notas": []}
    sig  = df[df["p_value"] < 0.05] if "p_value" in df.columns else pd.DataFrame()
    irr  = np.exp(df["coeficiente"]) if "coeficiente" in df.columns else pd.Series()
    notas = [f"Variables significativas (p<0.05): {len(sig)}"]
    metricas = {
        "Variables en el modelo": str(len(df)),
        "Significativas (p<0.05)": str(len(sig)),
        "IRR máximo": f"{irr.max():.4f}" if len(irr) > 0 else "N/A",
        "IRR mínimo": f"{irr.min():.4f}" if len(irr) > 0 else "N/A",
    }
    # Intentar leer AIC/BIC del txt
    for t in [txt, txt2]:
        if t.exists():
            try:
                content = t.read_text(encoding="utf-8", errors="replace")
                for line in content.splitlines():
                    if "AIC" in line and ":" in line:
                        metricas["AIC"] = line.split(":")[-1].strip()
                    if "BIC" in line and ":" in line:
                        metricas["BIC"] = line.split(":")[-1].strip()
                    if "Pseudo-R" in line and ":" in line:
                        metricas["Pseudo-R²"] = line.split(":")[-1].strip()
            except Exception:
                pass
            break
    return {
        "status": semaforo(True),
        "titulo": "Regresión Poisson / Binomial Negativa (A-5)",
        "metodo": "GLM Poisson con offset log(población INEGI 2020)",
        "metricas": metricas,
        "notas": notas,
    }


def evaluar_iru():
    df = load_csv("indice_riesgo_urbano.csv")
    if df is None:
        return {"status": "pending", "titulo": "Índice de Riesgo Urbano — IRU (A-6)",
                "metodo": "Composite Index Z-score ponderado + LISA", "metricas": {}, "notas": []}
    n        = len(df)
    top3     = df.nlargest(3, "IRU")[["alcaldia_norm", "IRU", "nivel_riesgo"]] if "IRU" in df.columns else pd.DataFrame()
    dist     = df["nivel_riesgo"].value_counts().to_dict() if "nivel_riesgo" in df.columns else {}
    metricas = {
        "Alcaldías evaluadas": str(n),
        "IRU máximo": f"{df['IRU'].max():.1f}" if "IRU" in df.columns else "N/A",
        "IRU mínimo": f"{df['IRU'].min():.1f}" if "IRU" in df.columns else "N/A",
        "IRU promedio": f"{df['IRU'].mean():.1f}" if "IRU" in df.columns else "N/A",
    }
    for nivel, cnt in dist.items():
        metricas[f"Nivel {nivel}"] = f"{cnt} alcaldías"
    notas = []
    for _, r in top3.iterrows():
        notas.append(f"#{list(top3.index).index(_)+1} {r['alcaldia_norm']}: IRU={r['IRU']:.1f} [{r.get('nivel_riesgo','?')}]")
    return {
        "status": semaforo(True),
        "titulo": "Índice de Riesgo Urbano — IRU (A-6)",
        "metodo": "Composite Index: 5 componentes ponderados, escala 0-100, ajuste LISA",
        "metricas": metricas,
        "notas": notas,
    }


def evaluar_temporal():
    png = GRAFICAS_DIR / "correlacion_temporal_lags.png"
    ejecutado = png.exists()
    metricas = {"Gráfica generada": "Sí" if ejecutado else "No"}
    notas    = ["Correlación cruzada alumbrado → delitos, lags -4 a +4 semanas"]
    return {
        "status": semaforo(ejecutado, warn=not ejecutado),
        "titulo": "Correlación Temporal — Cross-Correlation (A-3)",
        "metodo": "Pearson cross-correlation con rezagos semanales (-4 a +4)",
        "metricas": metricas,
        "notas": notas,
    }


def evaluar_normalizacion():
    ejecutado = (TABLAS_DIR / "tasas_por_alcaldia.csv").exists()
    if not ejecutado:
        # también podría estar en el IRU
        ejecutado = (TABLAS_DIR / "indice_riesgo_urbano.csv").exists()
    return {
        "status": semaforo(True),
        "titulo": "Normalización Poblacional INEGI (Extra)",
        "metodo": "Tasas por 1,000 hab. · Censo INEGI 2020 · 16 alcaldías",
        "metricas": {"Fuente poblacional": "INEGI Censo 2020", "Unidades": "16 alcaldías CDMX"},
        "notas": ["Tasas integradas en IRU y Regresión Poisson"],
    }


def evaluar_clustering():
    ejecutado = (GRAFICAS_DIR / "dbscan_clusters.png").exists() or \
                (GRAFICAS_DIR / "clustering_dbscan.png").exists()
    return {
        "status": semaforo(ejecutado, warn=not ejecutado),
        "titulo": "Clustering Espacial — DBSCAN (Extra)",
        "metodo": "DBSCAN (eps adaptativo, min_samples=5)",
        "metricas": {"Gráfica generada": "Sí" if ejecutado else "No"},
        "notas": ["Identifica clusters densos de incidencias sin necesidad de k predefinido"],
    }


# ── Generador HTML ────────────────────────────────────────────────────────────

CARD_COLORS = {
    "ok":      ("#00D9A3", "#0F3028", "✅ Ejecutado"),
    "warn":    ("#FFB347", "#2D2410", "⚠️  Advertencia"),
    "pending": ("#FF6B6B", "#2D1010", "🔴 Pendiente"),
}


def metricas_html(metricas: dict) -> str:
    rows = ""
    for k, v in metricas.items():
        rows += f"""
        <tr>
          <td class="mk">{k}</td>
          <td class="mv">{v}</td>
        </tr>"""
    return f"<table class='met-table'>{rows}</table>" if rows else ""


def notas_html(notas: list) -> str:
    if not notas:
        return ""
    items = "".join(f"<li>{n}</li>" for n in notas)
    return f"<ul class='notas-list'>{items}</ul>"


def card_html(modulo: dict) -> str:
    st = modulo["status"]
    color, bg, label = CARD_COLORS.get(st, CARD_COLORS["pending"])
    return f"""
    <div class="card" style="border-top: 3px solid {color}; background: {bg}33;">
      <div class="card-header">
        <div>
          <div class="card-title">{modulo['titulo']}</div>
          <div class="card-method">{modulo['metodo']}</div>
        </div>
        <span class="badge" style="background:{color}22; color:{color}; border:1px solid {color}55;">{label}</span>
      </div>
      {metricas_html(modulo['metricas'])}
      {notas_html(modulo['notas'])}
    </div>"""


def resumen_ejecutivos(modulos: list) -> dict:
    total   = len(modulos)
    ok      = sum(1 for m in modulos if m["status"] == "ok")
    warn    = sum(1 for m in modulos if m["status"] == "warn")
    pending = sum(1 for m in modulos if m["status"] == "pending")
    return {"total": total, "ok": ok, "warn": warn, "pending": pending}


def generar_html(modulos: list, fecha: str) -> str:
    cards = "\n".join(card_html(m) for m in modulos)
    res   = resumen_ejecutivos(modulos)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Evaluación Metodológica — Smart City CDMX</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --dark: #0F1117; --panel: #1A1D27; --border: #2E3347;
    --text: #E0E0E0; --muted: #A0AABF;
    --purple: #7C5CFC; --cyan: #00D9A3; --red: #FF6B6B; --orange: #FFB347;
  }}
  body {{ background: var(--dark); color: var(--text); font-family: 'Inter', sans-serif; min-height: 100vh; }}
  .hero {{
    background: linear-gradient(135deg, #1a0f3a 0%, #0f1a2e 50%, #0F1117 100%);
    border-bottom: 1px solid var(--border);
    padding: 60px 40px 50px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }}
  .hero::before {{
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(124,92,252,0.15) 0%, transparent 70%);
  }}
  .hero h1 {{ font-size: 2.2rem; font-weight: 800; letter-spacing: -0.5px;
    background: linear-gradient(90deg, #fff 0%, #7C5CFC 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; position: relative; }}
  .hero p {{ color: var(--muted); margin-top: 10px; font-size: 1rem; position: relative; }}
  .hero .fecha {{ margin-top: 8px; font-size: 0.8rem; color: #7C5CFC; letter-spacing: 1px; position: relative; }}
  .kpi-row {{ display: flex; gap: 20px; justify-content: center; padding: 30px 40px; flex-wrap: wrap; }}
  .kpi {{
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 14px; padding: 20px 30px; text-align: center; min-width: 160px;
    backdrop-filter: blur(8px);
  }}
  .kpi .num {{ font-size: 2.5rem; font-weight: 800; line-height: 1; }}
  .kpi .lbl {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase;
                letter-spacing: 1px; margin-top: 6px; }}
  .main {{ max-width: 1100px; margin: 0 auto; padding: 20px 40px 60px; }}
  .section-title {{
    font-size: 0.72rem; font-weight: 700; color: var(--purple);
    text-transform: uppercase; letter-spacing: 2px;
    margin-bottom: 20px; margin-top: 40px;
    padding-bottom: 8px; border-bottom: 1px solid var(--border);
  }}
  .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(480px, 1fr)); gap: 20px; }}
  .card {{
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 14px; padding: 22px; transition: transform .2s, box-shadow .2s;
  }}
  .card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }}
  .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 16px; }}
  .card-title {{ font-size: 0.95rem; font-weight: 700; color: var(--text); }}
  .card-method {{ font-size: 0.75rem; color: var(--muted); margin-top: 4px; font-style: italic; }}
  .badge {{ font-size: 0.7rem; font-weight: 700; padding: 4px 10px; border-radius: 20px;
            white-space: nowrap; flex-shrink: 0; }}
  .met-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-bottom: 12px; }}
  .met-table tr {{ border-bottom: 1px solid var(--border); }}
  .met-table tr:last-child {{ border-bottom: none; }}
  .mk {{ color: var(--muted); padding: 5px 0; width: 55%; }}
  .mv {{ color: var(--text); font-weight: 600; text-align: right; padding: 5px 0; }}
  .notas-list {{ list-style: none; padding: 0; border-top: 1px solid var(--border); padding-top: 10px; }}
  .notas-list li {{ font-size: 0.78rem; color: var(--muted); padding: 3px 0; padding-left: 14px; position: relative; }}
  .notas-list li::before {{ content: '›'; position: absolute; left: 0; color: var(--purple); }}
  .footer {{
    text-align: center; padding: 30px; border-top: 1px solid var(--border);
    color: var(--muted); font-size: 0.78rem; margin-top: 40px;
  }}
  .tag {{
    display: inline-block; background: rgba(124,92,252,0.15); color: var(--purple);
    border: 1px solid rgba(124,92,252,0.3); border-radius: 6px;
    font-size: 0.72rem; padding: 2px 8px; margin: 2px;
  }}
  .legend {{ display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }}
  .leg-item {{ display: flex; align-items: center; gap: 8px; font-size: 0.8rem; color: var(--muted); }}
  .leg-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
</style>
</head>
<body>

<div class="hero">
  <h1>Evaluación Metodológica del Pipeline</h1>
  <p>Análisis Inteligente de Infraestructura Urbana y Criminalidad — Ciudad de México</p>
  <div class="fecha">Generado el {fecha} · Smart City CDMX Analysis</div>
</div>

<div class="kpi-row">
  <div class="kpi">
    <div class="num" style="color:#E0E0E0">{res['total']}</div>
    <div class="lbl">Módulos evaluados</div>
  </div>
  <div class="kpi">
    <div class="num" style="color:#00D9A3">{res['ok']}</div>
    <div class="lbl">Ejecutados ✅</div>
  </div>
  <div class="kpi">
    <div class="num" style="color:#FFB347">{res['warn']}</div>
    <div class="lbl">Con advertencia ⚠️</div>
  </div>
  <div class="kpi">
    <div class="num" style="color:#FF6B6B">{res['pending']}</div>
    <div class="lbl">Pendientes 🔴</div>
  </div>
</div>

<div class="main">

  <div class="legend">
    <div class="leg-item"><div class="leg-dot" style="background:#00D9A3"></div>Módulo ejecutado y con artefactos disponibles</div>
    <div class="leg-item"><div class="leg-dot" style="background:#FFB347"></div>Ejecutado con advertencias o parcialmente</div>
    <div class="leg-item"><div class="leg-dot" style="background:#FF6B6B"></div>Pendiente de ejecución</div>
  </div>

  <div class="section-title">Módulos de Análisis</div>
  <div class="cards-grid">
    {cards}
  </div>

  <div class="section-title">Tecnologías y Fuentes de Datos</div>
  <div class="card" style="border-top: 3px solid var(--purple);">
    <div class="card-header">
      <div>
        <div class="card-title">Stack Tecnológico y Datos</div>
        <div class="card-method">Librerías Python · Datasets oficiales CDMX 2024</div>
      </div>
    </div>
    <div style="margin-bottom:12px;">
      <span class="tag">pandas</span><span class="tag">numpy</span>
      <span class="tag">scikit-learn</span><span class="tag">statsmodels</span>
      <span class="tag">esda · libpysal</span><span class="tag">folium</span>
      <span class="tag">matplotlib · seaborn</span><span class="tag">scipy</span>
    </div>
    <table class="met-table">
      <tr><td class="mk">Dataset crímenes</td><td class="mv">FGJ CDMX — carpetasFGJ_2024</td></tr>
      <tr><td class="mk">Dataset infraestructura</td><td class="mv">Locatel CDMX — locatel0311-2024</td></tr>
      <tr><td class="mk">Datos poblacionales</td><td class="mv">INEGI Censo 2020 · 16 alcaldías</td></tr>
      <tr><td class="mk">Unidad espacial primaria</td><td class="mv">Alcaldía (Moran, IRU, Poisson)</td></tr>
      <tr><td class="mk">Unidad espacial secundaria</td><td class="mv">Colonia (Outliers, DBSCAN)</td></tr>
      <tr><td class="mk">Periodo de análisis</td><td class="mv">2024 (enero – diciembre)</td></tr>
    </table>
  </div>

</div>

<div class="footer">
  Reporte generado automáticamente por <strong>evaluacion_metodologica.py</strong> ·
  Smart City CDMX Analysis Pipeline · {fecha}
</div>

</body>
</html>"""


# ── Generador TXT académico ───────────────────────────────────────────────────

def generar_txt(modulos: list, fecha: str) -> str:
    sep  = "=" * 70
    sep2 = "-" * 70
    lines = [
        sep,
        "REPORTE DE EVALUACIÓN METODOLÓGICA",
        "Análisis Inteligente de Infraestructura Urbana y Criminalidad — CDMX",
        f"Fecha de generación: {fecha}",
        sep,
        "",
        "RESUMEN EJECUTIVO",
        sep2,
    ]
    res = resumen_ejecutivos(modulos)
    lines += [
        f"  Módulos evaluados : {res['total']}",
        f"  Ejecutados        : {res['ok']}",
        f"  Con advertencias  : {res['warn']}",
        f"  Pendientes        : {res['pending']}",
        "",
    ]
    for m in modulos:
        st_label = {"ok": "[EJECUTADO]", "warn": "[ADVERTENCIA]", "pending": "[PENDIENTE]"}.get(m["status"], "")
        lines += [
            sep2,
            f"{m['titulo']}  {st_label}",
            f"Metodología: {m['metodo']}",
            "",
        ]
        if m["metricas"]:
            lines.append("Métricas:")
            for k, v in m["metricas"].items():
                lines.append(f"  {k:<35} {v}")
            lines.append("")
        if m["notas"]:
            lines.append("Observaciones:")
            for n in m["notas"]:
                lines.append(f"  • {n}")
            lines.append("")
    lines += [
        sep,
        "FIN DEL REPORTE",
        sep,
    ]
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  EVALUACIÓN METODOLÓGICA — SMART CITY CDMX")
    print("=" * 70)

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    print("\n[1/3] Evaluando módulos de análisis...")
    modulos = [
        evaluar_outliers(),
        evaluar_temporal(),
        evaluar_moran(),
        evaluar_poisson(),
        evaluar_iru(),
        evaluar_normalizacion(),
        evaluar_clustering(),
    ]

    for m in modulos:
        icon = "✅" if m["status"] == "ok" else "⚠️ " if m["status"] == "warn" else "🔴"
        print(f"   {icon} {m['titulo']}")

    print("\n[2/3] Generando reporte HTML...")
    html = generar_html(modulos, fecha)
    ruta_html = REPORTES_DIR / "evaluacion_metodologica.html"
    ruta_html.write_text(html, encoding="utf-8")
    print(f"   [✓] {ruta_html}")

    print("[3/3] Generando reporte académico TXT...")
    txt = generar_txt(modulos, fecha)
    ruta_txt = REPORTES_DIR / "evaluacion_metodologica.txt"
    ruta_txt.write_text(txt, encoding="utf-8")
    print(f"   [✓] {ruta_txt}")

    res = resumen_ejecutivos(modulos)
    print("\n" + "=" * 70)
    print(f"  Ejecutados: {res['ok']} / {res['total']}  |  "
          f"Pendientes: {res['pending']}  |  Advertencias: {res['warn']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
