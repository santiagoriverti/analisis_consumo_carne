"""
Carga de las series provenientes de archivos Excel en ``docs/``.

Funciona tanto en local (lee de disco) como en Google Colab sin clonar el repo
(lee los archivos por URL cruda de GitHub). Cada loader devuelve un DataFrame
limpio y tipado, listo para las tablas y figuras.

Fuentes:
- precio_carne / remuneraciones / ipc  →  INECO_carne.xlsx
- exportaciones (absolutas)            →  analisis_carne.xlsx
- relativos (asado/pollo)              →  ipcv_precios_carne_pollo.xlsx
- exportaciones (índices 2004=100)     →  exportaciones_indices_rubros.xlsx
"""

from __future__ import annotations

import io

import pandas as pd
import requests

from . import config as C

_TIMEOUT = 120


def _read_excel(fname: str, **kwargs) -> pd.DataFrame:
    """Lee un Excel de ``docs/`` (local) o de la URL cruda de GitHub (Colab)."""
    if C.DATA_IS_LOCAL:
        return pd.read_excel(C.DOCS / fname, **kwargs)
    url = f"{C.RAW_BASE}/docs/{fname}"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=_TIMEOUT)
    resp.raise_for_status()
    return pd.read_excel(io.BytesIO(resp.content), **kwargs)


def _to_month_start(s: pd.Series) -> pd.Series:
    """Normaliza una serie de fechas al primer día del mes."""
    dt = pd.to_datetime(s, errors="coerce")
    return dt.dt.to_period("M").dt.to_timestamp(how="start")


# ---------------------------------------------------------------------------
# INECO_carne.xlsx
# ---------------------------------------------------------------------------
def _ipcv_asado() -> pd.DataFrame:
    """Precio nominal del asado según IPCVA (llega hasta jun-2026). periodo, asado."""
    df = _read_excel(C.IPCV_FILE, sheet_name="Hoja1")[["fecha", "asado"]].copy()
    df["periodo"] = _to_month_start(df["fecha"])
    df["asado"] = pd.to_numeric(df["asado"], errors="coerce")
    return df.dropna(subset=["periodo", "asado"])[["periodo", "asado"]]


def precio_asado() -> pd.DataFrame:
    """
    Precio nominal mensual del kg de asado (1996 → jun-2026).

    Base: INECO_carne (1996 → dic-2025). Se extiende con IPCVA para los meses
    posteriores (ene–jun 2026), que es la MISMA serie (coinciden en dic-2025).
    """
    base = _read_excel("INECO_carne.xlsx", sheet_name="precio_carne")[["fecha", "asado"]].copy()
    base["periodo"] = _to_month_start(base["fecha"])
    base["asado"] = pd.to_numeric(base["asado"], errors="coerce")
    base = base.dropna(subset=["periodo", "asado"])[["periodo", "asado"]]

    last = base["periodo"].max()
    ext = _ipcv_asado()
    ext = ext[(ext["periodo"] > last) & (ext["periodo"] <= C.PROJECT_TO)]
    out = pd.concat([base, ext], ignore_index=True).sort_values("periodo")
    return out.reset_index(drop=True)


def remuneraciones() -> pd.DataFrame:
    """
    Remuneración promedio desestacionalizada (1996 → jun-2026).

    Base: INECO_carne (1996 → dic-2025). Los meses faltantes hasta ``PROJECT_TO``
    se proyectan aplicando la media móvil (``SALARY_MA_WINDOW`` meses) de la
    variación mensual reciente. Columna ``proyectado`` marca el dato estimado.
    """
    df = _read_excel("INECO_carne.xlsx", sheet_name="remuneraciones")[["periodo", "remuneracion_des"]].copy()
    df["periodo"] = _to_month_start(df["periodo"])
    df["remuneracion_des"] = pd.to_numeric(df["remuneracion_des"], errors="coerce")
    df = df.dropna(subset=["periodo", "remuneracion_des"]).sort_values("periodo").reset_index(drop=True)
    df["proyectado"] = False

    last = df["periodo"].max()
    if last < C.PROJECT_TO:
        growth = df["remuneracion_des"].pct_change().dropna()
        g = float(growth.tail(C.SALARY_MA_WINDOW).mean())
        val = float(df["remuneracion_des"].iloc[-1])
        m = last
        nuevos = []
        while m < C.PROJECT_TO:
            m = m + pd.offsets.MonthBegin(1)
            val = val * (1 + g)
            nuevos.append({"periodo": m, "remuneracion_des": val, "proyectado": True})
        df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
    return df.reset_index(drop=True)


def ipc_indec_nacional() -> pd.DataFrame:
    """IPC Nacional nivel general del INDEC (real hasta jun-2026). periodo, indec."""
    raw = _read_excel(C.IPC_INDEC_FILE, sheet_name="Índices IPC Cobertura Nacional", header=None)
    fechas = pd.to_datetime(raw.iloc[5, 1:], errors="coerce")
    row_idx = next(i for i in range(6, 25) if str(raw.iloc[i, 0]).strip() == "Nivel general")
    vals = pd.to_numeric(raw.iloc[row_idx, 1:], errors="coerce")
    s = pd.DataFrame({"periodo": fechas.values, "indec": vals.values}).dropna()
    s["periodo"] = pd.to_datetime(s["periodo"]).dt.to_period("M").dt.to_timestamp()
    return s.sort_values("periodo").reset_index(drop=True)


def rem_ipc_var() -> pd.DataFrame:
    """Expectativas REM de var.% mensual del IPC nivel general (columna Promedio). periodo, var_pct."""
    raw = _read_excel(C.REM_FILE, sheet_name="Cuadros de resultados", header=None)
    start = next(i for i in range(len(raw)) if "IPC nivel general" in str(raw.iloc[i, 0]))
    filas = []
    for i in range(start + 1, min(start + 40, len(raw))):
        d = pd.to_datetime(raw.iloc[i, 0], errors="coerce")
        if pd.isna(d):
            if filas:
                break
            continue
        prom = pd.to_numeric(raw.iloc[i, 3], errors="coerce")  # col 3 = Promedio
        if pd.notna(prom):
            filas.append({"periodo": d.to_period("M").to_timestamp(), "var_pct": float(prom)})
    return pd.DataFrame(filas)


def ipc_general() -> pd.DataFrame:
    """
    IPC nivel general (empalme largo, 1996 → jun-2026). Columnas: periodo, general, origen.

    Base: INECO_carne (1996 → dic-2025, ``origen='real'``). Se extiende con el IPC
    Nacional real del INDEC (``sh_ipc``, empalmado por nivel — coincide en dic-2025)
    hasta jun-2026. Si quedara algún mes posterior sin dato oficial, se proyecta con
    el REM (``origen='proyeccion_REM'``); con ``PROJECT_TO=jun-2026`` no hace falta.
    """
    df = _read_excel("INECO_carne.xlsx", sheet_name="ipc")[["periodo", "general"]].copy()
    df["periodo"] = _to_month_start(df["periodo"])
    df["general"] = pd.to_numeric(df["general"], errors="coerce")
    # NO usar ffill: dejaría los meses NaN de 2026 planos y bloquearía el empalme
    # con el INDEC real. Nos quedamos con el último dato real (dic-2025).
    df = df.dropna(subset=["periodo", "general"]).sort_values("periodo").reset_index(drop=True)
    df["origen"] = "real"

    # 1) Empalme con INDEC real (mismo índice; se re-escala por si el nivel difiere).
    last = df["periodo"].max()
    indec = ipc_indec_nacional()
    if last in set(indec["periodo"]):
        scale = float(df["general"].iloc[-1]) / float(indec.loc[indec["periodo"] == last, "indec"].iloc[0])
        ext = indec[(indec["periodo"] > last) & (indec["periodo"] <= C.PROJECT_TO)].copy()
        ext["general"] = ext["indec"] * scale
        ext["origen"] = "real"
        df = pd.concat([df, ext[["periodo", "general", "origen"]]], ignore_index=True)

    # 2) REM para meses aún faltantes (jul-2026 en adelante; dormant hasta jun-2026).
    last = df["periodo"].max()
    if last < C.PROJECT_TO:
        rem = rem_ipc_var().set_index("periodo")["var_pct"]
        val = float(df["general"].iloc[-1]); m = last; nuevos = []
        while m < C.PROJECT_TO:
            m = m + pd.offsets.MonthBegin(1)
            if m not in rem.index:
                break
            val = val * (1 + rem.loc[m] / 100.0)
            nuevos.append({"periodo": m, "general": val, "origen": "proyeccion_REM"})
        if nuevos:
            df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
    return df.sort_values("periodo").reset_index(drop=True)


# ---------------------------------------------------------------------------
# analisis_carne.xlsx / ipcv_precios_carne_pollo.xlsx
# ---------------------------------------------------------------------------
def exportaciones_absolutas() -> pd.DataFrame:
    """
    Exportaciones de carne bovina en valores absolutos, agregadas por año
    (suma de los NCM de carne fresca y congelada).

    Columnas: anio, peso_neto_kg, monto_fob_usd, millones_kg, miles_millones_usd.
    """
    df = _read_excel("analisis_carne.xlsx", sheet_name="exportaciones")
    for col in ["peso_neto(kg)", "monto_fob(usd)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["anio"] = pd.to_numeric(df["fecha"], errors="coerce").astype("Int64")
    anual = (
        df.groupby("anio", as_index=False)[["peso_neto(kg)", "monto_fob(usd)"]]
        .sum()
        .dropna(subset=["anio"])
        .sort_values("anio")
    )
    anual = anual.rename(
        columns={"peso_neto(kg)": "peso_neto_kg", "monto_fob(usd)": "monto_fob_usd"}
    )
    anual["millones_kg"] = anual["peso_neto_kg"] / 1e6
    anual["miles_millones_usd"] = anual["monto_fob_usd"] / 1e9
    return anual.reset_index(drop=True)


def relativos_pollo_asado() -> pd.DataFrame:
    """
    Precio relativo pollo/asado (kg de pollo que se compran con 1 kg de asado).
    Columnas: periodo, asado, pollo, pollo_por_asado.
    """
    df = _read_excel("ipcv_precios_carne_pollo.xlsx", sheet_name="Hoja1")
    df = df[["fecha", "asado", "pollo"]].copy()
    df["periodo"] = _to_month_start(df["fecha"])
    for col in ["asado", "pollo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["periodo", "asado", "pollo"])
    df["pollo_por_asado"] = df["asado"] / df["pollo"]
    return df[["periodo", "asado", "pollo", "pollo_por_asado"]].reset_index(drop=True)


def exportaciones_indices() -> pd.DataFrame:
    """
    Índices INDEC de exportación de carne bovina (base 2004=100), serie mensual.
    Devuelve: periodo, valor, cantidad (nivel general de 'Carnes y sus preparados'
    o el subrubro de carne bovina si existe).
    """
    def _serie(sheet: str) -> pd.Series:
        raw = _read_excel("exportaciones_indices_rubros.xlsx", sheet_name=sheet, header=None)
        # Fila 2 = fechas (a partir de la col 1); col 0 = etiqueta del rubro.
        fechas = pd.to_datetime(raw.iloc[2, 1:], errors="coerce")
        etiquetas = raw.iloc[3:, 0].astype(str).str.strip().str.lower()
        # Buscar fila de carne bovina; fallback a "carnes y sus preparados".
        mask_bovina = etiquetas.str.contains("bovina", na=False)
        mask_carnes = etiquetas.str.contains("carne", na=False)
        idx = raw.iloc[3:].index[mask_bovina.values]
        if len(idx) == 0:
            idx = raw.iloc[3:].index[mask_carnes.values]
        row = raw.loc[idx[0], 1:]
        s = pd.Series(pd.to_numeric(row.values, errors="coerce"), index=fechas.values)
        return s.dropna()

    val = _serie("Valor").rename("valor")
    qty = _serie("Cantidades").rename("cantidad")
    out = pd.concat([val, qty], axis=1).reset_index().rename(columns={"index": "periodo"})
    out["periodo"] = pd.to_datetime(out["periodo"])
    return out.dropna(subset=["periodo"]).sort_values("periodo").reset_index(drop=True)
