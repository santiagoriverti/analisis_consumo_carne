"""
Orquestador: ejecuta todo el análisis de punta a punta.

``run_all()``:
  1. Descarga los datos de la OCDE (y los guarda en docs/oecd_consumo_carne.xlsx).
  2. Carga las series de Excel (asado, IPC, remuneraciones, exportaciones, relativos).
  3. Calcula el precio real del asado y el esfuerzo salarial.
  4. Genera las 3 tablas (DataFrame + LaTeX) y las ~13 figuras a 600 dpi.
  5. Guarda los .tex en outputs/tablas/ y devuelve un manifiesto con todas las rutas.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config as C
from . import data, figures, oecd, tables


def _ipc_ref(ipc: pd.DataFrame) -> float:
    serie = ipc.loc[ipc["periodo"] == C.REF_DATE, "general"]
    if serie.empty:
        serie = ipc.loc[ipc["periodo"] <= C.REF_DATE, "general"]
    return float(serie.iloc[-1])


def calcular_asado_real(asado: pd.DataFrame, ipc: pd.DataFrame) -> pd.DataFrame:
    """Precio del asado deflactado a pesos de dic-2025 (IPC general)."""
    ref = _ipc_ref(ipc)
    df = asado.merge(ipc[["periodo", "general"]], on="periodo", how="left")
    df["asado_real"] = df["asado"] * (ref / df["general"])
    return df.dropna(subset=["asado_real"]).reset_index(drop=True)


def calcular_esfuerzo_salarial(remun: pd.DataFrame, asado: pd.DataFrame) -> pd.DataFrame:
    """Kg de asado que compra un salario (remuneración / precio del asado)."""
    df = remun.merge(asado, on="periodo", how="inner")
    df["kg_asado_por_salario"] = df["remuneracion_des"] / df["asado"]
    return df.dropna(subset=["kg_asado_por_salario"]).reset_index(drop=True)


def run_all(descargar_oecd: bool = True, verbose: bool = True) -> dict:
    """Ejecuta todo el pipeline y devuelve un manifiesto {clave: ruta/objeto}."""
    C.ensure_dirs()
    log = (lambda *a: print(*a)) if verbose else (lambda *a: None)
    manifest: dict = {"figuras": {}, "tablas": {}, "datos": {}}

    # --- 1. OCDE ---------------------------------------------------------
    log("-> Descargando datos de la OCDE (Agricultural Outlook)...")
    consumo_arg = oecd.consumo_argentina()
    intl = oecd.consumo_vacuno_internacional()
    if descargar_oecd:
        xls = oecd.descargar_a_excel()
        manifest["datos"]["oecd_excel"] = xls
        log(f"  OCDE guardada en {xls}")

    # --- 2. Series de Excel ---------------------------------------------
    log("-> Cargando series de Excel (INECO / IPCVA / INDEC)...")
    asado = data.precio_asado()
    ipc = data.ipc_general()
    remun = data.remuneraciones()
    exp_abs = data.exportaciones_absolutas()
    rel = data.relativos_pollo_asado()

    # --- 3. Cálculos -----------------------------------------------------
    asado_real = calcular_asado_real(asado, ipc)
    kg_df = calcular_esfuerzo_salarial(remun, asado)

    # --- 4. Tablas -------------------------------------------------------
    log("-> Generando tablas...")
    t1_df, t1_tex = tables.tabla_min_max_prom_carne(consumo_arg)
    t5_df, t5_tex = tables.tabla_asado_real(asado_real)
    t7_df, t7_tex = tables.tabla_esfuerzo_salarial(kg_df)
    for name, tex in [("tabla1_min_max_prom", t1_tex),
                      ("tabla5_asado_real", t5_tex),
                      ("tabla7_esfuerzo_salarial", t7_tex)]:
        p = C.TABLES_DIR / f"{name}.tex"
        p.write_text(tex, encoding="utf-8")
        manifest["tablas"][name] = p
    manifest["tablas_df"] = {"tabla1": t1_df, "tabla5": t5_df, "tabla7": t7_df}

    # --- 5. Figuras ------------------------------------------------------
    log("-> Generando figuras (600 dpi)...")
    f = manifest["figuras"]
    f["consumo_per_capita"] = figures.consumo_per_capita(consumo_arg)
    f["consumo_base100"] = figures.consumo_base100(consumo_arg)
    f["composicion_torta"] = figures.composicion_torta(consumo_arg)
    f["vacuno_absoluto"] = figures.vacuno_internacional_absoluto(intl)
    f["vacuno_base100"] = figures.vacuno_internacional_base100(intl)
    f["precio_asado_real"] = figures.precio_asado_real(asado_real)
    f["kg_asado_por_salario"] = figures.kg_asado_por_salario(kg_df)
    f["exportaciones_kg"] = figures.exportaciones_kg(exp_abs)
    f["exportaciones_usd"] = figures.exportaciones_usd(exp_abs)
    f["relativos"] = figures.relativos(rel)
    # Alternativa de exportaciones por índices (fuente exportaciones_indices_rubros)
    try:
        idx_df = data.exportaciones_indices()
        f["exportaciones_indices"] = figures.exportaciones_indices(idx_df)
    except Exception as e:  # pragma: no cover
        log(f"  (Aviso) No se pudo generar la figura de índices de exportación: {e}")

    # --- 6. Guardar dataframes de datos procesados ----------------------
    base100 = consumo_arg.div(consumo_arg.loc[C.YEAR_MIN]).mul(100)
    composicion = _composicion(consumo_arg, C.COMPOSITION_YEAR)
    manifest["dataframes"] = {
        "consumo_arg": consumo_arg, "intl": intl, "base100": base100,
        "composicion": composicion, "asado_real": asado_real, "kg_df": kg_df,
        "exportaciones": exp_abs, "relativos": rel,
    }

    # --- 7. Excel consolidado con todos los resultados ------------------
    log("-> Exportando Excel consolidado de resultados...")
    xls = exportar_resultados_excel(manifest)
    manifest["datos"]["resultados_excel"] = xls

    log(f"OK: Listo. {len(f)} figuras y {len(manifest['tablas'])} tablas en {C.OUTPUTS}")
    return manifest


def _composicion(consumo_arg: pd.DataFrame, year: int) -> pd.DataFrame:
    """Composición porcentual del consumo de carne para un año."""
    vals = consumo_arg.loc[year].dropna()
    out = vals.rename("kg_per_capita").to_frame()
    out["participacion_%"] = (vals / vals.sum() * 100).round(2)
    return out


def exportar_resultados_excel(manifest: dict, path=None):
    """
    Genera un único Excel con TODAS las series y resultados, ordenados por hoja.
    Se guarda en outputs/ para que quede dentro del .zip de descarga.
    """
    C.ensure_dirs()
    if path is None:
        path = C.OUTPUTS / "resultados_consumo_carne.xlsx"
    d = manifest["dataframes"]
    t = manifest["tablas_df"]

    meta = pd.DataFrame({
        "clave": ["proyecto", "fuente_OCDE", "dataflow_OCDE", "deflactor_base",
                  "mes_objetivo_series_mensuales", "generado", "anio_min", "anio_max"],
        "valor": ["Análisis del consumo de carne en Argentina - INECO (UADE)",
                  "OECD-FAO Agricultural Outlook (API SDMX)", C.OECD_DATAFLOW,
                  "$ de " + C.REF_DATE.strftime("%m-%Y"),
                  C.PROJECT_TO.strftime("%m-%Y"),
                  pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"), C.YEAR_MIN, C.YEAR_MAX],
    })

    def _fecha(df):
        df = df.copy()
        if "periodo" in df.columns:
            df["periodo"] = pd.to_datetime(df["periodo"]).dt.strftime("%Y-%m")
        return df

    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        meta.to_excel(xw, sheet_name="00_metadata", index=False)
        d["consumo_arg"].to_excel(xw, sheet_name="01_consumo_OCDE_arg")
        d["intl"].to_excel(xw, sheet_name="02_consumo_OCDE_intl")
        d["base100"].round(2).to_excel(xw, sheet_name="03_consumo_base100_arg")
        d["composicion"].to_excel(xw, sheet_name="04_composicion")
        _fecha(d["asado_real"][["periodo", "asado", "asado_real"]]).to_excel(
            xw, sheet_name="05_precio_asado", index=False)
        cols_kg = ["periodo", "remuneracion_des", "asado", "kg_asado_por_salario", "proyectado"]
        _fecha(d["kg_df"][[c for c in cols_kg if c in d["kg_df"].columns]]).to_excel(
            xw, sheet_name="06_esfuerzo_salarial", index=False)
        d["exportaciones"].to_excel(xw, sheet_name="07_exportaciones", index=False)
        _fecha(d["relativos"]).to_excel(xw, sheet_name="08_relativos", index=False)
        t["tabla1"].to_excel(xw, sheet_name="09_tabla1_min_max_prom", index=False)
        t["tabla5"].to_excel(xw, sheet_name="10_tabla5_asado_real", index=False)
        t["tabla7"].to_excel(xw, sheet_name="11_tabla7_esfuerzo", index=False)

    return path
