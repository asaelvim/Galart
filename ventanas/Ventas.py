from __future__ import annotations

import os
import subprocess
import tempfile
import sys
from contextlib import contextmanager
from html import escape
from typing import Any, Dict, List, Optional, Tuple

from config.conexion import obtener_conexion
from ventanas.Clientes import ClientesVentana
from ventanas.Vendedores import VendedoresVentana
from ventanas.Artistas import ArtistasVentana
from ventanas.Pinturas import PinturasVentana
from ventanas.Cotizaciones import CotizacionesVentana
from ventanas.RealizarVenta import RealizarVentaDialog

from PySide6.QtCore import Qt, QDate, QMarginsF, QRegularExpression
from PySide6.QtGui import QFont, QPainter, QPdfWriter, QPageSize, QPageLayout, QRegularExpressionValidator, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# =========================
# Paleta Opción A (Minimal Luxe)
# =========================
BG = "#F7F4EF"
SURFACE = "#FFFFFF"
BORDER = "#E7E1D8"
TEXT = "#2A2A2A"
MUTED = "#5B5B5B"

PRIMARY = "#111827"
GOLD = "#C8A24A"

BTN_BG = "#F6F1EA"
BTN_BORDER = "#DED6CC"
BTN_TEXT = "#2A2A2A"

_PDF_CSS = """
    body {
        font-family: "DejaVu Sans", Arial, sans-serif;
        font-size: 11pt;
        color: #1F1F1F;
        margin: 0;
        padding: 0;
    }
    .header { text-align: center; margin-bottom: 16px; }
    .brand { font-size: 18pt; font-weight: bold; letter-spacing: 1px; }
    .title { font-size: 13pt; font-weight: bold; margin-top: 4px; }
    .sub { font-size: 9pt; color: #5B5B5B; margin-top: 2px; }
    .line { border-top: 1px solid #E7E1D8; margin: 12px 0; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .info td { padding: 4px 0; vertical-align: top; word-wrap: break-word; }
    .info .label { width: 14%; font-weight: bold; }
    .info .value { width: 36%; }
    .items thead th {
        text-align: left; font-size: 10pt;
        border-bottom: 1px solid #1F1F1F; padding: 8px 8px 6px 8px;
    }
    .items td {
        border-bottom: 1px dotted #DED6CC;
        padding: 8px 8px; vertical-align: top; word-wrap: break-word;
    }
    .txt { word-break: break-word; }
    .num { text-align: right; white-space: nowrap; }
    .summary { margin-top: 16px; width: 100%; border-collapse: collapse; }
    .summary td { padding: 4px 8px; }
    .summary .label { width: 82%; text-align: right; font-weight: bold; font-size: 12pt; }
    .summary .value { width: 18%; text-align: right; font-size: 13pt; font-weight: bold; white-space: nowrap; }
    .footer { margin-top: 22px; text-align: center; font-size: 9pt; color: #5B5B5B; }
"""

_IVA_RATE = 0.16


@contextmanager
def db():
    conn = obtener_conexion()
    if conn is None:
        raise RuntimeError("No se pudo conectar a la base de datos.")
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _exec(cur, sql, params=()):
    cur.execute(sql, params)


# =========================
# Diálogo post-venta: Nota de Venta / Factura
# =========================
class _PostVentaDialog(QDialog):
    """Diálogo que aparece tras completar una venta con opciones de documento PDF."""

    def __init__(self, venta_id: int, forma_pago: str, cambio: float, parent=None):
        super().__init__(parent)
        self.venta_id = venta_id
        self._venta = None
        self._detalles: List[Any] = []

        self.setWindowTitle("Venta concretada")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setObjectName("PostVentaDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        lbl_titulo = QLabel("✓ Venta concretada")
        lbl_titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_titulo.setAlignment(Qt.AlignHCenter)
        layout.addWidget(lbl_titulo)

        msg = f"Venta #{venta_id} registrada correctamente."
        if forma_pago == "efectivo" and cambio > 0:
            msg += f"\nCambio entregado: ${cambio:.2f}"
        lbl_info = QLabel(msg)
        lbl_info.setAlignment(Qt.AlignHCenter)
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        lbl_docs = QLabel("Documentos de la venta:")
        lbl_docs.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        layout.addWidget(lbl_docs)

        nota_row = QHBoxLayout()
        nota_row.addWidget(QLabel("Nota de Venta:"))
        nota_row.addStretch(1)
        btn_prev_nota = QPushButton("Vista Previa")
        btn_prev_nota.setObjectName("DocBtn")
        btn_prev_nota.setCursor(Qt.PointingHandCursor)
        btn_prev_nota.clicked.connect(self._preview_nota)
        btn_gen_nota = QPushButton("Generar PDF")
        btn_gen_nota.setObjectName("DocBtn")
        btn_gen_nota.setCursor(Qt.PointingHandCursor)
        btn_gen_nota.clicked.connect(self._generar_nota)
        nota_row.addWidget(btn_prev_nota)
        nota_row.addSpacing(6)
        nota_row.addWidget(btn_gen_nota)
        layout.addLayout(nota_row)

        factura_row = QHBoxLayout()
        factura_row.addWidget(QLabel("Factura:"))
        factura_row.addStretch(1)
        btn_prev_fact = QPushButton("Vista Previa")
        btn_prev_fact.setObjectName("DocBtn")
        btn_prev_fact.setCursor(Qt.PointingHandCursor)
        btn_prev_fact.clicked.connect(self._preview_factura)
        btn_gen_fact = QPushButton("Generar PDF")
        btn_gen_fact.setObjectName("DocBtn")
        btn_gen_fact.setCursor(Qt.PointingHandCursor)
        btn_gen_fact.clicked.connect(self._generar_factura)
        factura_row.addWidget(btn_prev_fact)
        factura_row.addSpacing(6)
        factura_row.addWidget(btn_gen_fact)
        layout.addLayout(factura_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        layout.addWidget(sep2)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignRight)

        self.setStyleSheet("""
            QDialog#PostVentaDialog {
                background: #F7F4EF;
                font-family: "Segoe UI";
                font-size: 10pt;
                color: #2A2A2A;
            }
            QLabel { color: #2A2A2A; }
            QPushButton#DocBtn {
                background: #F6F1EA;
                color: #2A2A2A;
                border: 1px solid #DED6CC;
                border-radius: 8px;
                padding: 6px 14px;
                min-width: 110px;
            }
            QPushButton#DocBtn:hover { border: 1px solid #C8A24A; background: #F7F4EF; }
            QPushButton#DocBtn:pressed { background: #EFE7DD; }
            QPushButton {
                background: #F6F1EA;
                color: #2A2A2A;
                border: 1px solid #DED6CC;
                border-radius: 8px;
                padding: 6px 14px;
            }
            QPushButton:hover { border: 1px solid #C8A24A; }
        """)

        self._cargar_datos()

    def _cargar_datos(self):
        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(
                    cur,
                    "SELECT v.id_venta, v.fecha, v.forma_pago, v.total, "
                    "c.nombre AS cliente, c.correo, c.telefono, "
                    "ven.nombre AS vendedor "
                    "FROM Ventas v "
                    "LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente "
                    "LEFT JOIN Vendedores ven ON ven.id_vendedor = v.id_vendedor "
                    "WHERE v.id_venta = ?",
                    (self.venta_id,),
                )
                self._venta = cur.fetchone()
                _exec(
                    cur,
                    "SELECT p.titulo, dv.cantidad, dv.subtotal, p.precio "
                    "FROM DetalleVenta dv "
                    "LEFT JOIN Pinturas p ON p.id_pintura = dv.id_pintura "
                    "WHERE dv.id_venta = ? "
                    "ORDER BY dv.id_detalle ASC",
                    (self.venta_id,),
                )
                self._detalles = cur.fetchall()
        except Exception as e:
            QMessageBox.warning(
                self, "Advertencia",
                f"No se pudo cargar la venta para documentos:\n{e}"
            )

    def _fmt_fecha(self, valor):
        if valor is None:
            return "-"
        try:
            return valor.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(valor)

    def _filas_html(self):
        filas = ""
        for d in self._detalles:
            titulo = escape(str(d.titulo or ""))
            cantidad = int(d.cantidad or 0)
            precio_unitario = float(d.precio or 0)
            subtotal = float(d.subtotal or 0)
            filas += (
                f"<tr>"
                f"<td class='txt'>{titulo}</td>"
                f"<td class='num'>{cantidad}</td>"
                f"<td class='num'>${precio_unitario:,.2f}</td>"
                f"<td class='num'>${subtotal:,.2f}</td>"
                f"</tr>"
            )
        return filas

    def _info_cabecera(self):
        v = self._venta
        fecha = escape(self._fmt_fecha(v.fecha))
        cliente = escape(str(getattr(v, "cliente", "") or "-"))
        correo = escape(str(getattr(v, "correo", "") or "-"))
        telefono = escape(str(getattr(v, "telefono", "") or "-"))
        vendedor = escape(str(getattr(v, "vendedor", "") or "-"))
        forma_pago = escape(str(getattr(v, "forma_pago", "") or "-"))
        return fecha, cliente, correo, telefono, vendedor, forma_pago

    def _armar_html_nota(self):
        if not self._venta:
            return "<html><body>Sin datos de venta.</body></html>"
        v = self._venta
        fecha, cliente, correo, telefono, vendedor, forma_pago = self._info_cabecera()
        total = float(getattr(v, "total", 0) or 0)
        filas = self._filas_html()
        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">NOTA DE VENTA</div>
                <div class="sub">Folio #{v.id_venta}</div>
            </div>
            <div class="line"></div>
            <table class="info">
                <tr>
                    <td class="label">Fecha:</td><td class="value">{fecha}</td>
                    <td class="label">Cliente:</td><td class="value">{cliente}</td>
                </tr>
                <tr>
                    <td class="label">Correo:</td><td class="value">{correo}</td>
                    <td class="label">Teléfono:</td><td class="value">{telefono}</td>
                </tr>
                <tr>
                    <td class="label">Vendedor:</td><td class="value">{vendedor}</td>
                    <td class="label">Pago:</td><td class="value">{forma_pago}</td>
                </tr>
            </table>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:52%;">Pintura</th>
                        <th style="width:12%; text-align:right;">Cant.</th>
                        <th style="width:18%; text-align:right;">P.U.</th>
                        <th style="width:18%; text-align:right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>{filas}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label">TOTAL:</td>
                    <td class="value">${total:,.2f}</td>
                </tr>
            </table>
            <div class="footer">Gracias por su compra. Conserve este comprobante.</div>
        </div>
        </body></html>"""

    def _armar_html_factura(self):
        if not self._venta:
            return "<html><body>Sin datos de venta.</body></html>"
        v = self._venta
        fecha, cliente, correo, telefono, vendedor, forma_pago = self._info_cabecera()
        total_bruto = float(getattr(v, "total", 0) or 0)
        subtotal_sin_iva = total_bruto / (1 + _IVA_RATE)
        iva = total_bruto - subtotal_sin_iva
        filas = self._filas_html()
        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">FACTURA</div>
                <div class="sub">Folio #{v.id_venta}</div>
            </div>
            <div class="line"></div>
            <table class="info">
                <tr>
                    <td class="label">Fecha:</td><td class="value">{fecha}</td>
                    <td class="label">Cliente:</td><td class="value">{cliente}</td>
                </tr>
                <tr>
                    <td class="label">Correo:</td><td class="value">{correo}</td>
                    <td class="label">Teléfono:</td><td class="value">{telefono}</td>
                </tr>
                <tr>
                    <td class="label">Vendedor:</td><td class="value">{vendedor}</td>
                    <td class="label">Pago:</td><td class="value">{forma_pago}</td>
                </tr>
            </table>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:52%;">Pintura</th>
                        <th style="width:12%; text-align:right;">Cant.</th>
                        <th style="width:18%; text-align:right;">P.U.</th>
                        <th style="width:18%; text-align:right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>{filas}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label" style="font-size:11pt; font-weight:normal;">Subtotal (sin IVA):</td>
                    <td class="value" style="font-size:11pt;">${subtotal_sin_iva:,.2f}</td>
                </tr>
                <tr>
                    <td class="label" style="font-size:11pt; font-weight:normal;">IVA ({int(_IVA_RATE * 100)}%):</td>
                    <td class="value" style="font-size:11pt;">${iva:,.2f}</td>
                </tr>
                <tr>
                    <td class="label">TOTAL:</td>
                    <td class="value">${total_bruto:,.2f}</td>
                </tr>
            </table>
            <div class="footer">Gracias por su compra. Conserve esta factura.</div>
        </div>
        </body></html>"""

    def _escribir_pdf(self, ruta: str, titulo: str, html: str) -> None:
        dpi, margin_mm = 96, 15
        writer = QPdfWriter(ruta)
        writer.setResolution(dpi)
        writer.setTitle(titulo)
        writer.setCreator("Sistema Galería de Arte")
        writer.setPageSize(QPageSize(QPageSize.Letter))
        writer.setPageMargins(
            QMarginsF(margin_mm, margin_mm, margin_mm, margin_mm),
            QPageLayout.Millimeter,
        )
        rect = writer.pageLayout().paintRectPixels(writer.resolution())
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setHtml(html)
        doc.setTextWidth(rect.width())
        doc.adjustSize()
        painter = QPainter(writer)
        painter.setRenderHint(QPainter.Antialiasing)
        doc.drawContents(painter)
        painter.end()

    def _vista_previa(self, titulo: str, nombre_base: str, html: str) -> None:
        try:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf",
                prefix=nombre_base + "_preview_",
                delete=False,
            )
            ruta = tmp.name
            tmp.close()
            self._escribir_pdf(ruta, titulo, html)
            if sys.platform.startswith("win"):
                os.startfile(ruta)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar la vista previa:\n{e}")

    def _guardar_pdf(self, titulo: str, nombre_sugerido: str, html: str) -> None:
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", nombre_sugerido, "PDF (*.pdf)"
        )
        if not ruta:
            return
        try:
            self._escribir_pdf(ruta, titulo, html)
            QMessageBox.information(self, "Listo", f"PDF generado correctamente:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF:\n{e}")

    def _preview_nota(self):
        self._vista_previa(
            f"Nota de Venta #{self.venta_id}",
            f"nota_venta_{self.venta_id}",
            self._armar_html_nota(),
        )

    def _generar_nota(self):
        self._guardar_pdf(
            f"Nota de Venta #{self.venta_id}",
            f"nota_venta_{self.venta_id}.pdf",
            self._armar_html_nota(),
        )

    def _preview_factura(self):
        self._vista_previa(
            f"Factura #{self.venta_id}",
            f"factura_{self.venta_id}",
            self._armar_html_factura(),
        )

    def _generar_factura(self):
        self._guardar_pdf(
            f"Factura #{self.venta_id}",
            f"factura_{self.venta_id}.pdf",
            self._armar_html_factura(),
        )


# =========================
# Repositorio Ventas
# =========================
class VentasRepo:
    def fetch_all(self) -> List[Tuple[int, str, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT v.id_venta, "
                "COALESCE(cl.nombre, '') AS cliente, "
                "COALESCE(vd.nombre, '') AS vendedor, "
                "v.fecha, v.total, COALESCE(v.forma_pago, '') AS forma_pago "
                "FROM Ventas v "
                "LEFT JOIN Clientes cl ON v.id_cliente = cl.id_cliente "
                "LEFT JOIN Vendedores vd ON v.id_vendedor = vd.id_vendedor "
                "ORDER BY v.id_venta",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                vid = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                vendedor = str(r[2]) if r[2] else ""
                fecha = str(r[3])[:10] if r[3] else ""
                total = f"{float(r[4]):.2f}" if r[4] is not None else "0.00"
                forma_pago = str(r[5]).strip().capitalize() if r[5] else ""
                result.append((vid, cliente, vendedor, fecha, total, forma_pago))
            return result

    def fetch_by_id(self, venta_id: int) -> List[Tuple[int, str, str, str, str, int, int, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT v.id_venta, "
                "COALESCE(cl.nombre, '') AS cliente, "
                "COALESCE(vd.nombre, '') AS vendedor, "
                "v.fecha, v.total, v.id_cliente, v.id_vendedor, COALESCE(v.forma_pago, '') AS forma_pago "
                "FROM Ventas v "
                "LEFT JOIN Clientes cl ON v.id_cliente = cl.id_cliente "
                "LEFT JOIN Vendedores vd ON v.id_vendedor = vd.id_vendedor "
                "WHERE v.id_venta = ?",
                (venta_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                vid = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                vendedor = str(r[2]) if r[2] else ""
                fecha = str(r[3])[:10] if r[3] else ""
                total = f"{float(r[4]):.2f}" if r[4] is not None else "0.00"
                id_cliente = int(r[5]) if r[5] is not None else 0
                id_vendedor = int(r[6]) if r[6] is not None else 0
                forma_pago = str(r[7]).strip().capitalize() if r[7] else ""
                result.append((vid, cliente, vendedor, fecha, total, id_cliente, id_vendedor, forma_pago))
            return result

    def search_by_detail_name(self, texto: str, campo: str) -> List[Tuple[int, str, str, str, str, str]]:
        like = f"%{texto}%"
        if campo == "Artista":
            where_clause = "COALESCE(a.nombre, '') LIKE ?"
        else:
            where_clause = "COALESCE(p.titulo, '') LIKE ?"

        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                f"SELECT DISTINCT v.id_venta, "
                f"COALESCE(cl.nombre, '') AS cliente, "
                f"COALESCE(vd.nombre, '') AS vendedor, "
                f"v.fecha, v.total, COALESCE(v.forma_pago, '') AS forma_pago "
                f"FROM Ventas v "
                f"LEFT JOIN Clientes cl ON v.id_cliente = cl.id_cliente "
                f"LEFT JOIN Vendedores vd ON v.id_vendedor = vd.id_vendedor "
                f"INNER JOIN DetalleVenta d ON v.id_venta = d.id_venta "
                f"LEFT JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                f"LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                f"WHERE {where_clause} "
                f"ORDER BY v.id_venta",
                (like,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                vid = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                vendedor = str(r[2]) if r[2] else ""
                fecha = str(r[3])[:10] if r[3] else ""
                total = f"{float(r[4]):.2f}" if r[4] is not None else "0.00"
                forma_pago = str(r[5]).strip().capitalize() if r[5] else ""
                result.append((vid, cliente, vendedor, fecha, total, forma_pago))
            return result

    def insert(self, id_cliente: int, id_vendedor: int, fecha: str, total: float, forma_pago: str = "efectivo") -> int:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Ventas (id_cliente, id_vendedor, fecha, total, forma_pago) "
                "VALUES (?, ?, ?, ?, ?)",
                (id_cliente, id_vendedor, fecha, total, forma_pago),
            )
            new_id = cur.lastrowid
            conn.commit()
            return new_id

    def update(self, venta_id: int, id_cliente: int, id_vendedor: int, fecha: str, total: float, forma_pago: str = "efectivo") -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Ventas SET id_cliente = ?, id_vendedor = ?, fecha = ?, total = ?, forma_pago = ? "
                "WHERE id_venta = ?",
                (id_cliente, id_vendedor, fecha, total, forma_pago, venta_id),
            )
            conn.commit()

    def delete(self, venta_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleVenta WHERE id_venta = ?", (venta_id,))
            _exec(cur, "DELETE FROM Ventas WHERE id_venta = ?", (venta_id,))
            conn.commit()


# =========================
# Repositorio DetalleVenta
# =========================
class DetalleVentaRepo:
    def fetch_by_venta(self, venta_id: int) -> List[Tuple[int, str, str, int, str, int]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT d.id_detalle, COALESCE(p.titulo, '') AS titulo, "
                "COALESCE(a.nombre, '') AS artista, "
                "d.cantidad, d.subtotal, d.id_pintura "
                "FROM DetalleVenta d "
                "LEFT JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "WHERE d.id_venta = ? "
                "ORDER BY d.id_detalle",
                (venta_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_detalle = int(r[0])
                titulo = str(r[1]) if r[1] else ""
                artista = str(r[2]) if r[2] else ""
                cantidad = int(r[3]) if r[3] is not None else 0
                subtotal = f"{float(r[4]):.2f}" if r[4] is not None else "0.00"
                id_pintura = int(r[5]) if r[5] is not None else 0
                result.append((id_detalle, titulo, artista, cantidad, subtotal, id_pintura))
            return result


# =========================
# Repositorio Cotizaciones
# =========================
class CotizacionesImportRepo:
    def fetch_all(self) -> List[Tuple[int, str, str, str, int, int]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_cotizacion, "
                "COALESCE(cl.nombre, '') AS cliente, "
                "c.fecha, c.total, c.id_cliente, c.id_vendedor "
                "FROM Cotizaciones c "
                "LEFT JOIN Clientes cl ON c.id_cliente = cl.id_cliente "
                "WHERE COALESCE(c.concretada, 0) = 0 "
                "ORDER BY c.id_cotizacion",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_cotizacion = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                fecha = str(r[2])[:10] if r[2] else ""
                total = f"{float(r[3]):.2f}" if r[3] is not None else "0.00"
                id_cliente = int(r[4]) if r[4] is not None else 0
                id_vendedor = int(r[5]) if r[5] is not None else 0
                result.append((id_cotizacion, cliente, fecha, total, id_cliente, id_vendedor))
            return result

    def marcar_concretada(self, cotizacion_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Cotizaciones SET concretada = 1 WHERE id_cotizacion = ?",
                (cotizacion_id,),
            )
            conn.commit()

    def fetch_by_id(self, cotizacion_id: int) -> List[Tuple[int, str, str, str, int]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_cotizacion, "
                "COALESCE(cl.nombre, '') AS cliente, "
                "c.fecha, c.total, c.id_cliente "
                "FROM Cotizaciones c "
                "LEFT JOIN Clientes cl ON c.id_cliente = cl.id_cliente "
                "WHERE c.id_cotizacion = ?",
                (cotizacion_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_cotizacion = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                fecha = str(r[2])[:10] if r[2] else ""
                total = f"{float(r[3]):.2f}" if r[3] is not None else "0.00"
                id_cliente = int(r[4]) if r[4] is not None else 0
                result.append((id_cotizacion, cliente, fecha, total, id_cliente))
            return result

    def fetch_detalle(self, cotizacion_id: int) -> List[Tuple[int, str, str, int, float, float]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT d.id_pintura, COALESCE(p.titulo, '') AS titulo, "
                "COALESCE(a.nombre, '') AS artista, "
                "d.cantidad, d.precio_unitario, d.subtotal "
                "FROM DetalleCotizacion d "
                "LEFT JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "WHERE d.id_cotizacion = ? "
                "ORDER BY d.id_detalle",
                (cotizacion_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_pintura = int(r[0])
                titulo = str(r[1]) if r[1] else ""
                artista = str(r[2]) if r[2] else ""
                cantidad = int(r[3]) if r[3] is not None else 0
                precio_unitario = float(r[4]) if r[4] is not None else 0.0
                subtotal = float(r[5]) if r[5] is not None else 0.0
                result.append((id_pintura, titulo, artista, cantidad, precio_unitario, subtotal))
            return result


# =========================
# Repositorio Inventario
# =========================
class InventarioRepo:
    def get_disponible(self, id_pintura: int) -> int:
        with db() as conn:
            cur = conn.cursor()
            return self.get_disponible_cursor(cur, id_pintura)

    def get_disponible_cursor(self, cur, id_pintura: int) -> int:
        _exec(
            cur,
            "SELECT COALESCE(SUM(cantidad), 0) "
            "FROM Inventario "
            "WHERE id_pintura = ?",
            (id_pintura,),
        )
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def descontar_cursor(self, cur, id_pintura: int, cantidad: int) -> None:
        restante = int(cantidad)

        _exec(
            cur,
            "SELECT id_inventario, cantidad "
            "FROM Inventario "
            "WHERE id_pintura = ? AND cantidad > 0 "
            "ORDER BY id_inventario",
            (id_pintura,),
        )
        rows = cur.fetchall()

        for id_inventario, cant_actual in rows:
            if restante <= 0:
                break

            cant_actual = int(cant_actual)
            tomar = min(cant_actual, restante)
            nueva = cant_actual - tomar

            _exec(
                cur,
                "UPDATE Inventario SET cantidad = ? WHERE id_inventario = ?",
                (nueva, int(id_inventario)),
            )
            restante -= tomar

        if restante > 0:
            raise RuntimeError(f"No hay inventario suficiente para la pintura ID {id_pintura}.")

    def restaurar_cursor(self, cur, id_pintura: int, cantidad: int) -> None:
        _exec(
            cur,
            "SELECT id_inventario, cantidad "
            "FROM Inventario "
            "WHERE id_pintura = ? "
            "ORDER BY id_inventario "
            "LIMIT 1",
            (id_pintura,),
        )
        row = cur.fetchone()

        if row:
            id_inventario, cant_actual = row
            nueva = int(cant_actual) + int(cantidad)
            _exec(
                cur,
                "UPDATE Inventario SET cantidad = ? WHERE id_inventario = ?",
                (nueva, int(id_inventario)),
            )
        else:
            _exec(
                cur,
                "INSERT INTO Inventario (id_pintura, cantidad) VALUES (?, ?)",
                (id_pintura, int(cantidad)),
            )


# =========================
# UI Principal para VENTAS
# =========================
class VentasVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.ventana_clientes = None
        self.ventana_vendedores = None
        self.ventana_artistas = None
        self.ventana_cotizaciones = None
        self.ventana_pinturas = None

        self.setWindowTitle("Gestión de Ventas")
        self.setMinimumSize(1780, 860)

        self.repo = VentasRepo()
        self.detalle_repo = DetalleVentaRepo()
        self.cotizacion_repo = CotizacionesImportRepo()
        self.inventario_repo = InventarioRepo()

        self.current_id: Optional[int] = None
        self._cotizacion_id_cargada: Optional[int] = None
        self._detail_lines: List[Tuple[int, str, str, int, float, float]] = []

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(14)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 18)
        card_layout.setSpacing(10)

        title = QLabel("Gestión de Ventas")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        self._lbl_caja_cerrada = QLabel("🔒 Caja cerrada — el vendedor seleccionado no puede registrar ventas hoy.")
        self._lbl_caja_cerrada.setAlignment(Qt.AlignHCenter)
        self._lbl_caja_cerrada.setStyleSheet(
            "color: #B45309; background: #FEF3C7; border: 1px solid #F59E0B;"
            " border-radius: 8px; padding: 6px 12px; font-weight: 600;"
        )
        self._lbl_caja_cerrada.setVisible(False)
        card_layout.addWidget(self._lbl_caja_cerrada)

        row_cliente = QHBoxLayout()
        row_cliente.setSpacing(12)
        row_cliente.addStretch(1)
        lbl_cliente = QLabel("Cliente:")
        lbl_cliente.setObjectName("MutedLabel")
        self.cmbCliente = QComboBox()
        self.cmbCliente.setObjectName("Combo")
        self.cmbCliente.setFixedWidth(260)
        self.btnAdministrarClientes = self._button("Administrar clientes", self.abrir_clientes, wide=True)
        self.btnAdministrarClientes.setFixedWidth(190)
        row_cliente.addWidget(lbl_cliente)
        row_cliente.addWidget(self.cmbCliente)
        row_cliente.addWidget(self.btnAdministrarClientes)
        row_cliente.addStretch(1)
        card_layout.addLayout(row_cliente)

        row_vendedor = QHBoxLayout()
        row_vendedor.setSpacing(12)
        row_vendedor.addStretch(1)
        lbl_vendedor = QLabel("Vendedor:")
        lbl_vendedor.setObjectName("MutedLabel")
        self.cmbVendedor = QComboBox()
        self.cmbVendedor.setObjectName("Combo")
        self.cmbVendedor.setFixedWidth(260)
        self.cmbVendedor.currentIndexChanged.connect(self._actualizar_estado_caja)
        self.btnAdministrarVendedores = self._button("Administrar vendedores", self.abrir_vendedores, wide=True)
        self.btnAdministrarVendedores.setFixedWidth(200)
        row_vendedor.addWidget(lbl_vendedor)
        row_vendedor.addWidget(self.cmbVendedor)
        row_vendedor.addWidget(self.btnAdministrarVendedores)
        row_vendedor.addStretch(1)
        card_layout.addLayout(row_vendedor)

        row_cot = QHBoxLayout()
        row_cot.setSpacing(12)
        row_cot.addStretch(1)
        lbl_cot = QLabel("Cotización:")
        lbl_cot.setObjectName("MutedLabel")
        self.cmbCotizacion = QComboBox()
        self.cmbCotizacion.setObjectName("Combo")
        self.cmbCotizacion.setFixedWidth(340)
        self.btnAdministrarCotizaciones = self._button(
            "Administrar cotizaciones", self.abrir_cotizaciones, wide=True
        )
        self.btnAdministrarCotizaciones.setFixedWidth(220)
        self.btnImportarCotizacion = self._button("Importar cotización", self.on_import_cotizacion, wide=True)
        row_cot.addWidget(lbl_cot)
        row_cot.addWidget(self.cmbCotizacion)
        row_cot.addWidget(self.btnAdministrarCotizaciones)
        row_cot.addWidget(self.btnImportarCotizacion)
        row_cot.addStretch(1)
        card_layout.addLayout(row_cot)

        row_fecha = QHBoxLayout()
        row_fecha.setSpacing(12)
        row_fecha.addStretch(1)
        lbl_fecha = QLabel("Fecha:")
        lbl_fecha.setObjectName("MutedLabel")
        self.dateFecha = QDateEdit()
        self.dateFecha.setObjectName("dateFecha")
        self.dateFecha.setFixedWidth(200)
        self.dateFecha.setCalendarPopup(True)
        self.dateFecha.setDisplayFormat("yyyy-MM-dd")
        self.dateFecha.setDate(QDate.currentDate())
        row_fecha.addWidget(lbl_fecha)
        row_fecha.addWidget(self.dateFecha)
        row_fecha.addStretch(1)
        card_layout.addLayout(row_fecha)

        sep1 = QFrame()
        sep1.setObjectName("Separator")
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        card_layout.addWidget(sep1)

        row_filtros = QHBoxLayout()
        row_filtros.setSpacing(12)
        row_filtros.addStretch(1)

        lbl_artista = QLabel("Artista:")
        lbl_artista.setObjectName("MutedLabel")
        self.cmbArtista = QComboBox()
        self.cmbArtista.setObjectName("Combo")
        self.cmbArtista.setFixedWidth(250)
        self.cmbArtista.currentIndexChanged.connect(self.on_artista_changed)

        self.btnAdministrarArtistas = self._button("Administrar artistas", self.abrir_artistas, wide=True)
        self.btnAdministrarArtistas.setFixedWidth(190)

        lbl_pintura = QLabel("Pintura:")
        lbl_pintura.setObjectName("MutedLabel")
        self.cmbPintura = QComboBox()
        self.cmbPintura.setObjectName("Combo")
        self.cmbPintura.setFixedWidth(390)

        self.btnAdministrarPinturas = self._button("Administrar pinturas", self.abrir_pinturas, wide=True)
        self.btnAdministrarPinturas.setFixedWidth(190)

        lbl_cantidad = QLabel("Cantidad:")
        lbl_cantidad.setObjectName("MutedLabel")
        self.spnCantidad = QSpinBox()
        self.spnCantidad.setObjectName("SpinBox")
        self.spnCantidad.setMinimum(1)
        self.spnCantidad.setMaximum(99999)
        self.spnCantidad.setFixedWidth(100)
        self.spnCantidad.setValue(1)

        self.btnAgregarLinea = self._button("Agregar línea", self.on_add_line)

        row_filtros.addWidget(lbl_artista)
        row_filtros.addWidget(self.cmbArtista)
        row_filtros.addWidget(self.btnAdministrarArtistas)
        row_filtros.addSpacing(16)
        row_filtros.addWidget(lbl_pintura)
        row_filtros.addWidget(self.cmbPintura)
        row_filtros.addWidget(self.btnAdministrarPinturas)
        row_filtros.addWidget(lbl_cantidad)
        row_filtros.addWidget(self.spnCantidad)
        row_filtros.addWidget(self.btnAgregarLinea)
        row_filtros.addStretch(1)
        card_layout.addLayout(row_filtros)

        detail_frame = QFrame()
        detail_frame.setObjectName("TableFrame")
        df = QVBoxLayout(detail_frame)
        df.setContentsMargins(10, 10, 10, 10)

        self.detail_table = QTableWidget(0, 5)
        self.detail_table.setObjectName("Table")
        self.detail_table.setHorizontalHeaderLabels(["Pintura", "Artista", "Cantidad", "Subtotal", ""])
        self.detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.verticalHeader().setVisible(False)
        detail_header = self.detail_table.horizontalHeader()
        detail_header.setSectionResizeMode(0, QHeaderView.Stretch)
        detail_header.setSectionResizeMode(1, QHeaderView.Stretch)
        detail_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        detail_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        detail_header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.detail_table.setColumnWidth(4, 50)
        self.detail_table.setMaximumHeight(180)
        df.addWidget(self.detail_table)
        card_layout.addWidget(detail_frame)

        row_totals = QHBoxLayout()
        row_totals.addStretch(1)
        totals_widget = QWidget()
        totals_layout = QVBoxLayout(totals_widget)
        totals_layout.setSpacing(4)
        totals_layout.setContentsMargins(0, 0, 0, 0)
        self.lblSubtotal = QLabel("Subtotal: $0.00")
        self.lblSubtotal.setObjectName("MutedLabel")
        self.lblTotal = QLabel("Total: $0.00")
        self.lblTotal.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        totals_layout.addWidget(self.lblSubtotal)
        totals_layout.addWidget(self.lblTotal)
        row_totals.addWidget(totals_widget)
        card_layout.addLayout(row_totals)

        row_actions = QHBoxLayout()
        row_actions.setSpacing(12)
        row_actions.addStretch(1)
        self.btnGuardar = self._button("Realizar Venta", self.on_realizar_venta, wide=True)
        self.btnNueva = self._button("Nueva Venta", self.on_nueva, wide=True)
        self.btnEliminar = self._button("Eliminar Venta", self.on_eliminar, wide=True)
        self.btnEliminar.setEnabled(False)
        row_actions.addWidget(self.btnGuardar)
        row_actions.addWidget(self.btnNueva)
        row_actions.addWidget(self.btnEliminar)
        row_actions.addStretch(1)
        card_layout.addLayout(row_actions)

        sep2 = QFrame()
        sep2.setObjectName("Separator")
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        card_layout.addWidget(sep2)

        row_buscar = QHBoxLayout()
        row_buscar.setSpacing(12)
        row_buscar.addStretch(1)
        lbl_buscar_id = QLabel("Buscar por ID:")
        lbl_buscar_id.setObjectName("MutedLabel")
        self.txtBuscarID = QLineEdit()
        self.txtBuscarID.setObjectName("SearchBox")
        self.txtBuscarID.setFixedWidth(160)
        self.btnBuscarID = self._button("Buscar ID", self.on_buscar_id)
        self.btnMostrarTodas = self._button("Mostrar todas", self.on_mostrar_todas, wide=True)
        row_buscar.addWidget(lbl_buscar_id)
        row_buscar.addWidget(self.txtBuscarID)
        row_buscar.addWidget(self.btnBuscarID)
        row_buscar.addWidget(self.btnMostrarTodas)
        row_buscar.addStretch(1)
        card_layout.addLayout(row_buscar)

        row_buscar_detalle = QHBoxLayout()
        row_buscar_detalle.setSpacing(12)
        row_buscar_detalle.addStretch(1)

        lbl_buscar_detalle = QLabel("Buscar detalle por:")
        lbl_buscar_detalle.setObjectName("MutedLabel")

        self.cmbBuscarDetalle = QComboBox()
        self.cmbBuscarDetalle.setObjectName("Combo")
        self.cmbBuscarDetalle.setFixedWidth(160)
        self.cmbBuscarDetalle.addItem("Pintura", "Pintura")
        self.cmbBuscarDetalle.addItem("Artista", "Artista")

        self.txtBuscarDetalle = QLineEdit()
        self.txtBuscarDetalle.setObjectName("SearchBox")
        self.txtBuscarDetalle.setFixedWidth(260)

        self.btnBuscarDetalle = self._button("Buscar detalle", self.on_buscar_detalle)

        row_buscar_detalle.addWidget(lbl_buscar_detalle)
        row_buscar_detalle.addWidget(self.cmbBuscarDetalle)
        row_buscar_detalle.addWidget(self.txtBuscarDetalle)
        row_buscar_detalle.addWidget(self.btnBuscarDetalle)
        row_buscar_detalle.addStretch(1)
        card_layout.addLayout(row_buscar_detalle)

        # === Validadores de campos ===
        validator_numeros = QRegularExpressionValidator(
            QRegularExpression(r"^[0-9]+$")
        )
        validator_alfanumerico = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s]+$")
        )
        self.txtBuscarID.setValidator(validator_numeros)
        self.txtBuscarDetalle.setValidator(validator_alfanumerico)

        ventas_frame = QFrame()
        ventas_frame.setObjectName("TableFrame")
        vf = QVBoxLayout(ventas_frame)
        vf.setContentsMargins(10, 10, 10, 10)

        self.ventas_table = QTableWidget(0, 6)
        self.ventas_table.setObjectName("Table")
        self.ventas_table.setHorizontalHeaderLabels(["ID", "Cliente", "Vendedor", "Fecha", "Total", "Forma de Pago"])
        self.ventas_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ventas_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ventas_table.verticalHeader().setVisible(False)
        ventas_header = self.ventas_table.horizontalHeader()
        ventas_header.setSectionResizeMode(QHeaderView.Stretch)

        self.ventas_table.itemSelectionChanged.connect(self.on_venta_selected)
        vf.addWidget(self.ventas_table)
        card_layout.addWidget(ventas_frame)

        row_bottom = QHBoxLayout()
        row_bottom.addStretch(1)
        self.btnSalir = self._button("Salir", self.close, wide=True)
        row_bottom.addWidget(self.btnSalir)
        row_bottom.addStretch(1)
        card_layout.addLayout(row_bottom)

        main.addWidget(card)
        self.setStyleSheet(self._stylesheet())

        self._load_clientes_combo()
        self._load_vendedores_combo()
        self._load_artistas_combo()
        self._load_pinturas_combo(None)
        self._load_cotizaciones_combo()
        self.load_all()
        self._actualizar_estado_caja()

    def closeEvent(self, event):
        if self.ventana_principal is not None:
            self.ventana_principal.show()
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.actualizar_selects()
        self._actualizar_estado_caja()

    def actualizar_selects(self) -> None:
        cliente_actual = self.cmbCliente.currentData()
        vendedor_actual = self.cmbVendedor.currentData()
        cotizacion_actual = self.cmbCotizacion.currentData()
        artista_actual = self.cmbArtista.currentData()

        pintura_actual = None
        data_pintura = self.cmbPintura.currentData()
        if data_pintura is not None:
            pintura_actual = data_pintura[0]

        self._load_clientes_combo()
        idx_cliente = self.cmbCliente.findData(cliente_actual)
        if idx_cliente >= 0:
            self.cmbCliente.setCurrentIndex(idx_cliente)
        elif self.cmbCliente.count() > 0:
            self.cmbCliente.setCurrentIndex(0)

        self._load_vendedores_combo()
        idx_vendedor = self.cmbVendedor.findData(vendedor_actual)
        if idx_vendedor >= 0:
            self.cmbVendedor.setCurrentIndex(idx_vendedor)
        elif self.cmbVendedor.count() > 0:
            self.cmbVendedor.setCurrentIndex(0)

        self._load_cotizaciones_combo()
        if cotizacion_actual is not None:
            for i in range(self.cmbCotizacion.count()):
                data = self.cmbCotizacion.itemData(i)
                if data == cotizacion_actual:
                    self.cmbCotizacion.setCurrentIndex(i)
                    break
        elif self.cmbCotizacion.count() > 0:
            self.cmbCotizacion.setCurrentIndex(0)

        self._load_artistas_combo()
        idx_artista = self.cmbArtista.findData(artista_actual)
        if idx_artista >= 0:
            self.cmbArtista.setCurrentIndex(idx_artista)
        elif self.cmbArtista.count() > 0:
            self.cmbArtista.setCurrentIndex(0)

        id_artista = self.cmbArtista.currentData()
        self._load_pinturas_combo(id_artista if id_artista is not None else None)

        if pintura_actual is not None:
            for i in range(self.cmbPintura.count()):
                data = self.cmbPintura.itemData(i)
                if data is not None and data[0] == pintura_actual:
                    self.cmbPintura.setCurrentIndex(i)
                    break
        elif self.cmbPintura.count() > 0:
            self.cmbPintura.setCurrentIndex(0)

    def abrir_clientes(self) -> None:
        if self.ventana_clientes is None:
            self.ventana_clientes = ClientesVentana(self)
        self.hide()
        self.ventana_clientes.show()
        self.ventana_clientes.raise_()
        self.ventana_clientes.activateWindow()

    def abrir_vendedores(self) -> None:
        if self.ventana_vendedores is None:
            self.ventana_vendedores = VendedoresVentana(self)
        self.hide()
        self.ventana_vendedores.show()
        self.ventana_vendedores.raise_()
        self.ventana_vendedores.activateWindow()

    def abrir_artistas(self) -> None:
        if self.ventana_artistas is None:
            self.ventana_artistas = ArtistasVentana(self)
        self.hide()
        self.ventana_artistas.show()
        self.ventana_artistas.raise_()
        self.ventana_artistas.activateWindow()

    def abrir_pinturas(self) -> None:
        if self.ventana_pinturas is None:
            self.ventana_pinturas = PinturasVentana(self)
        self.hide()
        self.ventana_pinturas.show()
        self.ventana_pinturas.raise_()
        self.ventana_pinturas.activateWindow()

    def abrir_cotizaciones(self) -> None:
        if self.ventana_cotizaciones is None:
            self.ventana_cotizaciones = CotizacionesVentana(self)
        self.hide()
        self.ventana_cotizaciones.show()
        self.ventana_cotizaciones.raise_()
        self.ventana_cotizaciones.activateWindow()

    def _button(self, text: str, handler, wide: bool = False) -> QPushButton:
        b = QPushButton(text)
        b.setObjectName("Btn")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(handler)
        b.setFixedWidth(170 if wide else 110)
        b.setFixedHeight(34)
        return b

    def _stylesheet(self) -> str:
        return f"""
        QWidget#Root {{
            background: {BG};
            color: {TEXT};
            font-family: "Segoe UI";
            font-size: 10pt;
        }}
        QFrame#Card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 16px;
        }}
        QLabel#Title {{
            color: {TEXT};
            font-weight: 600;
            padding: 2px 0 6px 0;
        }}
        QLabel#MutedLabel {{
            color: {MUTED};
        }}
        QFrame#Separator {{
            background: {BORDER};
            border: none;
            height: 1px;
        }}
        QLineEdit {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 6px 10px;
            color: {TEXT};
        }}
        QLineEdit:focus {{
            border: 1px solid {GOLD};
        }}
        QDateEdit {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 6px 10px;
            color: {TEXT};
        }}
        QDateEdit:focus {{
            border: 1px solid {GOLD};
        }}
        QComboBox#Combo {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 6px 10px;
            color: {TEXT};
        }}
        QComboBox#Combo:focus {{
            border: 1px solid {GOLD};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 26px;
        }}
        QComboBox::down-arrow {{
            width: 10px;
            height: 10px;
        }}
        QSpinBox#SpinBox {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 6px 10px;
            color: {TEXT};
        }}
        QSpinBox#SpinBox:focus {{
            border: 1px solid {GOLD};
        }}
        QPushButton#Btn {{
            background: {BTN_BG};
            color: {BTN_TEXT};
            border: 1px solid {BTN_BORDER};
            border-radius: 9px;
        }}
        QPushButton#Btn:hover {{
            border: 1px solid {GOLD};
            background: {BG};
        }}
        QPushButton#Btn:pressed {{
            background: #EFE7DD;
        }}
        QPushButton#Btn:disabled {{
            color: {MUTED};
            border: 1px solid {BORDER};
        }}
        QFrame#TableFrame {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 14px;
        }}
        QTableWidget#Table {{
            background: #FFFFFF;
            border: none;
            gridline-color: {BORDER};
            selection-background-color: {PRIMARY};
            selection-color: #FFFFFF;
        }}
        QTableWidget::item {{
            color: {TEXT};
        }}
        QTableWidget::item:selected {{
            color: #FFFFFF;
        }}
        QHeaderView::section {{
            background: {BTN_BG};
            border: 1px solid {BORDER};
            padding: 6px;
            color: {MUTED};
            font-weight: 600;
        }}
        """

    def _show_error(self, title: str, msg: str) -> None:
        QMessageBox.critical(self, title, msg)

    def _caja_cerrada_hoy(self, id_vendedor: int) -> bool:
        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(
                    cur,
                    "SELECT COUNT(1) FROM CierreCaja "
                    "WHERE id_vendedor = ? "
                    "AND DATE(fecha) = DATE('now')",
                    (id_vendedor,),
                )
                row = cur.fetchone()
                return bool(row and row[0])
        except Exception:
            return False

    def _vendedor_tiene_apertura(self, id_vendedor: int) -> bool:
        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(
                    cur,
                    "SELECT COUNT(1) FROM AperturaCaja "
                    "WHERE id_vendedor = ? "
                    "AND DATE(fecha) = DATE('now')",
                    (id_vendedor,),
                )
                row = cur.fetchone()
                return bool(row and row[0])
        except Exception:
            return False

    def _actualizar_estado_caja(self) -> None:
        id_vendedor = self.cmbVendedor.currentData()
        cerrada = self._caja_cerrada_hoy(id_vendedor) if id_vendedor is not None else False
        self.btnGuardar.setEnabled(not cerrada)
        if cerrada:
            self.btnEliminar.setEnabled(False)
        self.btnAgregarLinea.setEnabled(not cerrada)
        self.btnImportarCotizacion.setEnabled(not cerrada)
        tooltip = "La caja del vendedor seleccionado está cerrada. No se pueden registrar ventas." if cerrada else ""
        self.btnGuardar.setToolTip(tooltip)
        self.btnEliminar.setToolTip(tooltip)
        self.btnAgregarLinea.setToolTip(tooltip)
        self.btnImportarCotizacion.setToolTip(tooltip)
        self._lbl_caja_cerrada.setVisible(cerrada)

    def _load_clientes_combo(self) -> None:
        self.cmbCliente.clear()
        self.cmbCliente.addItem("Selecciona un cliente", None)

        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(cur, "SELECT id_cliente, COALESCE(nombre, '') FROM Clientes ORDER BY nombre")
                rows = cur.fetchall()
                for r in rows:
                    self.cmbCliente.addItem(str(r[1]), r[0])
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _load_vendedores_combo(self) -> None:
        self.cmbVendedor.clear()
        self.cmbVendedor.addItem("Selecciona un vendedor", None)

        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(
                    cur,
                    "SELECT id_vendedor, COALESCE(nombre, '') "
                    "FROM Vendedores WHERE COALESCE(activo, 1) = 1 ORDER BY nombre",
                )
                rows = cur.fetchall()
                for r in rows:
                    self.cmbVendedor.addItem(str(r[1]), r[0])
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _load_artistas_combo(self) -> None:
        self.cmbArtista.blockSignals(True)
        self.cmbArtista.clear()
        self.cmbArtista.addItem("Cualquier Artista", None)

        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(cur, "SELECT id_artista, COALESCE(nombre, '') FROM Artistas ORDER BY nombre")
                rows = cur.fetchall()
                for r in rows:
                    self.cmbArtista.addItem(str(r[1]), r[0])
        except Exception as e:
            self._show_error("Error BD", str(e))

        self.cmbArtista.setCurrentIndex(0)
        self.cmbArtista.blockSignals(False)

    def _load_pinturas_combo(self, id_artista: Optional[int] = None) -> None:
        self.cmbPintura.clear()
        try:
            with db() as conn:
                cur = conn.cursor()
                if id_artista is None:
                    _exec(
                        cur,
                        "SELECT p.id_pintura, COALESCE(p.titulo, ''), COALESCE(a.nombre, ''), COALESCE(p.precio, 0) "
                        "FROM Pinturas p "
                        "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                        "ORDER BY p.titulo",
                    )
                else:
                    _exec(
                        cur,
                        "SELECT p.id_pintura, COALESCE(p.titulo, ''), COALESCE(a.nombre, ''), COALESCE(p.precio, 0) "
                        "FROM Pinturas p "
                        "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                        "WHERE p.id_artista = ? "
                        "ORDER BY p.titulo",
                        (id_artista,),
                    )

                rows = cur.fetchall()
                self.cmbPintura.addItem("-- Seleccionar pintura --", None)
                for r in rows:
                    id_pintura = int(r[0])
                    titulo = str(r[1]) if r[1] is not None else ""
                    artista = str(r[2]) if r[2] is not None else ""
                    precio = float(r[3]) if r[3] is not None else 0.0
                    texto = f"{titulo} - {artista} - ${precio:.2f}" if artista else f"{titulo} - ${precio:.2f}"
                    self.cmbPintura.addItem(texto, (id_pintura, titulo, artista, precio))
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_artista_changed(self, *_args) -> None:
        current_data = self.cmbPintura.currentData()
        current_painting_id = current_data[0] if current_data is not None else None

        id_artista = self.cmbArtista.currentData()
        self._load_pinturas_combo(id_artista if id_artista is not None else None)

        if current_painting_id is not None:
            for i in range(self.cmbPintura.count()):
                data = self.cmbPintura.itemData(i)
                if data and data[0] == current_painting_id:
                    self.cmbPintura.setCurrentIndex(i)
                    break

    def _load_cotizaciones_combo(self) -> None:
        self.cmbCotizacion.clear()
        try:
            cotizaciones = self.cotizacion_repo.fetch_all()
            self.cmbCotizacion.addItem("-- Seleccionar cotización --", None)
            for id_cotizacion, cliente, fecha, total, id_cliente, id_vendedor in cotizaciones:
                texto = f"#{id_cotizacion} | {cliente} | {fecha} | ${total}"
                self.cmbCotizacion.addItem(texto, (id_cotizacion, id_cliente, id_vendedor, fecha))
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _total_actual(self) -> float:
        return sum(line[5] for line in self._detail_lines)

    def _recalculate_totals(self) -> None:
        subtotal = self._total_actual()
        self.lblSubtotal.setText(f"Subtotal: ${subtotal:.2f}")
        self.lblTotal.setText(f"Total: ${subtotal:.2f}")

    def _cantidad_solicitada_por_pintura(self, id_pintura: int) -> int:
        return sum(cantidad for pid, _, _, cantidad, _, _ in self._detail_lines if pid == id_pintura)

    def _validar_existencia_para_agregar(self, id_pintura: int, cantidad_nueva: int) -> bool:
        disponible = self.inventario_repo.get_disponible(id_pintura)
        solicitada_total = self._cantidad_solicitada_por_pintura(id_pintura) + cantidad_nueva

        if solicitada_total > disponible:
            titulo = next(
                (t for pid, t, _, _, _, _ in self._detail_lines if pid == id_pintura),
                f"ID {id_pintura}",
            )
            self._show_error(
                "Existencias insuficientes",
                f"La pintura '{titulo}' solo tiene {disponible} en inventario.\n"
                f"Estás intentando pedir {solicitada_total}."
            )
            return False

        return True

    def _validar_existencias_totales(self) -> bool:
        acumuladas: dict[int, int] = {}

        for id_pintura, _, _, cantidad, _, _ in self._detail_lines:
            acumuladas[id_pintura] = acumuladas.get(id_pintura, 0) + cantidad

        for id_pintura, solicitada in acumuladas.items():
            disponible = self.inventario_repo.get_disponible(id_pintura)
            if solicitada > disponible:
                titulo = next(
                    (t for pid, t, _, _, _, _ in self._detail_lines if pid == id_pintura),
                    f"ID {id_pintura}",
                )
                self._show_error(
                    "Existencias insuficientes",
                    f"La pintura '{titulo}' tiene {disponible} en inventario.\n"
                    f"En la cotización estás solicitando {solicitada}."
                )
                return False

        return True

    def _validar_existencias_lineas_cursor(self, cur, lines) -> bool:
        acumuladas: dict[int, int] = {}

        for id_pintura, _, _, cantidad, _, _ in lines:
            acumuladas[id_pintura] = acumuladas.get(id_pintura, 0) + cantidad

        for id_pintura, solicitada in acumuladas.items():
            disponible = self.inventario_repo.get_disponible_cursor(cur, id_pintura)
            if solicitada > disponible:
                titulo = next(
                    (t for pid, t, _, _, _, _ in lines if pid == id_pintura),
                    f"ID {id_pintura}"
                )
                self._show_error(
                    "Existencias insuficientes",
                    f"La pintura '{titulo}' solo tiene {disponible} en inventario.\n"
                    f"Se están solicitando {solicitada}."
                )
                return False
        return True

    def _refresh_detail_table(self) -> None:
        self.detail_table.setRowCount(0)
        for idx, (id_pintura, titulo, artista, cantidad, precio_unitario, subtotal_linea) in enumerate(
            self._detail_lines
        ):
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)

            it_titulo = QTableWidgetItem(titulo)
            it_titulo.setFlags(it_titulo.flags() & ~Qt.ItemIsEditable)

            it_artista = QTableWidgetItem(artista)
            it_artista.setFlags(it_artista.flags() & ~Qt.ItemIsEditable)

            it_cantidad = QTableWidgetItem(str(cantidad))
            it_cantidad.setFlags(it_cantidad.flags() & ~Qt.ItemIsEditable)

            it_subtotal = QTableWidgetItem(f"${subtotal_linea:.2f}")
            it_subtotal.setFlags(it_subtotal.flags() & ~Qt.ItemIsEditable)

            self.detail_table.setItem(row, 0, it_titulo)
            self.detail_table.setItem(row, 1, it_artista)
            self.detail_table.setItem(row, 2, it_cantidad)
            self.detail_table.setItem(row, 3, it_subtotal)

            btn_quitar = QPushButton("X")
            btn_quitar.setObjectName("Btn")
            btn_quitar.setCursor(Qt.PointingHandCursor)
            btn_quitar.setFixedSize(30, 26)
            btn_quitar.clicked.connect(lambda checked=False, i=idx: self.on_remove_line(i))
            self.detail_table.setCellWidget(row, 4, btn_quitar)

        self._recalculate_totals()

    def clear_form(self) -> None:
        self.current_id = None
        self._cotizacion_id_cargada = None

        if self.cmbCliente.count() > 0:
            self.cmbCliente.setCurrentIndex(0)
        if self.cmbVendedor.count() > 0:
            self.cmbVendedor.setCurrentIndex(0)
        if self.cmbCotizacion.count() > 0:
            self.cmbCotizacion.setCurrentIndex(0)

        self.dateFecha.setDate(QDate.currentDate())
        self.spnCantidad.setValue(1)

        self.cmbArtista.blockSignals(True)
        self.cmbArtista.setCurrentIndex(0)
        self.cmbArtista.blockSignals(False)
        self._load_pinturas_combo(None)

        self.cmbPintura.setCurrentIndex(0)

        self._detail_lines.clear()
        self._refresh_detail_table()
        self.ventas_table.clearSelection()
        self.btnEliminar.setEnabled(False)
        self.btnGuardar.setEnabled(True)

        self.txtBuscarID.clear()
        self.txtBuscarDetalle.clear()
        self.cmbBuscarDetalle.setCurrentIndex(0)
        self._actualizar_estado_caja()

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_ventas_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_ventas_table(self, rows: List[Tuple]) -> None:
        self.ventas_table.setRowCount(0)
        for r, data in enumerate(rows):
            vid, cliente, vendedor, fecha, total, forma_pago = data[:6]
            self.ventas_table.insertRow(r)
            for col, val in enumerate([str(vid), cliente, vendedor, fecha, total, forma_pago]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.ventas_table.setItem(r, col, item)

    def on_add_line(self) -> None:
        if self.cmbPintura.count() == 0:
            self._show_error("Validación", "No hay pinturas disponibles.")
            return

        data = self.cmbPintura.currentData()
        if data is None:
            self._show_error("Validación", "Selecciona una pintura.")
            return

        id_pintura, titulo, artista, precio = data
        cantidad = self.spnCantidad.value()

        if cantidad <= 0:
            self._show_error("Validación", "La cantidad debe ser mayor que cero.")
            return

        if not self._validar_existencia_para_agregar(id_pintura, cantidad):
            return

        for i, (pid, t, a, cant, p_unit, sub) in enumerate(self._detail_lines):
            if pid == id_pintura:
                nueva_cantidad = cant + cantidad
                nuevo_subtotal = nueva_cantidad * p_unit
                self._detail_lines[i] = (pid, t, a, nueva_cantidad, p_unit, nuevo_subtotal)
                self._refresh_detail_table()
                self.spnCantidad.setValue(1)
                return

        subtotal_linea = precio * cantidad
        self._detail_lines.append((id_pintura, titulo, artista, cantidad, precio, subtotal_linea))
        self._refresh_detail_table()
        self.spnCantidad.setValue(1)

    def on_remove_line(self, index: int) -> None:
        if 0 <= index < len(self._detail_lines):
            self._detail_lines.pop(index)
            self._refresh_detail_table()

    def on_import_cotizacion(self) -> None:
        data = self.cmbCotizacion.currentData()
        if data is None:
            self._show_error("Validación", "Selecciona una cotización.")
            return

        id_cotizacion, id_cliente, id_vendedor, fecha_cotizacion = data

        try:
            detalle = self.cotizacion_repo.fetch_detalle(id_cotizacion)
            if not detalle:
                self._show_error("Validación", "La cotización seleccionada no tiene detalle.")
                return

            if self._detail_lines:
                r = QMessageBox.question(
                    self,
                    "Confirmar",
                    "Se reemplazará el detalle actual por el de la cotización seleccionada. ¿Deseas continuar?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if r != QMessageBox.Yes:
                    return

            acumuladas: dict[int, int] = {}
            for id_pintura, _, _, cantidad, _, _ in detalle:
                acumuladas[id_pintura] = acumuladas.get(id_pintura, 0) + cantidad

            for id_pintura, solicitada in acumuladas.items():
                disponible = self.inventario_repo.get_disponible(id_pintura)
                if solicitada > disponible:
                    titulo = next(
                        (t for pid, t, _, _, _, _ in detalle if pid == id_pintura),
                        f"ID {id_pintura}",
                    )
                    self._show_error(
                        "Existencias insuficientes",
                        f"La pintura '{titulo}' tiene {disponible} en inventario.\n"
                        f"En la cotización estás solicitando {solicitada}."
                    )
                    return

            self._detail_lines = list(detalle)
            self._refresh_detail_table()

            idx = self.cmbCliente.findData(id_cliente)
            if idx >= 0:
                self.cmbCliente.setCurrentIndex(idx)

            idx_v = self.cmbVendedor.findData(id_vendedor)
            if idx_v >= 0:
                self.cmbVendedor.setCurrentIndex(idx_v)

            if fecha_cotizacion:
                qd = QDate.fromString(fecha_cotizacion, "yyyy-MM-dd")
                if qd.isValid():
                    self.dateFecha.setDate(qd)

            self._cotizacion_id_cargada = id_cotizacion
            self.current_id = None
            self.btnEliminar.setEnabled(False)
            self.btnGuardar.setEnabled(True)

        except Exception as e:
            self._show_error("Error BD", str(e))

    def _guardar_venta_con_pago(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        if self.cmbCliente.count() == 0 or self.cmbCliente.currentData() is None:
            raise RuntimeError("Selecciona un cliente.")
        if self.cmbVendedor.count() == 0 or self.cmbVendedor.currentData() is None:
            raise RuntimeError("Selecciona un vendedor.")
        if not self._detail_lines:
            raise RuntimeError("Agrega al menos una línea de detalle.")

        if not self._validar_existencias_totales():
            raise RuntimeError("No hay existencias suficientes.")

        id_cliente = self.cmbCliente.currentData()
        id_vendedor = self.cmbVendedor.currentData()
        fecha = self.dateFecha.date().toString("yyyy-MM-dd")
        total = sum(line[5] for line in self._detail_lines)
        forma_pago = payment["forma_pago"]

        try:
            with db() as conn:
                cur = conn.cursor()

                if self.current_id is None:
                    if not self._validar_existencias_lineas_cursor(cur, self._detail_lines):
                        conn.rollback()
                        raise RuntimeError("No hay existencias suficientes.")

                    _exec(
                        cur,
                        "INSERT INTO Ventas (id_cliente, id_vendedor, fecha, total, forma_pago) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (id_cliente, id_vendedor, fecha, total, forma_pago),
                    )
                    venta_id = cur.lastrowid
                else:
                    old_rows = self.detalle_repo.fetch_by_venta(self.current_id)

                    for _, _, _, cantidad, _, id_pintura in old_rows:
                        self.inventario_repo.restaurar_cursor(cur, id_pintura, cantidad)

                    if not self._validar_existencias_lineas_cursor(cur, self._detail_lines):
                        conn.rollback()
                        raise RuntimeError("No hay existencias suficientes.")

                    _exec(
                        cur,
                        "UPDATE Ventas SET id_cliente = ?, id_vendedor = ?, fecha = ?, total = ?, forma_pago = ? "
                        "WHERE id_venta = ?",
                        (id_cliente, id_vendedor, fecha, total, forma_pago, self.current_id),
                    )
                    _exec(cur, "DELETE FROM DetalleVenta WHERE id_venta = ?", (self.current_id,))
                    venta_id = self.current_id

                for (id_pintura, titulo, artista, cantidad, precio_unitario, subtotal_linea) in self._detail_lines:
                    _exec(
                        cur,
                        "INSERT INTO DetalleVenta (id_venta, id_pintura, cantidad, subtotal) "
                        "VALUES (?, ?, ?, ?)",
                        (venta_id, id_pintura, cantidad, subtotal_linea),
                    )
                    self.inventario_repo.descontar_cursor(cur, id_pintura, cantidad)

                conn.commit()

            if self._cotizacion_id_cargada is not None:
                self.cotizacion_repo.marcar_concretada(self._cotizacion_id_cargada)
                self._cotizacion_id_cargada = None

            cambio = float(payment.get("cambio", 0.0) or 0.0)
            self.load_all()
            self._load_cotizaciones_combo()
            self.clear_form()

            return {
                "venta_id": venta_id,
                "forma_pago": forma_pago,
                "cambio": cambio,
            }

        except Exception:
            raise

    def on_realizar_venta(self) -> None:
        if self.current_id is not None:
            self._show_error("Validación", "La venta seleccionada ya fue realizada. Presiona 'Nueva Venta' para registrar otra.")
            return

        if self.cmbCliente.count() == 0 or self.cmbCliente.currentData() is None:
            self._show_error("Validación", "Selecciona un cliente.")
            return
        if self.cmbVendedor.count() == 0 or self.cmbVendedor.currentData() is None:
            self._show_error("Validación", "Selecciona un vendedor.")
            return
        if not self._detail_lines:
            self._show_error("Validación", "Agrega al menos una línea de detalle.")
            return

        id_vendedor = self.cmbVendedor.currentData()
        if id_vendedor is not None and not self._vendedor_tiene_apertura(id_vendedor):
            msg = QMessageBox(self)
            msg.setWindowTitle("Caja sin apertura")
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                "El vendedor seleccionado no tiene apertura de caja para hoy.\n"
                "Debes abrir la caja antes de realizar ventas."
            )
            btn_abrir = msg.addButton("Ir a Abrir Caja", QMessageBox.ActionRole)
            msg.addButton("Cancelar", QMessageBox.RejectRole)
            msg.exec()
            if msg.clickedButton() == btn_abrir:
                if self.ventana_principal is not None:
                    self.close()
                    self.ventana_principal.abrir_corte_caja()
            return

        total = self._total_actual()
        dlg = RealizarVentaDialog(total, self)
        if dlg.exec() != QDialog.Accepted:
            return

        payment = dlg.get_payment_data()
        if not payment:
            return

        try:
            resultado = self._guardar_venta_con_pago(payment)

            dlg_post = _PostVentaDialog(
                resultado["venta_id"],
                resultado["forma_pago"],
                resultado["cambio"],
                self,
            )
            dlg_post.exec()

        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_nueva(self) -> None:
        self.clear_form()

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona una venta de la tabla.")
            return

        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar la venta ID {self.current_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return

        try:
            with db() as conn:
                cur = conn.cursor()

                old_rows = self.detalle_repo.fetch_by_venta(self.current_id)

                for _, _, _, cantidad, _, id_pintura in old_rows:
                    self.inventario_repo.restaurar_cursor(cur, id_pintura, cantidad)

                _exec(cur, "DELETE FROM DetalleVenta WHERE id_venta = ?", (self.current_id,))
                _exec(cur, "DELETE FROM Ventas WHERE id_venta = ?", (self.current_id,))
                conn.commit()

            self.load_all()
            self._load_cotizaciones_combo()
            self.clear_form()

        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_venta_selected(self) -> None:
        items = self.ventas_table.selectedItems()
        if not items:
            return

        row = items[0].row()
        vid = int(self.ventas_table.item(row, 0).text())

        try:
            rows = self.repo.fetch_by_id(vid)
            if not rows:
                return

            _, cliente, vendedor, fecha, total, id_cliente, id_vendedor, forma_pago = rows[0]
            self.current_id = vid

            idx = self.cmbCliente.findData(id_cliente)
            if idx >= 0:
                self.cmbCliente.setCurrentIndex(idx)

            idx_v = self.cmbVendedor.findData(id_vendedor)
            if idx_v >= 0:
                self.cmbVendedor.setCurrentIndex(idx_v)

            if fecha:
                qd = QDate.fromString(fecha, "yyyy-MM-dd")
                if qd.isValid():
                    self.dateFecha.setDate(qd)
                else:
                    self.dateFecha.setDate(QDate.currentDate())
            else:
                self.dateFecha.setDate(QDate.currentDate())

            self._detail_lines.clear()
            detail_rows = self.detalle_repo.fetch_by_venta(vid)
            for _, titulo, artista, cantidad, subtotal_d, id_pintura in detail_rows:
                precio_unitario = float(subtotal_d) / cantidad if cantidad else 0.0
                self._detail_lines.append(
                    (
                        id_pintura,
                        titulo,
                        artista,
                        cantidad,
                        precio_unitario,
                        float(subtotal_d),
                    )
                )

            self._refresh_detail_table()
            self.btnEliminar.setEnabled(True)
            self.btnGuardar.setEnabled(False)
            self._actualizar_estado_caja()

        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_buscar_id(self) -> None:
        raw = self.txtBuscarID.text().strip()
        if not raw:
            self._show_error("Validación", "Escribe un ID para buscar.")
            return
        try:
            vid = int(raw)
        except ValueError:
            self._show_error("Validación", "El ID debe ser numérico.")
            return
        try:
            rows = self.repo.fetch_by_id(vid)
            display_rows = [(r[0], r[1], r[2], r[3], r[4], r[7]) for r in rows]
            if display_rows:
                self.populate_ventas_table(display_rows)
            else:
                self.populate_ventas_table([])
                QMessageBox.information(self, "Resultado", "No se encontró ninguna venta con ese ID.")
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_buscar_detalle(self) -> None:
        texto = self.txtBuscarDetalle.text().strip()
        if not texto:
            self.load_all()
            return

        campo = self.cmbBuscarDetalle.currentData() or "Pintura"

        try:
            rows = self.repo.search_by_detail_name(texto, campo)
            if rows:
                self.populate_ventas_table(rows)
            else:
                self.populate_ventas_table([])
                QMessageBox.information(
                    self,
                    "Resultado",
                    f"No se encontraron ventas por {campo.lower()} con ese texto.",
                )
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_mostrar_todas(self) -> None:
        self.txtBuscarID.clear()
        self.txtBuscarDetalle.clear()
        self.cmbBuscarDetalle.setCurrentIndex(0)
        self.load_all()
        self.clear_form()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = VentasVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
