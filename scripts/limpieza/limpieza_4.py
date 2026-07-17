import os
import sys
import json
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
#    Fuente: GeoJSON con 1,543 colonias de CDMX.
#    Estructura: { "type": "FeatureCollection", "features": [...] }
#    Cada feature tiene: properties (atributos tabulares) + geometry (polígono).
# =============================================================================
RUTA_RAW    = r'D:\cdmx-analysis\datasets\raw\catlogo-de-colonias.json'
RUTA_LIMPIO = r'D:\cdmx-analysis\datasets\processed\catlogo-de-colonias_limpio.csv'
RUTA_GEO    = r'D:\cdmx-analysis\datasets\processed\catlogo-de-colonias_limpio.geojson'

print("Cargando GeoJSON...")
with open(RUTA_RAW, encoding='utf-8') as f:
    geojson_raw = json.load(f)

features = geojson_raw.get('features', [])
print(f"\n{'='*60}")
print(f"  TOTAL DE FEATURES (colonias): {len(features):,}")
print(f"{'='*60}")

# =============================================================================
# 2. EXTRACCIÓN DE PROPIEDADES A DATAFRAME
#    Aplanamos el bloque 'properties' de cada feature para trabajar con Pandas.
#    Se conserva además el tipo de geometría para validación posterior.
# =============================================================================
print("\n===== EXTRAYENDO PROPIEDADES A DATAFRAME =====")

registros = []
for feat in features:
    props = feat.get('properties', {}) or {}
    geom  = feat.get('geometry',   {}) or {}
    registros.append({
        # Atributos tabulares
        'cve_ent': props.get('cve_ent'),
        'entidad': props.get('entidad'),
        'cve_alc': props.get('cve_alc'),
        'alc':     props.get('alc'),
        'cve_col': props.get('cve_col'),
        'colonia': props.get('colonia'),
        'clasif':  props.get('clasif'),
        # Metadato geométrico (no coordenadas crudas)
        'geom_type': geom.get('type'),
    })

df = pd.DataFrame(registros)
print(f"  DataFrame creado: {df.shape[0]:,} filas × {df.shape[1]} columnas")
print(f"  Columnas: {list(df.columns)}")

# =============================================================================
# 3. DIAGNÓSTICO INICIAL
# =============================================================================
print("\n===== DIAGNÓSTICO: VALORES FALTANTES POR COLUMNA (antes de limpieza) =====")
nulos     = df.isnull().sum()
nulos_pct = (nulos / len(df) * 100).round(2)
diag      = pd.DataFrame({'nulos': nulos, 'porcentaje': nulos_pct})
diag_con_nulos = diag[diag['nulos'] > 0]
if len(diag_con_nulos) > 0:
    print(diag_con_nulos.to_string())
else:
    print("  ✓ Sin valores nulos en las propiedades extraídas")

print("\n  Muestra de valores únicos por columna:")
for col in df.columns:
    unicos = df[col].dropna().unique()
    muestra = list(unicos[:8])
    print(f"  [{col}]  →  {muestra}{'...' if len(unicos) > 8 else ''}")

# =============================================================================
# 4. VALIDACIÓN DE GEOMETRÍAS
#    Verificar que todos los features tienen geometría válida y del tipo esperado.
# =============================================================================
print("\n===== VALIDACIÓN DE GEOMETRÍAS =====")

# Conteo por tipo de geometría
geom_counts = df['geom_type'].value_counts(dropna=False)
print(f"  Distribución de tipos de geometría:\n{geom_counts.to_string()}")

# Features sin geometría (geometry == null en el JSON original)
sin_geom = df['geom_type'].isnull().sum()
print(f"\n  Features sin geometría: {sin_geom:,}")
if sin_geom > 0:
    print("  → Se conservan en la tabla; se marcan con bandera 'sin_geometria'")
    df['sin_geometria'] = df['geom_type'].isnull()
else:
    print("  ✓ Todos los features tienen geometría")
    df['sin_geometria'] = False

# =============================================================================
# 5. LIMPIEZA Y ESTANDARIZACIÓN DE ATRIBUTOS
# =============================================================================
print("\n===== ESTANDARIZACIÓN DE ATRIBUTOS =====")

# --- 5a. Claves de entidad / alcaldía / colonia ---
#     Formato esperado: strings con ceros a la izquierda preservados.
#     pd.read_json los leería como int; aquí ya son str desde json.load.
for col in ['cve_ent', 'cve_alc', 'cve_col']:
    antes = df[col].isnull().sum()
    df[col] = df[col].astype(str).str.strip().replace({'None': pd.NA, 'nan': pd.NA})
    print(f"  [{col}] → str limpio | NaN antes: {antes:,} "
          f"| NaN después: {df[col].isnull().sum():,}")

# --- 5b. Texto: entidad, alc, colonia, clasif ---
#     Strip + UPPER + colapsar espacios múltiples.
COLS_TEXTO = ['entidad', 'alc', 'colonia', 'clasif']
for col in COLS_TEXTO:
    antes = df[col].isnull().sum()
    df[col] = (df[col]
               .astype(str)
               .str.strip()
               .str.upper()
               .str.replace(r'\s+', ' ', regex=True))
    # Revertir 'NONE' / 'NAN' que astype(str) genera sobre NaN reales
    df[col] = df[col].replace({'NONE': pd.NA, 'NAN': pd.NA})
    print(f"  [{col}] → str normalizado (upper) | NaN antes: {antes:,} "
          f"| NaN después: {df[col].isnull().sum():,}")

# =============================================================================
# 6. MANEJO DE VALORES FALTANTES (NA)
# =============================================================================
print("\n===== ESTRATEGIA DE IMPUTACIÓN / MANEJO DE NAs =====")

# --- 6a. cve_ent / entidad: todos deberían ser CDMX (09) ---
cve_ent_na = df['cve_ent'].isnull().sum()
if cve_ent_na > 0:
    df['cve_ent'] = df['cve_ent'].fillna('09')
    df['entidad'] = df['entidad'].fillna('CIUDAD DE MEXICO')
    print(f"  [cve_ent / entidad] {cve_ent_na:,} NaN → '09' / 'CIUDAD DE MEXICO'"
          " (valor único esperado para CDMX)")
else:
    print("  [cve_ent / entidad] ✓ Sin NaN")

# --- 6b. cve_alc / alc: clave y nombre de alcaldía ---
#     Si cve_alc tiene NaN pero alc no, se intenta derivar la clave.
#     Si ambos faltan → 'SIN DATO'.
cve_alc_na = df['cve_alc'].isnull().sum()
alc_na     = df['alc'].isnull().sum()
print(f"\n  [cve_alc] NaN: {cve_alc_na:,} | [alc] NaN: {alc_na:,}")

# Tabla de referencia alcaldías CDMX (clave INEGI → nombre)
ALC_REF = {
    '002': 'AZCAPOTZALCO', '003': 'COYOACAN', '004': 'CUAJIMALPA DE MORELOS',
    '005': 'GUSTAVO A. MADERO', '006': 'IZTACALCO', '007': 'IZTAPALAPA',
    '008': 'LA MAGDALENA CONTRERAS', '009': 'MILPA ALTA', '010': 'ALVARO OBREGON',
    '011': 'TLAHUAC', '012': 'TLALPAN', '013': 'XOCHIMILCO',
    '014': 'BENITO JUAREZ', '015': 'CUAUHTEMOC', '016': 'MIGUEL HIDALGO',
    '017': 'VENUSTIANO CARRANZA'
}
ALC_REF_INV = {v: k for k, v in ALC_REF.items()}

if cve_alc_na > 0:
    # Intentar derivar clave desde nombre de alcaldía
    mask = df['cve_alc'].isnull() & df['alc'].notna()
    df.loc[mask, 'cve_alc'] = df.loc[mask, 'alc'].map(ALC_REF_INV)
    aun_na = df['cve_alc'].isnull().sum()
    df['cve_alc'] = df['cve_alc'].fillna('SIN DATO')
    print(f"  [cve_alc] → recuperado desde 'alc' donde fue posible"
          f" | NaN residuales: {aun_na:,} → 'SIN DATO'")

if alc_na > 0:
    mask = df['alc'].isnull() & df['cve_alc'].notna() & (df['cve_alc'] != 'SIN DATO')
    df.loc[mask, 'alc'] = df.loc[mask, 'cve_alc'].map(ALC_REF)
    df['alc'] = df['alc'].fillna('DESCONOCIDA')
    print(f"  [alc] → recuperado desde 'cve_alc' donde fue posible"
          f" | restantes → 'DESCONOCIDA'")

# --- 6c. cve_col / colonia: clave y nombre de colonia ---
#     No existe tabla de referencia estándar, así que:
#     cve_col NA → 'SIN CLAVE'  |  colonia NA → 'DESCONOCIDA'
cve_col_na = df['cve_col'].isnull().sum()
col_na     = df['colonia'].isnull().sum()
print(f"\n  [cve_col] NaN: {cve_col_na:,} → 'SIN CLAVE'")
print(f"  [colonia] NaN: {col_na:,} → 'DESCONOCIDA'")
df['cve_col'] = df['cve_col'].fillna('SIN CLAVE')
df['colonia'] = df['colonia'].fillna('DESCONOCIDA')

# --- 6d. clasif: tipo de asentamiento (Colonia, Barrio, Pueblo, etc.) ---
clasif_na = df['clasif'].isnull().sum()
print(f"\n  [clasif] NaN: {clasif_na:,} → 'SIN CLASIFICAR'")
df['clasif'] = df['clasif'].fillna('SIN CLASIFICAR')

# --- 6e. geom_type: ya manejado con bandera 'sin_geometria' ---
# Se rellena el texto para consistencia tabular
df['geom_type'] = df['geom_type'].fillna('SIN GEOMETRIA')

# =============================================================================
# 7. VALIDACIONES DE INTEGRIDAD
# =============================================================================
print("\n===== VALIDACIONES DE INTEGRIDAD =====")

# 7a. Duplicados por cve_col (clave única de colonia)
dupes = df.duplicated(subset='cve_col', keep=False)
n_dupes = dupes.sum()
print(f"  Registros duplicados por cve_col: {n_dupes:,}")
if n_dupes > 0:
    print(df[dupes][['cve_col', 'colonia', 'alc']].to_string(index=False))

# 7b. Claves que no siguen el patrón esperado XXX-YYY
import re
patron_cve = re.compile(r'^\d{3}-\d{3}$')
mal_formato = df['cve_col'].apply(
    lambda x: not patron_cve.match(str(x)) if x not in ('SIN CLAVE',) else False
)
n_mal = mal_formato.sum()
print(f"  cve_col con formato inesperado (no NNN-NNN): {n_mal:,}")

# 7c. Registros con entidad distinta a CDMX (09)
fuera_cdmx = (df['cve_ent'] != '09') & (df['cve_ent'] != 'SIN DATO')
n_fuera = fuera_cdmx.sum()
print(f"  Registros con cve_ent ≠ '09' (fuera de CDMX): {n_fuera:,}")

# =============================================================================
# 8. CREACIÓN DE COLUMNAS DERIVADAS ÚTILES
# =============================================================================
print("\n===== COLUMNAS DERIVADAS =====")

# 8a. Nombre completo normalizado: "ALCALDÍA > COLONIA (CLASIF)"
df['nombre_completo'] = (
    df['alc'] + ' > ' + df['colonia'] + ' (' + df['clasif'] + ')'
)
print("  [nombre_completo] → 'ALC > COLONIA (CLASIF)' creada")

# 8b. Indicador de si la clasificación es una colonia formal
df['es_colonia_formal'] = df['clasif'].str.upper() == 'COLONIA'
print("  [es_colonia_formal] → True si clasif == 'COLONIA'")

# 8c. Timestamp de procesamiento (para trazabilidad de la limpieza)
df['fecha_procesamiento'] = datetime.date.today().isoformat()
print(f"  [fecha_procesamiento] → '{df['fecha_procesamiento'].iloc[0]}'")

# =============================================================================
# 9. RESUMEN FINAL
# =============================================================================
print(f"\n{'='*60}")
print(f"  DIMENSIONES FINALES: {df.shape[0]:,} filas × {df.shape[1]} columnas")
print(f"{'='*60}")

print("\n===== VALORES NULOS RESTANTES =====")
nulos_final    = df.isnull().sum()
cols_con_nulos = nulos_final[nulos_final > 0]
if len(cols_con_nulos) > 0:
    for col, n in cols_con_nulos.items():
        print(f"  {col:<35} {n:>6,}  ({n/len(df)*100:.1f}%)")
else:
    print("  ✓ Sin valores nulos en el dataset final")

print("\n===== DISTRIBUCIÓN POR ALCALDÍA =====")
print(df['alc'].value_counts().to_string())

print("\n===== DISTRIBUCIÓN POR CLASIFICACIÓN =====")
print(df['clasif'].value_counts().to_string())

print("\n===== TIPOS DE DATOS FINALES =====")
print(df.dtypes.to_string())

# =============================================================================
# 10. EXPORTAR RESULTADO
#     10a. CSV tabular (sin geometría): para análisis con Pandas / Excel.
#     10b. GeoJSON limpio (con geometría): para visualización cartográfica.
# =============================================================================
os.makedirs(os.path.dirname(RUTA_LIMPIO), exist_ok=True)

# --- 10a. CSV tabular ---
cols_csv = ['cve_ent', 'entidad', 'cve_alc', 'alc', 'cve_col', 'colonia',
            'clasif', 'nombre_completo', 'es_colonia_formal',
            'sin_geometria', 'geom_type', 'fecha_procesamiento']
df[cols_csv].to_csv(RUTA_LIMPIO, index=False, encoding='utf-8')
print(f"\n✓ CSV tabular guardado en:\n  {RUTA_LIMPIO}")

# --- 10b. GeoJSON limpio: reconstruir con propiedades normalizadas ---
features_limpios = []
df_reset = df.reset_index(drop=True)

for idx, feat in enumerate(features):
    fila = df_reset.iloc[idx]
    feat_limpio = {
        "type": "Feature",
        "properties": {
            "cve_ent":            fila['cve_ent'],
            "entidad":            fila['entidad'],
            "cve_alc":            fila['cve_alc'],
            "alc":                fila['alc'],
            "cve_col":            fila['cve_col'],
            "colonia":            fila['colonia'],
            "clasif":             fila['clasif'],
            "nombre_completo":    fila['nombre_completo'],
            "es_colonia_formal":  bool(fila['es_colonia_formal']),
            "sin_geometria":      bool(fila['sin_geometria']),
            "fecha_procesamiento": fila['fecha_procesamiento'],
        },
        "geometry": feat.get('geometry')   # preservar coordenadas originales
    }
    features_limpios.append(feat_limpio)

geojson_limpio = {
    "type": "FeatureCollection",
    "crs":  geojson_raw.get('crs'),
    "features": features_limpios
}

with open(RUTA_GEO, 'w', encoding='utf-8') as f:
    json.dump(geojson_limpio, f, ensure_ascii=False, indent=2)

print(f"✓ GeoJSON limpio guardado en:\n  {RUTA_GEO}")
