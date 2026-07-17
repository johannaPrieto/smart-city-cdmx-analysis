# Documento Metodológico
## Proyecto UrbanSignal CDMX — Análisis Espacial e Inteligente

**Título:** Infraestructura, Desorden y Delito: Análisis Espacial e Inteligente de la Relación entre Fallas de Servicios Urbanos e Incidencia Delictiva en la Ciudad de México

**Autor:** Johanna Prieto · **Estancia:** DELFIN 2026 · **Laboratorio:** GeoDataX / IA Geoespacial  
**Fecha de elaboración:** Semana 3 — Junio 2026

---

## 1. Pregunta de Investigación

> ¿Existe una relación estadísticamente significativa entre el volumen y tipo de fallas de infraestructura urbana reportadas por ciudadanos (Locatel 0311) y la incidencia delictiva registrada por la Fiscalía General de Justicia de la CDMX durante 2024?

**Hipótesis de trabajo:**
Las colonias y alcaldías con mayor concentración de reportes de fallas de alumbrado público presentan una mayor incidencia de delitos nocturnos y robo a transeúnte, controlando por la población total.

---

## 2. Diseño Metodológico General

El proyecto adopta un diseño **observacional, cuantitativo y geoespacial**. No es experimental (no hay intervención), pero busca identificar asociaciones estadísticas robustas entre variables de infraestructura urbana y criminalidad. El análisis opera en dos escalas espaciales:

- **Alcaldía** (n=16): unidad para Moran's I, IRU, regresión Poisson
- **Colonia** (n≈1,812): unidad para correlaciones espaciales, outliers, DBSCAN

---

## 3. Pipeline de Análisis

```
[DATOS CRUDOS]
      │
      ▼
[A] ETL — Limpieza y Transformación
      │  scripts/limpieza/limpieza_1.py (FGJ Carpetas)
      │  scripts/limpieza/limpieza_2.py (FGJ Víctimas)
      │  scripts/limpieza/limpieza_3.py (Locatel)
      │  scripts/limpieza/limpieza_4.py (Colonias GeoJSON)
      │
      ▼
[B] EDA — Análisis Exploratorio              [A-1]
      │  scripts/analisis/analisis_exploratorio.py
      │  → 13 tablas CSV + 12 gráficas PNG
      │
      ▼
[C] NORMALIZACIÓN POBLACIONAL                [A-3]
      │  scripts/analisis/normalizacion_inegi.py
      │  → Tasas por 1,000 hab. (INEGI Censo 2020)
      │
      ├──► [D] OUTLIERS                      [A-2]
      │         scripts/analisis/outliers.py
      │         → IQR, Z-Score, Isolation Forest
      │
      ├──► [E] CORRELACIÓN ESPACIAL
      │         scripts/analisis/correlacion_espacial.py
      │         → Pearson + Spearman por colonia
      │
      ├──► [F] CORRELACIÓN TEMPORAL
      │         scripts/analisis/correlacion_temporal.py
      │         → Cross-correlation lags semanales
      │
      ├──► [G] AUTOCORRELACIÓN ESPACIAL      [A-4]
      │         scripts/analisis/moran_I.py
      │         → Global Moran's I + LISA
      │
      ├──► [H] REGRESIÓN POISSON / NB        [A-5]
      │         scripts/analisis/regresion_poisson.py
      │         → Modelado causal infraestructura → delitos
      │
      ├──► [I] ÍNDICE DE RIESGO URBANO       [A-6]
      │         scripts/analisis/indice_riesgo_urbano.py
      │         → IRU compuesto 0-100 por alcaldía
      │
      └──► [J] CLUSTERING ESPACIAL
                scripts/analisis/clustering_dbscan.py
                scripts/analisis/clustering_ml.py
                → Zonas críticas urbanas
                → Perfil de víctimas en hotspots
```

---

## 4. Descripción de Cada Módulo Metodológico

### A. ETL — Extracción, Transformación y Carga

**Objetivo:** Obtener datasets limpios, normalizados y listos para análisis.

**Operaciones aplicadas:**
- Estandarización de formatos de fecha y hora (`datetime_hecho`, `datetime_solicitud`)
- Imputación de valores nulos en variables temporales con mediana diaria
- Relleno de campos geográficos nulos con `'DESCONOCIDA'` para preservar registros con coordenadas
- Conservación de registros sin coordenadas con bandera `sin_georeferencia`
- Normalización de texto: `.str.title().str.strip()` en alcaldía y colonia
- Eliminación de filas estructuralmente incompletas (<1% del total)

**Justificación:** No se imputan coordenadas (generaría ubicaciones falsas). Se opta por conservar registros geográficamente incompletos para el análisis temporal, y excluirlos solo en el análisis espacial.

---

### B. Análisis Exploratorio (EDA)

**Objetivo:** Describir la distribución de fallas e incidentes en tiempo, espacio y tipo.

**Variables analizadas:**
- Distribución por alcaldía, colonia, mes, día de semana, hora del día
- Top 15 delitos y temas de incidencia
- Comparativo temporal mensual Locatel vs FGJ

**Salidas:** 13 tablas CSV + 12 gráficas PNG (histogramas, barras, líneas de tiempo, comparativos)

---

### C. Normalización Poblacional

**Objetivo:** Eliminar el sesgo de tamaño poblacional al comparar alcaldías.

**Fórmula:** `tasa_X = (conteo_X / población_2020) × 1,000`

**Fuente poblacional:** INEGI Censo 2020, 16 alcaldías CDMX

**Variables normalizadas:** tasa de incidencias, tasa de delitos, tasa de fallas de alumbrado, tasa de delitos nocturnos.

**Impacto:** Las correlaciones calculadas sobre tasas son más robustas que sobre conteos brutos, especialmente al comparar Iztapalapa (1.8M hab) con Milpa Alta (152k hab).

---

### D. Detección de Valores Atípicos (Outliers)

**Objetivo:** Identificar colonias con comportamiento anómalo en una o más variables.

**Métodos aplicados:**
| Método | Criterio | Naturaleza |
|--------|----------|------------|
| IQR | Q3 + 1.5×IQR (Tukey) | Univariado |
| Z-Score | \|z\| > 3.0 | Univariado |
| Isolation Forest | contamination=0.05 | Multivariado |

**Decisión final:** Se considera outlier de consenso cuando ≥2 métodos coinciden.

---

### E. Correlación Espacial

**Objetivo:** Cuantificar la asociación lineal entre incidencias Locatel y delitos FGJ a nivel colonia.

**Unidad de análisis:** Colonia (n ≈ 1,300 con datos en ambos datasets)

**Correlaciones calculadas:**
1. Global: total incidencias vs total delitos → Pearson r, Spearman ρ
2. Específica: fallas de alumbrado vs delitos nocturnos (20h–05h) → Pearson r, Spearman ρ

---

### F. Correlación Temporal con Rezagos

**Objetivo:** Detectar si las fallas de alumbrado *preceden* (son predictivas de) los delitos o viceversa.

**Método:** Cross-correlation de Pearson con rezagos (lags) de −4 a +4 semanas.

**Interpretación:**
- Lag negativo: alumbrado precede al delito (relación causal posible)
- Lag positivo: delito precede al alumbrado
- Lag cero: concurrencia

---

### G. Autocorrelación Espacial — Moran's I + LISA

**Objetivo:** Determinar si la distribución espacial del crimen y de las fallas es aleatoria o presenta clustering estadístico.

**Métodos:**
- **Global Moran's I**: mide clustering en toda la ciudad. Rango [−1, 1]; valores positivos indican clustering, negativos dispersión.
- **LISA (Local Indicators of Spatial Association)**: clasifica cada unidad espacial en HH (hot spot), LL (cold spot), HL/LH (outliers espaciales) o NS (no significativo).

**Matriz de pesos:** KNN con k=4 vecinos más cercanos (row-standardized), adecuado para n=16 alcaldías.

**Nota metodológica:** Con solo 16 unidades espaciales (alcaldías), el poder estadístico de Moran's I es limitado. Resultados no significativos no implican ausencia de clustering, sino potencia insuficiente. Se recomienda reanálisis a nivel colonia con GeoJSON.

---

### H. Regresión de Poisson / Binomial Negativa

**Objetivo:** Modelar el número esperado de delitos por alcaldía en función de las fallas de infraestructura.

**Variable dependiente:** total_delitos (conteo por alcaldía)

**Predictores:**
- Top 5 categorías de incidencia Locatel más frecuentes (estandarizadas)
- Delitos nocturnos (estandarizado)

**Offset:** log(población_2020) — normaliza la tasa esperada de delitos por habitante

**Selección de modelo:**
- Si razón Varianza/Media > 1.5 → Binomial Negativa (sobredispersión)
- Si ≤ 1.5 → Poisson

**Resultado obtenido:** Razón V/M = 3,231 → modelo seleccionado: **Binomial Negativa** (AIC=292.61, BIC=298.79)

**Métricas de evaluación:** AIC, BIC, Log-Likelihood, Pseudo-R², IRR (Incidence Rate Ratio = exp(coeficiente))

---

### I. Índice de Riesgo Urbano (IRU)

**Objetivo:** Sintetizar múltiples dimensiones de riesgo en un indicador único por alcaldía, escalado de 0 a 100.

**Componentes y pesos:**

| Componente | Peso |
|------------|------|
| Tasa de delitos / 1,000 hab | 0.30 |
| Tasa de fallas de alumbrado / 1,000 hab | 0.20 |
| Tasa de delitos nocturnos / 1,000 hab | 0.20 |
| Proporción de delitos nocturnos (%) | 0.15 |
| Tasa de incidencias totales / 1,000 hab | 0.15 |

**Proceso de cálculo:**
1. Estandarización Z-score de cada componente
2. Suma ponderada: `IRU_raw = Σ(z_i × peso_i)`
3. Bonificación LISA: +0.5σ si alcaldía es HH (hot spot), −0.3σ si LL
4. Normalización Min-Max → escala 0–100
5. Clasificación: Bajo (<25), Medio (25–50), Alto (50–75), Muy Alto (>75)

---

### J. Clustering Espacial

**Objetivo:** Identificar macro-zonas geográficas de alta concentración de incidentes y delitos.

**Algoritmo:** DBSCAN (Density-Based Spatial Clustering of Applications with Noise)

**Ventajas sobre K-Means:**
- No requiere especificar k a priori
- Identifica clusters de forma arbitraria
- Clasifica puntos ruidosos como outliers (etiqueta −1)

**Uso:** Las zonas críticas identificadas alimentan el análisis de perfil de víctimas (`analisis_victimas.py`).

---

## 5. Limitaciones Metodológicas

1. **Causalidad no establecida:** Las correlaciones son asociaciones estadísticas, no pruebas de causalidad. La teoría respalda la dirección hipotética, pero no se puede descartar causalidad inversa.
2. **Sesgo de reporte:** Locatel solo captura incidencias *reportadas*. Áreas con menor participación ciudadana pueden estar subrepresentadas.
3. **Datos poblacionales desactualizados:** El Censo INEGI 2020 puede no reflejar la distribución poblacional actual (2024).
4. **Escala espacial:** El análisis a nivel alcaldía (n=16) tiene bajo poder estadístico. Los resultados a nivel colonia son más robustos.
5. **Periodo Locatel:** Los datos de Locatel cubren mar–nov 2024 (9 meses), mientras FGJ cubre los 12 meses. Las comparaciones temporales deben limitarse al periodo común.
6. **Datos del DENUE/INEGI:** No se pudo integrar datos económicos o de equipamiento urbano que podrían ser confusores importantes.

---

## 6. Consideraciones Éticas

- Todos los datos utilizados son datos abiertos del gobierno de la CDMX y del INEGI, de acceso público.
- No se utiliza información personal identificable de víctimas (los datos están agregados o anonimizados).
- El análisis no busca estigmatizar comunidades ni justificar políticas discriminatorias; su propósito es informar intervenciones de infraestructura basadas en evidencia.
