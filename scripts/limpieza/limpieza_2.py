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
RUTA_RAW   = r'D:\cdmx-analysis\datasets\raw\locatel0311-2024 (4).csv'
RUTA_LIMPIO = r'D:\cdmx-analysis\datasets\processed\locatel0311-2024_limpio.csv'

print("Cargando dataset...")

# IMPORTANTE: keep_default_na=False para evitar que Pandas interprete el
# string literal "NA" del CSV como NaN automáticamente. Lo convertiremos
# de forma explícita y controlada columna por columna.
df = pd.read_csv(
    RUTA_RAW,
    encoding='utf-8',
    on_bad_lines='skip',
    keep_default_na=False,
    na_values=[''],          # solo cadena vacía → NaN en esta etapa
    dtype=str                # todo como texto primero; tipamos después
)

print(f"\n{'='*55}")
print(f"  DIMENSIONES ORIGINALES: {df.shape[0]:,} filas x {df.shape[1]} columnas")
print(f"{'='*55}")
print(f"\nColumnas: {list(df.columns)}")

# =============================================================================
# 2. DIAGNÓSTICO INICIAL
#    El dataset usa el string "NA" como valor faltante, NO NaN de Python.
#    Primero contamos cuántos "NA" literales hay por columna.
# =============================================================================
print("\n===== DIAGNÓSTICO: NA LITERALES POR COLUMNA (antes de limpieza) =====")
for col in df.columns:
    n_na     = (df[col].astype(str).str.strip() == 'NA').sum()
    n_empty  = df[col].isnull().sum()
    total_faltantes = n_na + n_empty
    if total_faltantes > 0:
        pct = total_faltantes / len(df) * 100
        print(f"  {col:<35} {total_faltantes:>7,}  ({pct:5.2f}%)"
              f"  [NA literal: {n_na:,} | vacíos: {n_empty:,}]")

# =============================================================================
# 3. NORMALIZAR "NA" LITERALES → NaN REAL DE PANDAS
#    Columnas afectadas: todas excepto id_folio (es entero único).
#    También limpiamos espacios residuales en strings.
# =============================================================================
print("\n===== NORMALIZANDO NA LITERALES → NaN =====")

COLS_TEXTO = [
    'tipo_de_entrada', 'tema_solicitud', 'sexo',
    'colonia_solicitud', 'alcaldia_solicitud',
    'codigo_postal_solicitud', 'estatus',
    'fecha_concluido', 'alcaldia_catalogo', 'colonia_catalogo',
    'edad', 'longitud', 'latitud'
]

for col in COLS_TEXTO:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace('NA', pd.NA)

print("  OK - 'NA' string convertidos a NaN en todas las columnas relevantes")

# =============================================================================
# 4. UNIFICACIÓN DE FECHAS Y HORAS
#    fecha_solicitud  → datetime64 (YYYY-MM-DD)
#    fecha_concluido  → datetime64 (YYYY-MM-DD)  [tiene NaN legítimos]
#    hora_solicitud   → time (HH:MM:SS)
# =============================================================================
print("\n===== PROCESANDO COLUMNAS DE FECHA Y HORA =====")

# --- 4a. Fechas ---
COLS_FECHA = ['fecha_solicitud', 'fecha_concluido']
for col in COLS_FECHA:
    antes = df[col].isnull().sum()
    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
    despues = df[col].isnull().sum()
    nuevos_nat = despues - antes
    print(f"  [{col}] -> datetime64 | NaT previos: {antes:,} | "
          f"nuevos NaT por formato incorrecto: {nuevos_nat:,}")

# --- 4b. Hora solicitud ---
df['hora_solicitud'] = pd.to_datetime(
    df['hora_solicitud'].astype(str).str.strip(),
    format='%H:%M:%S', errors='coerce'
).dt.time
hora_nat = df['hora_solicitud'].isnull().sum()
print(f"  [hora_solicitud] -> time | NaT: {hora_nat:,}")

# --- 4c. Columna datetime completo (útil para análisis temporal) ---
df['datetime_solicitud'] = pd.to_datetime(
    df['fecha_solicitud'].astype(str) + ' ' +
    df['hora_solicitud'].astype(str).replace('None', pd.NA),
    errors='coerce'
)
print("  [datetime_solicitud] creada (fecha + hora combinadas)")

# =============================================================================
# 5. TIPADO DE COLUMNAS NUMÉRICAS
# =============================================================================
print("\n===== TIPANDO COLUMNAS NUMÉRICAS =====")

# --- 5a. id_folio: entero ---
df['id_folio'] = pd.to_numeric(df['id_folio'], errors='coerce').astype('Int64')
print("  [id_folio] -> Int64")

# --- 5b. edad: numérica; alto % de NAs (90%) → conservar como Int64 nullable ---
df['edad'] = pd.to_numeric(df['edad'], errors='coerce').astype('Int64')
edad_na = df['edad'].isnull().sum()
print(f"  [edad] -> Int64 | NaN: {edad_na:,} ({edad_na/len(df)*100:.1f}%)")

# --- 5c. longitud / latitud: float ---
df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
df['latitud']  = pd.to_numeric(df['latitud'],  errors='coerce')
lon_na = df['longitud'].isnull().sum()
print(f"  [longitud/latitud] -> float64 | NaN: {lon_na:,} ({lon_na/len(df)*100:.1f}%)")

# --- 5d. codigo_postal: limpiar valores especiales (-1, 00000) ---
df['codigo_postal_solicitud'] = pd.to_numeric(
    df['codigo_postal_solicitud'], errors='coerce'
)
# -1 y 0 son códigos centinela (sin dato real) → reemplazar por NaN
df.loc[df['codigo_postal_solicitud'] <= 0, 'codigo_postal_solicitud'] = pd.NA
df['codigo_postal_solicitud'] = df['codigo_postal_solicitud'].astype('Int64')
cp_na = df['codigo_postal_solicitud'].isnull().sum()
print(f"  [codigo_postal_solicitud] -> Int64 | NaN (incl. -1 y 0): {cp_na:,} "
      f"({cp_na/len(df)*100:.1f}%)")

# =============================================================================
# 6. MANEJO DE VALORES FALTANTES (NA) POR COLUMNA
# =============================================================================
print("\n===== ESTRATEGIA DE IMPUTACIÓN / MANEJO DE NAs =====")

# --- 6a. sexo: 2.69% NaN → 'NO ESPECIFICADO' (categoría ya existente en datos) ---
df['sexo'] = df['sexo'].fillna('NO ESPECIFICADO')
print("  [sexo] NaN -> 'NO ESPECIFICADO'")

# --- 6b. colonia_solicitud / alcaldia_solicitud: 40% NaN ---
#     NO imputar con inventos; rellenar con 'DESCONOCIDA' para mantener filas.
df['colonia_solicitud']   = df['colonia_solicitud'].fillna('DESCONOCIDA')
df['alcaldia_solicitud']  = df['alcaldia_solicitud'].fillna('DESCONOCIDA')
print("  [colonia_solicitud / alcaldia_solicitud] NaN -> 'DESCONOCIDA'")

# --- 6c. colonia_catalogo / alcaldia_catalogo: 65-66% NaN ---
#     Intentar recuperar desde colonia_solicitud / alcaldia_solicitud
#     cuando el campo estandarizado existe; si no, 'DESCONOCIDA'.
mask_alc = df['alcaldia_catalogo'].isnull() & (df['alcaldia_solicitud'] != 'DESCONOCIDA')
df.loc[mask_alc, 'alcaldia_catalogo'] = df.loc[mask_alc, 'alcaldia_solicitud'].str.title()
df['alcaldia_catalogo'] = df['alcaldia_catalogo'].fillna('DESCONOCIDA')

mask_col = df['colonia_catalogo'].isnull() & (df['colonia_solicitud'] != 'DESCONOCIDA')
df.loc[mask_col, 'colonia_catalogo'] = df.loc[mask_col, 'colonia_solicitud'].str.title()
df['colonia_catalogo'] = df['colonia_catalogo'].fillna('DESCONOCIDA')
print("  [alcaldia_catalogo] NaN -> recuperado desde alcaldia_solicitud o 'DESCONOCIDA'")
print("  [colonia_catalogo]  NaN -> recuperado desde colonia_solicitud  o 'DESCONOCIDA'")

# --- 6d. fecha_concluido: 28.86% NaN ---
#     Es válido que solicitudes aún abiertas no tengan fecha de cierre.
#     Se crea una bandera para identificarlas fácilmente.
df['solicitud_abierta'] = df['fecha_concluido'].isnull()
abiertos = df['solicitud_abierta'].sum()
print(f"  [fecha_concluido] NaN conservados | bandera 'solicitud_abierta' creada "
      f"({abiertos:,} registros abiertos)")

# --- 6e. longitud / latitud: 62-66% NaN → NO imputar coordenadas ---
#     Se crea bandera booleana para identificar registros sin georeferencia.
df['sin_georeferencia'] = df['latitud'].isnull()
sin_geo = df['sin_georeferencia'].sum()
print(f"  [longitud/latitud] NaN conservados | bandera 'sin_georeferencia' = True "
      f"({sin_geo:,} registros, {sin_geo/len(df)*100:.1f}%)")

# --- 6f. edad: 90.24% NaN → demasiado alta para imputar de forma confiable ---
#     Se conserva como NaN con bandera. Si se necesita para análisis,
#     usar solo el subconjunto con edad disponible.
df['edad_disponible'] = df['edad'].notna()
con_edad = df['edad_disponible'].sum()
print(f"  [edad] NaN conservados | bandera 'edad_disponible' = True "
      f"({con_edad:,} registros con edad, {con_edad/len(df)*100:.1f}%)")

# --- 6g. codigo_postal_solicitud: 2.75% + valores -1/0 → NaN ya corregidos ---
cp_na_final = df['codigo_postal_solicitud'].isnull().sum()
print(f"  [codigo_postal_solicitud] NaN finales: {cp_na_final:,} "
      f"({cp_na_final/len(df)*100:.1f}%)")

# =============================================================================
# 7. NORMALIZACIÓN DE TEXTO EN COLUMNAS CATEGÓRICAS
#    - Eliminar caracteres problemáticos (p.ej. "A?O" → "AÑO")
#    - Strip de espacios extra
# =============================================================================
print("\n===== NORMALIZANDO TEXTO EN COLUMNAS CATEGÓRICAS =====")

COLS_CAT = ['colonia_solicitud', 'alcaldia_solicitud',
            'colonia_catalogo', 'alcaldia_catalogo',
            'tema_solicitud', 'tipo_de_entrada']

for col in COLS_CAT:
    if col in df.columns:
        df[col] = (df[col]
                   .astype(str)
                   .str.strip()
                   .str.upper()
                   .str.replace(r'\s+', ' ', regex=True))   # espacios múltiples

print(f"  Columnas normalizadas: {COLS_CAT}")

# =============================================================================
# 8. RESUMEN FINAL
# =============================================================================
print(f"\n{'='*55}")
print(f"  DIMENSIONES FINALES: {df.shape[0]:,} filas x {df.shape[1]} columnas")
print(f"{'='*55}")

print("\n===== VALORES NULOS RESTANTES =====")
nulos_final = df.isnull().sum()
cols_con_nulos = nulos_final[nulos_final > 0]
if len(cols_con_nulos) > 0:
    for col, n in cols_con_nulos.items():
        print(f"  {col:<35} {n:>8,}  ({n/len(df)*100:.1f}%)")
else:
    print("  Sin valores nulos (excepto coordenadas y edad, intencionales)")

print("\n===== TIPOS DE DATOS FINALES =====")
print(df.dtypes.to_string())

# =============================================================================
# 9. GUARDAR DATASET LIMPIO
# =============================================================================
os.makedirs(os.path.dirname(RUTA_LIMPIO), exist_ok=True)
df.to_csv(RUTA_LIMPIO, index=False, encoding='utf-8')
print(f"\nDataset limpio guardado en:\n  {RUTA_LIMPIO}")