"""
Configuración central del proyecto.

Contiene:
- Rutas del proyecto (detección automática local / Google Colab).
- Parámetros de la API SDMX de la OCDE (OECD-FAO Agricultural Outlook).
- Definición de gestiones presidenciales, colores y etiquetas.

Todo el resto del código importa desde aquí para tener una única fuente de verdad.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Repositorio (para modo Colab / lectura por URL cruda)
# ---------------------------------------------------------------------------
GITHUB_USER = "santiagoriverti"
GITHUB_REPO = "analisis_consumo_carne"
GITHUB_BRANCH = "main"
RAW_BASE = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
)

IN_COLAB = "google.colab" in sys.modules


# ---------------------------------------------------------------------------
# Detección de rutas
# ---------------------------------------------------------------------------
def _find_root() -> Path:
    """
    Busca la raíz del repositorio (carpeta que contiene ``docs/INECO_carne.xlsx``)
    empezando por el archivo actual y subiendo por el árbol de directorios.
    Si no la encuentra (p. ej. Colab sin clonar), devuelve el CWD.
    """
    candidates = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in candidates:
        for folder in [start, *start.parents]:
            if (folder / "docs" / "INECO_carne.xlsx").exists():
                return folder
    return Path.cwd().resolve()


ROOT = _find_root()
DOCS = ROOT / "docs"
OUTPUTS = ROOT / "outputs"
FIGURES_DIR = OUTPUTS / "figuras"
TABLES_DIR = OUTPUTS / "tablas"

# ¿Tenemos los archivos fuente en disco? (modo local). Si no, se leen por URL.
DATA_IS_LOCAL = (DOCS / "INECO_carne.xlsx").exists()

# Fecha de referencia para deflactar precios a pesos constantes.
REF_DATE = pd.Timestamp("2025-12-01")

# Último año observado que se usa para el análisis (la OCDE proyecta hasta 2035).
YEAR_MIN = 1990
YEAR_MAX = 2025

# Resolución de las figuras exportadas (informe INECO: 600 dpi).
DPI = 600


# ---------------------------------------------------------------------------
# API OCDE — OECD-FAO Agricultural Outlook
# ---------------------------------------------------------------------------
# Dataflow verificado (edición 2026-2035, con historia desde 1990).
OECD_AGENCY = "OECD.TAD.ATM"
OECD_DATAFLOW = "DSD_AGR@DF_OUTLOOK_2026_2035"
OECD_MEASURE = "FO_PC"  # Consumo humano per cápita (kg/hab/año)
OECD_BASE_URL = "https://sdmx.oecd.org/public/rest/data"

# Códigos de commodity (CPC 2.1) → etiqueta en español.
# Orden = orden de presentación en tablas/figuras.
MEATS: dict[str, str] = {
    "CPC_EX_BV": "Carne vacuna",
    "CPC_EX_PT": "Carne avícola",
    "CPC_EX_PK": "Carne porcina",
    "CPC_04": "Pescado",
    "CPC_EX_SH": "Carne ovina",
}

# Colores por tipo de carne (consistentes entre figuras).
MEAT_COLORS: dict[str, str] = {
    "Carne vacuna": "#B22222",   # rojo carne
    "Carne avícola": "#E8A33D",  # amarillo pollo
    "Carne porcina": "#E9779E",  # rosa cerdo
    "Pescado": "#2E86AB",        # azul
    "Carne ovina": "#6C757D",    # gris
}

# Comparación internacional (código ISO3 = REF_AREA en la OCDE) → nombre.
COUNTRIES_INTL: dict[str, str] = {
    "ARG": "Argentina",
    "AUS": "Australia",
    "GBR": "Reino Unido",
    "ISR": "Israel",
    "MEX": "México",
    "TUR": "Turquía",
    "CHE": "Suiza",
    "RUS": "Rusia",
    "IND": "India",
    "IDN": "Indonesia",
}


# ---------------------------------------------------------------------------
# Gestiones presidenciales (para tablas y sombreado de figuras)
# ---------------------------------------------------------------------------
# (nombre, inicio, fin, color) — colores del informe original INECO.
GESTIONES: list[tuple[str, pd.Timestamp, pd.Timestamp, str]] = [
    ("Menem",              pd.Timestamp("1996-01-01"), pd.Timestamp("1999-12-31"), "#054FAC"),
    ("De la Rúa",          pd.Timestamp("2000-01-01"), pd.Timestamp("2001-12-31"), "#ff0000"),
    ("Duhalde + NK + CFK", pd.Timestamp("2002-01-01"), pd.Timestamp("2015-12-31"), "#00b0ff"),
    ("Macri",              pd.Timestamp("2016-01-01"), pd.Timestamp("2019-12-31"), "#FFD700"),
    ("A. Fernández",       pd.Timestamp("2020-01-01"), pd.Timestamp("2023-12-31"), "#00b0ff"),
    ("Milei",              pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31"), "#8000ff"),
]


# ---------------------------------------------------------------------------
# Utilidades de formato (estilo argentino: coma decimal, punto de miles)
# ---------------------------------------------------------------------------
def fmt_money_ar(x: float, decimals: int = 0) -> str:
    """Formatea un número como pesos argentinos: ``$ 15.340``."""
    if pd.isna(x):
        return ""
    s = f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {s}"


def fmt_num_ar(x: float, decimals: int = 2) -> str:
    """Formatea un número con coma decimal y punto de miles: ``39,50``."""
    if pd.isna(x):
        return ""
    return f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ensure_dirs() -> None:
    """Crea las carpetas de salida si no existen."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
