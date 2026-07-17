"""
Regresión de Poisson / Binomial Negativa — Smart City CDMX  [A-5]
==================================================================
Modela el número esperado de delitos por alcaldía en función de las
fallas de infraestructura urbana (Locatel), controlando por tipo de
incidencia y normalizando como offset la población (INEGI 2020).

Metodología:
  1. Exploración: distribución del conteo de delitos (media vs varianza)
  2. Test de sobredispersión: decide entre Poisson y Binomial Negativa
  3. Modelo Poisson con offset log(población)
  4. Modelo Binomial Negativa si varianza >> media (sobredispersión)
  5. Comparación de modelos (AIC, BIC, pseudo-R²)
  6. Visualización de coeficientes e intervalos de confianza al 95%

Salidas:
  resultados/reportes/modelo_regresion_poisson.txt
  resultados/tablas/coeficientes_modelo.csv
  resultados/graficas/coeficientes_modelo.png
  resultados/graficas/residuos_modelo.png

Uso:
  python scripts/analisis/regresion_poisson.py
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

warnings.filterwarnings("ignore")

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from statsmodels.discrete.discrete_model import Poisson, NegativeBinomial
    HAS_SM = True
except ImportError:
    HAS_SM = False
    print("ERROR: statsmodels no está instalado.")
    print("Ejecuta: pip install statsmodels")
    sys.exit(1)

ROOT        = Path(__file__).resolve().parents[2]
DATA_DIR    = ROOT / "datasets" / "processed"
TABLAS_DIR  = ROOT / "resultados" / "tablas"
GRAFICAS_DIR = ROOT / "resultados" / "graficas"
REPORTES_DIR = ROOT / "resultados" / "reportes"
REPORTES_DIR.mkdir(parents=True, exist_ok=True)

DARK, PANEL, BORDER = "#0F1117", "#1A1D27", "#2E3347"
TEXT, MUTED = "#E0E0E0", "#A0AABF"
PURPLE, CYAN, RED, ORANGE = "#7C5CFC", "#00D9A3", "#FF6B6B", "#FFB347"

plt.rcParams.update({
    "figure.facecolor": DARK, "axes.facecolor": PANEL,
    "axes.edgecolor": BORDER, "axes.labelcolor": TEXT,
    "text.color": TEXT, "xtick.color": MUTED, "ytick.color": MUTED,
    "grid.color": BORDER, "grid.alpha": 0.5, "font.family": "sans-serif",
})

# Población INEGI 2020 (misma que normalizacion_inegi.py)
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


def normalizar_nombre(s):
    import unicodedata
    s = str(s).strip().title()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def build_modelo_df(locatel, carpetas):
    """Construye tabla por alcaldía con predictores de infraestructura."""
    for df in [locatel, carpetas]:
        df["alcaldia_norm"] = df["alcaldia_catalogo"].apply(normalizar_nombre)

    locatel  = locatel[locatel["alcaldia_norm"].isin(POBLACION_INEGI)]
    carpetas = carpetas[carpetas["alcaldia_norm"].isin(POBLACION_INEGI)]

    k = "alcaldia_norm"
    # Variable dependiente
    del_ = carpetas.groupby(k).size().reset_index(name="total_delitos")

    # Predictores de infraestructura (tipos de Locatel)
    tipos_locatel = locatel.groupby([k, "tema_solicitud"]).size().unstack(fill_value=0)
    tipos_locatel.columns = [f"inc_{col.lower().replace(' ','_')[:20]}"
                             for col in tipos_locatel.columns]
    tipos_locatel = tipos_locatel.reset_index()

    carpetas["hora"] = pd.to_datetime(
        carpetas["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    noc = carpetas[(carpetas["hora"] >= 20) | (carpetas["hora"] <= 5)]
    noc_ = noc.groupby(k).size().reset_index(name="delitos_nocturnos")

    df_mod = (del_.merge(tipos_locatel, on=k, how="left")
                  .merge(noc_,         on=k, how="left")
                  .fillna(0))
    df_mod["poblacion"] = df_mod[k].map(POBLACION_INEGI)
    df_mod = df_mod.dropna(subset=["poblacion"])
    df_mod["log_poblacion"] = np.log(df_mod["poblacion"].astype(float))

    return df_mod


def test_sobredispersion(y):
    """Razón varianza/media. >1.5 indica sobredispersión."""
    mean_y = y.mean()
    var_y  = y.var()
    ratio  = var_y / mean_y
    print(f"\n   Media de delitos : {mean_y:.2f}")
    print(f"   Varianza         : {var_y:.2f}")
    print(f"   Razón Var/Media  : {ratio:.2f}  "
          f"{'→ sobredispersión (usar Neg. Binomial)' if ratio > 1.5 else '→ OK para Poisson'}")
    return ratio


def plot_coeficientes(params, pvalues, ci, model_name):
    """params: pd.Series, pvalues: pd.Series, ci: pd.DataFrame (2 cols), ya normalizados."""
    coef  = params.drop(["Intercept", "const", "alpha"], errors="ignore")
    ci2   = ci.drop(["Intercept", "const", "alpha"],     errors="ignore")
    pvs   = pvalues.drop(["Intercept", "const", "alpha"],errors="ignore")

    mask = pvs < 0.15
    coef, ci2, pvs = coef[mask], ci2[mask], pvs[mask]
    if len(coef) == 0:
        print("   (ningún predictor con p<0.15 para graficar)")
        return

    coef = coef.sort_values()
    ci2  = ci2.loc[coef.index]
    pvs  = pvs.loc[coef.index]

    fig, ax = plt.subplots(figsize=(12, max(5, len(coef) * 0.55 + 2)), facecolor=DARK)
    fig.suptitle(f"Coeficientes del Modelo {model_name}\n"
                 "(Exponencial = IRR: >1 aumenta delitos, <1 los reduce)",
                 fontsize=13, fontweight="bold", y=1.01)

    colors_bar = [RED if c > 0 else CYAN for c in coef]
    yerr_low  = coef - ci2.iloc[:, 0]
    yerr_high = ci2.iloc[:, 1] - coef

    ax.barh(range(len(coef)), coef, color=colors_bar, alpha=0.75,
            edgecolor=BORDER, height=0.6)
    ax.errorbar(coef, range(len(coef)),
                xerr=[yerr_low.values, yerr_high.values],
                fmt="none", color="white", elinewidth=1.5, capsize=4)

    for i, (c, p) in enumerate(zip(coef, pvs)):
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "·"
        ax.text(c + (0.005 if c > 0 else -0.005), i,
                f"  {sig} (p={p:.3f})", va="center", fontsize=7.5, color=TEXT)

    ax.set_yticks(range(len(coef)))
    ax.set_yticklabels([lbl[:30] for lbl in coef.index], fontsize=8)
    ax.axvline(0, color=MUTED, lw=1, ls="--", alpha=0.7)
    ax.set_xlabel("Coeficiente (log-scale)")
    ax.grid(axis="x", linestyle="--", alpha=0.25)

    fig.tight_layout(pad=2.0)
    ruta = GRAFICAS_DIR / "coeficientes_modelo.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] {ruta.name}")


def plot_residuos(result, y, model_name):
    fitted  = result.fittedvalues
    resid_p = result.resid_pearson if hasattr(result, "resid_pearson") else result.resid

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor=DARK)
    fig.suptitle(f"Diagnóstico de Residuos — Modelo {model_name}",
                 fontsize=13, fontweight="bold", y=1.01)

    # Residuos vs Fitted
    axes[0].scatter(fitted, resid_p, alpha=0.65, color=PURPLE, s=50, edgecolors="none")
    axes[0].axhline(0, color=RED, lw=1.5, ls="--")
    axes[0].set_xlabel("Valores Ajustados")
    axes[0].set_ylabel("Residuos de Pearson")
    axes[0].set_title("Residuos vs Fitted", fontweight="bold", pad=10)
    axes[0].grid(True, linestyle="--", alpha=0.25)

    # QQ-Plot
    (osm, osr), (slope, intercept, r) = stats.probplot(resid_p)
    axes[1].scatter(osm, osr, alpha=0.65, color=CYAN, s=40, edgecolors="none")
    x_line = np.linspace(min(osm), max(osm), 100)
    axes[1].plot(x_line, slope * x_line + intercept, color=RED, lw=2)
    axes[1].set_xlabel("Cuantiles Teóricos (Normal)")
    axes[1].set_ylabel("Cuantiles de Residuos")
    axes[1].set_title("Q-Q Plot de Residuos", fontweight="bold", pad=10)
    axes[1].grid(True, linestyle="--", alpha=0.25)

    # Observado vs Predicho
    axes[2].scatter(y, fitted, alpha=0.65, color=ORANGE, s=50, edgecolors="none")
    lim = max(y.max(), fitted.max())
    axes[2].plot([0, lim], [0, lim], color=RED, lw=1.5, ls="--", label="Línea perfecta")
    axes[2].set_xlabel("Delitos Observados")
    axes[2].set_ylabel("Delitos Predichos")
    axes[2].set_title("Observado vs Predicho", fontweight="bold", pad=10)
    axes[2].legend(fontsize=9)
    axes[2].grid(True, linestyle="--", alpha=0.25)

    fig.tight_layout(pad=2.5)
    ruta = GRAFICAS_DIR / "residuos_modelo.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] {ruta.name}")


def main():
    print("=" * 70)
    print("  REGRESIÓN POISSON / BINOMIAL NEGATIVA  [A-5]")
    print("=" * 70)

    print("\n[1/5] Cargando datasets...")
    locatel  = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    print("[2/5] Construyendo tabla del modelo por alcaldía...")
    df_mod = build_modelo_df(locatel, carpetas)
    print(f"   Unidades de análisis (alcaldías): {len(df_mod)}")

    y = df_mod["total_delitos"].astype(int)
    ratio = test_sobredispersion(y)
    usar_nb = ratio > 1.5

    # ── 3. Seleccionar predictores disponibles ─────────────────────────────
    print("[3/5] Seleccionando predictores de infraestructura...")
    inc_cols = [c for c in df_mod.columns if c.startswith("inc_")]
    if not inc_cols:
        print("   ADVERTENCIA: No se encontraron columnas 'inc_*'.")
        print("   Usando solo 'delitos_nocturnos' como predictor.")
        inc_cols = []

    # Usar las top 5 variables de incidencia más frecuentes + delitos nocturnos
    if inc_cols:
        top_inc = df_mod[inc_cols].sum().nlargest(5).index.tolist()
    else:
        top_inc = []

    predictores = top_inc + (["delitos_nocturnos"] if "delitos_nocturnos" in df_mod.columns else [])
    if not predictores:
        predictores = []
        print("   No se encontraron predictores; ajustando modelo nulo.")

    # Asegurar que todas las variables predictoras sean numéricas y sin NaN
    for col in predictores:
        df_mod[col] = pd.to_numeric(df_mod[col], errors="coerce").fillna(0)

    # Estandarizar predictores para comparabilidad de coeficientes
    X_raw = df_mod[predictores].copy() if predictores else pd.DataFrame(index=df_mod.index)
    for col in predictores:
        std = X_raw[col].std()
        X_raw[col] = (X_raw[col] - X_raw[col].mean()) / std if std > 0 else 0.0

    X = sm.add_constant(X_raw)
    offset = df_mod["log_poblacion"].values

    # ── 4. Ajustar modelos ─────────────────────────────────────────────────
    print(f"\n[4/5] Ajustando {'Poisson + Binomial Negativa' if usar_nb else 'Poisson'}...")

    # Poisson
    try:
        mod_poi  = sm.GLM(y, X, family=sm.families.Poisson(),
                          offset=offset).fit(disp=False)
        print(f"\n   Modelo Poisson:")
        print(f"      AIC          : {mod_poi.aic:.2f}")
        print(f"      BIC          : {mod_poi.bic:.2f}")
        print(f"      Pseudo-R²    : {1 - mod_poi.deviance / mod_poi.null_deviance:.4f}")
        poi_ok = True
    except Exception as e:
        print(f"   Error en Poisson: {e}")
        poi_ok = False
        mod_poi = None

    # Binomial Negativa (si hay sobredispersión)
    nb_ok = False
    mod_nb = None
    if usar_nb and poi_ok:
        try:
            from statsmodels.discrete.discrete_model import NegativeBinomial as NBinom
            mod_nb = NBinom(y.values, X.values,
                            exposure=np.exp(offset)).fit(disp=0, maxiter=100)
            print(f"\n   Modelo Binomial Negativa:")
            print(f"      AIC          : {mod_nb.aic:.2f}")
            print(f"      BIC          : {mod_nb.bic:.2f}")
            print(f"      Log-Lik      : {mod_nb.llf:.2f}")
            nb_ok = True
        except Exception as e:
            print(f"   Error en Neg. Binomial: {e}  → se usa solo Poisson")

    # Seleccionar el mejor modelo
    best_model  = mod_nb if (nb_ok and usar_nb) else mod_poi
    model_name  = "Binomial Negativa" if (nb_ok and usar_nb) else "Poisson"
    print(f"\n   → Modelo seleccionado: {model_name}")

    # ── 5. Exportar resultados ─────────────────────────────────────────────
    print("[5/5] Exportando resultados y generando visualizaciones...")
    ruta_txt = REPORTES_DIR / "modelo_regresion_poisson.txt"
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("MODELO DE REGRESIÓN — SMART CITY CDMX\n")
        f.write(f"Tipo: {model_name}\n")
        f.write(f"Variable dependiente: Total Delitos por Alcaldía\n")
        f.write(f"Offset: log(Población INEGI 2020)\n")
        f.write(f"Unidades de análisis: {len(df_mod)} alcaldías\n")
        f.write(f"Razón Varianza/Media: {ratio:.2f} {'→ sobredispersión' if ratio > 1.5 else ''}\n")
        f.write("=" * 70 + "\n\n")
        if best_model is not None:
            f.write(best_model.summary().as_text())
    print(f"   [✓] Reporte: {ruta_txt.name}")

    # Tabla de coeficientes
    if best_model is not None:
        # NegativeBinomial retorna params como ndarray (sin índice pandas);
        # GLM Poisson retorna un Series con índice. Se normaliza ambos casos.
        params = best_model.params
        pvalues = best_model.pvalues
        ci = best_model.conf_int()

        if isinstance(params, np.ndarray):
            col_names = list(X.columns)
            # NegativeBinomial agrega 'alpha' al final
            if len(params) == len(col_names) + 1:
                col_names = col_names + ["alpha"]
            params  = pd.Series(params,  index=col_names[:len(params)])
            pvalues = pd.Series(pvalues, index=col_names[:len(pvalues)])
            ci = pd.DataFrame(ci, index=col_names[:len(ci)])

        coef_df = pd.DataFrame({
            "variable": params.index,
            "coeficiente": params.values,
            "exp_coef_IRR": np.exp(params.values),
            "p_value": pvalues.values,
            "IC_95_low": ci.iloc[:, 0].values,
            "IC_95_high": ci.iloc[:, 1].values,
        })
        coef_df["significativo"] = coef_df["p_value"] < 0.05
        ruta_coef = TABLAS_DIR / "coeficientes_modelo.csv"
        coef_df.to_csv(ruta_coef, index=False, encoding="utf-8-sig")
        print(f"   [✓] Coeficientes: {ruta_coef.name}")

        plot_coeficientes(params, pvalues, ci, model_name)
        plot_residuos(best_model, y, model_name)

    print("\n" + "=" * 70)
    print(f"  REGRESIÓN COMPLETADA — Modelo: {model_name}")
    print("=" * 70)


if __name__ == "__main__":
    main()
