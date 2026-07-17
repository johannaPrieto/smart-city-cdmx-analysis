import os
import sys
import warnings
import datetime
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
RUTA_RAW   = r'D:\cdmx-analysis\datasets\raw\victimasFGJ_2024.csv'
RUTA_LIMPIO = r'D:\cdmx-analysis\datasets\processed\victimasFGJ_2024_limpio.csv'

print("Cargando dataset...")

# keep_default_na=False para evitar que Pandas interprete strings vacíos
# de forma ambigua; dtype=str permite un diagnóstico previo seguro.
df = pd.read_csv(
    RUTA_RAW,
    encoding='utf-8',
    on_bad_lines='skip',
    keep_default_na=False,
    na_values=[''],          # solo cadena vacía → NaN en esta etapa
    dtype=str                # todo como texto; tipamos después
)

print(f"\n{'='*60}")
print(f"  DIMENSIONES ORIGINALES: {df.shape[0]:,} filas × {df.shape[1]} columnas")
print(f"{'='*60}")
print(f"\nColumnas detectadas: {list(df.columns)}")

# =============================================================================
# 2. DIAGNÓSTICO INICIAL
#    El dataset puede contener el string literal "NA" como valor faltante.
#    Contamos ambos: NaN de Pandas y el string "NA".
# =============================================================================
print("\n===== DIAGNÓSTICO: VALORES FALTANTES POR COLUMNA (antes de limpieza) =====")
for col in df.columns:
    n_na_str = (df[col].astype(str).str.strip() == 'NA').sum()
    n_nan    = df[col].isnull().sum()
    total    = n_na_str + n_nan
    if total > 0:
        pct = total / len(df) * 100
        print(f"  {col:<35} {total:>8,}  ({pct:5.2f}%)"
              f"  [NA literal: {n_na_str:,} | vacíos/NaN: {n_nan:,}]")

# =============================================================================
# 3. NORMALIZAR STRINGS "NA" LITERALES → NaN REAL DE PANDAS
# =============================================================================
print("\n===== NORMALIZANDO 'NA' LITERALES → NaN =====")

COLS_TEXTO = [
    'delito', 'categoria_delito', 'sexo', 'tipo_persona',
    'calidad_juridica', 'competencia',
    'colonia_hecho', 'colonia_catalogo',
    'alcaldia_hecho', 'alcaldia_catalogo',
    'municipio_hecho', 'latitud', 'longitud',
    'edad', 'mes_inicio', 'mes_hecho'
]

for col in COLS_TEXTO:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace('NA', pd.NA)

print("  OK – 'NA' string convertidos a NaN en todas las columnas relevantes")

# =============================================================================
# 4. ESTANDARIZACIÓN DE FECHAS Y HORAS
#    Columnas de fecha : fecha_inicio, fecha_hecho  → datetime64 (YYYY-MM-DD)
#    Columnas de hora  : hora_inicio,  hora_hecho   → time       (HH:MM:SS)
#    Columnas de año   : anio_inicio,  anio_hecho   → Int64
#    Columna combinada : datetime_inicio, datetime_hecho (fecha + hora)
# =============================================================================
print("\n===== ESTANDARIZACIÓN DE FECHAS Y HORAS =====")

# --- 4a. Columnas de fecha → datetime64 ---
COLS_FECHA = ['fecha_inicio', 'fecha_hecho']
for col in COLS_FECHA:
    antes  = df[col].isnull().sum()
    # Intentamos primero el formato más común del dataset
    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
    despues = df[col].isnull().sum()
    nuevos_nat = despues - antes
    print(f"  [{col}] → datetime64  | NaT previos: {antes:,} "
          f"| nuevos NaT por formato incorrecto: {nuevos_nat:,}")

# --- 4b. Columnas de hora → time (HH:MM:SS) ---
COLS_HORA = ['hora_inicio', 'hora_hecho']
for col in COLS_HORA:
    antes  = df[col].isnull().sum()
    df[col] = pd.to_datetime(
        df[col].astype(str).str.strip(),
        format='%H:%M:%S', errors='coerce'
    ).dt.time
    despues    = df[col].isnull().sum()
    nuevos_nat = despues - antes
    print(f"  [{col}] → time        | NaT previos: {antes:,} "
          f"| nuevos NaT por formato incorrecto: {nuevos_nat:,}")

# --- 4c. Columnas de año → entero nullable ---
COLS_ANIO = ['anio_inicio', 'anio_hecho']
for col in COLS_ANIO:
    df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    print(f"  [{col}] → Int64")

# --- 4d. Columnas combinadas datetime completo (fecha + hora) ---
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
# 5. TIPADO DE COLUMNAS NUMÉRICAS
# =============================================================================
print("\n===== TIPANDO COLUMNAS NUMÉRICAS =====")

# edad: numérica; puede tener NaN → usar Int64 nullable
df['edad'] = pd.to_numeric(df['edad'], errors='coerce').astype('Int64')
edad_na = df['edad'].isnull().sum()
print(f"  [edad] → Int64 | NaN: {edad_na:,} ({edad_na/len(df)*100:.1f}%)")

# latitud / longitud → float64
df['latitud']  = pd.to_numeric(df['latitud'],  errors='coerce')
df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
lat_na = df['latitud'].isnull().sum()
print(f"  [latitud/longitud] → float64 | NaN: {lat_na:,} ({lat_na/len(df)*100:.1f}%)")

# =============================================================================
# 6. MANEJO DE VALORES FALTANTES (NA) POR COLUMNA
# =============================================================================
print("\n===== ESTRATEGIA DE IMPUTACIÓN / MANEJO DE NAs =====")

# --- 6a. hora_inicio: NAs por datos corruptos ---
#     Imputamos con la mediana global de hora (en minutos desde medianoche)
#     para no perder registros que sí tienen fecha y datos categóricos válidos.
hora_inicio_nulos = df['hora_inicio'].isnull().sum()
print(f"\n  [hora_inicio] NaN: {hora_inicio_nulos:,} ({hora_inicio_nulos/len(df)*100:.2f}%)")
if hora_inicio_nulos > 0:
    horas_min = df['hora_inicio'].apply(
        lambda t: t.hour * 60 + t.minute if pd.notna(t) else pd.NA
    )
    med_global = int(horas_min.median())
    h_g, m_g   = divmod(med_global, 60)
    hora_global = datetime.time(h_g, m_g, 0)
    df['hora_inicio'] = df['hora_inicio'].apply(
        lambda t: hora_global if pd.isna(t) else t
    )
    print(f"  → Imputados con mediana global ({hora_global})")
else:
    print("  → Sin NaN. No requiere imputación.")

# --- 6b. fecha_hecho: filas con fecha_hecho nula = registros incompletos ---
#     Si representan < 1% del total, se eliminan para preservar
#     la integridad temporal de los análisis.
filas_sin_fecha = df['fecha_hecho'].isnull().sum()
print(f"\n  [fecha_hecho] NaN: {filas_sin_fecha:,} "
      f"({filas_sin_fecha/len(df)*100:.2f}%)")
if filas_sin_fecha < len(df) * 0.01:
    df = df[df['fecha_hecho'].notna()].copy()
    print("  → Eliminadas (< 1% del total): se preserva integridad temporal")
else:
    print("  → Conservadas (> 1%); se crea bandera 'sin_fecha_hecho'")
    df['sin_fecha_hecho'] = df['fecha_hecho'].isnull()

# --- 6c. hora_hecho: imputar con mediana diaria → fallback mediana global ---
hora_hecho_nulos = df['hora_hecho'].isnull().sum()
print(f"\n  [hora_hecho] NaN: {hora_hecho_nulos:,} ({hora_hecho_nulos/len(df)*100:.2f}%)")
if hora_hecho_nulos > 0:
    df['_hora_min'] = df['hora_hecho'].apply(
        lambda t: t.hour * 60 + t.minute if pd.notna(t) else pd.NA
    )
    mediana_diaria = df.groupby('fecha_hecho')['_hora_min'].transform('median')
    df['_hora_min'] = df['_hora_min'].fillna(mediana_diaria)

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
    print("  → Imputados con mediana diaria (fallback: mediana global)")
else:
    print("  → Sin NaN. No requiere imputación.")

# --- 6d. sexo: categoría de texto ---
#     Rellenar con 'NO ESPECIFICADO' para conservar los registros.
df['sexo'] = df['sexo'].fillna('NO ESPECIFICADO')
print(f"\n  [sexo] NaN → 'NO ESPECIFICADO'")

# --- 6e. edad: alto porcentaje de NaN → conservar como NaN ---
#     Se crea una bandera booleana para identificar registros con/sin edad.
edad_na = df['edad'].isnull().sum()
df['edad_disponible'] = df['edad'].notna()
print(f"\n  [edad] NaN: {edad_na:,} ({edad_na/len(df)*100:.1f}%) → conservados"
      f" | bandera 'edad_disponible' creada")

# --- 6f. tipo_persona / calidad_juridica / competencia: texto categórico ---
for col in ['tipo_persona', 'calidad_juridica', 'competencia']:
    nulos = df[col].isnull().sum()
    df[col] = df[col].fillna('SIN DATO')
    print(f"\n  [{col}] NaN: {nulos:,} → 'SIN DATO'")

# --- 6g. colonia_hecho / colonia_catalogo / alcaldia_hecho /
#          alcaldia_catalogo / municipio_hecho: texto geográfico ---
#     Intentar recuperar alcaldia/colonia_catalogo desde su contraparte
#     de solicitud cuando esté disponible; si no → 'DESCONOCIDA'.
COLS_GEO_PARES = [
    ('alcaldia_catalogo', 'alcaldia_hecho'),
    ('colonia_catalogo',  'colonia_hecho'),
]
for col_cat, col_hecho in COLS_GEO_PARES:
    mask = df[col_cat].isnull() & (df[col_hecho] != 'DESCONOCIDA') & df[col_hecho].notna()
    df.loc[mask, col_cat] = df.loc[mask, col_hecho].str.title()
    df[col_cat]  = df[col_cat].fillna('DESCONOCIDA')
    n = df[col_cat].isnull().sum()
    print(f"\n  [{col_cat}] NaN → recuperado de '{col_hecho}' o 'DESCONOCIDA'"
          f" | NaN residuales: {n:,}")

for col in ['colonia_hecho', 'alcaldia_hecho', 'municipio_hecho']:
    nulos = df[col].isnull().sum()
    df[col] = df[col].fillna('DESCONOCIDA')
    print(f"\n  [{col}] NaN: {nulos:,} → 'DESCONOCIDA'")

# --- 6h. latitud / longitud: NO imputar coordenadas inventadas ---
#     Se crea bandera booleana 'sin_georeferencia'.
df['sin_georeferencia'] = df['latitud'].isnull()
sin_geo = df['sin_georeferencia'].sum()
print(f"\n  [latitud/longitud] NaN conservados ({sin_geo:,} registros)"
      " | bandera 'sin_georeferencia' creada")

# =============================================================================
# 7. NORMALIZACIÓN DE TEXTO EN COLUMNAS CATEGÓRICAS
#    - Strip de espacios extra
#    - Mayúsculas consistentes
#    - Colapsar espacios múltiples
# =============================================================================
print("\n===== NORMALIZANDO TEXTO EN COLUMNAS CATEGÓRICAS =====")

COLS_CAT = [
    'delito', 'categoria_delito', 'sexo', 'tipo_persona',
    'calidad_juridica', 'competencia',
    'colonia_hecho', 'colonia_catalogo',
    'alcaldia_hecho', 'alcaldia_catalogo',
    'municipio_hecho', 'mes_inicio', 'mes_hecho'
]

for col in COLS_CAT:
    if col in df.columns:
        df[col] = (df[col]
                   .astype(str)
                   .str.strip()
                   .str.upper()
                   .str.replace(r'\s+', ' ', regex=True))
        # Revertir el string 'NAN' que astype(str) genera para NaN reales
        df[col] = df[col].replace('NAN', pd.NA)

print(f"  Columnas normalizadas (strip + upper + collapse spaces): {COLS_CAT}")

# =============================================================================
# 8. RESUMEN FINAL
# =============================================================================
print(f"\n{'='*60}")
print(f"  DIMENSIONES FINALES: {df.shape[0]:,} filas × {df.shape[1]} columnas")
print(f"{'='*60}")

print("\n===== VALORES NULOS RESTANTES =====")
nulos_final     = df.isnull().sum()
cols_con_nulos  = nulos_final[nulos_final > 0]
if len(cols_con_nulos) > 0:
    for col, n in cols_con_nulos.items():
        print(f"  {col:<35} {n:>8,}  ({n/len(df)*100:.1f}%)")
else:
    print("  ✓ Sin valores nulos (excepto lat/lon y edad, intencionales)")

print("\n===== TIPOS DE DATOS FINALES =====")
print(df.dtypes.to_string())

# =============================================================================
# 9. GUARDAR DATASET LIMPIO
# =============================================================================
os.makedirs(os.path.dirname(RUTA_LIMPIO), exist_ok=True)
df.to_csv(RUTA_LIMPIO, index=False, encoding='utf-8')
print(f"\n✓ Dataset limpio guardado en:\n  {RUTA_LIMPIO}")
