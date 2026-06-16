"""Generación de reportes PDF (RF010) usando fpdf2."""

from __future__ import annotations

from datetime import datetime, timezone

from fpdf import FPDF

from app.schemas.reportes import ResumenReporte

_TIPO_FALLA_LABEL: dict[str, str] = {
    "sin_senal": "Sin señal",
    "lentitud": "Lentitud",
    "desconexion_intermitente": "Desconexión intermitente",
    "otro": "Otro",
}

_GRANULARIDAD_LABEL: dict[str, str] = {
    "day": "día",
    "week": "semana",
    "month": "mes",
}


def _fmt_fecha(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y")


def _fmt_periodo(dt: datetime, granularidad: str) -> str:
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
             "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    if granularidad == "month":
        return f"{meses[dt.month - 1]} {dt.year}"
    if granularidad == "week":
        return f"Sem {dt.strftime('%d/%m')}"
    return dt.strftime("%d/%m/%Y")


def _seccion(pdf: FPDF, titulo: str) -> None:
    """Encabezado de sección con línea divisoria."""
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, titulo, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(203, 213, 225)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 190, pdf.get_y())
    pdf.ln(3)


def generar_reporte_pdf(resumen: ResumenReporte) -> bytes:
    """Genera el PDF del reporte SLA y devuelve los bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Encabezado ───────────────────────────────────────────────────────────
    pdf.set_fill_color(30, 64, 175)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 13, "UniNet Connect - Reporte SLA",
             new_x="LMARGIN", new_y="NEXT", fill=True, align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_fill_color(71, 85, 105)
    pdf.cell(0, 7, "ESCOM-IPN | Sistema de Monitoreo Wi-Fi",
             new_x="LMARGIN", new_y="NEXT", fill=True, align="C")

    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Helvetica", "", 9)
    pdf.ln(3)
    pdf.cell(0, 5,
             f"Periodo:  {_fmt_fecha(resumen.desde)}  -  {_fmt_fecha(resumen.hasta)}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    # ── Resumen ejecutivo ─────────────────────────────────────────────────────
    _seccion(pdf, "Resumen ejecutivo")

    mttr_txt = f"{resumen.mttr_horas} h" if resumen.mttr_horas is not None else "-"
    tasa = (
        f"{round(resumen.por_estado.resuelto / resumen.total * 100)}%"
        if resumen.total > 0 else "-"
    )
    metricas = [
        ("Total tickets", str(resumen.total)),
        ("Tasa de resolución", tasa),
        ("Activos", str(resumen.por_estado.activo)),
        ("En proceso", str(resumen.por_estado.en_proceso)),
        ("Resueltos", str(resumen.por_estado.resuelto)),
        ("Sin asignar", str(resumen.sin_asignar)),
        ("MTTR", mttr_txt),
    ]

    for i in range(0, len(metricas), 2):
        left = metricas[i]
        right = metricas[i + 1] if i + 1 < len(metricas) else None

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(45, 6, left[0] + ":")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        if right:
            pdf.cell(50, 6, left[1])
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(45, 6, right[0] + ":")
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(50, 6, right[1], new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(50, 6, left[1], new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # ── Top edificios ─────────────────────────────────────────────────────────
    if resumen.top_edificios:
        _seccion(pdf, "Top edificios con más reportes")

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(30, 7, "Código", border=1, fill=True)
        pdf.cell(120, 7, "Nombre", border=1, fill=True)
        pdf.cell(40, 7, "Tickets", border=1, fill=True, align="C",
                 new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        for edif in resumen.top_edificios:
            pdf.cell(30, 6, edif.codigo, border=1)
            pdf.cell(120, 6, edif.nombre, border=1)
            pdf.cell(40, 6, str(edif.total), border=1, align="C",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

    # ── Tipos de falla ────────────────────────────────────────────────────────
    if resumen.top_tipos:
        _seccion(pdf, "Tipos de falla")

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(150, 7, "Tipo", border=1, fill=True)
        pdf.cell(40, 7, "Tickets", border=1, fill=True, align="C",
                 new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        for t in resumen.top_tipos:
            label = _TIPO_FALLA_LABEL.get(str(t.tipo), str(t.tipo))
            pdf.cell(150, 6, label, border=1)
            pdf.cell(40, 6, str(t.total), border=1, align="C",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

    # ── Serie temporal ────────────────────────────────────────────────────────
    if resumen.serie_temporal:
        gran_lbl = _GRANULARIDAD_LABEL.get(resumen.granularidad, resumen.granularidad)
        _seccion(pdf, f"Tickets por {gran_lbl}")

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(150, 7, "Periodo", border=1, fill=True)
        pdf.cell(40, 7, "Tickets", border=1, fill=True, align="C",
                 new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        for punto in resumen.serie_temporal:
            periodo_lbl = _fmt_periodo(punto.fecha, resumen.granularidad)
            pdf.cell(150, 6, periodo_lbl, border=1)
            pdf.cell(40, 6, str(punto.total), border=1, align="C",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

    # ── Pie de página ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(148, 163, 184)
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    pdf.cell(0, 6, f"Generado: {now}  |  UniNet Connect / ESCOM-IPN", align="C")

    return bytes(pdf.output())
