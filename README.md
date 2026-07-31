# Análisis del consumo de carne en Argentina

**Instituto de Economía de UADE (INECO)**

Pipeline reproducible para explorar la evolución del consumo de carne en Argentina
y su comparación internacional, y para generar **todas las tablas y figuras** que
alimentan el informe de prensa. Los datos de consumo se descargan en vivo desde la
**API de la OCDE** (OECD-FAO Agricultural Outlook); los precios, salarios y
exportaciones provienen de fuentes locales (IPCVA, INDEC, SIPA).

## ▶️ Ejecutar en Google Colab

Abrí el notebook y ejecutá **Entorno de ejecución → Ejecutar todo**. Al finalizar
se descarga un `.zip` con las figuras (600 dpi) y las tablas en LaTeX.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/analisis_consumo_carne/blob/main/notebooks/analisis_consumo_carne.ipynb)

## Productos que genera

| # | Producto | Fuente |
|---|----------|--------|
| 1 | Tabla: mín./máx./promedio por tipo de carne (1990-2025) | OCDE |
| 2 | Figura: consumo per cápita por tipo de carne | OCDE |
| 3 | Figura: consumo per cápita base 100 = 1990 | OCDE |
| 4 | Figura: composición del consumo (torta, dic-2025) | OCDE |
| 5 | Tabla: precio real del asado por gestión ($ dic-2025) | IPCVA + INDEC (IPC) |
| 6 | Figura: evolución del precio real del asado | IPCVA + INDEC (IPC) |
| 7 | Tabla: esfuerzo salarial (kg de asado por salario) | IPCVA + SIPA |
| 8 | Figura: kg de asado que compra un salario | IPCVA + SIPA |
| 9 | Figuras: consumo vacuno internacional (absoluto + base 100) | OCDE |
| 10 | Figuras: exportaciones de carne (volumen + valor) | INDEC |
| 11 | Figura: precio relativo pollo/asado | IPCVA |

> **Exportaciones:** se generan las dos versiones — valores **absolutos** (M kg y M USD,
> desde `analisis_carne.xlsx`, idéntica al informe) y **índices base 2004=100**
> (desde `exportaciones_indices_rubros.xlsx`).

## Estructura del proyecto

```
analisis_consumo_carne/
├── notebooks/
│   └── analisis_consumo_carne.ipynb   # notebook principal (Colab)
├── src/                                # paquete: fuente de verdad
│   ├── config.py    # rutas, parámetros OCDE, gestiones, colores
│   ├── oecd.py      # descarga API SDMX de la OCDE → Excel
│   ├── data.py      # carga de series Excel (local o por URL)
│   ├── tables.py    # tablas 1, 5, 7 (+ LaTeX)
│   ├── figures.py   # todas las figuras a 600 dpi
│   └── pipeline.py  # orquestador run_all()
├── docs/                               # fuentes de datos (.xlsx / .xls)
│   ├── INECO_carne.xlsx                # asado, IPC general, remuneraciones (1996+)
│   ├── analisis_carne.xlsx             # exportaciones absolutas + relativos
│   ├── ipcv_precios_carne_pollo.xlsx   # asado / pollo (IPCVA)
│   ├── exportaciones_indices_rubros.xlsx  # índices INDEC base 2004=100
│   └── fuentes.txt
└── outputs/                            # generado (figuras/ + tablas/)
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
