"""
Descarga del consumo per cápita de carne desde la API SDMX de la OCDE
(OECD-FAO Agricultural Outlook) y volcado a Excel en ``docs/``.

Endpoint verificado (formato de clave: REF_AREA.FREQ.COMMODITY.MEASURE.UNIT.VERSION):

    https://sdmx.oecd.org/public/rest/data/
        OECD.TAD.ATM,DSD_AGR@DF_OUTLOOK_2026_2035,/
        {areas}.A.{commodities}.FO_PC..
        ?startPeriod=1990&endPeriod=2025&dimensionAtObservation=AllDimensions

Se solicita CSV (`application/vnd.sdmx.data+csv`), que es estable y liviano.
"""

from __future__ import annotations

import io

import pandas as pd
import requests

from . import config as C

_ACCEPT_CSV = "application/vnd.sdmx.data+csv"
_HEADERS = {"Accept": _ACCEPT_CSV, "User-Agent": "Mozilla/5.0 (INECO-analisis-carne)"}
_TIMEOUT = 180


def _build_url(areas: list[str], commodities: list[str],
               start: int = C.YEAR_MIN, end: int = C.YEAR_MAX) -> str:
    area_key = "+".join(areas)
    com_key = "+".join(commodities)
    key = f"{area_key}.A.{com_key}.{C.OECD_MEASURE}.."
    return (
        f"{C.OECD_BASE_URL}/{C.OECD_AGENCY},{C.OECD_DATAFLOW},/{key}"
        f"?startPeriod={start}&endPeriod={end}&dimensionAtObservation=AllDimensions"
    )


def _fetch(areas: list[str], commodities: list[str],
           start: int = C.YEAR_MIN, end: int = C.YEAR_MAX) -> pd.DataFrame:
    """Devuelve un DataFrame tidy: REF_AREA, COMMODITY, anio, valor."""
    url = _build_url(areas, commodities, start, end)
    resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
    resp.raise_for_status()
    raw = pd.read_csv(io.StringIO(resp.text))
    out = raw[["REF_AREA", "COMMODITY", "TIME_PERIOD", "OBS_VALUE"]].copy()
    out.columns = ["REF_AREA", "COMMODITY", "anio", "valor"]
    out["anio"] = out["anio"].astype(int)
    out["valor"] = pd.to_numeric(out["valor"], errors="coerce")
    return out.sort_values(["REF_AREA", "COMMODITY", "anio"]).reset_index(drop=True)


def consumo_argentina(start: int = C.YEAR_MIN, end: int = C.YEAR_MAX) -> pd.DataFrame:
    """
    Consumo per cápita (kg/hab) en Argentina por tipo de carne.

    Devuelve un DataFrame ancho: índice = año, columnas = etiquetas en español
    (Carne vacuna, Carne avícola, Carne porcina, Pescado, Carne ovina).
    """
    tidy = _fetch(["ARG"], list(C.MEATS.keys()), start, end)
    wide = tidy.pivot(index="anio", columns="COMMODITY", values="valor")
    wide = wide.rename(columns=C.MEATS)
    # Ordenar columnas según config.MEATS
    cols = [C.MEATS[k] for k in C.MEATS if C.MEATS[k] in wide.columns]
    return wide[cols].sort_index()


def consumo_vacuno_internacional(start: int = C.YEAR_MIN,
                                 end: int = C.YEAR_MAX) -> pd.DataFrame:
    """
    Consumo per cápita de carne vacuna por país (comparación internacional).

    Devuelve un DataFrame ancho: índice = año, columnas = nombre de país.
    """
    tidy = _fetch(list(C.COUNTRIES_INTL.keys()), ["CPC_EX_BV"], start, end)
    wide = tidy.pivot(index="anio", columns="REF_AREA", values="valor")
    wide = wide.rename(columns=C.COUNTRIES_INTL)
    cols = [C.COUNTRIES_INTL[k] for k in C.COUNTRIES_INTL if C.COUNTRIES_INTL[k] in wide.columns]
    return wide[cols].sort_index()


def descargar_a_excel(path=None) -> "pd.Path | str":
    """
    Descarga ambos datasets de la OCDE y los guarda en un Excel dentro de ``docs/``.

    Hojas:
      - ``consumo_argentina``          (año x tipo de carne)
      - ``vacuno_internacional``       (año x país)
      - ``metadata``                   (fuente, fecha de descarga, parámetros)
    """
    C.ensure_dirs()
    if path is None:
        path = C.DOCS / "oecd_consumo_carne.xlsx"

    arg = consumo_argentina()
    intl = consumo_vacuno_internacional()

    meta = pd.DataFrame(
        {
            "clave": [
                "fuente", "dataflow", "agencia", "medida",
                "descargado", "anio_min", "anio_max",
            ],
            "valor": [
                "OECD-FAO Agricultural Outlook (data-explorer.oecd.org)",
                C.OECD_DATAFLOW, C.OECD_AGENCY, C.OECD_MEASURE,
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                C.YEAR_MIN, C.YEAR_MAX,
            ],
        }
    )

    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        arg.to_excel(xw, sheet_name="consumo_argentina")
        intl.to_excel(xw, sheet_name="vacuno_internacional")
        meta.to_excel(xw, sheet_name="metadata", index=False)

    return path
