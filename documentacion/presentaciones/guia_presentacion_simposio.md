# Guía de Presentación — Mini Simposio DELFIN
## UrbanSignal CDMX · Julio 2026

**Duración:** 10–15 minutos + 5 min preguntas  
**Audiencia:** Investigadores, asesores y estudiantes del programa DELFIN

---

## Estructura Sugerida de la Presentación (12 diapositivas)

---

### Diapositiva 1 — Portada
- **Título:** Infraestructura, Desorden y Delito: Análisis Espacial e Inteligente de la Relación entre Fallas de Servicios Urbanos e Incidencia Delictiva en la CDMX
- **Autor:** [Tu nombre]
- **Institución / Laboratorio GeoDataX**
- **Fecha:** Julio 2026, Mini Simposio DELFIN
- *Imagen de fondo: mapa de CDMX o infografía dark mode*

---

### Diapositiva 2 — El Problema (1.5 min)
**Pregunta guía:** ¿Dónde y cuándo ocurre el crimen en CDMX, y tiene algo que ver con las fallas de infraestructura?

**Puntos a comunicar:**
- CDMX registra >129,000 delitos en 2024
- Teoría de las "Ventanas Rotas" (Wilson & Kelling, 1982): el deterioro urbano facilita el delito
- La relación entre infraestructura y crimen nunca ha sido cuantificada sistemáticamente con datos abiertos de la CDMX

**Pregunta de investigación en la pantalla:**
> "¿Existe una correlación estadísticamente significativa entre las fallas de alumbrado público reportadas vía Locatel y la incidencia delictiva nocturna en la CDMX?"

---

### Diapositiva 3 — Datos Utilizados (1 min)
**Tabla visual de los datasets:**

| Dataset | Fuente | Registros |
|---------|--------|-----------|
| FGJ Carpetas 2024 | datos.cdmx.gob.mx | ~129,000 |
| FGJ Víctimas 2024 | datos.cdmx.gob.mx | ~126,000 |
| Locatel 0311 2024 | datos.cdmx.gob.mx | ~57,000 |
| Colonias CDMX | SEDATU | 1,812 colonias |
| INEGI Censo 2020 | INEGI | 16 alcaldías |

**Mensaje:** Todos son datos abiertos del gobierno, lo que hace el análisis reproducible.

---

### Diapositiva 4 — Metodología Pipeline (1.5 min)
**Diagrama de flujo del pipeline:**

```
Datos crudos → ETL/Limpieza → EDA → Correlación → Moran's I → Regresión → IRU → Resultados
```

**Técnicas clave a mencionar:**
- Limpieza y normalización con pandas
- Correlación Pearson/Spearman espacial y temporal (lags)
- Autocorrelación espacial con Moran's I + LISA
- Regresión Binomial Negativa con offset poblacional
- DBSCAN para zonas críticas
- Índice de Riesgo Urbano (IRU) compuesto

---

### Diapositiva 5 — Mapa de Calor: ¿Dónde ocurren los delitos? (1 min)
**Mostrar:** `resultados/mapas/mapa_comparativo_incidencias_delitos.html`

**Mensaje:** La distribución no es uniforme — existe concentración geográfica evidente.

---

### Diapositiva 6 — Correlación Espacial y Temporal (1.5 min)
**Mostrar:** `resultados/graficas/dispersion_alumbrado_delitos.png`  
**Mostrar:** `resultados/graficas/correlacion_temporal_lags.png`

**Mensaje a comunicar:**
- Existe correlación positiva entre fallas de alumbrado y delitos nocturnos a nivel colonia
- El análisis de lags muestra que la relación es concurrente (no hay rezago claro), lo que sugiere que ambos fenómenos responden a factores estructurales comunes

---

### Diapositiva 7 — Autocorrelación Espacial (Moran's I + LISA) (1.5 min)
**Mostrar:** `resultados/graficas/moran_scatterplot.png`  
**Mostrar:** `resultados/mapas/mapa_lisa_clusters.html`

**Mensaje:**
- Moran's I a nivel alcaldía no es significativo (p≈0.96), lo cual se explica por el bajo n (16 unidades)
- Los clusters LISA identifican patrones locales relevantes incluso con Moran global no significativo
- **Nota metodológica:** Se recomienda reanálisis a nivel colonia (n>1,000) para mayor poder estadístico

---

### Diapositiva 8 — Regresión Binomial Negativa (1 min)
**Mostrar:** `resultados/graficas/coeficientes_modelo.png`

**Resultados clave:**
- Razón Varianza/Media = 3,231 → sobredispersión → Binomial Negativa
- AIC = 292.61, BIC = 298.79
- Los coeficientes más significativos indican qué tipos de fallas se asocian más con el número de delitos

---

### Diapositiva 9 — Índice de Riesgo Urbano (1 min)
**Mostrar:** `resultados/graficas/ranking_riesgo_alcaldias.png`  
**Mostrar:** `resultados/mapas/mapa_riesgo_coropletico.html`

**Mensaje:**
- El IRU integra 5 componentes en un indicador único (0–100) por alcaldía
- Permite priorizar intervenciones de política pública de forma objetiva y reproducible
- Top 3 alcaldías de mayor riesgo: [del CSV `indice_riesgo_urbano.csv`]

---

### Diapositiva 10 — Zonas Críticas y Perfil de Víctimas (1 min)
**Mostrar:** `resultados/mapas/mapa_clusters_criticos.html`  
**Mostrar:** `resultados/graficas/perfil_victimas_zonas_criticas.png`

**Mensaje:**
- DBSCAN identificó macro-zonas de concentración de incidentes
- En las zonas críticas: mayoría de víctimas son hombres de 20–40 años

---

### Diapositiva 11 — Conclusiones (1.5 min)

**Lo que encontramos:**
1. Existe correlación positiva entre fallas de alumbrado y delitos nocturnos, aunque moderada
2. La distribución del crimen en CDMX no es aleatoria — hay zonas de concentración persistente
3. El modelo Binomial Negativa identifica las categorías de falla de infraestructura más asociadas con delitos
4. El IRU proporciona una herramienta operativa para priorizar intervenciones

**Limitaciones:**
- Causalidad no establecida (correlación ≠ causalidad)
- Sesgo de reporte en Locatel
- Bajo n para análisis a nivel alcaldía (n=16)

---

### Diapositiva 12 — Trabajo Futuro y Agradecimientos (30 seg)

**Trabajo futuro:**
- Análisis a nivel colonia con polígonos GeoJSON (mayor poder estadístico)
- Integración de datos económicos (DENUE, IDH por colonia)
- Modelo predictivo temporal (ARIMA, Prophet)
- Dashboard interactivo para tomadores de decisiones

**Agradecimientos:** [Tu asesor / Laboratorio / DELFIN]

---

## Notas para la Presentación

- **Abrir los mapas HTML antes de la presentación** para que carguen correctamente
- **Tener el reporte HTML** de evaluación metodológica como respaldo
- **Preparar respuesta** para la pregunta sobre Moran's I no significativo (es esperado con n=16)
- **Tiempo estimado:** 12 min exposición + 3 min preguntas
