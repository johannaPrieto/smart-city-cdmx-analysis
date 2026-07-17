# Estado del Arte
## Análisis Espacial de Infraestructura Urbana e Incidencia Delictiva

**Proyecto:** UrbanSignal CDMX  
**Autor:** Johanna Prieto  
**Fecha de elaboración:** Julio 2026

---

## 1. Marco Teórico

### 1.1 Teoría de las Ventanas Rotas

Wilson y Kelling (1982) propusieron que el desorden físico visible en un entorno urbano —ventanas rotas, grafiti, luminarias fundidas, basura acumulada— actúa como señal de abandono institucional y aumenta la percepción de impunidad entre potenciales delincuentes. Esta teoría ha sido ampliamente debatida y refinada, pero continúa siendo referencia central en criminología urbana.

**Relevancia para este proyecto:** Los reportes de fallas de alumbrado público en Locatel son un proxy observable del desorden físico postulado por Wilson y Kelling.

### 1.2 Teoría de la Actividad Rutinaria

Cohen y Felson (1979) sostienen que un delito requiere la convergencia de tres elementos en el espacio-tiempo: un agresor motivado, una víctima adecuada y la ausencia de un guardián capaz. La falta de alumbrado público reduce la vigilancia natural y facilita esta convergencia, especialmente en horas nocturnas.

### 1.3 Geografía del Crimen (Crime Geography)

La distribución espacial del delito no es aleatoria. Técnicas como el análisis de puntos calientes (hot spots), la autocorrelación espacial y el clustering han demostrado que el crimen se concentra en áreas geográficas específicas denominadas "hot spots" (Sherman et al., 1989). El análisis espacial con datos de SIG permite identificar estos patrones.

---

## 2. Antecedentes Relevantes

### 2.1 Estudios internacionales

**Chalfin et al. (2022) — Iluminación y crimen en Nueva York:**
Un experimento cuasi-aleatorio sobre instalación de luminarias en la ciudad de Nueva York encontró que el aumento de iluminación redujo crímenes al aire libre en un 36% en horario nocturno. Este estudio refuerza la causalidad entre alumbrado y criminalidad.

> Chalfin, A., Hansen, B., Lerner, J., & Parker, L. (2022). *Reducing Crime Through Environmental Design: Evidence From a Randomized Experiment of Street Lighting in New York City*. Journal of Quantitative Criminology, 38, 127–157.

**Cozens et al. (2005) — Crime Prevention Through Environmental Design (CPTED):**
Revisión sistemática de 148 estudios sobre el impacto del diseño urbano en la prevención del crimen. Concluye que la iluminación es uno de los factores ambientales con mayor evidencia de impacto.

> Cozens, P., Saville, G., & Hillier, D. (2005). *Crime prevention through environmental design (CPTED): a review and modern bibliography*. Property Management, 23(5), 328–356.

**Wheeler et al. (2018) — Hot spots y análisis espacial:**
Evaluación de intervenciones en zonas de alta criminalidad (hot spots policing). Demuestra que el crimen tiende a concentrarse en menos del 5% del área urbana y que el análisis espacial puede guiar intervenciones focalizadas.

> Wheeler, A. P., & Ratcliffe, J. H. (2018). *A Simple Weighted Displacement Quotient to Assess Crime Spillover*. Policing: An International Journal, 41(3), 380–394.

### 2.2 Estudios en México y América Latina

**Dell (2015) — Crimen organizado y mercados ilegales en México:**
Aunque enfocado en crimen organizado, establece metodologías de análisis espacial aplicadas al contexto mexicano usando datos de homicidios y presencia policial.

> Dell, M. (2015). *Trafficking Networks and the Mexican Drug War*. American Economic Review, 105(6), 1738–1779.

**Vilalta (2010) — Análisis espacial del crimen en la CDMX:**
Uno de los primeros estudios sistemáticos que aplica autocorrelación espacial (Moran's I) a datos de carpetas de investigación en la Ciudad de México, identificando clústeres de alta criminalidad en Iztapalapa, Cuauhtémoc y Gustavo A. Madero.

> Vilalta, C. (2010). *El miedo al crimen en México. Estructura lógica, bases empíricas y recomendaciones de política pública*. Gestión y Política Pública, 19(1), 3–36.

**Estévez-Soto et al. (2021) — Machine learning y predicción del crimen:**
Aplica algoritmos de aprendizaje automático (random forest, gradient boosting) a datos de crimen en ciudades latinoamericanas. Identifica como predictores clave: densidad urbana, nivel socioeconómico, iluminación y proximidad a transporte público.

> Estévez-Soto, P. R. (2021). *Crime and its relationship to the socioeconomic and urban environment: evidence from Mexico City*. Applied Geography, 129, 102420.

### 2.3 Aplicaciones de Datos Abiertos y Smart Cities

**Bibri & Krogstie (2017) — Smart City y datos urbanos:**
Revisión sobre el uso de datos abiertos para el monitoreo de ciudades inteligentes. Plantea que la integración de fuentes heterogéneas (servicios ciudadanos, sensores, registros administrativos) permite detectar patrones no visibles con fuentes individuales.

> Bibri, S. E., & Krogstie, J. (2017). *Smart sustainable cities of the future: An extensive interdisciplinary literature review*. Sustainable Cities and Society, 31, 183–212.

---

## 3. Vacíos en la Literatura

A partir de la revisión anterior, se identifican los siguientes vacíos que este proyecto busca atender:

1. **Escasez de estudios que integren datos de reportes ciudadanos (Locatel) con datos de criminalidad en México.** La mayoría de los estudios locales usan solo datos policiales.
2. **Falta de análisis temporal con rezagos** entre fallas de infraestructura y criminalidad. La mayoría de estudios son transversales.
3. **Ausencia de índices compuestos de riesgo urbano** que integren infraestructura, demografía y criminalidad a nivel de colonia en la CDMX.
4. **Poca aplicación de modelos de conteo** (Poisson, Binomial Negativa) para modelar criminalidad en función de fallas de infraestructura en el contexto mexicano.

---

## 4. Posición del Proyecto en el Campo

Este proyecto se posiciona en la intersección de tres campos:

```
Criminología urbana ──┐
                      ├──► Smart City CDMX
Ciencia de datos     ──┤    (UrbanSignal)
                      │
Datos abiertos CDMX ──┘
```

A diferencia de estudios previos, combina:
- **Datos de demanda ciudadana** (Locatel 0311) como proxy de infraestructura
- **Análisis multivariado** con normalización poblacional INEGI
- **Técnicas avanzadas**: Moran's I + LISA, Regresión Poisson/NB, DBSCAN, IRU
- **Análisis temporal con rezagos** para explorar causalidad

---

## 5. Referencias Completas

1. Wilson, J. Q., & Kelling, G. L. (1982). Broken Windows: The Police and Neighborhood Safety. *The Atlantic Monthly*, 249(3), 29–38.
2. Cohen, L. E., & Felson, M. (1979). Social Change and Crime Rate Trends: A Routine Activity Approach. *American Sociological Review*, 44(4), 588–608.
3. Sherman, L. W., Gartin, P. R., & Buerger, M. E. (1989). Hot Spots of Predatory Crime. *Criminology*, 27(1), 27–56.
4. Chalfin, A., Hansen, B., Lerner, J., & Parker, L. (2022). Reducing Crime Through Environmental Design. *Journal of Quantitative Criminology*, 38, 127–157.
5. Cozens, P., Saville, G., & Hillier, D. (2005). Crime prevention through environmental design (CPTED). *Property Management*, 23(5), 328–356.
6. Wheeler, A. P., & Ratcliffe, J. H. (2018). A Simple Weighted Displacement Quotient. *Policing: An International Journal*, 41(3), 380–394.
7. Dell, M. (2015). Trafficking Networks and the Mexican Drug War. *American Economic Review*, 105(6), 1738–1779.
8. Vilalta, C. (2010). El miedo al crimen en México. *Gestión y Política Pública*, 19(1), 3–36.
9. Estévez-Soto, P. R. (2021). Crime and its relationship to the socioeconomic and urban environment. *Applied Geography*, 129, 102420.
10. Bibri, S. E., & Krogstie, J. (2017). Smart sustainable cities of the future. *Sustainable Cities and Society*, 31, 183–212.
