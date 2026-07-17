# Diccionario de Datos - Proyecto UrbanSignal CDMX

Este documento describe la estructura y las variables de los conjuntos de datos procesados (limpios) utilizados en los análisis y modelos del proyecto "UrbanSignal CDMX" (Programa DELFIN). Los datasets se encuentran en la carpeta `datasets/processed/`.

## 1. Carpetas de Investigación de la FGJ CDMX (2024)
**Archivo:** `carpetasFGJ_2024_limpio.csv`
**Descripción:** Contiene los registros a nivel carpeta de investigación sobre la incidencia delictiva reportada en la Ciudad de México durante el año 2024.

| Variable | Tipo de Dato | Descripción |
|----------|--------------|-------------|
| `anio_inicio` | Entero | Año en que se inició la carpeta de investigación. |
| `mes_inicio` | Texto | Mes en que se inició la carpeta de investigación. |
| `fecha_inicio` | Fecha (YYYY-MM-DD) | Fecha de inicio de la carpeta. |
| `hora_inicio` | Tiempo (HH:MM:SS) | Hora de inicio de la carpeta. |
| `anio_hecho` | Entero | Año en que ocurrió el presunto delito. |
| `mes_hecho` | Texto | Mes en que ocurrió el presunto delito. |
| `fecha_hecho` | Fecha (YYYY-MM-DD) | Fecha en que ocurrió el presunto delito. |
| `hora_hecho` | Tiempo (HH:MM:SS) | Hora en que ocurrió el presunto delito. |
| `delito` | Texto | Descripción específica del delito reportado. |
| `categoria_delito` | Texto | Clasificación general o impacto del delito (ej. Bajo Impacto, Alto Impacto). |
| `competencia` | Texto | Instancia judicial competente (ej. Fuero Común). |
| `fiscalia` | Texto | Fiscalía encargada de la investigación. |
| `agencia` | Texto | Agencia del Ministerio Público donde se abrió la carpeta. |
| `unidad_investigacion` | Texto | Unidad de investigación asignada. |
| `colonia_hecho` | Texto | Nombre de la colonia donde ocurrió el hecho (original). |
| `colonia_catalogo` | Texto | Nombre estandarizado de la colonia según el catálogo geográfico. |
| `alcaldia_hecho` | Texto | Nombre de la alcaldía donde ocurrió el hecho (original). |
| `alcaldia_catalogo` | Texto | Nombre estandarizado de la alcaldía. |
| `municipio_hecho` | Texto | Municipio (generalmente coincide con la alcaldía para la CDMX). |
| `latitud` | Flotante | Coordenada geográfica (latitud) del lugar de los hechos. |
| `longitud` | Flotante | Coordenada geográfica (longitud) del lugar de los hechos. |
| `datetime_inicio` | Fecha y Hora | Variable combinada de fecha y hora de inicio de carpeta. |
| `datetime_hecho` | Fecha y Hora | Variable combinada de fecha y hora del hecho. |
| `sin_georeferencia` | Booleano | Indica (`True`/`False`) si el registro carece de coordenadas geográficas válidas. |

---

## 2. Víctimas en Carpetas de Investigación de la FGJ CDMX (2024)
**Archivo:** `victimasFGJ_2024_limpio.csv`
**Descripción:** Registros desagregados a nivel víctima para los delitos reportados. Puede haber múltiples víctimas por carpeta de investigación.

| Variable | Tipo de Dato | Descripción |
|----------|--------------|-------------|
| `anio_inicio` | Entero | Año de inicio de la investigación. |
| `mes_inicio` | Texto | Mes de inicio de la investigación. |
| `fecha_inicio` | Fecha | Fecha de inicio de la investigación. |
| `hora_inicio` | Tiempo | Hora de inicio de la investigación. |
| `anio_hecho` | Entero | Año del hecho delictivo. |
| `mes_hecho` | Texto | Mes del hecho delictivo. |
| `fecha_hecho` | Fecha | Fecha del hecho delictivo. |
| `hora_hecho` | Tiempo | Hora del hecho delictivo. |
| `delito` | Texto | Delito específico cometido contra la víctima. |
| `categoria_delito` | Texto | Categoría de impacto del delito. |
| `sexo` | Texto | Sexo de la víctima (Femenino, Masculino, etc.). |
| `edad` | Entero / Flotante | Edad de la víctima reportada en años. |
| `tipo_persona` | Texto | Indica si es Persona Física o Persona Moral. |
| `calidad_juridica` | Texto | Estatus o calidad jurídica (ej. Víctima, Ofendido). |
| `competencia` | Texto | Fuero del delito. |
| `colonia_hecho` | Texto | Colonia original del hecho. |
| `colonia_catalogo` | Texto | Colonia estandarizada (catálogo). |
| `alcaldia_hecho` | Texto | Alcaldía original del hecho. |
| `alcaldia_catalogo` | Texto | Alcaldía estandarizada (catálogo). |
| `municipio_hecho` | Texto | Municipio del hecho. |
| `latitud` | Flotante | Latitud del hecho. |
| `longitud` | Flotante | Longitud del hecho. |
| `datetime_inicio` | Fecha y Hora | Fecha y hora combinadas (inicio). |
| `datetime_hecho` | Fecha y Hora | Fecha y hora combinadas (hecho). |
| `edad_disponible` | Booleano | Indica si el dato de la edad es válido y se proporcionó. |
| `sin_georeferencia` | Booleano | Indica si faltan las coordenadas del hecho. |

---

## 3. Reportes del Sistema Universitario Locatel y SUAC (2024)
**Archivo:** `locatel0311-2024_limpio.csv`
**Descripción:** Incidentes, solicitudes de servicio y reportes de fallas en infraestructura urbana (ej. alumbrado, baches, fugas) registrados en el Sistema Único de Atención Ciudadana (SUAC).

| Variable | Tipo de Dato | Descripción |
|----------|--------------|-------------|
| `id_folio` | Texto | Identificador único del reporte ciudadano. |
| `fecha_solicitud` | Fecha | Fecha en que se realizó el reporte/solicitud. |
| `hora_solicitud` | Tiempo | Hora exacta en que se ingresó la solicitud. |
| `tipo_de_entrada` | Texto | Medio por el cual se recibió el reporte (App, Teléfono, Web, etc.). |
| `tema_solicitud` | Texto | Clasificación del problema reportado (ej. Luminaria apagada, Fuga de agua). |
| `sexo` | Texto | Sexo de la persona que reporta. |
| `edad` | Entero / Flotante | Edad de la persona que reporta. |
| `colonia_solicitud` | Texto | Colonia donde ocurre el problema reportado. |
| `alcaldia_solicitud` | Texto | Alcaldía donde ocurre el problema reportado. |
| `codigo_postal_solicitud`| Texto/Entero | Código postal de la ubicación del problema. |
| `estatus` | Texto | Estado del reporte (ej. Concluido, Abierto, En proceso). |
| `fecha_concluido` | Fecha | Fecha en que el servicio o reporte fue cerrado o resuelto. |
| `alcaldia_catalogo` | Texto | Alcaldía estandarizada. |
| `colonia_catalogo` | Texto | Colonia estandarizada acorde al catálogo geográfico. |
| `longitud` | Flotante | Longitud geográfica del reporte. |
| `latitud` | Flotante | Latitud geográfica del reporte. |
| `datetime_solicitud` | Fecha y Hora | Fecha y hora exactas de la solicitud en formato integrado. |
| `solicitud_abierta` | Booleano | Indica si la solicitud aún no ha sido concluida. |
| `sin_georeferencia` | Booleano | Indica si el reporte carece de coordenadas de ubicación. |
| `edad_disponible` | Booleano | Indica si se proporcionó una edad válida para el solicitante. |
