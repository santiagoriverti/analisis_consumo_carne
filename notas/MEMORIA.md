# Memoria del proyecto (bitácora)

## Estado actual: ✅ funcionando, actualizado a junio 2026

Última corrida validada end-to-end (pipeline + notebook por `nbconvert`): **0 errores**.

## Resultados clave de la última corrida (a jun-2026)

**Tabla 1 (OCDE, 1990-2026)** — kg/hab, mín/máx (año) y promedio:
- Carne vacuna: 32,30 (2024) / 52,05 (1990) / prom 39,63
- Carne avícola: 5,78 (1990) / 28,51 (2026) / prom 18,78
- Pescado: 5,72 (2010) / 11,91 (1997) / prom 7,72
- Carne porcina: 3,30 (1991) / 13,13 (2026) / prom 6,93
- Carne ovina: 0,70 (2021) / 1,74 (1994) / prom 0,97

**Composición 2026 (torta):** vacuna 40,6% · avícola 33,8% · porcina 15,6% ·
pescado 9,2% · ovina 0,8% (vacuna+avícola ≈ 74%).

**Tabla 5 (precio real asado, $ dic-2025):**
- Global: mín $6.534 (2002-07) · máx **$17.011 (2026-03)** · prom $10.540
- Milei: mín $10.333 (2024-09) · máx $17.011 (2026-03) · prom $13.024
- Menem→A. Fernández: idénticos al informe original (validado).

**Tabla 7 (kg de asado por salario):**
- Global: mín **108 (2026-03)** · máx 277 (2008-01) · prom 190
- Milei: mín 108 (2026-03) · máx 185 (2024-11) · prom 146

**Exportaciones (absolutas, anual):** 2002 = 159 M kg → 2025 = 524 M kg (+230%).

## Qué se hizo en cada sesión

### Sesión 1 (2026-07-31) — armado inicial
- Arquitectura `src/` + notebook Colab + README con badge + requirements + .gitignore.
- API OCDE resuelta y verificada (dataflow, códigos, países).
- Tablas 5 y 7 reprodujeron **exactamente** el informe original → metodología validada.
- Commit + push a `main`.

### Sesión 2 (2026-07-31) — actualización a jun-2026
- `config.py`: `YEAR_MAX=2026`, `PROJECT_TO=jun-2026`, `COMPOSITION_YEAR=2026`,
  `SALARY_MA_WINDOW=6`; Milei extendida a 2026-12-31; nuevos archivos fuente.
- `data.py`: asado extendido con IPCVA; salario proyectado (media móvil); IPC empalmado
  con INDEC real (`sh_ipc`) + REM como fallback. **Bug corregido**: quitar `ffill` en
  `ipc_general` (aplanaba 2026 y no deflactaba el asado).
- `tables.py`: Tabla 1 con layout de Tabla 5 y rango dinámico.
- `figures.py`: torta a 2026 + fix de etiquetas de porciones chicas.
- `pipeline.py`: Excel consolidado `resultados_consumo_carne.xlsx`.
- Notas de memoria (esta carpeta) + CLAUDE.md.

## Pendientes / posibles mejoras

- [ ] **Exportaciones 2026**: cuando cierre el año (o si se consigue el dato anualizado),
      agregar la barra 2026 en `analisis_carne.xlsx!exportaciones` (hoy solo hasta 2025).
- [ ] **Salario real 2026**: si aparece el dato SIPA oficial de 2026 (hoy proyectado con
      media móvil), reemplazar la proyección por el dato real en `INECO_carne!remuneraciones`.
- [ ] **Prosa del informe `.tex`**: actualizar las cifras del texto (p. ej. asado máx real
      ahora ~$17.011 en 2026-03, no $15.657; consumo vacuno 2025 ≈ 33,5 kg). Las tablas y
      figuras ya salen actualizadas; falta ajustar los números citados en el cuerpo.
- [ ] **Decisión de estilo** (abierta con el usuario): dejar exportaciones en una sola
      versión (absoluta vs índices) y si la Figura 2/3 van con 4 o 5 tipos de carne
      (hoy 5, incluye ovina).
- [ ] Si se cambia la **base de deflación** a jun-2026, ajustar `REF_DATE` y captions.

## Trampas conocidas (no repetir)

- No usar `ffill` en el IPC largo: aplana 2026 y arruina la deflación.
- OCDE es **anual**: no intentar granularidad mensual en la Tabla 1.
- Las exportaciones absolutas son **anuales**: no meter 2026 parcial como si fuera un año.
- Windows cp1252: no imprimir Unicode raro en `print` del pipeline.
- IPCVA e INECO comparten la serie de asado y **coinciden en dic-2025**; verificar ese
  empalme si se cambian los archivos.
