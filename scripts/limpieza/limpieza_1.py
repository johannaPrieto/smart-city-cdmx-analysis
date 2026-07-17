import os
import sys
import warnings
import pandas as pd

# Forzar salida UTF-8 en terminales Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Silenciar FutureWarning de downcasting en fillna
warnings.filterwarnings('ignore', category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

# =============================================================================
# 1. CARGA DEL DATASET
# =============================================================================
RUTA_RAW = r'D:\cdmx-analysis\datasets\raw\carpetasFGJ_2024.csv'
RUTA_LIMPIO = r'D:\cdmx-analysis\datasets\processed\carpetasFGJ_2024_limpio.csv'

print("Cargando dataset...")
df = pd.read_csv(RUTA_RAW, encoding='utf-8', on_bad_lines='skip')

print(f"\n{'='*55}")
print(f"  DIMENSIONES ORIGINALES: {df.shape[0]:,} filas × {df.shape[1]} columnas")
print(f"{'='*55}")

# =============================================================================
# 2. DIAGNÓSTICO INICIAL
# =============================================================================
print("\n===== VALORES NULOS POR COLUMNA (antes de limpieza) =====")
nulos = df.isnull().sum()
nulos_pct = (nulos / len(df) * 100).round(2)
diagnostico = pd.DataFrame({'nulos': nulos, 'porcentaje': nulos_pct})
print(diagnostico[diagnostico['nulos'] > 0].to_string())

# =============================================================================
# 3. UNIFICACIÓN DE FECHAS
#    Columnas: fecha_inicio, fecha_hecho  →  formato datetime (YYYY-MM-DD)
#    Columnas: hora_inicio, hora_hecho    →  formato time (HH:MM:SS)
# =============================================================================
print("\n===== PROCESANDO COLUMNAS DE FECHA Y HORA =====")

COLS_FECHA = ['fecha_inicio', 'fecha_hecho']
COLS_HORA  = ['hora_inicio', 'hora_hecho']

# Convertir columnas de fecha a datetime
for col in COLS_FECHA:
    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
    invalidas = df[col].isnull().sum()
    print(f"  [{col}] → datetime | fechas inválidas/NaT: {invalidas}")

# Convertir columnas de hora: primero a string limpio, luego extraer como time
for col in COLS_HORA:
    df[col] = pd.to_datetime(
        df[col].astype(str).str.strip(), format='%H:%M:%S', errors='coerce'
    ).dt.time
    invalidas = df[col].isnull().sum()
    print(f"  [{col}] → time     | horas inválidas/NaT:  {invalidas}")

# Columna combinada datetime completo (fecha + hora) – útil para análisis temporal
df['datetime_inicio'] = pd.to_datetime(
    df['fecha_inicio'].astype(str) + ' ' +
    df['hora_inicio'].astype(str).replace('None', pd.NA),
    errors='coerce'
)
df['datetime_hecho'] = pd.to_datetime(
    df['fecha_hecho'].astype(str) + ' ' +
    df['hora_hecho'].astype(str).replace('None', pd.NA),
    errors='coerce'
)

print("\n  ✓ Columnas 'datetime_inicio' y 'datetime_hecho' creadas (fecha + hora combinadas)")

# =============================================================================
# 4. MANEJO DE VALORES FALTANTES (NA)
# =============================================================================
print("\n===== ESTRATEGIA DE IMPUTACIÓN / MANEJO DE NAs =====")

# --- 4a. hora_inicio: NAs por datos corruptos (solo 12 casos, 0.01%) ---
hora_inicio_nulos = df['hora_inicio'].isnull().sum()
if hora_inicio_nulos > 0:
    med_min = df['_hora_min_inicio'] if '_hora_min_inicio' in df.columns else None
    # Calcular mediana global de hora_inicio en minutos
    horas_min = df['hora_inicio'].apply(
        lambda t: t.hour * 60 + t.minute if pd.notna(t) else pd.NA
    )
    med_global = int(horas_min.median())
    h_g, m_g = divmod(med_global, 60)
    import datetime
    hora_global = datetime.time(h_g, m_g, 0)
    df['hora_inicio'] = df['hora_inicio'].apply(
        lambda t: hora_global if pd.isna(t) else t
    )
    print(f"  hora_inicio: {hora_inicio_nulos} NAs imputados con mediana global ({hora_global})")

# --- 4b. Columnas temporales: filas con fecha_hecho o anio_hecho nulo ---
#     Son registros incompletos estructuralmente; se eliminan si hay muy pocos.
filas_sin_fecha_hecho = df['fecha_hecho'].isnull().sum()
print(f"\n  Filas sin fecha_hecho: {filas_sin_fecha_hecho} "
      f"({filas_sin_fecha_hecho/len(df)*100:.2f}%)")

if filas_sin_fecha_hecho < len(df) * 0.01:   # < 1% -> eliminar
    df = df[df['fecha_hecho'].notna()].copy()
    print("  -> Eliminadas (< 1% del total): se preserva integridad temporal")
else:
    print("  -> Conservadas (> 1%); marcar con bandera si es necesario")

# --- 4c. hora_hecho: NAs temporales -> imputar con mediana del mismo dia ---
#     Muchos analisis de tiempo necesitan la hora; imputamos con un valor
#     representativo del mismo dia para no perder filas geoespaciales.
hora_nulos = df['hora_hecho'].isnull().sum()
print(f"\n  Nulos en hora_hecho: {hora_nulos} ({hora_nulos/len(df)*100:.2f}%)")

if hora_nulos > 0:
    # Convertir a minutos para calcular mediana por fecha
    df['_hora_min'] = df['hora_hecho'].apply(
        lambda t: t.hour * 60 + t.minute if pd.notna(t) else pd.NA
    )
    mediana_diaria = df.groupby('fecha_hecho')['_hora_min'].transform('median')
    df['_hora_min'] = df['_hora_min'].fillna(mediana_diaria)

    # Fallback: mediana global si el día no tiene ningún valor
    mediana_global = df['_hora_min'].median()
    df['_hora_min'] = df['_hora_min'].fillna(mediana_global)

    def minutos_a_time(m):
        try:
            h, mi = divmod(int(m), 60)
            return pd.Timestamp(f"2000-01-01 {h:02d}:{mi:02d}:00").time()
        except Exception:
            return None

    df['hora_hecho'] = df.apply(
        lambda row: minutos_a_time(row['_hora_min'])
        if pd.isna(row['hora_hecho']) else row['hora_hecho'],
        axis=1
    )
    df.drop(columns=['_hora_min'], inplace=True)
    print(f"  → Imputados con mediana diaria (fallback: mediana global)")

# --- 4c. unidad_investigacion: texto → rellenar con 'SIN DATO' ---
df['unidad_investigacion'] = df['unidad_investigacion'].fillna('SIN DATO')
print(f"\n  unidad_investigacion NAs → rellenados con 'SIN DATO'")

# --- 4d. colonia_hecho / colonia_catalogo: texto geográfico ---
#     Rellenar con 'DESCONOCIDA' para conservar los registros geoespaciales
#     que sí tienen latitud/longitud.
df['colonia_hecho']    = df['colonia_hecho'].fillna('DESCONOCIDA')
df['colonia_catalogo'] = df['colonia_catalogo'].fillna('DESCONOCIDA')
print("  colonia_hecho / colonia_catalogo NAs → 'DESCONOCIDA'")

# --- 4e. alcaldia_hecho / alcaldia_catalogo / municipio_hecho ---
#     Intentar recuperar desde latitud/longitud no está en este script;
#     se rellena con 'DESCONOCIDA' para mantener consistencia.
df['alcaldia_hecho']    = df['alcaldia_hecho'].fillna('DESCONOCIDA')
df['alcaldia_catalogo'] = df['alcaldia_catalogo'].fillna('DESCONOCIDA')
df['municipio_hecho']   = df['municipio_hecho'].fillna('DESCONOCIDA')
print("  alcaldia_hecho / alcaldia_catalogo / municipio_hecho NAs → 'DESCONOCIDA'")

# --- 4f. latitud / longitud: coordenadas faltantes ---
#     NO se imputan (imputar coordenadas inventaría ubicaciones falsas).
#     Se crea una bandera booleana para identificar registros sin georef.
df['sin_georeferencia'] = df['latitud'].isnull()
coord_nulos = df['sin_georeferencia'].sum()
print(f"\n  latitud/longitud: {coord_nulos} registros sin coordenadas")
print("  → Se conservan con NaN; bandera 'sin_georeferencia' = True añadida")

# =============================================================================
# 5. RESUMEN FINAL
# =============================================================================
print(f"\n{'='*55}")
print("  DIMENSIONES FINALES:", df.shape)
print(f"{'='*55}")
print("\n===== VALORES NULOS RESTANTES =====")
nulos_final = df.isnull().sum()
print(nulos_final[nulos_final > 0].to_string()
      if nulos_final.any() else "  ✓ Sin valores nulos (excepto lat/lon intencionados)")

print("\n===== TIPOS DE DATOS FINALES =====")
print(df.dtypes)

# =============================================================================
# 6. GUARDAR DATASET LIMPIO
# =============================================================================
import os
os.makedirs(os.path.dirname(RUTA_LIMPIO), exist_ok=True)
df.to_csv(RUTA_LIMPIO, index=False, encoding='utf-8')
print(f"\n✓ Dataset limpio guardado en:\n  {RUTA_LIMPIO}")
