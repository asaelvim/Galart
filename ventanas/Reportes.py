from html import escape

from PySide6.QtCore import Qt, QSize, QDate, QSizeF, QMarginsF
from PySide6.QtGui import (
    QFont, QPainter, QColor, QPdfWriter, QPageSize, QPageLayout, QTextDocument
)
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QDateEdit, QAbstractItemView, QComboBox, QSpinBox, QWidget
)
from modulos.ItemMenu import ItemMenu
from modulos.Fondo import Fondo
from modulos.Carta import Carta
from modulos.PaletaColores import *
from ventanas.NotaVentas import NotaVentasVentana

# ---------------------------------------------------------------------------
# Helpers compartidos
# ---------------------------------------------------------------------------

_MESES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _fmt_fecha(valor):
    if valor is None:
        return "-"
    try:
        return valor.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(valor)


def _fmt_fecha_corta(valor):
    if valor is None:
        return "-"
    try:
        return valor.strftime("%Y-%m-%d")
    except Exception:
        return str(valor)


def _fmt_money(valor):
    try:
        return f"${float(valor):,.2f}"
    except Exception:
        return "$0.00"


# Stylesheet compartido para todas las ventanas de reporte
_VENTANA_STYLE = f"""
    QMainWindow {{
        background: {FONDO_A};
    }}
    QWidget {{
        color: {TEXTO};
        font-family: "Segoe UI";
    }}
    QLabel {{
        color: {TEXTO};
    }}
    QDateEdit {{
        background: {SUPERFICIE};
        color: {TEXTO};
        border: 1px solid {BORDE_BOTON};
        border-radius: 8px;
        padding: 6px 10px;
        selection-background-color: {PRIMARIO};
        selection-color: white;
    }}
    QDateEdit::drop-down {{
        border: none;
        width: 22px;
    }}
    QComboBox {{
        background: {SUPERFICIE};
        color: {TEXTO};
        border: 1px solid {BORDE_BOTON};
        border-radius: 8px;
        padding: 6px 10px;
    }}
    QSpinBox {{
        background: {SUPERFICIE};
        color: {TEXTO};
        border: 1px solid {BORDE_BOTON};
        border-radius: 8px;
        padding: 6px 10px;
    }}
    QTableWidget {{
        background: {SUPERFICIE};
        alternate-background-color: {FONDO_B};
        color: {TEXTO};
        gridline-color: {BORDE};
        border: 1px solid {BORDE};
        border-radius: 10px;
        selection-background-color: {FONDO_ACTIVO};
        selection-color: white;
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        color: {TEXTO};
    }}
    QTableWidget::item:alternate {{
        background: {FONDO_B};
    }}
    QTableWidget::item:selected,
    QTableWidget::item:selected:active,
    QTableWidget::item:selected:!active {{
        background: {FONDO_ACTIVO};
        color: white;
    }}
    QHeaderView::section {{
        background: {FONDO_BOTON};
        color: {TEXTO_BOTON};
        border: none;
        border-bottom: 1px solid {BORDE};
        padding: 8px;
        font-weight: bold;
    }}
"""

_BTN_BUSCAR_STYLE = f"""
    QPushButton {{
        background: {PRIMARIO};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{
        background: {FONDO_ACTIVO};
    }}
    QPushButton:pressed {{
        background: {ACENTO};
        color: {TEXTO};
    }}
"""

_BTN_PDF_STYLE = f"""
    QPushButton {{
        background: {PRIMARIO};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 16px;
    }}
    QPushButton:hover {{
        background: {FONDO_ACTIVO};
    }}
    QPushButton:pressed {{
        background: {ACENTO};
        color: {TEXTO};
    }}
    QPushButton:disabled {{
        background: {BORDE_BOTON};
        color: {DESACTIVADO};
    }}
"""

_BTN_VOLVER_STYLE = f"""
    QPushButton {{
        background: transparent;
        color: {DESACTIVADO};
        border: none;
    }}
    QPushButton:hover {{
        color: {PRIMARIO};
        text-decoration: underline;
    }}
"""

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
        border-bottom: 1px solid #1F1F1F; padding: 8px 0 6px 0;
    }
    .items td {
        border-bottom: 1px dotted #DED6CC;
        padding: 8px 0; vertical-align: top; word-wrap: break-word;
    }
    .txt { word-break: break-word; }
    .num { text-align: right; white-space: nowrap; }
    .summary { margin-top: 16px; width: 100%; border-collapse: collapse; }
    .summary td { padding: 4px 0; }
    .summary .label { width: 82%; text-align: right; font-weight: bold; font-size: 12pt; }
    .summary .value { width: 18%; text-align: right; font-size: 13pt; font-weight: bold; white-space: nowrap; }
    .footer { margin-top: 22px; text-align: center; font-size: 9pt; color: #5B5B5B; }
"""


def _guardar_pdf(ventana, titulo_doc, nombre_sugerido, html):
    ruta, _ = QFileDialog.getSaveFileName(
        ventana, "Guardar PDF", nombre_sugerido, "PDF (*.pdf)"
    )
    if not ruta:
        return
    try:
        dpi = 96
        margin_mm = 15
        writer = QPdfWriter(ruta)
        writer.setResolution(dpi)
        writer.setTitle(titulo_doc)
        writer.setCreator("Sistema Galería de Arte")
        writer.setPageSize(QPageSize(QPageSize.Letter))
        writer.setPageMargins(
            QMarginsF(margin_mm, margin_mm, margin_mm, margin_mm),
            QPageLayout.Millimeter
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
        QMessageBox.information(ventana, "Listo", f"PDF generado correctamente:\n{ruta}")
    except Exception as e:
        QMessageBox.critical(ventana, "Error", f"No se pudo generar el PDF:\n{e}")


def _tabla_item(texto, align=Qt.AlignLeft | Qt.AlignVCenter):
    item = QTableWidgetItem(str(texto))
    item.setForeground(QColor(TEXTO))
    item.setTextAlignment(align)
    return item


def _make_tabla(headers, min_height=260):
    tabla = QTableWidget(0, len(headers))
    tabla.setHorizontalHeaderLabels(headers)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SingleSelection)
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabla.verticalHeader().setVisible(False)
    tabla.setAlternatingRowColors(True)
    tabla.setFont(QFont("Segoe UI", 10))
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tabla.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    tabla.setMinimumHeight(min_height)
    return tabla


# ---------------------------------------------------------------------------
# 1. VentanaReporteVentasPeriodo
# ---------------------------------------------------------------------------

class VentanaReporteVentasPeriodo(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self._datos = []

        self.setWindowTitle("Ventas por periodo")
        self.setMinimumSize(QSize(980, 660))
        self.setStyleSheet(_VENTANA_STYLE)

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setMinimumSize(940, 600)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)
        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(28, 22, 28, 22)
        content.setSpacing(12)

        titulo = QLabel("Ventas por periodo")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(titulo)

        subtitulo = QLabel("Consulta las ventas realizadas en un rango de fechas")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(linea)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDisplayFormat("yyyy-MM-dd")
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_desde.setFixedHeight(36)
        self.fecha_desde.setFont(QFont("Segoe UI", 10))

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDisplayFormat("yyyy-MM-dd")
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.setFixedHeight(36)
        self.fecha_hasta.setFont(QFont("Segoe UI", 10))

        lbl_desde = QLabel("Desde:")
        lbl_hasta = QLabel("Hasta:")
        lbl_desde.setStyleSheet(f"color: {DESACTIVADO};")
        lbl_hasta.setStyleSheet(f"color: {DESACTIVADO};")

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.setFixedHeight(36)
        btn_buscar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_buscar.setStyleSheet(_BTN_BUSCAR_STYLE)
        btn_buscar.clicked.connect(self.cargar_datos)

        filtros.addWidget(lbl_desde)
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(lbl_hasta)
        filtros.addWidget(self.fecha_hasta)
        filtros.addStretch(1)
        filtros.addWidget(btn_buscar)
        content.addLayout(filtros)

        self.tabla = _make_tabla(
            ["ID", "Fecha", "Cliente", "Vendedor", "Forma de Pago", "Total"]
        )
        content.addWidget(self.tabla)

        self.lbl_total = QLabel("Total del periodo: -")
        self.lbl_total.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.lbl_total.setStyleSheet(
            f"color: {TEXTO_BOTON}; background: {FONDO_B}; border: 1px solid {BORDE};"
            f" border-radius: 8px; padding: 6px 10px;"
        )
        content.addWidget(self.lbl_total, alignment=Qt.AlignRight)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT v.id_venta, v.fecha, c.nombre AS cliente,
                       ven.nombre AS vendedor, v.forma_pago, v.total
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                LEFT JOIN Vendedores ven ON ven.id_vendedor = v.id_vendedor
                WHERE CAST(v.fecha AS date) BETWEEN ? AND ?
                ORDER BY v.fecha DESC
            """
            cursor.execute(sql, (
                self.fecha_desde.date().toPython(),
                self.fecha_hasta.date().toPython(),
            ))
            filas = cursor.fetchall()
            self._datos = filas

            self.tabla.setRowCount(0)
            total = 0.0
            for fila in filas:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                valores = [
                    fila.id_venta,
                    _fmt_fecha(fila.fecha),
                    fila.cliente or "",
                    fila.vendedor or "",
                    fila.forma_pago or "",
                    _fmt_money(fila.total),
                ]
                aligns = [
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla.setItem(row, col, _tabla_item(valor, align))
                try:
                    total += float(fila.total or 0)
                except Exception:
                    pass

            self.lbl_total.setText(f"Total del periodo: {_fmt_money(total)}")
            self.btn_pdf.setEnabled(bool(filas))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos:\n{e}")

    def exportar_pdf(self):
        desde = self.fecha_desde.date().toString("yyyy-MM-dd")
        hasta = self.fecha_hasta.date().toString("yyyy-MM-dd")
        _guardar_pdf(
            self,
            "Reporte Ventas por Periodo",
            f"ventas_periodo_{desde}_{hasta}.pdf",
            self._armar_html(desde, hasta),
        )

    def _armar_html(self, desde, hasta):
        total = 0.0
        filas_html = ""
        for d in self._datos:
            total += float(d.total or 0)
            filas_html += f"""
                <tr>
                    <td class="num">{escape(str(d.id_venta))}</td>
                    <td class="txt">{escape(_fmt_fecha(d.fecha))}</td>
                    <td class="txt">{escape(str(d.cliente or ""))}</td>
                    <td class="txt">{escape(str(d.vendedor or ""))}</td>
                    <td class="txt">{escape(str(d.forma_pago or ""))}</td>
                    <td class="num">{escape(_fmt_money(d.total))}</td>
                </tr>"""
        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">REPORTE DE VENTAS POR PERIODO</div>
                <div class="sub">Del {escape(desde)} al {escape(hasta)}</div>
            </div>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:8%; text-align:right;">ID</th>
                        <th style="width:17%;">Fecha</th>
                        <th style="width:20%;">Cliente</th>
                        <th style="width:20%;">Vendedor</th>
                        <th style="width:17%;">Forma de Pago</th>
                        <th style="width:18%; text-align:right;">Total</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label">TOTAL DEL PERIODO:</td>
                    <td class="value">{escape(_fmt_money(total))}</td>
                </tr>
            </table>
            <div class="footer">Reporte generado por Sistema Galería de Arte</div>
        </div>
        </body></html>"""

    def regresar(self):
        self.hide()
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# 2. VentanaReportePinturasPopulares
# ---------------------------------------------------------------------------

class VentanaReportePinturasPopulares(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self._datos = []

        self.setWindowTitle("Pinturas populares")
        self.setMinimumSize(QSize(980, 640))
        self.setStyleSheet(_VENTANA_STYLE)

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setMinimumSize(940, 580)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)
        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(28, 22, 28, 22)
        content.setSpacing(12)

        titulo = QLabel("Pinturas populares")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(titulo)

        subtitulo = QLabel("Ranking de pinturas más vendidas por cantidad en el periodo")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(linea)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDisplayFormat("yyyy-MM-dd")
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_desde.setFixedHeight(36)
        self.fecha_desde.setFont(QFont("Segoe UI", 10))

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDisplayFormat("yyyy-MM-dd")
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.setFixedHeight(36)
        self.fecha_hasta.setFont(QFont("Segoe UI", 10))

        lbl_desde = QLabel("Desde:")
        lbl_hasta = QLabel("Hasta:")
        lbl_desde.setStyleSheet(f"color: {DESACTIVADO};")
        lbl_hasta.setStyleSheet(f"color: {DESACTIVADO};")

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.setFixedHeight(36)
        btn_buscar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_buscar.setStyleSheet(_BTN_BUSCAR_STYLE)
        btn_buscar.clicked.connect(self.cargar_datos)

        filtros.addWidget(lbl_desde)
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(lbl_hasta)
        filtros.addWidget(self.fecha_hasta)
        filtros.addStretch(1)
        filtros.addWidget(btn_buscar)
        content.addLayout(filtros)

        self.tabla = _make_tabla(
            ["#", "Título", "Artista", "Precio", "Cant. vendida", "Total generado"]
        )
        content.addWidget(self.tabla)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT p.titulo, a.nombre AS artista, p.precio,
                       SUM(dv.cantidad) AS total_vendidas,
                       SUM(dv.subtotal) AS total_generado
                FROM DetalleVenta dv
                JOIN Pinturas p ON p.id_pintura = dv.id_pintura
                LEFT JOIN Artistas a ON a.id_artista = p.id_artista
                JOIN Ventas v ON v.id_venta = dv.id_venta
                WHERE CAST(v.fecha AS date) BETWEEN ? AND ?
                GROUP BY p.titulo, a.nombre, p.precio
                ORDER BY total_vendidas DESC
            """
            cursor.execute(sql, (
                self.fecha_desde.date().toPython(),
                self.fecha_hasta.date().toPython(),
            ))
            filas = cursor.fetchall()
            self._datos = filas

            self.tabla.setRowCount(0)
            for pos, fila in enumerate(filas, start=1):
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                valores = [
                    pos,
                    fila.titulo or "",
                    fila.artista or "",
                    _fmt_money(fila.precio),
                    int(fila.total_vendidas or 0),
                    _fmt_money(fila.total_generado),
                ]
                aligns = [
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla.setItem(row, col, _tabla_item(valor, align))

            self.btn_pdf.setEnabled(bool(filas))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos:\n{e}")

    def exportar_pdf(self):
        desde = self.fecha_desde.date().toString("yyyy-MM-dd")
        hasta = self.fecha_hasta.date().toString("yyyy-MM-dd")
        _guardar_pdf(
            self,
            "Reporte Pinturas Populares",
            f"pinturas_populares_{desde}_{hasta}.pdf",
            self._armar_html(desde, hasta),
        )

    def _armar_html(self, desde, hasta):
        filas_html = ""
        for pos, d in enumerate(self._datos, start=1):
            filas_html += f"""
                <tr>
                    <td class="num">{pos}</td>
                    <td class="txt">{escape(str(d.titulo or ""))}</td>
                    <td class="txt">{escape(str(d.artista or ""))}</td>
                    <td class="num">{escape(_fmt_money(d.precio))}</td>
                    <td class="num">{int(d.total_vendidas or 0)}</td>
                    <td class="num">{escape(_fmt_money(d.total_generado))}</td>
                </tr>"""
        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">PINTURAS MÁS POPULARES</div>
                <div class="sub">Del {escape(desde)} al {escape(hasta)}</div>
            </div>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:6%; text-align:right;">#</th>
                        <th style="width:28%;">Título</th>
                        <th style="width:22%;">Artista</th>
                        <th style="width:14%; text-align:right;">Precio</th>
                        <th style="width:14%; text-align:right;">Cant.</th>
                        <th style="width:16%; text-align:right;">Total generado</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
            <div class="footer">Reporte generado por Sistema Galería de Arte</div>
        </div>
        </body></html>"""

    def regresar(self):
        self.hide()
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# 3. VentanaReporteInventario
# ---------------------------------------------------------------------------

class VentanaReporteInventario(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self._datos = []

        self.setWindowTitle("Inventario")
        self.setMinimumSize(QSize(980, 660))
        self.setStyleSheet(_VENTANA_STYLE)

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setMinimumSize(940, 600)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)
        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(28, 22, 28, 22)
        content.setSpacing(12)

        titulo = QLabel("Inventario")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(titulo)

        subtitulo = QLabel("Estado actual del inventario de pinturas")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(linea)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet(f"color: {DESACTIVADO};")

        self.combo_estado = QComboBox()
        self.combo_estado.setFixedHeight(36)
        self.combo_estado.setFont(QFont("Segoe UI", 10))
        self.combo_estado.addItems(["Todos", "Disponible", "Vendido", "Reservado"])

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.setFixedHeight(36)
        btn_buscar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_buscar.setStyleSheet(_BTN_BUSCAR_STYLE)
        btn_buscar.clicked.connect(self.cargar_datos)

        filtros.addWidget(lbl_estado)
        filtros.addWidget(self.combo_estado)
        filtros.addStretch(1)
        filtros.addWidget(btn_buscar)
        content.addLayout(filtros)

        self.tabla = _make_tabla(
            ["ID", "Título", "Artista", "Técnica", "Precio", "Estado"]
        )
        content.addWidget(self.tabla)

        totales_row = QHBoxLayout()
        totales_row.setSpacing(10)

        self.lbl_total_pinturas = QLabel("Total: 0")
        self.lbl_disponibles = QLabel("Disponibles: 0")
        self.lbl_vendidas = QLabel("Vendidas: 0")

        lbl_style = (
            f"color: {TEXTO_BOTON}; background: {FONDO_B}; border: 1px solid {BORDE};"
            f" border-radius: 8px; padding: 6px 10px;"
        )
        for lbl in (self.lbl_total_pinturas, self.lbl_disponibles, self.lbl_vendidas):
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(lbl_style)
            totales_row.addWidget(lbl)

        totales_row.addStretch(1)
        content.addLayout(totales_row)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            cursor = self.conexion.cursor()
            estado = self.combo_estado.currentText()
            if estado == "Todos":
                sql = """
                    SELECT p.id_pintura, p.titulo, a.nombre AS artista,
                           p.tecnica, p.precio, p.estado
                    FROM Pinturas p
                    LEFT JOIN Artistas a ON a.id_artista = p.id_artista
                    ORDER BY p.id_pintura
                """
                cursor.execute(sql)
            else:
                sql = """
                    SELECT p.id_pintura, p.titulo, a.nombre AS artista,
                           p.tecnica, p.precio, p.estado
                    FROM Pinturas p
                    LEFT JOIN Artistas a ON a.id_artista = p.id_artista
                    WHERE p.estado = ?
                    ORDER BY p.id_pintura
                """
                cursor.execute(sql, (estado,))

            filas = cursor.fetchall()
            self._datos = filas

            self.tabla.setRowCount(0)
            cnt_disponibles = 0
            cnt_vendidas = 0
            for fila in filas:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                estado_val = str(fila.estado or "")
                if estado_val.lower() == "disponible":
                    cnt_disponibles += 1
                elif estado_val.lower() == "vendido":
                    cnt_vendidas += 1

                valores = [
                    fila.id_pintura,
                    fila.titulo or "",
                    fila.artista or "",
                    fila.tecnica or "",
                    _fmt_money(fila.precio),
                    estado_val,
                ]
                aligns = [
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla.setItem(row, col, _tabla_item(valor, align))

            self.lbl_total_pinturas.setText(f"Total: {len(filas)}")
            self.lbl_disponibles.setText(f"Disponibles: {cnt_disponibles}")
            self.lbl_vendidas.setText(f"Vendidas: {cnt_vendidas}")
            self.btn_pdf.setEnabled(bool(filas))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos:\n{e}")

    def exportar_pdf(self):
        estado = self.combo_estado.currentText()
        _guardar_pdf(
            self,
            "Reporte Inventario",
            f"inventario_{estado.lower()}.pdf",
            self._armar_html(estado),
        )

    def _armar_html(self, estado):
        cnt_disp = sum(1 for d in self._datos if str(d.estado or "").lower() == "disponible")
        cnt_vend = sum(1 for d in self._datos if str(d.estado or "").lower() == "vendido")
        filas_html = ""
        for d in self._datos:
            filas_html += f"""
                <tr>
                    <td class="num">{escape(str(d.id_pintura))}</td>
                    <td class="txt">{escape(str(d.titulo or ""))}</td>
                    <td class="txt">{escape(str(d.artista or ""))}</td>
                    <td class="txt">{escape(str(d.tecnica or ""))}</td>
                    <td class="num">{escape(_fmt_money(d.precio))}</td>
                    <td class="txt">{escape(str(d.estado or ""))}</td>
                </tr>"""
        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">INVENTARIO DE PINTURAS</div>
                <div class="sub">Filtro: {escape(estado)}</div>
            </div>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:8%; text-align:right;">ID</th>
                        <th style="width:26%;">Título</th>
                        <th style="width:20%;">Artista</th>
                        <th style="width:18%;">Técnica</th>
                        <th style="width:14%; text-align:right;">Precio</th>
                        <th style="width:14%;">Estado</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label">TOTAL PINTURAS:</td>
                    <td class="value">{len(self._datos)}</td>
                </tr>
                <tr>
                    <td class="label">DISPONIBLES:</td>
                    <td class="value">{cnt_disp}</td>
                </tr>
                <tr>
                    <td class="label">VENDIDAS:</td>
                    <td class="value">{cnt_vend}</td>
                </tr>
            </table>
            <div class="footer">Reporte generado por Sistema Galería de Arte</div>
        </div>
        </body></html>"""

    def regresar(self):
        self.hide()
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# 4. VentanaReporteComprasPorProveedor
# ---------------------------------------------------------------------------

class VentanaReporteComprasPorProveedor(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self._datos = []

        self.setWindowTitle("Compras por proveedor")
        self.setMinimumSize(QSize(980, 760))
        self.setStyleSheet(_VENTANA_STYLE)

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setMinimumSize(940, 700)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)
        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(28, 22, 28, 22)
        content.setSpacing(12)

        titulo = QLabel("Compras por proveedor")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(titulo)

        subtitulo = QLabel("Resumen de compras agrupadas por proveedor en el periodo")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(linea)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDisplayFormat("yyyy-MM-dd")
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_desde.setFixedHeight(36)
        self.fecha_desde.setFont(QFont("Segoe UI", 10))

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDisplayFormat("yyyy-MM-dd")
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.setFixedHeight(36)
        self.fecha_hasta.setFont(QFont("Segoe UI", 10))

        lbl_desde = QLabel("Desde:")
        lbl_hasta = QLabel("Hasta:")
        lbl_desde.setStyleSheet(f"color: {DESACTIVADO};")
        lbl_hasta.setStyleSheet(f"color: {DESACTIVADO};")

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.setFixedHeight(36)
        btn_buscar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_buscar.setStyleSheet(_BTN_BUSCAR_STYLE)
        btn_buscar.clicked.connect(self.cargar_datos)

        filtros.addWidget(lbl_desde)
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(lbl_hasta)
        filtros.addWidget(self.fecha_hasta)
        filtros.addStretch(1)
        filtros.addWidget(btn_buscar)
        content.addLayout(filtros)

        self.tabla = _make_tabla(
            ["Proveedor", "Núm. compras", "Total gastado"],
            min_height=220,
        )
        self.tabla.itemSelectionChanged.connect(self._seleccion_cambio)
        content.addWidget(self.tabla)

        lbl_detalle = QLabel("Compras del proveedor seleccionado")
        lbl_detalle.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        lbl_detalle.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(lbl_detalle)

        self.tabla_detalle = _make_tabla(
            ["ID Compra", "Fecha", "Total"],
            min_height=180,
        )
        self.tabla_detalle.setSelectionMode(QAbstractItemView.NoSelection)
        content.addWidget(self.tabla_detalle)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT pr.nombre AS proveedor,
                       COUNT(c.id_compra) AS num_compras,
                       SUM(c.total) AS total_gastado
                FROM Compras c
                LEFT JOIN Proveedores pr ON pr.id_proveedor = c.id_proveedor
                WHERE CAST(c.fecha AS date) BETWEEN ? AND ?
                GROUP BY pr.nombre
                ORDER BY total_gastado DESC
            """
            cursor.execute(sql, (
                self.fecha_desde.date().toPython(),
                self.fecha_hasta.date().toPython(),
            ))
            filas = cursor.fetchall()
            self._datos = filas

            self.tabla.setRowCount(0)
            self.tabla_detalle.setRowCount(0)
            for fila in filas:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                valores = [
                    fila.proveedor or "",
                    int(fila.num_compras or 0),
                    _fmt_money(fila.total_gastado),
                ]
                aligns = [
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla.setItem(row, col, _tabla_item(valor, align))

            if filas:
                self.tabla.selectRow(0)

            self.btn_pdf.setEnabled(bool(filas))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos:\n{e}")

    def _seleccion_cambio(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            self.tabla_detalle.setRowCount(0)
            return
        proveedor = self.tabla.item(fila, 0)
        if not proveedor:
            return
        nombre_proveedor = proveedor.text()
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT c.id_compra, c.fecha, c.total
                FROM Compras c
                LEFT JOIN Proveedores pr ON pr.id_proveedor = c.id_proveedor
                WHERE pr.nombre = ?
                  AND CAST(c.fecha AS date) BETWEEN ? AND ?
                ORDER BY c.fecha DESC
            """
            cursor.execute(sql, (
                nombre_proveedor,
                self.fecha_desde.date().toPython(),
                self.fecha_hasta.date().toPython(),
            ))
            detalles = cursor.fetchall()
            self.tabla_detalle.setRowCount(0)
            for det in detalles:
                row = self.tabla_detalle.rowCount()
                self.tabla_detalle.insertRow(row)
                valores = [
                    det.id_compra,
                    _fmt_fecha(det.fecha),
                    _fmt_money(det.total),
                ]
                aligns = [
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla_detalle.setItem(row, col, _tabla_item(valor, align))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el detalle:\n{e}")

    def exportar_pdf(self):
        desde = self.fecha_desde.date().toString("yyyy-MM-dd")
        hasta = self.fecha_hasta.date().toString("yyyy-MM-dd")
        _guardar_pdf(
            self,
            "Reporte Compras por Proveedor",
            f"compras_proveedor_{desde}_{hasta}.pdf",
            self._armar_html(desde, hasta),
        )

    def _armar_html(self, desde, hasta):
        total_general = sum(float(d.total_gastado or 0) for d in self._datos)
        filas_html = ""
        for d in self._datos:
            filas_html += f"""
                <tr>
                    <td class="txt">{escape(str(d.proveedor or ""))}</td>
                    <td class="num">{int(d.num_compras or 0)}</td>
                    <td class="num">{escape(_fmt_money(d.total_gastado))}</td>
                </tr>"""
        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">COMPRAS POR PROVEEDOR</div>
                <div class="sub">Del {escape(desde)} al {escape(hasta)}</div>
            </div>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:50%;">Proveedor</th>
                        <th style="width:24%; text-align:right;">Núm. compras</th>
                        <th style="width:26%; text-align:right;">Total gastado</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label">TOTAL GENERAL:</td>
                    <td class="value">{escape(_fmt_money(total_general))}</td>
                </tr>
            </table>
            <div class="footer">Reporte generado por Sistema Galería de Arte</div>
        </div>
        </body></html>"""

    def regresar(self):
        self.hide()
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# 5. VentanaReporteVentasPorCliente
# ---------------------------------------------------------------------------

class VentanaReporteVentasPorCliente(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self._datos = []

        self.setWindowTitle("Ventas por cliente")
        self.setMinimumSize(QSize(980, 760))
        self.setStyleSheet(_VENTANA_STYLE)

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setMinimumSize(940, 700)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)
        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(28, 22, 28, 22)
        content.setSpacing(12)

        titulo = QLabel("Ventas por cliente")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(titulo)

        subtitulo = QLabel("Resumen de ventas agrupadas por cliente en el periodo")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(linea)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDisplayFormat("yyyy-MM-dd")
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_desde.setFixedHeight(36)
        self.fecha_desde.setFont(QFont("Segoe UI", 10))

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDisplayFormat("yyyy-MM-dd")
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.setFixedHeight(36)
        self.fecha_hasta.setFont(QFont("Segoe UI", 10))

        lbl_desde = QLabel("Desde:")
        lbl_hasta = QLabel("Hasta:")
        lbl_desde.setStyleSheet(f"color: {DESACTIVADO};")
        lbl_hasta.setStyleSheet(f"color: {DESACTIVADO};")

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.setFixedHeight(36)
        btn_buscar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_buscar.setStyleSheet(_BTN_BUSCAR_STYLE)
        btn_buscar.clicked.connect(self.cargar_datos)

        filtros.addWidget(lbl_desde)
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(lbl_hasta)
        filtros.addWidget(self.fecha_hasta)
        filtros.addStretch(1)
        filtros.addWidget(btn_buscar)
        content.addLayout(filtros)

        self.tabla = _make_tabla(
            ["Cliente", "Núm. ventas", "Total comprado"],
            min_height=220,
        )
        self.tabla.itemSelectionChanged.connect(self._seleccion_cambio)
        content.addWidget(self.tabla)

        lbl_detalle = QLabel("Ventas del cliente seleccionado")
        lbl_detalle.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        lbl_detalle.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(lbl_detalle)

        self.tabla_detalle = _make_tabla(
            ["ID", "Fecha", "Total", "Forma de pago"],
            min_height=180,
        )
        self.tabla_detalle.setSelectionMode(QAbstractItemView.NoSelection)
        content.addWidget(self.tabla_detalle)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT c.nombre AS cliente,
                       COUNT(v.id_venta) AS num_ventas,
                       SUM(v.total) AS total_comprado
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                WHERE CAST(v.fecha AS date) BETWEEN ? AND ?
                GROUP BY c.nombre
                ORDER BY total_comprado DESC
            """
            cursor.execute(sql, (
                self.fecha_desde.date().toPython(),
                self.fecha_hasta.date().toPython(),
            ))
            filas = cursor.fetchall()
            self._datos = filas

            self.tabla.setRowCount(0)
            self.tabla_detalle.setRowCount(0)
            for fila in filas:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                valores = [
                    fila.cliente or "",
                    int(fila.num_ventas or 0),
                    _fmt_money(fila.total_comprado),
                ]
                aligns = [
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla.setItem(row, col, _tabla_item(valor, align))

            if filas:
                self.tabla.selectRow(0)

            self.btn_pdf.setEnabled(bool(filas))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos:\n{e}")

    def _seleccion_cambio(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            self.tabla_detalle.setRowCount(0)
            return
        cliente_item = self.tabla.item(fila, 0)
        if not cliente_item:
            return
        nombre_cliente = cliente_item.text()
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT v.id_venta, v.fecha, v.total, v.forma_pago
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                WHERE c.nombre = ?
                  AND CAST(v.fecha AS date) BETWEEN ? AND ?
                ORDER BY v.fecha DESC
            """
            cursor.execute(sql, (
                nombre_cliente,
                self.fecha_desde.date().toPython(),
                self.fecha_hasta.date().toPython(),
            ))
            detalles = cursor.fetchall()
            self.tabla_detalle.setRowCount(0)
            for det in detalles:
                row = self.tabla_detalle.rowCount()
                self.tabla_detalle.insertRow(row)
                valores = [
                    det.id_venta,
                    _fmt_fecha(det.fecha),
                    _fmt_money(det.total),
                    det.forma_pago or "",
                ]
                aligns = [
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla_detalle.setItem(row, col, _tabla_item(valor, align))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el detalle:\n{e}")

    def exportar_pdf(self):
        desde = self.fecha_desde.date().toString("yyyy-MM-dd")
        hasta = self.fecha_hasta.date().toString("yyyy-MM-dd")
        _guardar_pdf(
            self,
            "Reporte Ventas por Cliente",
            f"ventas_cliente_{desde}_{hasta}.pdf",
            self._armar_html(desde, hasta),
        )

    def _armar_html(self, desde, hasta):
        total_general = sum(float(d.total_comprado or 0) for d in self._datos)
        filas_html = ""
        for d in self._datos:
            filas_html += f"""
                <tr>
                    <td class="txt">{escape(str(d.cliente or ""))}</td>
                    <td class="num">{int(d.num_ventas or 0)}</td>
                    <td class="num">{escape(_fmt_money(d.total_comprado))}</td>
                </tr>"""
        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">VENTAS POR CLIENTE</div>
                <div class="sub">Del {escape(desde)} al {escape(hasta)}</div>
            </div>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:50%;">Cliente</th>
                        <th style="width:24%; text-align:right;">Núm. ventas</th>
                        <th style="width:26%; text-align:right;">Total comprado</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label">TOTAL GENERAL:</td>
                    <td class="value">{escape(_fmt_money(total_general))}</td>
                </tr>
            </table>
            <div class="footer">Reporte generado por Sistema Galería de Arte</div>
        </div>
        </body></html>"""

    def regresar(self):
        self.hide()
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# 6. VentanaReporteVentasPorMes
# ---------------------------------------------------------------------------

class VentanaReporteVentasPorMes(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self._datos = []

        self.setWindowTitle("Ventas por mes")
        self.setMinimumSize(QSize(780, 620))
        self.setStyleSheet(_VENTANA_STYLE)

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setMinimumSize(740, 560)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)
        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(28, 22, 28, 22)
        content.setSpacing(12)

        titulo = QLabel("Ventas por mes")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(titulo)

        subtitulo = QLabel("Ventas agrupadas por mes para el año seleccionado")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(linea)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        lbl_anio = QLabel("Año:")
        lbl_anio.setStyleSheet(f"color: {DESACTIVADO};")

        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2000, 2100)
        self.spin_anio.setValue(QDate.currentDate().year())
        self.spin_anio.setFixedHeight(36)
        self.spin_anio.setFont(QFont("Segoe UI", 10))

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.setFixedHeight(36)
        btn_buscar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_buscar.setStyleSheet(_BTN_BUSCAR_STYLE)
        btn_buscar.clicked.connect(self.cargar_datos)

        filtros.addWidget(lbl_anio)
        filtros.addWidget(self.spin_anio)
        filtros.addStretch(1)
        filtros.addWidget(btn_buscar)
        content.addLayout(filtros)

        self.tabla = _make_tabla(["Mes", "Núm. ventas", "Total"])
        content.addWidget(self.tabla)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT MONTH(fecha) AS mes,
                       COUNT(*) AS num_ventas,
                       SUM(total) AS total
                FROM Ventas
                WHERE YEAR(fecha) = ?
                GROUP BY MONTH(fecha)
                ORDER BY mes
            """
            cursor.execute(sql, (self.spin_anio.value(),))
            filas = cursor.fetchall()
            self._datos = filas

            self.tabla.setRowCount(0)
            for fila in filas:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                mes_num = int(fila.mes or 0)
                nombre_mes = _MESES_ES[mes_num] if 1 <= mes_num <= 12 else str(mes_num)
                valores = [
                    nombre_mes,
                    int(fila.num_ventas or 0),
                    _fmt_money(fila.total),
                ]
                aligns = [
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla.setItem(row, col, _tabla_item(valor, align))

            self.btn_pdf.setEnabled(bool(filas))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos:\n{e}")

    def exportar_pdf(self):
        anio = self.spin_anio.value()
        _guardar_pdf(
            self,
            f"Reporte Ventas por Mes {anio}",
            f"ventas_mes_{anio}.pdf",
            self._armar_html(anio),
        )

    def _armar_html(self, anio):
        total_general = sum(float(d.total or 0) for d in self._datos)
        total_ventas = sum(int(d.num_ventas or 0) for d in self._datos)
        filas_html = ""
        for d in self._datos:
            mes_num = int(d.mes or 0)
            nombre_mes = _MESES_ES[mes_num] if 1 <= mes_num <= 12 else str(mes_num)
            filas_html += f"""
                <tr>
                    <td class="txt">{escape(nombre_mes)}</td>
                    <td class="num">{int(d.num_ventas or 0)}</td>
                    <td class="num">{escape(_fmt_money(d.total))}</td>
                </tr>"""
        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">VENTAS POR MES — {anio}</div>
            </div>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:40%;">Mes</th>
                        <th style="width:28%; text-align:right;">Núm. ventas</th>
                        <th style="width:32%; text-align:right;">Total</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label">VENTAS TOTALES:</td>
                    <td class="value">{total_ventas}</td>
                </tr>
                <tr>
                    <td class="label">TOTAL DEL AÑO:</td>
                    <td class="value">{escape(_fmt_money(total_general))}</td>
                </tr>
            </table>
            <div class="footer">Reporte generado por Sistema Galería de Arte</div>
        </div>
        </body></html>"""

    def regresar(self):
        self.hide()
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# 7. VentanaReporteFacturas
# ---------------------------------------------------------------------------

class VentanaReporteFacturas(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self.venta_actual = None
        self.detalles_actuales = []

        self.setWindowTitle("Facturas")
        self.setMinimumSize(QSize(980, 760))
        self.setStyleSheet(_VENTANA_STYLE)

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setMinimumSize(940, 700)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)
        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(28, 22, 28, 22)
        content.setSpacing(12)

        titulo = QLabel("Facturas")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(titulo)

        subtitulo = QLabel("Selecciona una venta y genera la factura en PDF con desglose de IVA")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(linea)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDisplayFormat("yyyy-MM-dd")
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_desde.setFixedHeight(36)
        self.fecha_desde.setFont(QFont("Segoe UI", 10))

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDisplayFormat("yyyy-MM-dd")
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.setFixedHeight(36)
        self.fecha_hasta.setFont(QFont("Segoe UI", 10))

        lbl_desde = QLabel("Desde:")
        lbl_hasta = QLabel("Hasta:")
        lbl_desde.setStyleSheet(f"color: {DESACTIVADO};")
        lbl_hasta.setStyleSheet(f"color: {DESACTIVADO};")

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.setFixedHeight(36)
        btn_buscar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_buscar.setStyleSheet(_BTN_BUSCAR_STYLE)
        btn_buscar.clicked.connect(self.cargar_ventas)

        filtros.addWidget(lbl_desde)
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(lbl_hasta)
        filtros.addWidget(self.fecha_hasta)
        filtros.addStretch(1)
        filtros.addWidget(btn_buscar)
        content.addLayout(filtros)

        self.tabla_ventas = _make_tabla(
            ["ID", "Fecha", "Cliente", "Vendedor", "Pago", "Total"],
            min_height=240,
        )
        self.tabla_ventas.itemSelectionChanged.connect(self._seleccion_cambio)
        content.addWidget(self.tabla_ventas)

        detalle_header = QHBoxLayout()
        lbl_detalle = QLabel("Detalle de la venta seleccionada")
        lbl_detalle.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        lbl_detalle.setStyleSheet(f"color: {TEXTO};")
        detalle_header.addWidget(lbl_detalle)
        detalle_header.addStretch(1)
        self.lbl_venta_info = QLabel("Sin venta seleccionada")
        self.lbl_venta_info.setFont(QFont("Segoe UI", 10))
        self.lbl_venta_info.setStyleSheet(f"color: {DESACTIVADO};")
        detalle_header.addWidget(self.lbl_venta_info)
        content.addLayout(detalle_header)

        self.tabla_detalle = _make_tabla(
            ["Pintura", "Cantidad", "Precio unitario", "Subtotal"],
            min_height=180,
        )
        self.tabla_detalle.setSelectionMode(QAbstractItemView.NoSelection)
        content.addWidget(self.tabla_detalle)

        resumen = QHBoxLayout()
        self.lbl_cliente = QLabel("Cliente: -")
        self.lbl_vendedor = QLabel("Vendedor: -")
        self.lbl_pago = QLabel("Forma de pago: -")
        self.lbl_total = QLabel("Total: -")

        lbl_style = (
            f"color: {TEXTO_BOTON}; background: {FONDO_B}; border: 1px solid {BORDE};"
            f" border-radius: 8px; padding: 6px 10px;"
        )
        for lbl in (self.lbl_cliente, self.lbl_vendedor, self.lbl_pago, self.lbl_total):
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(lbl_style)
            resumen.addWidget(lbl)
        resumen.addStretch(1)
        content.addLayout(resumen)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_pdf = QPushButton("Generar Factura PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.cargar_ventas()

    def cargar_ventas(self):
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT v.id_venta, v.fecha, c.nombre AS cliente,
                       ven.nombre AS vendedor, v.forma_pago, v.total
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                LEFT JOIN Vendedores ven ON ven.id_vendedor = v.id_vendedor
                WHERE CAST(v.fecha AS date) BETWEEN ? AND ?
                ORDER BY v.fecha DESC, v.id_venta DESC
            """
            cursor.execute(sql, (
                self.fecha_desde.date().toPython(),
                self.fecha_hasta.date().toPython(),
            ))
            filas = cursor.fetchall()

            self.tabla_ventas.setRowCount(0)
            self.venta_actual = None
            self.detalles_actuales = []
            self.tabla_detalle.setRowCount(0)
            self.btn_pdf.setEnabled(False)

            for fila in filas:
                row = self.tabla_ventas.rowCount()
                self.tabla_ventas.insertRow(row)
                valores = [
                    fila.id_venta,
                    _fmt_fecha(fila.fecha),
                    fila.cliente or "",
                    fila.vendedor or "",
                    fila.forma_pago or "",
                    _fmt_money(fila.total),
                ]
                aligns = [
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla_ventas.setItem(row, col, _tabla_item(valor, align))

            if filas:
                self.tabla_ventas.selectRow(0)
            else:
                self._limpiar_detalle()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las ventas:\n{e}")

    def _seleccion_cambio(self):
        fila = self.tabla_ventas.currentRow()
        if fila < 0:
            self._limpiar_detalle()
            return
        try:
            id_venta = int(self.tabla_ventas.item(fila, 0).text())
            self.cargar_detalle_venta(id_venta)
        except Exception:
            self._limpiar_detalle()

    def cargar_detalle_venta(self, id_venta):
        try:
            cursor = self.conexion.cursor()
            sql_cabecera = """
                SELECT v.id_venta, v.fecha, v.forma_pago, v.total,
                       c.id_cliente, c.nombre AS cliente, c.correo, c.telefono,
                       ven.nombre AS vendedor
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                LEFT JOIN Vendedores ven ON ven.id_vendedor = v.id_vendedor
                WHERE v.id_venta = ?
            """
            cursor.execute(sql_cabecera, (id_venta,))
            venta = cursor.fetchone()
            if not venta:
                self._limpiar_detalle()
                return

            sql_detalle = """
                SELECT p.titulo, dv.cantidad, dv.subtotal, p.precio
                FROM DetalleVenta dv
                LEFT JOIN Pinturas p ON p.id_pintura = dv.id_pintura
                WHERE dv.id_venta = ?
                ORDER BY dv.id_detalle ASC
            """
            cursor.execute(sql_detalle, (id_venta,))
            detalles = cursor.fetchall()

            self.venta_actual = venta
            self.detalles_actuales = detalles

            self.lbl_venta_info.setText(f"Venta #{venta.id_venta} | {_fmt_fecha(venta.fecha)}")
            self.lbl_cliente.setText(f"Cliente: {venta.cliente or '-'}")
            self.lbl_vendedor.setText(f"Vendedor: {venta.vendedor or '-'}")
            self.lbl_pago.setText(f"Forma de pago: {venta.forma_pago or '-'}")
            self.lbl_total.setText(f"Total: {_fmt_money(venta.total)}")

            self.tabla_detalle.setRowCount(0)
            for det in detalles:
                row = self.tabla_detalle.rowCount()
                self.tabla_detalle.insertRow(row)
                precio_unitario = det.precio if det.precio is not None else 0
                subtotal = det.subtotal if det.subtotal is not None else 0
                valores = [
                    det.titulo or "",
                    str(det.cantidad or 0),
                    _fmt_money(precio_unitario),
                    _fmt_money(subtotal),
                ]
                aligns = [
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla_detalle.setItem(row, col, _tabla_item(valor, align))

            self.btn_pdf.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el detalle:\n{e}")

    def _limpiar_detalle(self):
        self.venta_actual = None
        self.detalles_actuales = []
        self.lbl_venta_info.setText("Sin venta seleccionada")
        self.lbl_cliente.setText("Cliente: -")
        self.lbl_vendedor.setText("Vendedor: -")
        self.lbl_pago.setText("Forma de pago: -")
        self.lbl_total.setText("Total: -")
        self.tabla_detalle.setRowCount(0)
        self.btn_pdf.setEnabled(False)

    def exportar_pdf(self):
        if not self.venta_actual:
            QMessageBox.information(self, "Sin selección", "Selecciona una venta primero.")
            return
        nombre_sugerido = f"factura_{self.venta_actual.id_venta}.pdf"
        _guardar_pdf(
            self,
            f"Factura #{self.venta_actual.id_venta}",
            nombre_sugerido,
            self._armar_html_factura(self.venta_actual, self.detalles_actuales),
        )

    def _armar_html_factura(self, venta, detalles):
        total_bruto = float(getattr(venta, "total", 0) or 0)
        iva_rate = 0.16
        subtotal_sin_iva = total_bruto / (1 + iva_rate)
        iva = total_bruto - subtotal_sin_iva

        filas_html = ""
        for d in detalles:
            titulo = escape(str(d.titulo or ""))
            cantidad = int(d.cantidad or 0)
            precio_unitario = float(d.precio or 0)
            subtotal = float(d.subtotal or 0)
            filas_html += f"""
                <tr>
                    <td class="txt">{titulo}</td>
                    <td class="num">{cantidad}</td>
                    <td class="num">{escape(_fmt_money(precio_unitario))}</td>
                    <td class="num">{escape(_fmt_money(subtotal))}</td>
                </tr>"""

        fecha = escape(_fmt_fecha(venta.fecha))
        cliente = escape(str(getattr(venta, "cliente", "") or "-"))
        correo = escape(str(getattr(venta, "correo", "") or "-"))
        telefono = escape(str(getattr(venta, "telefono", "") or "-"))
        vendedor = escape(str(getattr(venta, "vendedor", "") or "-"))
        forma_pago = escape(str(getattr(venta, "forma_pago", "") or "-"))

        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">FACTURA</div>
                <div class="sub">Folio #{venta.id_venta}</div>
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
                <tbody>{filas_html}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label" style="font-size:11pt; font-weight:normal;">Subtotal (sin IVA):</td>
                    <td class="value" style="font-size:11pt;">{escape(_fmt_money(subtotal_sin_iva))}</td>
                </tr>
                <tr>
                    <td class="label" style="font-size:11pt; font-weight:normal;">IVA (16%):</td>
                    <td class="value" style="font-size:11pt;">{escape(_fmt_money(iva))}</td>
                </tr>
                <tr>
                    <td class="label">TOTAL:</td>
                    <td class="value">{escape(_fmt_money(total_bruto))}</td>
                </tr>
            </table>
            <div class="footer">
                Gracias por su compra. Conserve esta factura.
            </div>
        </div>
        </body></html>"""

    def regresar(self):
        self.hide()
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)

class ReporteSimpleVentana(QMainWindow):
    def __init__(self, titulo_reporte, ventana_padre=None):
        super().__init__(ventana_padre)
        self.ventana_padre = ventana_padre
        self.setWindowTitle(titulo_reporte)
        self.setMinimumSize(QSize(520, 360))

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setFixedSize(520, 360)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)

        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(30, 24, 30, 24)
        content.setSpacing(14)

        lbl_titulo = QLabel(titulo_reporte)
        lbl_titulo.setAlignment(Qt.AlignHCenter)
        lbl_titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.DemiBold))
        lbl_titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(lbl_titulo)

        lbl_info = QLabel("Aquí irá el formulario, consulta o gráfico de este reporte.")
        lbl_info.setAlignment(Qt.AlignHCenter)
        lbl_info.setWordWrap(True)
        lbl_info.setFont(QFont("Segoe UI", 11))
        lbl_info.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(lbl_info)

        content.addStretch(1)

        btn_regresar = QPushButton("Cerrar")
        btn_regresar.setCursor(Qt.PointingHandCursor)
        btn_regresar.setFixedHeight(40)
        btn_regresar.setFont(QFont("Segoe UI", 12))
        btn_regresar.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {PRIMARIO};
                border: 1px solid {BORDE};
                border-radius: 10px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {PRIMARIO};
                color: white;
            }}
        """)
        btn_regresar.clicked.connect(self.close)
        content.addWidget(btn_regresar, alignment=Qt.AlignHCenter)

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)


class ReportesVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__(ventana_principal)
        self.ventana_principal = ventana_principal

        self.setWindowTitle("Reportes")
        self.setMinimumSize(QSize(590, 829))

        self.ventana_reporte_actual = None

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(3)

        card = Carta()
        card.setFixedSize(590, 909)

        card_wrap = QHBoxLayout()
        card_wrap.addStretch(1)
        card_wrap.addWidget(card)
        card_wrap.addStretch(1)
        main.addLayout(card_wrap)

        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(42, 36, 42, 30)
        content.setSpacing(14)

        lbl_title = QLabel("Reportes")
        lbl_title.setAlignment(Qt.AlignHCenter)
        lbl_title.setFont(QFont("Segoe UI", 28, QFont.Weight.DemiBold))
        lbl_title.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(lbl_title)

        lbl_sub = QLabel("Selecciona el tipo de reporte que deseas consultar")
        lbl_sub.setAlignment(Qt.AlignHCenter)
        lbl_sub.setFont(QFont("Segoe UI", 12))
        lbl_sub.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(lbl_sub)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(line)

        content.addSpacing(6)

        botones = [
            ("Ventas por periodo", self.abrir_ventas_por_periodo),
            ("Pinturas populares", self.abrir_pinturas_populares),
            ("Inventario", self.abrir_inventario),
            ("Compras por proveedor", self.abrir_compras_por_proveedor),
            ("Ventas por cliente", self.abrir_ventas_por_cliente),
            ("Ventas por mes", self.abrir_ventas_por_mes),
            ("Facturas", self.abrir_facturas),
            ("Nota de ventas", self.abrir_nota_de_ventas),
        ]

        self.menu_items = []
        content.addSpacing(6)
        for texto, accion in botones:
            item = ItemMenu(texto)
            self.menu_items.append(item)
            content.addWidget(item)
            content.addSpacing(ESPACIADO_BOTON)

            item.button.clicked.connect(accion)

        content.addStretch(1)

        btn_back = QPushButton("Regresar")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setFixedHeight(40)
        btn_back.setFont(QFont("Segoe UI", 13))
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {DESACTIVADO};
                border: none;
            }}
            QPushButton:hover {{
                color: {PRIMARIO};
                text-decoration: underline;
            }}
        """)
        btn_back.clicked.connect(self.regresar)
        content.addWidget(btn_back, alignment=Qt.AlignHCenter)

    def regresar(self):
        self.hide()
        if self.ventana_principal is not None:
            self.ventana_principal.show()
            self.ventana_principal.raise_()
            self.ventana_principal.activateWindow()

    def _abrir(self, ventana):
        self.ventana_reporte_actual = ventana
        self.hide()
        ventana.show()
        ventana.raise_()
        ventana.activateWindow()

    def abrir_ventas_por_periodo(self):
        self._abrir(VentanaReporteVentasPeriodo(self.ventana_principal.conexion, self))

    def abrir_pinturas_populares(self):
        self._abrir(VentanaReportePinturasPopulares(self.ventana_principal.conexion, self))

    def abrir_inventario(self):
        self._abrir(VentanaReporteInventario(self.ventana_principal.conexion, self))

    def abrir_compras_por_proveedor(self):
        self._abrir(VentanaReporteComprasPorProveedor(self.ventana_principal.conexion, self))

    def abrir_ventas_por_cliente(self):
        self._abrir(VentanaReporteVentasPorCliente(self.ventana_principal.conexion, self))

    def abrir_ventas_por_mes(self):
        self._abrir(VentanaReporteVentasPorMes(self.ventana_principal.conexion, self))

    def abrir_facturas(self):
        self._abrir(VentanaReporteFacturas(self.ventana_principal.conexion, self))

    def abrir_nota_de_ventas(self):
        self.ventana_reporte_actual = NotaVentasVentana(self.ventana_principal.conexion, self)
        self.hide()
        self.ventana_reporte_actual.show()
        self.ventana_reporte_actual.raise_()
        self.ventana_reporte_actual.activateWindow()
