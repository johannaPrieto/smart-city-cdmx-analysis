# Inventario de Fuentes de Información
## Proyecto UrbanSignal CDMX · Semana 2

**Fecha de elaboración:** Junio–Julio 2026

---

## Datasets Principales

| # | Dataset | Fuente | URL / Portal | Fecha descarga | Periodo cobertura | Formato | Tamaño raw | Variables clave | Calidad |
|---|---------|--------|-------------|----------------|-------------------|---------|------------|-----------------|---------|
| 1 | Carpetas de investigación FGJ 2024 | Fiscalía General de Justicia CDMX | datos.cdmx.gob.mx | Jun 2026 | Ene–Dic 2024 | CSV | ~39 MB | latitud, longitud, alcaldia_catalogo, colonia_catalogo, delito, categoria_delito, fecha_hecho, hora_hecho | Alta — datos oficiales, ~99% completos en fecha |
| 2 | Víctimas FGJ 2024 | Fiscalía General de Justicia CDMX | datos.cdmx.gob.mx | Jun 2026 | Ene–Dic 2024 | CSV | ~36 MB | sexo, edad, delito, alcaldia_catalogo, fecha_hecho | Alta — 85% con datos demográficos completos |
| 3 | Locatel 0311 2024 | Gobierno CDMX (CEAL) | datos.cdmx.gob.mx | Jun 2026 | Mar–Nov 2024 | CSV | ~16 MB | latitud, longitud, alcaldia_catalogo, colonia_catalogo, tema_solicitud, hora_solicitud, datetime_solicitud | Media — ~20% sin coordenadas |
| 4 | Catálogo de Colonias CDMX | SEDATU / Portal CDMX | datos.cdmx.gob.mx | Jun 2026 | 2023 | JSON/GeoJSON | ~10 MB raw / 22 MB procesado | geometry (polígonos), cve_col, nom_col, nom_mun | Alta |
| 5 | Población INEGI Censo 2020 | INEGI | inegi.org.mx | Integrado en código | Censo 2020 | Integrado (dict) | — | poblacion_2020 por alcaldía | Alta — fuente oficial |

---

## Variables Identificadas como Relevantes

### Dataset Locatel (Fallas de Infraestructura)

| Variable | Tipo | Descripción | Relevancia |
|----------|------|-------------|------------|
| `tema_solicitud` | Categórica | Tipo de falla (ALUMBRADO, AGUA, VIALIDAD…) | **Alta** — predictor principal |
| `alcaldia_catalogo` | Categórica | Alcaldía del reporte normalizada | Alta |
| `colonia_catalogo` | Categórica | Colonia del reporte | Alta |
| `latitud` / `longitud` | Numérica | Coordenadas geográficas | Alta |
| `datetime_solicitud` | Temporal | Fecha y hora del reporte | Alta |
| `hora_solicitud` | Temporal | Hora del reporte | Media |

### Dataset Carpetas FGJ (Criminalidad)

| Variable | Tipo | Descripción | Relevancia |
|----------|------|-------------|------------|
| `delito` | Categórica | Tipo de delito específico | **Alta** |
| `categoria_delito` | Categórica | Categoría del delito | Alta |
| `alcaldia_catalogo` | Categórica | Alcaldía del evento | Alta |
| `colonia_catalogo` | Categórica | Colonia del evento | Alta |
| `latitud` / `longitud` | Numérica | Coordenadas geográficas | Alta |
| `fecha_hecho` / `hora_hecho` | Temporal | Fecha y hora del delito | Alta |
| `datetime_hecho` | Temporal | Combinación fecha+hora | Alta |

### Dataset Víctimas FGJ

| Variable | Tipo | Descripción | Relevancia |
|----------|------|-------------|------------|
| `sexo` | Categórica | Sexo de la víctima | Media |
| `edad` | Numérica | Edad de la víctima | Media |
| `delito` | Categórica | Delito sufrido | Alta |
| `alcaldia_catalogo` | Categórica | Alcaldía del evento | Alta |

---

## Cobertura Espacial, Temporal y Calidad

| Dataset | Cobertura espacial | Cobertura temporal | Registros raw | Registros limpios | Nulos relevantes |
|---------|-------------------|-------------------|---------------|-------------------|-----------------|
| FGJ Carpetas | 16 alcaldías CDMX | Ene–Dic 2024 (12 meses) | ~129,601 | ~129,580 | lat/lon: ~10% |
| FGJ Víctimas | 16 alcaldías CDMX | Ene–Dic 2024 (12 meses) | ~126,xxx | ~126,xxx | edad: ~15% |
| Locatel | 16 alcaldías CDMX | Mar–Nov 2024 (9 meses) | ~57,xxx | ~57,xxx | lat/lon: ~20% |
| Colonias GeoJSON | 1,812 colonias CDMX | Estático 2023 | 1,812 polígonos | 1,812 | — |

---

## Fuentes Consultadas pero No Integradas

| Fuente | Razón de no integración |
|--------|------------------------|
| DENUE INEGI | Disponible pero no procesado en el periodo de trabajo |
| IECM (datos electorales) | No relevante para el objetivo del proyecto |
| Barómetro de Percepción de Inseguridad CDMX | Sin datos abiertos para 2024 en el momento de la descarga |
| Datos meteorológicos | Fuera del alcance del proyecto en esta etapa |
