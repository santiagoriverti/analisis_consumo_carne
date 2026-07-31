# Análisis del consumo de carne en Argentina

**Instituto de Economía de UADE (INECO)**

Pipeline reproducible para explorar la evolución del consumo de carne en Argentina
y su comparación internacional, y para generar **todas las tablas y figuras** que
alimentan el informe de prensa, **actualizadas a junio de 2026**. Los datos de consumo
se descargan en vivo desde la **API de la OCDE** (OECD-FAO Agricultural Outlook); los
precios, salarios y exportaciones provienen de fuentes locales (IPCVA, INDEC, SIPA).

> 📄 Para retomar el proyecto en otra PC/sesión, leé primero
> [`CLAUDE.md`](CLAUDE.md) y las notas en [`notas/`](notas/) (contexto, memoria y
> especificaciones técnicas).

## ▶️ Ejecutar en Google Colab

Abrí el notebook y ejecutá **Entorno de ejecución → Ejecutar todo**. Al finalizar
se descarga un `.zip` con las figuras (600 dpi) y las tablas en LaTeX.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/analisis_consumo_carne/blob/main/notebooks/analisis_consumo_carne.ipynb)

## Productos que genera

| # | Producto | Fuente | Cobertura |
|---|----------|--------|-----------|
| 1 | Tabla: mín./máx./promedio por tipo de carne | OCDE | 1990-2026 |
| 2 | Figura: consumo per cápita por tipo de carne | OCDE | 1990-2026 |
| 3 | Figura: consumo per cápita base 100 = 1990 | OCDE | 1990-2026 |
| 4 | Figura: composición del consumo (torta) | OCDE | 2026 |
| 5 | Tabla: precio real del asado por gestión ($ dic-2025) | IPCVA + INDEC (IPC) | 1996 → jun-2026 |
| 6 | Figura: evolución del precio real del asado | IPCVA + INDEC (IPC) | 1996 → jun-2026 |
| 7 | Tabla: esfuerzo salarial (kg de asado por salario) | IPCVA + SIPA | 1996 → jun-2026 |
| 8 | Figura: kg de asado que compra un salario | IPCVA + SIPA | 1996 → jun-2026 |
| 9 | Figuras: consumo vacuno internacional (absoluto + base 100) | OCDE | 1990-2026 |
| 10 | Figuras: exportaciones de carne (volumen + valor) | INDEC | 2002-2025 (anual) |
| 11 | Figura: precio relativo pollo/asado | IPCVA | 2000 → jun-2026 |

**Notas de cobertura a jun-2026:**
- **OCDE** es anual; se pide a la API hasta **2026** (primer año de la edición 2026-2035).
- **Asado**: INECO (1996→dic-2025) extendido con **IPCVA real** (ene–jun 2026).
- **IPC (deflactor)**: INECO extendido con **INDEC Nacional real** (`sh_ipc`, hasta jun-2026);
  el **REM** queda como proyección para meses futuros (jul-2026+).
- **Salario**: se **proyecta con media móvil** de la variación reciente (ene–jun 2026).
- **Exportaciones absolutas**: anuales, solo hasta **2025** (2026 es año incompleto).
  La versión de **índices INDEC base 2004=100** sí llega a jun-2026.

## Estructura del proyecto

```
analisis_consumo_carne/
├── CLAUDE.md                           # contexto para retomar con Claude
├── notas/                              # memoria del proyecto (para otra sesión/PC)
│   ├── CONTEXTO.md
│   ├── MEMORIA.md
│   └── ESPECIFICACIONES_TECNICAS.md
├── notebooks/
│   └── analisis_consumo_carne.ipynb   # notebook principal (Colab)
├── src/                                # paquete: fuente de verdad
│   ├── config.py    # rutas, parámetros OCDE, gestiones, colores, PROJECT_TO
│   ├── oecd.py      # descarga API SDMX de la OCDE → Excel
│   ├── data.py      # carga + extensión/proyección de series a jun-2026
│   ├── tables.py    # tablas 1, 5, 7 (+ LaTeX)
│   ├── figures.py   # todas las figuras a 600 dpi
│   └── pipeline.py  # orquestador run_all() + Excel consolidado
├── docs/                               # fuentes de datos (.xlsx / .xls)
│   ├── INECO_carne.xlsx                # asado, IPC general, remuneraciones (1996→dic-2025)
│   ├── analisis_carne.xlsx             # exportaciones absolutas + relativos
│   ├── ipcv_precios_carne_pollo.xlsx   # asado / pollo (IPCVA, hasta jun-2026)
│   ├── sh_ipc_07_26.xls                # IPC Nacional INDEC (real hasta jun-2026)
│   ├── tablas-relevamiento-...-jun-2026.xlsx  # REM (expectativas de mercado)
│   ├── exportaciones_indices_rubros.xlsx      # índices INDEC base 2004=100
│   └── fuentes.txt
└── outputs/                            # generado (NO versionado)
    ├── figuras/                        # PNG 600 dpi
    ├── tablas/                         # .tex
    └── resultados_consumo_carne.xlsx   # Excel consolidado con todas las series
```

## Ejecución local

```bash
pip install -r requirements.txt
python -c "from src import pipeline; pipeline.run_all()"
```

Las figuras quedan en `outputs/figuras/` (PNG 600 dpi) y las tablas en
`outputs/tablas/` (`.tex` listos para el informe). Los datos de la OCDE se guardan
en `docs/oecd_consumo_carne.xlsx`.

## Fuentes de datos

- **OCDE-FAO Agricultural Outlook** — consumo per cápita por tipo de carne, vía API
  SDMX (`data-explorer.oecd.org`).
- **IPCVA** — precios al consumidor de asado y pollo.
- **INDEC** — IPC nivel general (deflactor) e índices de exportación por rubros.
- **SIPA / Trabajo Registrado** — remuneración promedio del sector privado registrado.
