"""Utilidades compartidas para generación de PDF (PySide6)."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from datetime import date
from html import escape

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import (
    QFont, QPainter, QPdfWriter, QPageLayout, QPageSize, QTextDocument,
)
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidget

_PDF_CSS = """
    body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 11pt;
           color: #1F1F1F; margin: 0; padding: 0; }
    .header { text-align: center; margin-bottom: 16px; }
    .brand { font-size: 18pt; font-weight: bold; letter-spacing: 1px; }
    .title { font-size: 13pt; font-weight: bold; margin-top: 4px; }
    .sub { font-size: 9pt; color: #5B5B5B; margin-top: 2px; }
    .line { border-top: 1px solid #E7E1D8; margin: 12px 0; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .items thead th { text-align: left; font-size: 10pt;
        border-bottom: 1px solid #1F1F1F; padding: 8px 8px 6px 8px; }
    .items td { border-bottom: 1px dotted #DED6CC;
        padding: 8px 8px; vertical-align: top; word-wrap: break-word; }
    .txt { word-break: break-word; }
    .num { text-align: right; white-space: nowrap; }
    .footer { margin-top: 22px; text-align: center; font-size: 9pt; color: #5B5B5B; }
"""


def _escribir_pdf(ruta: str, titulo_doc: str, html: str) -> None:
    dpi = 96
    margin_mm = 15
    writer = QPdfWriter(ruta)
    writer.setResolution(dpi)
    writer.setTitle(titulo_doc)
    writer.setCreator("Sistema Galería de Arte")
    writer.setPageSize(QPageSize(QPageSize.Letter))
    writer.setPageMargins(
        QMarginsF(margin_mm, margin_mm, margin_mm, margin_mm),
        QPageLayout.Millimeter,
    )
    page_rect = writer.pageLayout().paintRectPixels(writer.resolution())
    doc = QTextDocument()
    doc.setDocumentMargin(0)
    doc.setDefaultFont(QFont("DejaVu Sans", 11))
    doc.setHtml(html)
    doc.setTextWidth(page_rect.width())
    doc.adjustSize()
    painter = QPainter(writer)
    painter.setRenderHint(QPainter.Antialiasing)
    doc.drawContents(painter)
    painter.end()


def guardar_pdf(ventana, titulo_doc: str, nombre_sugerido: str, html: str) -> None:
    """Abre diálogo de guardado y escribe el PDF."""
    ruta, _ = QFileDialog.getSaveFileName(
        ventana, "Guardar PDF", nombre_sugerido, "PDF (*.pdf)"
    )
    if not ruta:
        return
    try:
        _escribir_pdf(ruta, titulo_doc, html)
        QMessageBox.information(ventana, "Listo", f"PDF generado correctamente:\n{ruta}")
    except Exception as e:
        QMessageBox.critical(ventana, "Error", f"No se pudo generar el PDF:\n{e}")


def vista_previa_pdf(ventana, titulo_doc: str, nombre_base: str, html: str) -> None:
    """Genera PDF temporal y lo abre con el visor del sistema."""
    try:
        tmp = tempfile.NamedTemporaryFile(
            suffix=".pdf",
            prefix=nombre_base.replace(".pdf", "_") + "_preview_",
            delete=False,
        )
        ruta = tmp.name
        tmp.close()
        _escribir_pdf(ruta, titulo_doc, html)
        if sys.platform.startswith("win"):
            os.startfile(ruta)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta])
    except Exception as e:
        QMessageBox.critical(ventana, "Error", f"No se pudo generar la vista previa:\n{e}")


def html_tabla_widget(tabla: QTableWidget, titulo: str, subtitulo: str = "") -> str:
    """Genera HTML de reporte a partir de un QTableWidget.

    Las columnas con encabezado vacío se omiten (suelen contener botones de acción).
    """
    col_count = tabla.columnCount()
    headers: list[str] = []
    include_cols: list[int] = []
    for c in range(col_count):
        h = tabla.horizontalHeaderItem(c)
        text = h.text().strip() if h else ""
        if text:
            headers.append(text)
            include_cols.append(c)

    header_row = "".join(f"<th>{escape(h)}</th>" for h in headers)

    filas_html = ""
    for r in range(tabla.rowCount()):
        cells = ""
        for c in include_cols:
            item = tabla.item(r, c)
            cells += f'<td class="txt">{escape(item.text() if item else "")}</td>'
        filas_html += f"<tr>{cells}</tr>"

    today = date.today().strftime("%Y-%m-%d")
    sub_line = escape(subtitulo) if subtitulo else f"Generado: {today}"
    return f"""
    <html><head><style>{_PDF_CSS}</style></head><body>
    <div class="page">
        <div class="header">
            <div class="brand">GALERÍA DE ARTE</div>
            <div class="title">{escape(titulo)}</div>
            <div class="sub">{sub_line}</div>
        </div>
        <div class="line"></div>
        <table class="items">
            <thead><tr>{header_row}</tr></thead>
            <tbody>{filas_html}</tbody>
        </table>
        <div class="footer">Reporte generado por Sistema Galería de Arte</div>
    </div>
    </body></html>"""
