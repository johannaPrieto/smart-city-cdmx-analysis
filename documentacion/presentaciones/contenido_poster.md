# Contenido para Póster Científico — Programa DELFÍN 2026

A continuación se detalla la información exacta y estructurada que debes colocar en tu póster, cumpliendo estrictamente con las reglas de diseño (menos texto, más visual, paleta institucional, etc.).

---

## 1. Título
**Infraestructura, Desorden y Delito: Análisis Espacial e Inteligente de la Relación entre Fallas Urbanas y Crimen en la CDMX**

* **Estudiantes:** Johanna Prieto
* **Universidad de origen:** UPIITA
* **Laboratorio:** Laboratorio de Inteligencia Geo-Espacial y Cómputo Móvil, UPIITA – IPN
* **Investigador responsable:** Dr. Miguel Felix Mata Rivera

## 2. Problema de Investigación
La teoría de las "ventanas rotas" sugiere que el deterioro urbano propicia la delincuencia. Sin embargo, en la CDMX esta relación no se había cuantificado espacialmente utilizando datos ciudadanos abiertos, lo que limita la creación de estrategias preventivas conjuntas entre servicios urbanos y seguridad pública.

## 3. Objetivo
*Analyze the spatio-temporal relationship between reported urban infrastructure failures and crime incidence in Mexico City using geospatial artificial intelligence and open data.*

## 4. Datos Utilizados
*(Mostrar como tabla simple sin bordes pesados)*

| Dataset | Fuente | Registros |
| :--- | :--- | :--- |
| Carpetas de Investigación (2024) | FGJ CDMX | 129,580 |
| Víctimas (2024) | FGJ CDMX | 126,000 |
| Reportes Locatel 0311 | Gobierno CDMX | 57,000 |
| Censo de Población (2020) | INEGI | 16 Alcaldías |

## 5. Metodología
*(No uses texto. Usa flechas e íconos grandes)*
`[Ícono de Base de datos]` ETL (Limpieza y Fusión) ➔ `[Ícono de Lupa]` Análisis Exploratorio ➔ `[Ícono de Mapa]` Autocorrelación Espacial (Moran's I) ➔ `[Ícono de Red]` Clustering (DBSCAN) ➔ `[Ícono de Gráfica de barras]` Regresión Binomial Negativa e IRU.

## 6. Tecnologías Utilizadas
*(Solo coloca los logotipos oficiales)*
* Python
* Pandas & GeoPandas
* Plotly & Dash
* Scikit-Learn
* Folium

## 7. Resultados (Evidencia Visual recomendada)
*Deben ocupar el 50% de tu póster. Te sugiero usar estas 4 imágenes que ya generamos (las encuentras en `resultados/graficas/` y `resultados/mapas/`):*

1. **`dispersion_alumbrado_delitos.png`** 
   * *Pie de figura (Fig. 1):* Correlación lineal positiva entre reportes de falta de alumbrado y volumen de delitos nocturnos a nivel colonia.
2. **Captura de pantalla de `mapa_riesgo_coropletico.html`** *(toma un screenshot atractivo del mapa en dark mode)*
   * *Pie de figura (Fig. 2):* Índice de Riesgo Urbano (IRU) por Alcaldía, normalizado por población.
3. **`coeficientes_modelo.png`**
   * *Pie de figura (Fig. 3):* Coeficientes del modelo de Regresión Binomial Negativa (IRR); evidencia qué fallas aumentan más el riesgo delictivo.
4. **`perfil_victimas_zonas_criticas.png`**
   * *Pie de figura (Fig. 4):* Distribución demográfica de víctimas dentro de los *hotspots* detectados por DBSCAN.

## 8. Principales Hallazgos
* Se validó una correlación estadísticamente significativa entre fallas de alumbrado y delitos nocturnos.
* La Regresión Binomial Negativa comprobó la sobredispersión espacial del delito en zonas de alta falla estructural.
* Se identificaron *hotspots* críticos donde coexisten ambas problemáticas urbanas.
* Los datos abiertos ciudadanos sirvieron exitosamente como *proxy* temprano para la prevención criminal.

## 9. Conclusiones
* **¿Se cumplió el objetivo?:** Se cuantificó exitosamente la relación espacial usando IA y estadística.
* **Aporte:** El modelo evidencia que reparar la ciudad es una medida directa de seguridad pública.
* **Aplicación:** El Índice de Riesgo Urbano (IRU) funciona como herramienta para asignar presupuestos policiales y de servicios.
* **Trabajo Futuro:** Implementar series de tiempo (ARIMA/Prophet) para predecir fluctuaciones criminales a nivel colonia.

## 10. Productos Generados
*(Usa íconos grandes vectoriales)*
* `[Ícono Github]` Repositorio de Código Open Source
* `[Ícono Dashboard/Web]` Dashboard Interactivo (Dash)
* `[Ícono Mapa]` 6 Mapas interactivos (Folium)
* `[Ícono PDF]` Reporte Metodológico automatizado

## 11. Códigos QR
*(Genera dos QRs gratuitos en internet)*
1. **QR 1:** Hacia tu repositorio de GitHub (para ver el código).
2. **QR 2:** Hacia un pequeño video de 30 segundos (grabación de pantalla interactuando con tu Dashboard y los mapas) o directo a la URL de tu Dashboard si logras publicarlo.

## 12. Agradecimientos
*(Logotipos en la parte inferior o texto breve)*
Programa DELFÍN 2026 | Laboratorio de Inteligencia Geo-Espacial y Cómputo Móvil | UPIITA - IPN | [Nombre de tu universidad de origen]

## 13. Referencias
1. Wilson, J. Q., & Kelling, G. L. (1982). Broken Windows: The Police and Neighborhood Safety. *The Atlantic Monthly*.
2. Chalfin, A., et al. (2022). Reducing Crime Through Environmental Design: Evidence From Street Lighting. *J. Quant. Criminol*.
3. Vilalta, C. (2010). El miedo al crimen en México: Análisis espacial. *Gestión y Política Pública*.

---

### Recomendaciones adicionales de Diseño para ti:
* **Fondo:** Usa un fondo blanco o gris muy claro (#F5F5F5) para que las gráficas que generamos en *Dark Mode* resalten muchísimo.
* **Color de acento:** Usa el morado (`#7C5CFC`) o el turquesa (`#00D9A3`) que usamos en tus gráficas para los subtítulos del póster.
* **Espacio:** No tengas miedo de dejar espacios en blanco; ayuda a que el jurado lea más rápido.
