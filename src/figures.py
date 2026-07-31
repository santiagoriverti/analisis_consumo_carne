"""
Generación de todas las figuras del informe, exportadas a PNG a 600 dpi.

Cada función recibe DataFrames ya procesados y devuelve la ruta del PNG guardado.
El estilo (marco negro, grilla tenue, sombreado por gestión) replica el del
informe original de INECO.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend no interactivo (seguro en Colab y en scripts)
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch, Rectangle

from . import config as C

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "figure.autolayout": False,
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _black_frame(fig) -> None:
    """Agrega el marco negro característico del informe INECO."""
    fig.patches.append(
        Rectangle((0, 0), 1, 1, transform=fig.transFigure,
                  fill=False, linewidth=2.0, edgecolor="black", zorder=10)
    )


def _save(fig, name: str) -> Path:
    C.ensure_dirs()
    path = C.FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=C.DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _shade_gestiones(ax, xmin, xmax):
    """Sombrea las gestiones y devuelve los handles para la leyenda."""
    handles = []
    for label, start, end, color in C.GESTIONES:
        s, e = max(start, xmin), min(end, xmax)
        if s <= e:
            ax.axvspan(s, e, color=color, alpha=0.35, zorder=0)
            handles.append(Patch(facecolor=color, alpha=0.35, label=label))
    return handles


# ---------------------------------------------------------------------------
# OCDE — consumo nacional
# ---------------------------------------------------------------------------
def consumo_per_capita(consumo_arg) -> Path:
    """Figura: evolución del consumo per cápita (kg) por tipo de carne."""
    fig, ax = plt.subplots(figsize=(13, 6.5))
    for meat in consumo_arg.columns:
        ax.plot(consumo_arg.index, consumo_arg[meat], linewidth=2.2,
                marker="o", markersize=3, color=C.MEAT_COLORS.get(meat), label=meat)
    ax.set_xlabel("")
    ax.set_ylabel("Kg por habitante por año")
    ax.grid(True, linewidth=0.6, alpha=0.5)
    ax.set_xlim(consumo_arg.index.min(), consumo_arg.index.max())
    ax.margins(y=0.05)
    ax.legend(title="Tipo de carne", ncol=2, frameon=True, loc="upper right")
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, "consumo_per_capita")


def consumo_base100(consumo_arg, base_year: int = 1990) -> Path:
    """Figura: consumo per cápita en índice base 100 = 1990."""
    fig, ax = plt.subplots(figsize=(13, 6.5))
    for meat in consumo_arg.columns:
        s = consumo_arg[meat].dropna()
        base = s.loc[base_year] if base_year in s.index else s.iloc[0]
        idx = s / base * 100
        ax.plot(idx.index, idx.values, linewidth=2.2,
                color=C.MEAT_COLORS.get(meat), label=meat)
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xlabel("")
    ax.set_ylabel(f"Índice base 100 = {base_year}")
    ax.grid(True, linewidth=0.6, alpha=0.5)
    ax.set_xlim(consumo_arg.index.min(), consumo_arg.index.max())
    ax.margins(y=0.05)
    ax.legend(title="Tipo de carne", ncol=2, frameon=True, loc="upper left")
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, "evolucion_carne_vacuna")


def composicion_torta(consumo_arg, year: int = C.COMPOSITION_YEAR) -> Path:
    """Figura: composición del consumo de carne (torta) para un año dado."""
    vals = consumo_arg.loc[year].dropna()
    vals = vals[vals > 0]
    total = vals.sum()
    colors = [C.MEAT_COLORS.get(m, "#999999") for m in vals.index]
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, _texts, autotexts = ax.pie(
        vals.values, labels=vals.index, colors=colors,
        autopct=lambda p: f"{p:.1f}%".replace(".", ","),
        startangle=90, counterclock=False, pctdistance=0.75,
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
        textprops=dict(fontsize=12),
    )
    # Porciones chicas (<3%): sacar el % hacia afuera para que no se solapen.
    for at, v in zip(autotexts, vals.values):
        if v / total < 0.03:
            x, y = at.get_position()
            at.set_position((x * 1.7, y * 1.7))
            at.set_color("black")
        else:
            at.set_color("white")
        at.set_fontweight("bold")
    ax.set_aspect("equal")
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, "composicion_consumo_carne")


# ---------------------------------------------------------------------------
# OCDE — comparación internacional (carne vacuna)
# ---------------------------------------------------------------------------
def vacuno_internacional_absoluto(intl) -> Path:
    """Figura: consumo vacuno internacional en términos absolutos (kg/hab)."""
    fig, ax = plt.subplots(figsize=(11, 7))
    cmap = plt.get_cmap("tab10")
    for i, pais in enumerate(intl.columns):
        s = intl[pais].dropna()
        es_arg = pais == "Argentina"
        ax.plot(s.index, s.values,
                linewidth=3 if es_arg else 1.6,
                color="black" if es_arg else cmap(i % 10),
                zorder=5 if es_arg else 3, label=pais)
    ax.set_xlabel("")
    ax.set_ylabel("Kg por habitante por año")
    ax.grid(True, linewidth=0.6, alpha=0.5)
    ax.set_xlim(intl.index.min(), intl.index.max())
    ax.legend(ncol=2, frameon=True, fontsize=9, loc="upper right")
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, "carne_vacuna_absoluto")


def vacuno_internacional_base100(intl, base_year: int = 1990) -> Path:
    """Figura: consumo vacuno internacional en índice base 100."""
    fig, ax = plt.subplots(figsize=(11, 7))
    cmap = plt.get_cmap("tab10")
    for i, pais in enumerate(intl.columns):
        s = intl[pais].dropna()
        base = s.loc[base_year] if base_year in s.index else s.iloc[0]
        idx = s / base * 100
        es_arg = pais == "Argentina"
        ax.plot(idx.index, idx.values,
                linewidth=3 if es_arg else 1.6,
                color="black" if es_arg else cmap(i % 10),
                zorder=5 if es_arg else 3, label=pais)
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xlabel("")
    ax.set_ylabel(f"Índice base 100 = {base_year}")
    ax.grid(True, linewidth=0.6, alpha=0.5)
    ax.set_xlim(intl.index.min(), intl.index.max())
    ax.legend(ncol=2, frameon=True, fontsize=9, loc="upper left")
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, "carne_vacuna_base100")


# ---------------------------------------------------------------------------
# Precios reales y esfuerzo salarial (series mensuales con sombreado)
# ---------------------------------------------------------------------------
def _serie_con_gestiones(df, col, ylabel, name, money=False) -> Path:
    fig, ax = plt.subplots(figsize=(13, 6.5))
    xmin, xmax = df["periodo"].min(), df["periodo"].max()
    handles = _shade_gestiones(ax, xmin, xmax)

    ax.plot(df["periodo"], df[col], linewidth=2, color="black", zorder=3)

    prom = float(df[col].mean())
    ax.axhline(prom, color="red", linestyle="--", linewidth=1.8, zorder=2)
    prom_txt = C.fmt_money_ar(prom, 0) if money else f"{prom:.1f} kg"
    ax.text(xmin + (xmax - xmin) / 60, prom * 1.03,
            f"Promedio histórico: {prom_txt}", fontsize=9, va="bottom", zorder=5)

    s = df[col].astype(float)
    imax, imin = s.idxmax(), s.idxmin()
    xmax_p, ymax = df.loc[imax, "periodo"], float(s.loc[imax])
    xmin_p, ymin = df.loc[imin, "periodo"], float(s.loc[imin])
    ax.scatter([xmax_p], [ymax], s=30, color="red", zorder=6)
    ax.scatter([xmin_p], [ymin], s=30, color="green", zorder=6)
    lab_max = C.fmt_money_ar(ymax, 0) if money else f"{ymax:.1f} kg"
    lab_min = C.fmt_money_ar(ymin, 0) if money else f"{ymin:.1f} kg"
    ax.annotate(f"Máximo: {lab_max}", xy=(xmax_p, ymax), xytext=(10, -90),
                textcoords="offset points", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="red", alpha=0.95),
                arrowprops=dict(arrowstyle="->", lw=1, color="red"),
                ha="left", va="bottom", zorder=7, annotation_clip=False)
    ax.annotate(f"Mínimo: {lab_min}", xy=(xmin_p, ymin), xytext=(-10, 60),
                textcoords="offset points", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="green", alpha=0.95),
                arrowprops=dict(arrowstyle="->", lw=1, color="green"),
                ha="right", va="top", zorder=7, annotation_clip=False)

    ax.set_xlabel("")
    ax.set_ylabel(ylabel)
    if money:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: C.fmt_money_ar(x, 0)))
    else:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:.0f}"))
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", labelrotation=45)
    for lbl in ax.get_xticklabels():
        lbl.set_horizontalalignment("right")
    ax.grid(True, linewidth=0.6, alpha=0.5, zorder=1)
    ax.set_xlim(xmin, xmax)
    ax.margins(y=0.05)
    ax.legend(handles=handles, title="Administraciones", ncol=3, frameon=True, loc="upper left")
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, name)


def precio_asado_real(asado_real) -> Path:
    """Figura 4: evolución del precio real del asado ($ de dic-2025)."""
    return _serie_con_gestiones(
        asado_real, "asado_real",
        "Precio del asado ($ de dic-2025 por kg)",
        "INECO_precio_asado_real_ipc_general", money=True,
    )


def kg_asado_por_salario(kg_df) -> Path:
    """Figura 5: kg de asado que compra un salario."""
    return _serie_con_gestiones(
        kg_df, "kg_asado_por_salario",
        "Kg de asado por remuneración",
        "INECO_kg_asado_por_remuneracion", money=False,
    )


# ---------------------------------------------------------------------------
# Exportaciones (absolutas — barras) y relativos
# ---------------------------------------------------------------------------
def _barras(anual, col, ylabel, name, decimals=0) -> Path:
    fig, ax = plt.subplots(figsize=(14, 6))
    x = anual["anio"].astype(int).astype(str)
    bars = ax.bar(x, anual[col], width=0.75, color="#054FAC")
    ax.set_xlabel("")
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(anual)))
    ax.set_xticklabels(x, rotation=45, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, p: C.fmt_num_ar(v, decimals))
    )
    for rect, val in zip(bars, anual[col]):
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height(),
                C.fmt_num_ar(val, decimals), ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, name)


def exportaciones_kg(anual) -> Path:
    """Figura: exportaciones de carne bovina en volumen (millones de kg)."""
    return _barras(anual, "millones_kg", "Millones de kg", "evolucion_kg", decimals=0)


def exportaciones_usd(anual) -> Path:
    """Figura: exportaciones de carne bovina en valor (miles de millones USD)."""
    return _barras(anual, "miles_millones_usd", "Miles de millones USD",
                   "evolucion_usd", decimals=1)


def exportaciones_indices(idx_df) -> Path:
    """Figura alternativa: índices INDEC de exportación de carne bovina (base 2004=100)."""
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(idx_df["periodo"], idx_df["cantidad"], linewidth=2,
            color="#054FAC", label="Cantidad (volumen)")
    ax.plot(idx_df["periodo"], idx_df["valor"], linewidth=2,
            color="#B22222", label="Valor (USD)")
    ax.set_xlabel("")
    ax.set_ylabel("Índice base 2004 = 100")
    ax.grid(True, linewidth=0.6, alpha=0.5)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", labelrotation=45)
    ax.legend(frameon=True)
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, "exportaciones_indices_2004")


def relativos(rel) -> Path:
    """Figura: kg de pollo que se compran con 1 kg de asado."""
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(rel["periodo"], rel["pollo_por_asado"], linewidth=2, color="#054FAC")
    ax.set_xlabel("")
    ax.set_ylabel("kg de pollo por 1 kg de asado")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: C.fmt_num_ar(v, 2)))
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", labelrotation=45)
    for lbl in ax.get_xticklabels():
        lbl.set_horizontalalignment("right")
    fig.tight_layout()
    _black_frame(fig)
    return _save(fig, "evolucion_relativos")
