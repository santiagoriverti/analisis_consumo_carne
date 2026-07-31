# Contexto del proyecto

## Objetivo

Actualizar el **informe de prensa de INECO (UADE)** sobre la evolución del consumo de
carne en Argentina y su comparación internacional. El informe es un `.tex` (documento
LaTeX) que contiene tablas y figuras generadas a partir de datos. Este repositorio
**automatiza la generación de esos insumos** (tablas + figuras + Excel) de forma
reproducible, para que actualizar el informe cada período sea trivial.

Flujo previsto por el usuario (Santiago Riverti):
1. Abrir el notebook desde el README de GitHub (badge "Open in Colab").
2. "Ejecutar todo" → se descargan todas las figuras (600 dpi), las tablas en LaTeX y un
   Excel consolidado con las series.
3. Pegar tablas/figuras actualizadas en el `.tex` del informe.

## Los 11 productos que pide el informe

1. **Tabla 1** — mín./máx./promedio por tipo de carne (OCDE).
2. **Figura 2** — consumo per cápita por tipo de carne (OCDE).
3. **Figura 3** — consumo per cápita, base 100 = 1990 (OCDE).
4. **Figura 4** — torta de composición del consumo (OCDE).
5. **Tabla 5** — precio real del asado por gestión, $ de dic-2025 (IPCVA + IPC INDEC).
6. **Figura 5** — evolución del precio real del asado (IPCVA + IPC).
7. **Tabla 7** — esfuerzo salarial: kg de asado por salario, por gestión (IPCVA + SIPA).
8. **Figura 6** — kg de asado que compra un salario (IPCVA + SIPA).
9. **Figuras 7a/7b** — consumo vacuno internacional, absoluto y base 100 (OCDE).
10. **Figuras 8a/8b** — exportaciones de carne bovina, volumen y valor (INDEC).
11. **Figura 9** — precio relativo pollo/asado (IPCVA).

## Historia del desarrollo

- **Sesión 1**: se armó la arquitectura completa (`src/` + notebook + README + Colab
  badge). Se resolvió y verificó la **API SDMX de la OCDE**. Las tablas 5 y 7
  reprodujeron **exactamente** los valores del informe original (validación fuerte de
  que la metodología de deflación y esfuerzo salarial es correcta). Se publicó en GitHub.
- **Sesión 2**: actualización **a junio de 2026**:
  - OCDE anual pedida hasta 2026.
  - Asado, IPC y salario extendidos/proyectados a jun-2026 (ver `ESPECIFICACIONES_TECNICAS.md`).
  - Tabla 1 reestructurada al layout de la Tabla 5.
  - Se agregó el **Excel consolidado** de resultados.
  - Se crearon estos archivos de memoria.

## Fuentes de datos (carpeta `docs/`)

| Archivo | Contenido | Cobertura |
|---|---|---|
| `INECO_carne.xlsx` | asado nominal, IPC general (empalme largo), remuneración des. | 1996 → dic-2025 |
| `ipcv_precios_carne_pollo.xlsx` | asado / pollo (IPCVA) | 2000-10 → jun-2026 |
| `analisis_carne.xlsx` | exportaciones absolutas (kg/USD) + relativos | exp. 2002-2025 |
| `sh_ipc_07_26.xls` | IPC Nacional INDEC (índices) | dic-2016 → jun-2026 |
| `tablas-relevamiento-expectativas-mercado-jun-2026.xlsx` | REM (expectativas) | jun-2026 → dic-2026 |
| `exportaciones_indices_rubros.xlsx` | índices INDEC de exportación (base 2004=100) | 2004 → jun-2026 |
| `oecd_consumo_carne.xlsx` | **generado** por el pipeline (descarga OCDE) | 1990-2026 |

## Decisiones clave tomadas (y por qué)

1. **OCDE es anual**, no mensual. La Tabla 1 usa el layout de la Tabla 5 pero la "fecha"
   del mín./máx. es el **año** (no hay mes en datos anuales).
2. **IPC a jun-2026**: se descubrió que el IPC Nacional del INDEC (`sh_ipc`) tiene dato
   **real hasta jun-2026** y **coincide exactamente** con la serie larga de INECO en
   dic-2025. Por eso el deflactor usa dato **real** (no proyección) hasta junio. El REM
   quedó implementado como fallback para meses futuros (jul-2026+), honrando el pedido.
3. **Salario**: la serie SIPA (INECO) termina en dic-2025. Se **proyecta ene–jun 2026**
   con media móvil (6 meses) de la variación mensual reciente.
4. **Asado**: la serie larga de INECO termina en dic-2025; se extiende con IPCVA (misma
   serie, coincide en dic-2025 = $15.340) para ene–jun 2026.
5. **Exportaciones absolutas**: son anuales y la fuente llega a **2025**. 2026 es año en
   curso (incompleto) → NO se grafica como barra anual. La versión de índices sí llega a
   jun-2026.
6. **Base de deflación**: se mantiene **dic-2025** ($ constantes), como en el informe.

## Consecuencia analítica de la actualización

Con IPC e IPCVA reales de 2026, el **máximo real del asado pasó a marzo-2026 (~$17.011)**,
superando el pico previo de dic-2015 ($15.657). El poder de compra del salario en kg de
asado cae a ~108 kg (mín. histórico) en mar-2026. Son cambios legítimos por datos nuevos.
