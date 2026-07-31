"""Paquete de análisis del consumo de carne en Argentina (INECO - UADE)."""

from . import config, oecd, data, figures, tables, pipeline  # noqa: F401

__all__ = ["config", "oecd", "data", "figures", "tables", "pipeline"]
