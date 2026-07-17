# Marco Teórico y Estado del Arte

**Proyecto:** UrbanSignal CDMX - Análisis Inteligente de Infraestructura Urbana y Criminalidad
**Programa:** DELFIN 2026

---

## 1. Marco Teórico

El presente análisis se fundamenta teóricamente en la intersección de la criminología ambiental y el urbanismo preventivo. Específicamente, el modelo se sostiene sobre dos pilares conceptuales clave:

### 1.1 Teoría de las Actividades Rutinarias (Cohen y Felson, 1979)
Esta teoría postula que un delito ocurre cuando convergen en el tiempo y el espacio tres elementos fundamentales:
1. Un ofensor motivado.
2. Un objetivo adecuado (víctima o bien material).
3. La ausencia de un guardián capaz (vigilancia formal o informal).

En el contexto de este proyecto, las **fallas en la infraestructura urbana** (como la falta de alumbrado público o la presencia de espacios degradados reportados a Locatel) actúan suprimiendo la figura del "guardián capaz". La oscuridad y el abandono limitan la vigilancia natural de los vecinos y transeúntes, facilitando la convergencia delictiva.

### 1.2 Prevención del Delito Mediante el Diseño Ambiental (CPTED)
El enfoque CPTED (Crime Prevention Through Environmental Design) sostiene que el diseño adecuado y el uso efectivo del entorno construido pueden reducir el miedo al crimen y la incidencia delictiva. Uno de sus principios básicos es la **vigilancia natural**, la cual se ve directamente vulnerada cuando la infraestructura lumínica o el mantenimiento de las calles falla. Nuestro proyecto cuantifica este postulado empíricamente cruzando reportes de deterioro físico (SUAC/Locatel) con carpetas de investigación (FGJ).

---

## 2. Estado del Arte (Revisión Bibliográfica)

El uso de técnicas de *Machine Learning* y análisis de datos geoespaciales para el estudio del crimen en contextos urbanos ha avanzado significativamente hacia lo que hoy denominamos Ciudades Inteligentes (Smart Cities).

### 2.1 Análisis Geoespacial y Detección de Hotspots
Históricamente, el análisis criminal dependía de mapas estáticos de calor (Kernel Density Estimation). Sin embargo, la literatura reciente favorece algoritmos basados en densidad que no asumen distribuciones paramétricas uniformes. 
* El uso de **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** se ha consolidado como el estándar de oro para descubrir aglomeraciones espaciales irregulares de delitos (hotspots), permitiendo discriminar casos aislados (ruido) de verdaderos focos de criminalidad sistemática. Nuestro proyecto implementa DBSCAN calibrando el parámetro de vecindad ($\epsilon$) específicamente para la densidad demográfica de la CDMX.

### 2.2 Autocorrelación Espacial
Investigaciones en geografía cuantitativa demuestran que el crimen no ocurre de forma aleatoria, sino que exhibe una fuerte dependencia espacial (lo que ocurre en una colonia afecta a la vecina).
* Para validar estadísticamente esta premisa antes del modelado, el estado del arte exige el cálculo del **Índice Global y Local de Moran (Moran's I)**. Esta técnica asegura que los clústeres observados son estadísticamente significativos y no producto del azar, paso que fue integrado exitosamente en el flujo de procesamiento (ETL) de nuestro repositorio.

### 2.3 Modelado Predictivo de Conteos (Count Data Models)
En la literatura econométrica y criminológica, el modelado de eventos delictivos por cuadrante territorial requiere manejar variables de conteo discreto (número de delitos) que presentan sobredispersión (la varianza es mayor que la media, debido a zonas con cero delitos y otras con cientos).
* Los estudios modernos descartan la Regresión Lineal Ordinaria (OLS) a favor de la **Regresión de Poisson** o la **Regresión Binomial Negativa**. Este proyecto implementa esta última para extraer el *Incidence Rate Ratio (IRR)*, permitiendo responder con rigor empírico a la pregunta: *"¿En qué porcentaje aumenta la probabilidad de que ocurra un delito por cada falla de infraestructura no atendida en una misma colonia?"*

### 2.4 Sistemas de Soporte a la Decisión (Dashboards)
Finalmente, la vanguardia en políticas públicas basadas en evidencia apunta a democratizar el acceso a los modelos algorítmicos. La construcción de un **Dashboard interactivo** (desarrollado en Dash/Plotly) permite a los tomadores de decisiones visualizar el *Índice de Riesgo Urbano* y la tendencia espacio-temporal de los delitos en tiempo real, alineándose con las mejores prácticas del diseño de herramientas analíticas para gobiernos locales.

---

## 3. Justificación del Proyecto
Mientras que muchos análisis delictivos en México se limitan a la estadística descriptiva, el proyecto **UrbanSignal CDMX** aporta valor científico al integrar:
1. Una base teórica robusta (Actividades Rutinarias).
2. Técnicas avanzadas de clustering (DBSCAN).
3. Inferencia estadística espacial (Moran's I y Regresión Binomial Negativa).

Este pipeline tecnológico transforma datos gubernamentales aislados (abiertos) en un **Sistema de Inteligencia Geoespacial** aplicable y escalable.
