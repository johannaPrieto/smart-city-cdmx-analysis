# Resumen DELFIN
## Estancia de Investigación · Verano 2026

**Título del proyecto:**
Infraestructura, Desorden y Delito: Análisis Espacial e Inteligente de la Relación entre Fallas de Servicios Urbanos e Incidencia Delictiva en la Ciudad de México

**Autor:** Johanna Prieto  
**Institución de adscripción:** Unidad Profesional Interdisciplinaria en Ingeniería y Tecnologías Avanzadas 
**Laboratorio receptor:** GeoDataX / Laboratorio de Inteligencia Artificial Geoespacial  
**Asesor:** Dr. Miguel Felix Mata Rivera
**Fecha:** Julio 2026

---

## Resumen (200–250 palabras)

La Ciudad de México (CDMX) registra simultáneamente altas tasas de fallas de infraestructura urbana —reportadas por la ciudadanía vía Locatel 0311— y elevados índices de incidencia delictiva documentados por la Fiscalía General de Justicia. Este proyecto analiza cuantitativamente la relación entre ambos fenómenos mediante un pipeline de análisis geoespacial, estadístico y de inteligencia artificial aplicado a datos abiertos del año 2024.

Se procesaron tres datasets principales: carpetas de investigación FGJ (~129,000 registros), víctimas FGJ (~126,000 registros) y reportes Locatel 0311 (~57,000 registros), integrándolos mediante técnicas de limpieza, normalización poblacional con datos del Censo INEGI 2020, y cruce espacial a nivel de colonia y alcaldía.

Los análisis realizados incluyen: correlación de Pearson y Spearman entre fallas de alumbrado y delitos nocturnos; correlación cruzada temporal con rezagos de hasta cuatro semanas; autocorrelación espacial con Moran's I global y LISA; regresión de Binomial Negativa con offset poblacional; detección de outliers mediante IQR, Z-Score e Isolation Forest; clustering espacial con DBSCAN; y construcción de un Índice de Riesgo Urbano (IRU) compuesto escalado de 0 a 100 por alcaldía.

Los resultados muestran patrones diferenciados de riesgo entre las 16 alcaldías, con correlaciones positivas entre fallas de infraestructura y delincuencia en zonas específicas. El IRU permite priorizar alcaldías para intervención de política pública basada en evidencia, aportando una herramienta de toma de decisiones para el modelo de ciudad inteligente de la CDMX.

**Palabras clave:** Smart City, infraestructura urbana, criminalidad, análisis espacial, Moran's I, CDMX, datos abiertos.

---

## Abstract (English version)

Mexico City simultaneously experiences high rates of urban infrastructure failures —reported by citizens through the Locatel 0311 service— and elevated crime rates documented by the General Justice Prosecutor's Office. This project quantitatively analyzes the relationship between both phenomena using a geospatial, statistical, and artificial intelligence analysis pipeline applied to open data from 2024.

Three main datasets were processed: FGJ investigation files (~129,000 records), FGJ victim records (~126,000 records), and Locatel 0311 reports (~57,000 records), integrated through data cleaning, population normalization using 2020 INEGI Census data, and spatial matching at the borough and neighborhood levels.

Analyses include: Pearson and Spearman correlation between lighting failures and nighttime crime; temporal cross-correlation with lags of up to four weeks; spatial autocorrelation using Global Moran's I and LISA; Negative Binomial regression with population offset; outlier detection using IQR, Z-Score, and Isolation Forest; spatial clustering with DBSCAN; and construction of a composite Urban Risk Index (URI) scaled 0–100 by borough.

Results show differentiated risk patterns across Mexico City's 16 boroughs, with positive correlations between infrastructure failures and crime in specific areas. The URI enables evidence-based prioritization for public policy intervention, providing a decision-making tool for Mexico City's smart city model.

**Keywords:** Smart City, urban infrastructure, crime, spatial analysis, Moran's I, Mexico City, open data.
