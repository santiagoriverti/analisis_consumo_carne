# CLAUDE.md — Proyecto: Análisis del consumo de carne en Argentina (INECO/UADE)

> Este archivo lo lee Claude Code automáticamente al abrir el repo. Da el contexto
> mínimo para retomar el trabajo. Para el detalle completo, leé la carpeta `notas/`.

## Qué es

Pipeline reproducible (paquete `src/` + notebook Colab) que genera **todas las tablas y
figuras** del informe de prensa de INECO sobre la evolución del consumo de carne en
Argentina y su comparación internacional. Todo **actualizado a junio de 2026**.

El objetivo final: que desde el README de GitHub se abra el notebook en Colab, se
ejecute "Ejecutar todo", y se descargue un `.zip` con figuras (600 dpi), tablas LaTeX
y un Excel consolidado — listos para actualizar el informe (`.tex`).

## Arquitectura (fuente de verdad = `src/`)

- `src/config.py` — parámetros: OCDE (dataflow, códigos), gestiones, colores, `REF_DATE`
  (dic-2025, base de deflación), `PROJECT_TO` (jun-2026), `YEAR_MAX` (2026).
- `src/oecd.py` — descarga consumo per cápita vía **API SDMX de la OCDE**.
- `src/data.py` — carga y **extiende/proyecta** las series de Excel a jun-2026.
- `src/tables.py` — tablas 1, 5, 7 (DataFrame + LaTeX).
- `src/figures.py` — todas las figuras a 600 dpi.
- `src/pipeline.py` — `run_all()`: orquesta todo y arma el Excel consolidado.

El notebook `notebooks/analisis_consumo_carne.ipynb` es delgado: clona el repo (en
Colab), importa `src` y llama `pipeline.run_all()`.

## Reglas del repo

- **Commits**: solo bajo el usuario **Santiago Riverti**. NUNCA agregar
  `Co-Authored-By: Claude` ni atribución de Claude en commits ni PRs.
- **No versionar** `outputs/` ni `docs/oecd_consumo_carne.xlsx` (regenerables; ya en `.gitignore`).
- Las figuras se exportan siempre a **600 dpi**.
- Formato numérico argentino: coma decimal, punto de miles (`src/config.py:fmt_*`).

## Cómo correr y verificar

```bash
pip install -r requirements.txt
python -c "from src import pipeline; pipeline.run_all()"
```
Genera `outputs/figuras/*.png`, `outputs/tablas/*.tex` y
`outputs/resultados_consumo_carne.xlsx`. Para validar el notebook end-to-end:
`jupyter nbconvert --to notebook --execute notebooks/analisis_consumo_carne.ipynb`.

## Estado actual

Todo funciona y está **actualizado a jun-2026**, con las figuras y tablas revisadas y
aprobadas por el usuario. Listo para redactar el informe.

- **Contexto y objetivo** → `notas/CONTEXTO.md` (incluye "Cómo retomar en otra PC/sesión").
- **Bitácora, resultados y pendientes** → `notas/MEMORIA.md`.
- **Detalle técnico** (API OCDE, empalmes/proyecciones, checklist de actualización) →
  `notas/ESPECIFICACIONES_TECNICAS.md`.

**Pendiente principal**: actualizar las cifras de la **prosa** del informe `.tex` contra
los resultados nuevos (las tablas/figuras ya salen actualizadas). Ver pendientes en
`notas/MEMORIA.md`.
