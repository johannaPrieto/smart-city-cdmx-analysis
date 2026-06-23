$dirs = @(
  'datasets\raw\fgj_delitos',
  'datasets\raw\locatel_0311',
  'datasets\raw\denue',
  'datasets\raw\geojson',
  'datasets\raw\inegi',
  'datasets\clean\delitos_limpios',
  'datasets\clean\locatel_limpio',
  'datasets\clean\geojson_procesado',
  'datasets\clean\dataset_final',
  'notebooks',
  'scripts\limpieza',
  'scripts\geoprocesamiento',
  'scripts\modelos',
  'scripts\visualizacion',
  'dashboard\powerbi',
  'dashboard\dash',
  'dashboard\exportaciones',
  'resultados\mapas',
  'resultados\graficas',
  'resultados\tablas',
  'resultados\modelos',
  'resultados\reportes',
  'documentacion\estado_del_arte',
  'documentacion\metodologia',
  'documentacion\referencias',
  'documentacion\avances',
  'documentacion\presentaciones',
  'modelos\entrenados',
  'modelos\metricas',
  'modelos\predicciones',
  'imagenes\diagramas',
  'imagenes\dashboards',
  'imagenes\mapas'
)

foreach ($dir in $dirs) {
  $path = Join-Path 'd:\cdmx-analysis' $dir
  if (-not (Test-Path $path)) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
    New-Item -ItemType File -Path (Join-Path $path '.gitkeep') -Force | Out-Null
    Write-Host "CREADO: $dir"
  } else {
    Write-Host "YA EXISTE: $dir"
  }
}
Write-Host "Listo!"
