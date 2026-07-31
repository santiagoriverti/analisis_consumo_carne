"""
Generación de las tablas del informe (DataFrame para inspección + LaTeX listo
para pegar en el documento).

Tablas:
  1. Min/máx/promedio por tipo de carne (OCDE, 1990-2025).
  5. Precio real del asado por gestión ($ de dic-2025).
  7. Esfuerzo salarial: kg de asado por salario, por gestión.
"""

from __future__ import annotations

import pandas as pd

from . import config as C


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _stats_por_gestion(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Calcula mínimo, máximo, promedio (y fechas) por gestión y una fila Global.
    ``df`` debe tener columna ``periodo`` (datetime) y la columna ``col``.
    """
    rows = []
    for nombre, ini, fin, _ in C.GESTIONES:
        tramo = df[(df["periodo"] >= ini) & (df["periodo"] <= fin)]
        if tramo.empty:
            rows.append({"Gestión": nombre})
            continue
        s = tramo[col].astype(float)
        imin, imax = s.idxmin(), s.idxmax()
        rows.append({
            "Gestión": nombre,
            "min_val": float(s.loc[imin]),
            "min_fecha": tramo.loc[imin, "periodo"].strftime("%Y-%m"),
            "max_val": float(s.loc[imax]),
            "max_fecha": tramo.loc[imax, "periodo"].strftime("%Y-%m"),
            "prom": float(s.mean()),
        })
    # Global
    s = df[col].astype(float)
    imin, imax = s.idxmin(), s.idxmax()
    rows.append({
        "Gestión": "Global",
        "min_val": float(s.loc[imin]),
        "min_fecha": df.loc[imin, "periodo"].strftime("%Y-%m"),
        "max_val": float(s.loc[imax]),
        "max_fecha": df.loc[imax, "periodo"].strftime("%Y-%m"),
        "prom": float(s.mean()),
    })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tabla 1 — OCDE
# ---------------------------------------------------------------------------
def tabla_min_max_prom_carne(consumo_arg: pd.DataFrame):
    """
    Min/máx/promedio por tipo de carne (1990-2026). Ordenada por promedio desc.
    Mismo layout que la Tabla 5 (columnas de fecha). Como la serie de la OCDE es
    ANUAL, la "fecha" es el año en que ocurre el mínimo/máximo.
    Devuelve (DataFrame_legible, latex_str).
    """
    rango = f"{consumo_arg.index.min()}-{consumo_arg.index.max()}"
    rows = []
    for meat in consumo_arg.columns:
        s = consumo_arg[meat].dropna()
        rows.append({
            "Producto": meat,
            "Mínimo": s.min(),
            "Fecha mín.": str(int(s.idxmin())),
            "Máximo": s.max(),
            "Fecha máx.": str(int(s.idxmax())),
            "Promedio": s.mean(),
        })
    df = pd.DataFrame(rows).sort_values("Promedio", ascending=False).reset_index(drop=True)

    disp = df.copy()
    for c in ["Mínimo", "Máximo", "Promedio"]:
        disp[c] = disp[c].map(lambda v: C.fmt_num_ar(v, 2))

    # LaTeX (layout análogo a la Tabla 5: l r l r l r)
    body = ""
    for _, r in df.iterrows():
        body += (
            f"{r['Producto']:<13} & {C.fmt_num_ar(r['Mínimo'], 2)} & {r['Fecha mín.']} "
            f"& {C.fmt_num_ar(r['Máximo'], 2)} & {r['Fecha máx.']} "
            f"& {C.fmt_num_ar(r['Promedio'], 2)} \\\\\n"
        )
    latex = (
        "\\begin{table}[H]\n\\centering\n\\renewcommand{\\arraystretch}{1.15}\n"
        f"\\caption{{Valores mínimo, máximo y promedio por tipo de carne ({rango})}}\n"
        "\\begin{tabular}{@{}l r l r l r@{}}\n\\toprule\n"
        "\\textbf{Producto} & \\textbf{Mínimo} & \\textbf{Año mín.} & "
        "\\textbf{Máximo} & \\textbf{Año máx.} & \\textbf{Promedio} \\\\\n\\midrule\n"
        f"{body}\\bottomrule\n\\end{{tabular}}\n\\vspace{{0.3cm}}\n"
        "\\caption*{Fuente: Instituto de Economía de UADE (INECO) en base a "
        "\\cite{OECD_AgriculturalOutlook_Data}}\n\\label{tab:precios_carne}\n\\end{table}\n"
    )
    return disp, latex


# ---------------------------------------------------------------------------
# Tabla 5 — Precio real del asado por gestión
# ---------------------------------------------------------------------------
def tabla_asado_real(asado_real: pd.DataFrame):
    """
    ``asado_real`` con columnas periodo, asado_real. Devuelve (DataFrame, latex_str).
    """
    st = _stats_por_gestion(asado_real, "asado_real")
    disp = st.copy()
    for c in ["min_val", "max_val", "prom"]:
        disp[c] = disp[c].map(lambda v: C.fmt_money_ar(v, 0))
    disp = disp.rename(columns={
        "min_val": "Mínimo", "min_fecha": "Fecha mín.",
        "max_val": "Máximo", "max_fecha": "Fecha máx.", "prom": "Promedio",
    })

    def _money_tex(v):
        return "\\$\\," + f"{v:,.0f}".replace(",", ".")

    body = ""
    for _, r in st.iterrows():
        if r["Gestión"] == "Global":
            body += "\\midrule\n"
        body += (
            f"{r['Gestión']:<22} & {_money_tex(r['min_val'])} & {r['min_fecha']} "
            f"& {_money_tex(r['max_val'])} & {r['max_fecha']} "
            f"& {_money_tex(r['prom'])} \\\\\n"
        )
    latex = (
        "\\begin{table}[H]\n\\centering\n\\renewcommand{\\arraystretch}{1.15}\n"
        "\\caption{El precio del asado en términos reales: valores mínimo, máximo y promedio}\n"
        "\\begin{tabular}{@{}l r l r l r@{}}\n\\toprule\n"
        "\\textbf{Gestión} &\n\\textbf{Mínimo} &\n\\textbf{Fecha mín.} &\n"
        "\\textbf{Máximo} &\n\\textbf{Fecha máx.} &\n\\textbf{Promedio} \\\\\n\\midrule\n"
        f"{body}\\bottomrule\n\\end{{tabular}}\\\\[0.2cm]\n"
        "\\caption*{\\small Fuente: Instituto de Economía de UADE (INECO) en base a "
        "\\cite{IPCVA_web} e \\cite{INDEC_IPC_web}}\n\\label{tab:precio_asado_real}\n\\end{table}\n"
    )
    return disp, latex


# ---------------------------------------------------------------------------
# Tabla 7 — Esfuerzo salarial (kg de asado por salario) por gestión
# ---------------------------------------------------------------------------
def tabla_esfuerzo_salarial(kg_df: pd.DataFrame):
    """
    ``kg_df`` con columnas periodo, kg_asado_por_salario. Devuelve (DataFrame, latex_str).
    """
    st = _stats_por_gestion(kg_df, "kg_asado_por_salario")
    disp = st.copy()
    for c in ["min_val", "max_val", "prom"]:
        disp[c] = disp[c].map(lambda v: C.fmt_num_ar(v, 0))
    disp = disp.rename(columns={
        "min_val": "Mínimo", "min_fecha": "Fecha mín.",
        "max_val": "Máximo", "max_fecha": "Fecha máx.", "prom": "Promedio",
    })

    body = ""
    for _, r in st.iterrows():
        if r["Gestión"] == "Global":
            body += "\\addlinespace\n"
            body += (
                f"\\textbf{{Global}}    & \\textbf{{{r['min_fecha']}}} & \\textbf{{{r['min_val']:.0f}}} & "
                f"\\textbf{{{r['max_fecha']}}} & \\textbf{{{r['max_val']:.0f}}} & "
                f"\\textbf{{{r['prom']:.0f}}} \\\\\n"
            )
        else:
            body += (
                f"{r['Gestión']:<18} & {r['min_fecha']} & {r['min_val']:.0f} & "
                f"{r['max_fecha']} & {r['max_val']:.0f} & {r['prom']:.0f} \\\\\n"
            )
    latex = (
        "\\begin{table}[H]\n\\centering\n\\renewcommand{\\arraystretch}{1.15}\n"
        "\\caption{Valores mínimos, máximos y promedio según gestión y global}\n"
        "\\begin{tabular}{@{}l@{\\hspace{0.6cm}} r r r r c@{}}\n\\toprule\n"
        "\\multirow{2}{*}{\\textbf{Gestión}} &\n\\multicolumn{2}{c}{\\textbf{Mínimo}} &\n"
        "\\multicolumn{2}{c}{\\textbf{Máximo}} &\n\\multicolumn{1}{c}{\\textbf{Promedio}} \\\\\n"
        "\\cmidrule(lr){2-3} \\cmidrule(lr){4-5} \\cmidrule(lr){6-6}\n"
        "& \\textbf{Fecha} & \\textbf{Valor} &\n  \\textbf{Fecha} & \\textbf{Valor} &\n  \\textbf{} \\\\\n"
        "\\midrule\n"
        f"{body}\\bottomrule\n\\end{{tabular}}\\\\[0.2cm]\n"
        "\\caption*{\\small Fuente: Instituto de Economía de UADE (INECO) en base a "
        "\\cite{IPCVA_web} y \\cite{SIPA_trabajo_registrado}}\n"
        "\\label{tab:valores_gestion_global}\n\\end{table}\n"
    )
    return disp, latex
