# UrbanSignal CDMX

> **Infraestructura, Desorden y Delito:** Análisis Espacial e Inteligente de la Relación entre Fallas de Servicios Urbanos e Incidencia Delictiva en la Ciudad de México.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![Estancia DELFIN](https://img.shields.io/badge/Estancia-DELFIN%202026-purple)](https://www.delfin.org.mx)

---

## Objetivo

Analizar la relación entre reportes ciudadanos de infraestructura urbana (Locatel 0311) e incidencia delictiva (FGJ CDMX) mediante técnicas de análisis geoespacial, ciencia de datos e inteligencia artificial aplicadas a datos abiertos del año 2024.

## Pregunta de Investigación

¿Existe una correlación estadísticamente significativa entre las fallas de infraestructura urbana reportadas y la incidencia delictiva en la CDMX a nivel de colonia y alcaldía?

---

## Datasets Principales

| Dataset | Fuente | Registros |
|---------|--------|-----------|
| FGJ CDMX — Carpetas de investigación | datos.cdmx.gob.mx | ~129,000 |
| FGJ CDMX — Víctimas | datos.cdmx.gob.mx | ~126,000 |
| Locatel 0311 — Reportes ciudadanos | datos.cdmx.gob.mx | ~57,000 |
| Catálogo de Colonias CDMX | datos.cdmx.gob.mx | 1,812 colonias |
| INEGI Censo 2020 | inegi.org.mx | 16 alcaldías |

---

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd cdmx-analysis

# Crear y activar entorno virtual
python -m venv urban_env
urban_env\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar librerías espaciales (si es necesario)
pip install esda libpysal
```

---

## Ejecución del Pipeline

Los scripts deben ejecutarse en el siguiente orden desde la raíz del proyecto:

```bash
# 1. ETL — Limpieza de datos
python scripts/limpieza/limpieza_1.py   # FGJ Carpetas
python scripts/limpieza/limpieza_2.py   # FGJ Víctimas
python scripts/limpieza/limpieza_3.py   # Locatel
python scripts/limpieza/limpieza_4.py   # Colonias GeoJSON

# 2. Análisis Exploratorio
python scripts/analisis/analisis_exploratorio.py

# 3. Normalización INEGI
python scripts/analisis/normalizacion_inegi.py

# 4. Outliers
python scripts/analisis/outliers.py

# 5. Correlación Espacial (Pearson + Spearman)
python scripts/analisis/correlacion_espacial.py

# 6. Correlación Temporal (lags)
python scripts/analisis/correlacion_temporal.py

# 7. Clustering DBSCAN
python scripts/analisis/clustering_dbscan.py
python scripts/analisis/clustering_ml.py

# 8. Análisis de Víctimas
python scripts/analisis/analisis_victimas.py

# 9. Autocorrelación Espacial (Moran's I + LISA)
python scripts/analisis/moran_I.py

# 10. Regresión Poisson / Binomial Negativa
python scripts/analisis/regresion_poisson.py

# 11. Índice de Riesgo Urbano
python scripts/analisis/indice_riesgo_urbano.py

# 12. Mapas interactivos
python scripts/visualizacion/generar_mapas.py

# 13. Reporte de evaluación metodológica
python scripts/analisis/evaluacion_metodologica.py
```

---

## Resultados Generados

### Tablas (`resultados/tablas/`)
| Archivo | Descripción |
|---------|-------------|
| `indice_riesgo_urbano.csv` | IRU 0–100 por alcaldía con nivel de riesgo |
| `moran_I_resultados.csv` | Moran's I global y conteo LISA por variable |
| `coeficientes_modelo.csv` | Coeficientes IRR del modelo Binomial Negativa |
| `outliers_detectados.csv` | Colonias atípicas por IQR, Z-Score e IsoForest |
| `correlacion_espacial.csv` | Cruce Locatel × FGJ por colonia (>67,000 filas) |

### Gráficas (`resultados/graficas/`)
22 PNGs: rankings por alcaldía, series temporales, dispersión alumbrado vs delitos, Moran scatter plot, boxplots, Isolation Forest, radar IRU, perfiles de víctimas.

### Mapas Interactivos (`resultados/mapas/`)
| Mapa | Descripción |
|------|-------------|
| `mapa_delitos_fgj.html` | Heatmap de delitos FGJ 2024 |
| `mapa_incidencias_locatel.html` | Heatmap de incidencias Locatel |
| `mapa_comparativo_incidencias_delitos.html` | Comparativo dual |
| `mapa_clusters_criticos.html` | Zonas críticas DBSCAN |
| `mapa_lisa_clusters.html` | Clusters LISA (HH/LL/HL/LH) |
| `mapa_riesgo_coropletico.html` | Índice de Riesgo Urbano por alcaldía |

### Reportes (`resultados/reportes/`)
| Reporte | Descripción |
|---------|-------------|
| `evaluacion_metodologica.html` | Evaluación visual del pipeline |
| `modelo_regresion_poisson.txt` | Resumen estadístico del modelo |

---

## Estructura del Proyecto

```
cdmx-analysis/
├── datasets/
│   ├── raw/              # Datos originales sin modificar
│   ├── processed/        # Datos limpios listos para análisis
│   └── clean/            # Versiones finales exportadas
├── scripts/
│   ├── limpieza/         # ETL: limpieza_1.py a limpieza_4.py
│   ├── analisis/         # 11 scripts de análisis (EDA, ML, espacial)
│   ├── visualizacion/    # Generación de mapas Folium
│   └── geoprocesamiento/ # Procesamiento de GeoJSON
├── resultados/
│   ├── graficas/         # 22 gráficas PNG
│   ├── tablas/           # 21 tablas CSV
│   ├── mapas/            # 6 mapas HTML interactivos
│   └── reportes/         # Reportes de texto y HTML
├── documentacion/
│   ├── metodologia/      # Documento metodológico
│   ├── estado_del_arte/  # Revisión bibliográfica + inventario
│   ├── avances/          # Propuesta inicial y avances
│   └── presentaciones/   # Presentación y resumen DELFIN
├── notebooks/            # Jupyter notebooks exploratorios
├── dashboard/            # Prototipo de dashboard
├── modelos/              # Modelos entrenados guardados
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Herramientas

| Categoría | Librería |
|-----------|----------|
| Manipulación de datos | pandas, numpy |
| Análisis espacial | geopandas, esda, libpysal |
| Visualización | matplotlib, seaborn, folium, plotly |
| Machine Learning | scikit-learn |
| Estadística | scipy, statsmodels |
| Otros | tqdm, pathlib |

---

## Documentación Adicional

- [Propuesta inicial](documentacion/avances/propuesta_inicial.md)
- [Estado del arte](documentacion/estado_del_arte/estado_del_arte.md)
- [Inventario de fuentes](documentacion/estado_del_arte/inventario_fuentes.md)
- [Documento metodológico](documentacion/metodologia/metodologia.md)
- [Resumen DELFIN](documentacion/presentaciones/resumen_delfin.md)
- [Evaluación metodológica](resultados/reportes/evaluacion_metodologica.html)

---

## Autor

**Johanna Prieto** · Estancia de Investigación DELFIN 2026  
Laboratorio de Inteligencia Artificial Geoespacial / GeoDataX