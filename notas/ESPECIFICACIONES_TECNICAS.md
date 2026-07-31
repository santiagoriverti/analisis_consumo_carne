# Especificaciones técnicas

Detalle para reproducir, mantener o extender el pipeline.

## 1. API SDMX de la OCDE (OECD-FAO Agricultural Outlook)

- **Base**: `https://sdmx.oecd.org/public/rest/data`
- **Agencia / dataflow**: `OECD.TAD.ATM` / `DSD_AGR@DF_OUTLOOK_2026_2035` (edición más
  reciente; historia desde 1990, proyecciones hasta 2035).
- **Orden de dimensiones de la clave**:
  `REF_AREA.FREQ.COMMODITY.MEASURE.UNIT_MEASURE.VERSION_ID`
- **Clave usada**: `{areas}.A.{commodities}.FO_PC..`
  - `FREQ = A` (anual). **La serie es anual, no mensual.**
  - `MEASURE = FO_PC` (consumo humano per cápita, unidad `KG_PS` = kg/hab).
- **Cabecera**: `Accept: application/vnd.sdmx.data+csv` (CSV estable y liviano).
- **Parámetros**: `?startPeriod=1990&endPeriod=2026&dimensionAtObservation=AllDimensions`

### Códigos de commodity (CPC 2.1)
| Código | Etiqueta | 
|---|---|
| `CPC_EX_BV` | Carne vacuna (Beef and veal) |
| `CPC_EX_PT` | Carne avícola (Poultry meat) |
| `CPC_EX_PK` | Carne porcina (Pigmeat) |
| `CPC_EX_SH` | Carne ovina (Sheepmeat) |
| `CPC_04`    | Pescado (Fish and other fishing products) |

### Países comparación internacional (REF_AREA = ISO3)
`ARG, AUS, GBR, ISR, MEX, TUR, CHE, RUS, IND, IDN` (Rusia desde 1992; resto desde 1990).

Se hacen 2 llamadas: (a) ARG × 5 commodities; (b) 10 países × carne vacuna.

## 2. Series de Excel — carga, extensión y proyección (`src/data.py`)

Todas las funciones leen de `docs/` en local, o por **URL cruda de GitHub** en Colab
(`_read_excel`). Fecha normalizada al primer día de mes (`_to_month_start`).

- **`precio_asado()`** — asado nominal. Base INECO `precio_carne.asado` (1996→dic-2025)
  **+** IPCVA (`ipcv_precios_carne_pollo.xlsx!Hoja1`) para meses > dic-2025 y ≤ `PROJECT_TO`.
  Ambas coinciden en dic-2025 ($15.340), por eso se concatenan directo.
- **`remuneraciones()`** — `INECO_carne!remuneraciones.remuneracion_des` (1996→dic-2025).
  Meses faltantes hasta `PROJECT_TO` se **proyectan** con `g = media(pct_change últimos
  SALARY_MA_WINDOW meses)`, aplicando `val *= (1+g)`. Columna `proyectado` marca el estimado.
- **`ipc_general()`** — `INECO_carne!ipc.general` (empalme largo, 1996→dic-2025).
  **IMPORTANTE: NO usar `ffill`** (rellenaría los NaN de 2026 con dic-2025 y rompería el
  empalme). Se extiende con el **INDEC Nacional real** (`ipc_indec_nacional()`), re-escalado
  por nivel para coincidir en dic-2025 (el factor sale ≈ 1,0 porque son la misma serie).
  Si quedaran meses > último dato oficial, se proyectan con **REM** (`rem_ipc_var()`,
  columna Promedio). Con `PROJECT_TO = jun-2026` el tramo REM queda inactivo (INDEC ya
  llega a junio). Columna `origen` ∈ {`real`, `proyeccion_REM`}.
- **`ipc_indec_nacional()`** — lee `sh_ipc_07_26.xls!'Índices IPC Cobertura Nacional'`,
  fila con etiqueta exacta `Nivel general`; fechas en la fila 5.
- **`rem_ipc_var()`** — lee `REM_FILE!'Cuadros de resultados'`, bloque
  `Precios minoristas (IPC nivel general-Nacional; INDEC)`. Columnas: `col0`=fecha,
  `col2`=Mediana, **`col3`=Promedio** (la que se usa), var. % mensual.
- **`exportaciones_absolutas()`** — `analisis_carne!exportaciones`, suma de los 2 NCM
  (fresca + congelada) por año → `millones_kg`, `miles_millones_usd`. Anual, 2002-2025.
- **`relativos_pollo_asado()`** — IPCVA; `pollo_por_asado = asado / pollo`.
- **`exportaciones_indices()`** — `exportaciones_indices_rubros.xlsx` (base 2004=100),
  fila de carne bovina (o "carnes y preparados"), hojas `Valor` y `Cantidades`.

## 3. Cálculos (`src/pipeline.py`)

- **Precio real del asado**: `asado_real = asado_nominal * (IPC[REF_DATE] / IPC[t])`.
  `REF_DATE = dic-2025`. `_ipc_ref` toma el índice en REF_DATE (o el último ≤ REF_DATE).
- **Esfuerzo salarial**: `kg_asado_por_salario = remuneracion_des / asado_nominal`
  (merge mensual por `periodo`).
- **Base 100**: `serie / serie[1990] * 100`.
- **Composición (torta)**: participación % de cada carne en `COMPOSITION_YEAR` (2026).

## 4. Tablas (`src/tables.py`)

- `_stats_por_gestion(df, col)` → mín./máx./promedio + fechas por gestión y fila Global.
  Las **gestiones** están en `config.GESTIONES` (Milei extendida hasta **2026-12-31** para
  incluir 2026). Devuelven DataFrame legible + string LaTeX (estilo `booktabs` del informe).
- Tabla 1: layout `l r l r l r` (como Tabla 5); "fecha" del mín./máx. = año (dato anual).

## 5. Figuras (`src/figures.py`)

- Backend `Agg`. Todas a **600 dpi**, con marco negro (`_black_frame`) estilo INECO.
- Series mensuales con **sombreado por gestión** (`_shade_gestiones`) + anotación de
  mín./máx./promedio (asado real y kg/salario).
- Nombres de archivo replican los del informe: `consumo_per_capita.png`,
  `evolucion_carne_vacuna.png` (base 100), `composicion_consumo_carne.png`,
  `carne_vacuna_absoluto.png`, `carne_vacuna_base100.png`,
  `INECO_precio_asado_real_ipc_general.png`, `INECO_kg_asado_por_remuneracion.png`,
  `evolucion_kg.png`, `evolucion_usd.png`, `evolucion_relativos.png`,
  `exportaciones_indices_2004.png` (alternativa).

## 6. Excel consolidado (`pipeline.exportar_resultados_excel`)

`outputs/resultados_consumo_carne.xlsx` con hojas numeradas: `00_metadata`,
`01_consumo_OCDE_arg`, `02_consumo_OCDE_intl`, `03_consumo_base100_arg`,
`04_composicion`, `05_precio_asado`, `06_esfuerzo_salarial` (incluye `proyectado`),
`07_exportaciones`, `08_relativos`, `09_tabla1`, `10_tabla5`, `11_tabla7`.

## 6.bis Notebook (`notebooks/analisis_consumo_carne.ipynb`)

- **Celda de setup (idempotente)**: en Colab clona a la ruta FIJA
  `/content/analisis_consumo_carne`; si ya existe, hace
  `git fetch --depth 1 origin main && git reset --hard origin/main` (trae SIEMPRE lo último,
  sin anidar). En local, sube por el árbol hasta la carpeta con `src/` y `docs/`.
- **Celda de run**: borra `src*` de `sys.modules` antes de `from src import pipeline`
  (fuerza usar el código recién traído, no una versión cacheada).
- **Celda de descarga**: arma el ZIP con rutas ABSOLUTAS
  (`shutil.make_archive(str(C.ROOT/'resultados_consumo_carne'),'zip',str(C.OUTPUTS))`).
- Para que un cambio pusheado tome efecto, **reabrir el notebook desde el link de Colab**
  (Colab recarga el `.ipynb` desde GitHub).

## 6.ter Ejes de las figuras

- `figures._year_xticks(ax, years)` fuerza el tick del **último año** en las 4 figuras
  anuales de la OCDE (para que 2026 quede etiquetado pese al paso de 5 años).
- Las series mensuales usan `mdates.YearLocator(1)`; en `relativos` se fija
  `set_xlim(min, max)` para no mostrar un tick de año posterior al último dato.

## 7. Parámetros editables (`src/config.py`)

- `REF_DATE` (base de deflación) — hoy `2025-12-01`.
- `PROJECT_TO` (mes objetivo de series mensuales) — hoy `2026-06-01`.
- `YEAR_MIN`/`YEAR_MAX` (rango OCDE) — `1990` / `2026`.
- `COMPOSITION_YEAR` (año de la torta) — `2026`.
- `SALARY_MA_WINDOW` (ventana media móvil salario) — `6`.
- `GESTIONES` (rangos y colores), `MEATS`, `MEAT_COLORS`, `COUNTRIES_INTL`.

## 8. Cómo actualizar a un período futuro (checklist)

1. Actualizar los Excel de `docs/` con datos nuevos (asado IPCVA, IPC INDEC, salario SIPA,
   exportaciones, REM del mes).
2. Ajustar en `config.py`: `PROJECT_TO`, `REF_DATE` (si se cambia la base), `YEAR_MAX`,
   `COMPOSITION_YEAR`, y el fin de la gestión vigente en `GESTIONES`. Actualizar
   `IPC_INDEC_FILE` / `REM_FILE` si cambian los nombres.
3. Correr `pipeline.run_all()` y verificar tablas + figuras.
4. Commit + push (usuario Santiago Riverti). Re-ejecutar el notebook desde Colab.

## Entorno

- Python 3.14, pandas 2.3, matplotlib ≥3.7, openpyxl, xlrd (para `.xls`), requests.
- En Windows, la consola es cp1252: evitar imprimir Unicode no-ASCII en `print` del pipeline
  (ya resuelto). En Colab/Jupyter es UTF-8.
