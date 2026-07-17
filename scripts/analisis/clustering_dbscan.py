"""
Validación de Clusters: DBSCAN vs KMeans — Smart City CDMX  [A-1]
===================================================================
Compara MiniBatchKMeans (existente) con DBSCAN y valida los clusters
mediante Silhouette Score y Davies-Bouldin Index.

Metodología:
  1. Elbow + Silhouette Curve para elegir K óptimo en KMeans (K=3..25)
  2. DBSCAN con calibración de epsilon via Nearest Neighbor Distance
  3. Comparación de métricas: Silhouette, Davies-Bouldin, nº clusters
  4. Mapa Folium interactivo con los clusters DBSCAN

Salidas:
  resultados/tablas/validacion_clusters.csv
  resultados/graficas/elbow_silhouette.png
  resultados/graficas/comparacion_dbscan_kmeans.png
  resultados/mapas/mapa_clusters_dbscan.html

Uso:
  python scripts/analisis/clustering_dbscan.py
"""

import io, sys, warnings
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from sklearn.cluster import MiniBatchKMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

warnings.filterwarnings("ignore")

ROOT        = Path(__file__).resolve().parents[2]
DATA_DIR    = ROOT / "datasets" / "processed"
TABLAS_DIR  = ROOT / "resultados" / "tablas"
GRAFICAS_DIR = ROOT / "resultados" / "graficas"
MAPAS_DIR   = ROOT / "resultados" / "mapas"

DARK, PANEL, BORDER = "#0F1117", "#1A1D27", "#2E3347"
TEXT, MUTED = "#E0E0E0", "#A0AABF"
PURPLE, CYAN, RED, ORANGE = "#7C5CFC", "#00D9A3", "#FF6B6B", "#FFB347"
CDMX_CENTER = [19.38, -99.14]

plt.rcParams.update({
    "figure.facecolor": DARK, "axes.facecolor": PANEL,
    "axes.edgecolor": BORDER, "axes.labelcolor": TEXT,
    "text.color": TEXT, "xtick.color": MUTED, "ytick.color": MUTED,
    "grid.color": BORDER, "grid.alpha": 0.5, "font.family": "sans-serif",
})

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
body { font-family: 'Inter', sans-serif !important; background-color: #0f1117; }
.modern-title {
    position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999;
    background: rgba(20,22,30,0.82); backdrop-filter: blur(12px);
    padding: 14px 32px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
    color: #fff; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.modern-title h1 { margin: 0; font-size: 19px; font-weight: 700; }
.modern-title p  { margin: 3px 0 0 0; font-size: 11px; color: #00D9A3; font-weight: 600; }
.legend-box {
    position: fixed; bottom: 40px; right: 20px; z-index: 9999;
    background: rgba(20,22,30,0.82); backdrop-filter: blur(12px);
    padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
    color: #fff; font-size: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.legend-box h4 { margin: 0 0 8px 0; font-size: 13px; color: #E0E0E0; }
.dot { height:12px; width:12px; border-radius:50%; display:inline-block; margin-right:6px; }
</style>
"""


def filtrar_coords(df):
    mask = (df["latitud"].notna() & df["longitud"].notna() &
            (df["latitud"] > 19.0) & (df["latitud"] < 19.8) &
            (df["longitud"] > -99.5) & (df["longitud"] < -98.8))
    return df[mask]


def plot_elbow_silhouette(coords_scaled, k_range):
    inercias, silhouettes, db_scores = [], [], []

    for k in k_range:
        km = MiniBatchKMeans(n_clusters=k, random_state=42, n_init="auto")
        labels = km.fit_predict(coords_scaled)
        inercias.append(km.inertia_)
        silhouettes.append(silhouette_score(coords_scaled, labels, sample_size=5000))
        db_scores.append(davies_bouldin_score(coords_scaled, labels))

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor=DARK)
    fig.suptitle("Validación de KMeans: Elbow · Silhouette · Davies-Bouldin",
                 fontsize=14, fontweight="bold", y=1.01)

    # Elbow
    axes[0].plot(k_range, inercias, color=PURPLE, marker="o", lw=2, markersize=6)
    axes[0].set_title("Elbow Curve (Inercia)", fontweight="bold", pad=10)
    axes[0].set_xlabel("Número de Clusters (K)")
    axes[0].set_ylabel("Inercia (WCSS)")
    axes[0].grid(True, linestyle="--", alpha=0.3)

    # Silhouette
    best_k_sil = k_range[np.argmax(silhouettes)]
    axes[1].plot(k_range, silhouettes, color=CYAN, marker="s", lw=2, markersize=6)
    axes[1].axvline(best_k_sil, color=RED, ls="--", lw=1.5,
                    label=f"Mejor K={best_k_sil} ({max(silhouettes):.3f})")
    axes[1].set_title("Silhouette Score (mayor es mejor)", fontweight="bold", pad=10)
    axes[1].set_xlabel("Número de Clusters (K)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].legend(fontsize=9)
    axes[1].grid(True, linestyle="--", alpha=0.3)

    # Davies-Bouldin
    best_k_db = k_range[np.argmin(db_scores)]
    axes[2].plot(k_range, db_scores, color=ORANGE, marker="^", lw=2, markersize=6)
    axes[2].axvline(best_k_db, color=RED, ls="--", lw=1.5,
                    label=f"Mejor K={best_k_db} ({min(db_scores):.3f})")
    axes[2].set_title("Davies-Bouldin Index (menor es mejor)", fontweight="bold", pad=10)
    axes[2].set_xlabel("Número de Clusters (K)")
    axes[2].set_ylabel("Davies-Bouldin Index")
    axes[2].legend(fontsize=9)
    axes[2].grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout(pad=2.5)
    ruta = GRAFICAS_DIR / "elbow_silhouette.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] {ruta.name}")
    return best_k_sil, silhouettes, db_scores, k_range


def calibrar_epsilon(coords_scaled, min_samples=10):
    """K-distance graph para estimar epsilon óptimo de DBSCAN."""
    nbrs = NearestNeighbors(n_neighbors=min_samples).fit(coords_scaled)
    distances, _ = nbrs.kneighbors(coords_scaled)
    k_distances = np.sort(distances[:, -1])[::-1]

    # Derivada segunda para encontrar el codo
    deriv2 = np.gradient(np.gradient(k_distances))
    eps_idx = np.argmax(np.abs(deriv2[10:-10])) + 10
    eps_opt = float(k_distances[eps_idx])
    return eps_opt, k_distances


def plot_comparacion(df_ml, labels_km, labels_db, best_k):
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), facecolor=DARK)
    fig.suptitle(
        f"Comparación de Algoritmos de Clustering — KMeans (K={best_k}) vs DBSCAN",
        fontsize=14, fontweight="bold", y=1.01)

    cmap = plt.cm.get_cmap("tab20", best_k)

    for ax, labels, title in [
        (axes[0], labels_km, f"KMeans (K={best_k})"),
        (axes[1], labels_db, "DBSCAN"),
    ]:
        # Noise en DBSCAN = -1
        mask_noise = labels == -1
        n_clusters = len(set(labels[~mask_noise]))

        colors_arr = [cmap(l / max(labels.max(), 1)) if l >= 0 else (0.4, 0.4, 0.4, 0.3)
                      for l in labels]
        ax.scatter(df_ml["longitud"], df_ml["latitud"],
                   c=colors_arr, alpha=0.5, s=4, edgecolors="none")
        if mask_noise.any():
            ax.scatter(df_ml.loc[mask_noise, "longitud"],
                       df_ml.loc[mask_noise, "latitud"],
                       c="gray", alpha=0.15, s=2, edgecolors="none", label="Noise")

        ax.set_title(f"{title}\n{n_clusters} clusters | Noise: {mask_noise.sum():,} pts",
                     fontweight="bold", pad=10)
        ax.set_xlabel("Longitud")
        ax.set_ylabel("Latitud")
        ax.grid(True, linestyle="--", alpha=0.2)
        ax.set_aspect("equal")
        ax.legend(fontsize=8)

    fig.tight_layout(pad=2.0)
    ruta = GRAFICAS_DIR / "comparacion_dbscan_kmeans.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"   [✓] {ruta.name}")


def generar_mapa_dbscan(df_ml, labels_db):
    n_clusters = len(set(labels_db[labels_db >= 0]))
    m = folium.Map(location=CDMX_CENTER, zoom_start=11,
                   tiles="CartoDB dark_matter", control_scale=True, prefer_canvas=True)
    m.get_root().html.add_child(folium.Element(GLOBAL_CSS))
    m.get_root().html.add_child(folium.Element(f"""
    <div class="modern-title">
        <h1>Clusters Espaciales — DBSCAN</h1>
        <p>{n_clusters} clusters significativos | Tolerante a formas irregulares</p>
    </div>"""))

    palette = list(mcolors.TABLEAU_COLORS.values()) + [
        "#FF6B6B","#7C5CFC","#00D9A3","#FFB347","#FF85A1","#5CE1E6",
        "#B5D99C","#C77DFF","#FFD166","#06D6A0",
    ]

    df_ml = df_ml.copy()
    df_ml["cluster_db"] = labels_db
    noise = df_ml[df_ml["cluster_db"] == -1]

    # Añadir puntos noise (muy transparentes)
    for _, row in noise.sample(min(len(noise), 2000), random_state=42).iterrows():
        folium.CircleMarker(
            [row["latitud"], row["longitud"]],
            radius=1.5, color="#555", fill=True,
            fill_color="#555", fill_opacity=0.2, weight=0
        ).add_to(m)

    # Centroides y círculos por cluster
    cluster_info = []
    for cid in sorted(set(labels_db[labels_db >= 0])):
        subset = df_ml[df_ml["cluster_db"] == cid]
        lat_c  = subset["latitud"].mean()
        lon_c  = subset["longitud"].mean()
        n_pts  = len(subset)
        color  = palette[cid % len(palette)]

        folium.Circle([lat_c, lon_c], radius=800,
                      color=color, fill=True, fill_color=color,
                      fill_opacity=0.12, weight=1).add_to(m)
        folium.CircleMarker([lat_c, lon_c], radius=5,
                            color=color, fill=True, fill_color=color,
                            fill_opacity=0.9,
                            popup=folium.Popup(
                                f"<b>Cluster #{cid}</b><br>Puntos: {n_pts:,}", max_width=200)
                            ).add_to(m)
        cluster_info.append({"cluster_id": cid, "lat": lat_c, "lon": lon_c,
                              "n_puntos": n_pts, "color": color})

    ruta_mapa = MAPAS_DIR / "mapa_clusters_dbscan.html"
    m.save(str(ruta_mapa))
    print(f"   [✓] {ruta_mapa.name}")
    return cluster_info


def main():
    print("=" * 70)
    print("  VALIDACIÓN CLUSTERS: DBSCAN vs KMEANS  [A-1]")
    print("=" * 70)

    print("\n[1/5] Cargando y preparando datos geoespaciales...")
    locatel  = pd.read_csv(DATA_DIR / "locatel0311-2024_limpio.csv")
    carpetas = pd.read_csv(DATA_DIR / "carpetasFGJ_2024_limpio.csv")

    locatel  = filtrar_coords(locatel)
    carpetas = filtrar_coords(carpetas)

    alumb = locatel[locatel["tema_solicitud"] == "ALUMBRADO"].copy()
    carpetas["hora"] = pd.to_datetime(
        carpetas["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour
    nocturnos = carpetas[(carpetas["hora"] >= 20) | (carpetas["hora"] <= 5)].copy()

    alumb["origen"]     = "Alumbrado"
    nocturnos["origen"] = "Delito Nocturno"
    df_ml = pd.concat([
        alumb[["latitud","longitud","origen"]],
        nocturnos[["latitud","longitud","origen"]]
    ]).reset_index(drop=True)

    print(f"   Total puntos: {len(df_ml):,}")

    coords = df_ml[["latitud","longitud"]].values
    scaler = StandardScaler()
    coords_scaled = scaler.fit_transform(coords)

    # ── 2. Elbow + Silhouette + Davies-Bouldin ────────────────────────────────
    print("[2/5] Calculando métricas KMeans (K=3..25) — puede tardar ~1 min...")
    # Muestrear para velocidad
    idx_sample = np.random.RandomState(42).choice(len(coords_scaled),
                                                   min(len(coords_scaled), 30000),
                                                   replace=False)
    cs_sample = coords_scaled[idx_sample]
    k_range   = list(range(3, 26))
    best_k, silhouettes, db_scores, ks = plot_elbow_silhouette(cs_sample, k_range)
    print(f"   K óptimo por Silhouette: {best_k}")

    # ── 3. DBSCAN ─────────────────────────────────────────────────────────────
    print("[3/5] Calibrando y entrenando DBSCAN...")
    MIN_SAMPLES = 50
    eps_opt, _ = calibrar_epsilon(cs_sample[:5000], min_samples=MIN_SAMPLES)
    print(f"   Epsilon estimado (k-distance): {eps_opt:.4f}  |  min_samples={MIN_SAMPLES}")

    db = DBSCAN(eps=eps_opt, min_samples=MIN_SAMPLES, n_jobs=-1)
    labels_db_full = db.fit_predict(coords_scaled)
    df_ml["cluster_dbscan"] = labels_db_full

    n_clusters_db = len(set(labels_db_full[labels_db_full >= 0]))
    noise_pct = (labels_db_full == -1).mean() * 100
    print(f"   DBSCAN → {n_clusters_db} clusters | Noise: {noise_pct:.1f}%")

    # ── 4. KMeans con K óptimo ────────────────────────────────────────────────
    print(f"[4/5] Entrenando KMeans con K={best_k} (óptimo)...")
    km_best = MiniBatchKMeans(n_clusters=best_k, random_state=42, n_init="auto")
    labels_km = km_best.fit_predict(coords_scaled)
    df_ml["cluster_kmeans"] = labels_km

    # Métricas finales
    sil_km = silhouette_score(coords_scaled[idx_sample], labels_km[idx_sample])
    db_km  = davies_bouldin_score(coords_scaled[idx_sample], labels_km[idx_sample])

    mask_valid = labels_db_full != -1
    sil_db = (silhouette_score(coords_scaled[mask_valid][::5],
                               labels_db_full[mask_valid][::5])
              if mask_valid.sum() > 1000 else np.nan)
    db_db  = (davies_bouldin_score(coords_scaled[mask_valid][::5],
                                   labels_db_full[mask_valid][::5])
              if mask_valid.sum() > 1000 else np.nan)

    print(f"\n   {'Métrica':<30} {'KMeans':>10} {'DBSCAN':>10}")
    print(f"   {'-'*50}")
    print(f"   {'Silhouette Score':<30} {sil_km:>10.4f} {sil_db:>10.4f}")
    print(f"   {'Davies-Bouldin Index':<30} {db_km:>10.4f} {db_db:>10.4f}")
    print(f"   {'Nº de Clusters':<30} {best_k:>10} {n_clusters_db:>10}")
    print(f"   {'Noise Points':<30} {'0%':>10} {noise_pct:>9.1f}%")

    # Tabla de validación completa
    rows_val = []
    for k, sil, dbi in zip(ks, silhouettes, db_scores):
        rows_val.append({"k": k, "silhouette": round(sil, 5), "davies_bouldin": round(dbi, 5)})
    df_val = pd.DataFrame(rows_val)
    df_val.loc[len(df_val)] = {
        "k": f"DBSCAN ({n_clusters_db})",
        "silhouette": round(sil_db, 5) if not np.isnan(sil_db) else "N/A",
        "davies_bouldin": round(db_db, 5) if not np.isnan(db_db) else "N/A",
    }
    ruta_val = TABLAS_DIR / "validacion_clusters.csv"
    df_val.to_csv(ruta_val, index=False, encoding="utf-8-sig")
    print(f"\n   [✓] Tabla exportada: {ruta_val.name}")

    # ── 5. Visualizaciones ────────────────────────────────────────────────────
    print("[5/5] Generando visualizaciones...")
    plot_comparacion(df_ml, labels_km, labels_db_full, best_k)
    generar_mapa_dbscan(df_ml, labels_db_full)

    print("\n" + "=" * 70)
    print("  VALIDACIÓN CLUSTERS COMPLETADA")
    print(f"  KMeans K óptimo: {best_k}  |  DBSCAN: {n_clusters_db} clusters")
    print("=" * 70)


if __name__ == "__main__":
    main()
