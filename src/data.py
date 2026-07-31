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
def precio_asado() -> pd.DataFrame:
    """Precio nominal mensual del kg de asado. Columnas: periodo, asado."""
    df = _read_excel("INECO_carne.xlsx", sheet_name="precio_carne")
    df = df[["fecha", "asado"]].copy()
    df["periodo"] = _to_month_start(df["fecha"])
    df["asado"] = pd.to_numeric(df["asado"], errors="coerce")
    return df.dropna(subset=["periodo", "asado"])[["periodo", "asado"]].reset_index(drop=True)


def remuneraciones() -> pd.DataFrame:
    """Remuneración promedio (desestacionalizada). Columnas: periodo, remuneracion_des."""
    df = _read_excel("INECO_carne.xlsx", sheet_name="remuneraciones")
    df = df[["periodo", "remuneracion_des"]].copy()
    df["periodo"] = _to_month_start(df["periodo"])
    df["remuneracion_des"] = pd.to_numeric(df["remuneracion_des"], errors="coerce")
    return df.dropna(subset=["periodo", "remuneracion_des"]).reset_index(drop=True)


def ipc_general() -> pd.DataFrame:
    """Índice de Precios al Consumidor (nivel general, empalme largo). Columnas: periodo, general."""
    df = _read_excel("INECO_carne.xlsx", sheet_name="ipc")
    df = df[["periodo", "general"]].copy()
    df["periodo"] = _to_month_start(df["periodo"])
    df["general"] = pd.to_numeric(df["general"], errors="coerce").ffill()
    return df.dropna(subset=["periodo", "general"]).reset_index(drop=True)


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
