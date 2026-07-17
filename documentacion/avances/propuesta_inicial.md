# Propuesta Inicial — Producto Integrador
## Estancia de Investigación DELFIN · Semana 1

**Título del proyecto:**
Infraestructura, Desorden y Delito: Análisis Espacial e Inteligente de la Relación entre Fallas de Servicios Urbanos e Incidencia Delictiva en la Ciudad de México

**Autor:** Johanna Prieto  
**Institución de adscripción:** Unidad Profesional Interdisciplinaria en Ingeniería y Tecnologías Avanzadas  
**Laboratorio receptor:** Laboratorio de Inteligencia Artificial Geoespacial / GeoDataX  
**Fecha:** Junio 2026

---

## 1. Descripción del Problema

La Ciudad de México (CDMX) enfrenta un desafío dual: deterioro de la infraestructura urbana (alumbrado, agua, vialidades) y alta incidencia delictiva. La teoría de las "ventanas rotas" (Wilson & Kelling, 1982) postula que el desorden físico observable en el entorno urbano —como luminarias fundidas o banquetas en mal estado— puede actuar como señal de abandono institucional y facilitar la comisión de delitos.

Sin embargo, en el contexto de la CDMX, esta relación no ha sido cuantificada de forma sistemática, ni se ha validado estadísticamente a nivel de colonia o alcaldía combinando fuentes de datos abiertas del gobierno local con técnicas modernas de ciencia de datos.

**Pregunta de investigación:**
> ¿Existe una correlación estadísticamente significativa entre el volumen y tipo de fallas de infraestructura urbana reportadas vía Locatel y la incidencia delictiva registrada por la Fiscalía General de Justicia de la CDMX durante 2024, a nivel de colonia y alcaldía?

---

## 2. Objetivo General

Analizar la relación espacio-temporal entre reportes ciudadanos de fallas de infraestructura urbana (Locatel 0311) e incidencia delictiva (FGJ CDMX) mediante técnicas de análisis geoespacial, ciencia de datos e inteligencia artificial aplicadas a datos abiertos del año 2024.

## 3. Objetivos Específicos

1. Limpiar, integrar y normalizar los datasets Locatel, FGJ Carpetas y FGJ Víctimas.
2. Calcular estadísticas descriptivas y generar visualizaciones geoespaciales de la distribución de fallas e incidentes.
3. Evaluar la correlación espacial (Pearson, Spearman, Moran's I) entre variables de infraestructura y criminalidad.
4. Analizar la correlación temporal con rezagos entre fallas de alumbrado y delitos nocturnos.
5. Construir un Índice de Riesgo Urbano (IRU) compuesto por alcaldía.
6. Identificar zonas críticas mediante algoritmos de clustering (DBSCAN).
7. Modelar la relación mediante regresión de Poisson o Binomial Negativa.

---

## 4. Datasets Principales

| Dataset | Fuente | Periodo | Formato | Descripción |
|---------|--------|---------|---------|-------------|
| Carpetas de investigación FGJ | Fiscalía General de Justicia CDMX | 2024 | CSV | Delitos denunciados con coordenadas |
| Víctimas FGJ | Fiscalía General de Justicia CDMX | 2024 | CSV | Perfil demográfico de víctimas |
| Locatel 0311 | Gobierno CDMX | Mar–Nov 2024 | CSV | Reportes ciudadanos de fallas urbanas |
| Catálogo de Colonias | SEDATU / CDMX | 2023 | GeoJSON | Polígonos de colonias y alcaldías |
| Población por alcaldía | INEGI Censo 2020 | 2020 | Integrado | Para normalización de tasas |

---

## 5. Metodología Preliminar

- **ETL:** Limpieza y normalización de los tres datasets con pandas
- **EDA:** Estadística descriptiva, histogramas, series temporales y mapas de calor
- **Análisis espacial:** Correlación por colonia/alcaldía, Moran's I global y LISA
- **Análisis temporal:** Correlación cruzada con rezagos semanales
- **Modelado predictivo:** Regresión de Poisson / Binomial Negativa
- **Índice compuesto:** IRU ponderado por tasas de delitos, alumbrado y LISA

---

## 6. Productos Esperados

- Dataset limpio e integrado de fallas urbanas y criminalidad
- Mapas interactivos de calor y clusters
- Tablas de correlación y modelos estadísticos
- Índice de Riesgo Urbano por alcaldía
- Reporte técnico y presentación científica
- Resumen DELFIN para el simposio

---

## 7. Herramientas

Python · pandas · GeoPandas · Folium · Scikit-learn · statsmodels · esda · libpysal · matplotlib · seaborn · Plotly
