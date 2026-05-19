import os
import subprocess
import sys
import tempfile
from html import escape

from PySide6.QtCore import Qt, QSize, QDate, QSizeF, QMarginsF
from PySide6.QtGui import (
    QFont, QPainter, QColor, QPdfWriter, QPageSize, QPageLayout, QTextDocument
)
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QDateEdit, QAbstractItemView
)

from modulos.Fondo import Fondo
from modulos.Carta import Carta
from modulos.PaletaColores import *


class NotaVentasVentana(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self.venta_actual = None
        self.detalles_actuales = []

        self.setWindowTitle("Nota de ventas")
        self.setMinimumSize(QSize(980, 760))

        self.setStyleSheet(f"""
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

            QTableWidget {{
                background: {SUPERFICIE};
                color: {TEXTO};
                gridline-color: {BORDE};
                border: 1px solid {BORDE};
                border-radius: 10px;
                alternate-background-color: {FONDO_B};
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
        """)

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

        titulo = QLabel("Nota de ventas")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(titulo)

        subtitulo = QLabel("Selecciona una venta y genera la nota en PDF tamaño carta")
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

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDisplayFormat("yyyy-MM-dd")
        self.fecha_hasta.setDate(QDate.currentDate())

        for w in (self.fecha_desde, self.fecha_hasta):
            w.setFixedHeight(36)
            w.setFont(QFont("Segoe UI", 10))

        lbl_desde = QLabel("Desde:")
        lbl_hasta = QLabel("Hasta:")
        lbl_desde.setStyleSheet(f"color: {DESACTIVADO};")
        lbl_hasta.setStyleSheet(f"color: {DESACTIVADO};")

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.setFixedHeight(36)
        btn_buscar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_buscar.setStyleSheet(f"""
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
        """)
        btn_buscar.clicked.connect(self.cargar_ventas)

        filtros.addWidget(lbl_desde)
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(lbl_hasta)
        filtros.addWidget(self.fecha_hasta)
        filtros.addStretch(1)
        filtros.addWidget(btn_buscar)

        content.addLayout(filtros)

        self.tabla_ventas = QTableWidget(0, 6)
        self.tabla_ventas.setHorizontalHeaderLabels([
            "ID", "Fecha", "Cliente", "Vendedor", "Pago", "Total"
        ])
        self.tabla_ventas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_ventas.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_ventas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_ventas.verticalHeader().setVisible(False)
        self.tabla_ventas.setAlternatingRowColors(True)
        self.tabla_ventas.setFont(QFont("Segoe UI", 10))
        self.tabla_ventas.setStyleSheet(f"""
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
        """)
        self.tabla_ventas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_ventas.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tabla_ventas.setMinimumHeight(260)
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

        self.tabla_detalle = QTableWidget(0, 4)
        self.tabla_detalle.setHorizontalHeaderLabels([
            "Pintura", "Cantidad", "Precio unitario", "Subtotal"
        ])
        self.tabla_detalle.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_detalle.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabla_detalle.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_detalle.verticalHeader().setVisible(False)
        self.tabla_detalle.setAlternatingRowColors(True)
        self.tabla_detalle.setFont(QFont("Segoe UI", 10))
        self.tabla_detalle.setStyleSheet(self.tabla_ventas.styleSheet())
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla_detalle.setMinimumHeight(220)
        content.addWidget(self.tabla_detalle)

        resumen = QHBoxLayout()
        self.lbl_cliente = QLabel("Cliente: -")
        self.lbl_vendedor = QLabel("Vendedor: -")
        self.lbl_pago = QLabel("Forma de pago: -")
        self.lbl_total = QLabel("Total: -")

        for lbl in (self.lbl_cliente, self.lbl_vendedor, self.lbl_pago, self.lbl_total):
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(f"""
                color: {TEXTO_BOTON};
                background: {FONDO_B};
                border: 1px solid {BORDE};
                border-radius: 8px;
                padding: 6px 10px;
            """)
            resumen.addWidget(lbl)

        resumen.addStretch(1)
        content.addLayout(resumen)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_preview = QPushButton("Vista Previa")
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        self.btn_preview.setFixedHeight(40)
        self.btn_preview.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_preview.setStyleSheet(f"""
            QPushButton {{
                background: {SUPERFICIE};
                color: {PRIMARIO};
                border: 1px solid {PRIMARIO};
                border-radius: 10px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {PRIMARIO};
                color: white;
            }}
            QPushButton:pressed {{
                background: {ACENTO};
                color: {TEXTO};
            }}
            QPushButton:disabled {{
                background: {BORDE_BOTON};
                color: {DESACTIVADO};
                border: 1px solid {BORDE_BOTON};
            }}
        """)
        self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self.vista_previa_pdf)

        self.btn_pdf = QPushButton("Generar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(f"""
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
        """)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(f"""
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
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_preview)
        acciones.addSpacing(8)
        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.cargar_ventas()

    def cargar_ventas(self):
        try:
            cursor = self.conexion.cursor()
            sql = """
                SELECT
                    v.id_venta,
                    v.fecha,
                    c.nombre AS cliente,
                    ven.nombre AS vendedor,
                    v.forma_pago,
                    v.total
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                LEFT JOIN Vendedores ven ON ven.id_vendedor = v.id_vendedor
                WHERE DATE(v.fecha) BETWEEN ? AND ?
                ORDER BY v.fecha DESC, v.id_venta DESC;
            """
            cursor.execute(sql, (
                self.fecha_desde.date().toPython(),
                self.fecha_hasta.date().toPython()
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
                    self._fmt_fecha(fila.fecha),
                    fila.cliente or "",
                    fila.vendedor or "",
                    fila.forma_pago or "",
                    self._fmt_money(fila.total)
                ]

                for col, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))
                    item.setForeground(QColor(TEXTO))
                    if col in (0, 5):
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.tabla_ventas.setItem(row, col, item)

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
                SELECT
                    v.id_venta,
                    v.fecha,
                    v.forma_pago,
                    v.total,
                    c.id_cliente,
                    c.nombre AS cliente,
                    c.correo,
                    c.telefono,
                    ven.nombre AS vendedor
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                LEFT JOIN Vendedores ven ON ven.id_vendedor = v.id_vendedor
                WHERE v.id_venta = ?;
            """
            cursor.execute(sql_cabecera, (id_venta,))
            venta = cursor.fetchone()
            if not venta:
                self._limpiar_detalle()
                return

            sql_detalle = """
                SELECT
                    p.titulo,
                    dv.cantidad,
                    dv.subtotal,
                    p.precio
                FROM DetalleVenta dv
                LEFT JOIN Pinturas p ON p.id_pintura = dv.id_pintura
                WHERE dv.id_venta = ?
                ORDER BY dv.id_detalle ASC;
            """
            cursor.execute(sql_detalle, (id_venta,))
            detalles = cursor.fetchall()

            self.venta_actual = venta
            self.detalles_actuales = detalles

            self.lbl_venta_info.setText(f"Venta #{venta.id_venta} | {self._fmt_fecha(venta.fecha)}")
            self.lbl_cliente.setText(f"Cliente: {venta.cliente or '-'}")
            self.lbl_vendedor.setText(f"Vendedor: {venta.vendedor or '-'}")
            self.lbl_pago.setText(f"Forma de pago: {venta.forma_pago or '-'}")
            self.lbl_total.setText(f"Total: {self._fmt_money(venta.total)}")

            self.tabla_detalle.setRowCount(0)
            for det in detalles:
                row = self.tabla_detalle.rowCount()
                self.tabla_detalle.insertRow(row)

                precio_unitario = det.precio if det.precio is not None else 0
                subtotal = det.subtotal if det.subtotal is not None else 0

                valores = [
                    det.titulo or "",
                    str(det.cantidad or 0),
                    self._fmt_money(precio_unitario),
                    self._fmt_money(subtotal),
                ]

                for col, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))
                    item.setForeground(QColor(TEXTO))
                    if col == 0:
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.tabla_detalle.setItem(row, col, item)

            self.btn_pdf.setEnabled(True)
            self.btn_preview.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el detalle:\n{e}")

    def exportar_pdf(self):
        if not self.venta_actual:
            QMessageBox.information(self, "Sin selección", "Selecciona una venta primero.")
            return

        nombre_sugerido = f"nota_venta_{self.venta_actual.id_venta}.pdf"
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar nota de venta",
            nombre_sugerido,
            "PDF (*.pdf)"
        )
        if not ruta:
            return

        try:
            self._crear_pdf_carta(ruta)
            QMessageBox.information(self, "Listo", f"PDF generado correctamente:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF:\n{e}")

    def vista_previa_pdf(self):
        if not self.venta_actual:
            QMessageBox.information(self, "Sin selección", "Selecciona una venta primero.")
            return
        try:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf",
                prefix=f"nota_venta_{self.venta_actual.id_venta}_preview_",
                delete=False,
            )
            ruta = tmp.name
            tmp.close()
            self._crear_pdf_carta(ruta)
            if sys.platform.startswith("win"):
                os.startfile(ruta)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar la vista previa:\n{e}")

    def _crear_pdf_carta(self, ruta_pdf):
        if not self.venta_actual:
            raise ValueError("No hay una venta seleccionada.")

        venta = self.venta_actual
        html = self._armar_html_carta(venta, self.detalles_actuales)

        dpi = 96
        margin_mm = 15

        writer = QPdfWriter(ruta_pdf)
        writer.setResolution(dpi)
        writer.setTitle(f"Nota de venta #{venta.id_venta}")
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


    def _armar_html_carta(self, venta, detalles):
        filas = ""
        for d in detalles:
            titulo = escape(str(d.titulo or ""))
            cantidad = int(d.cantidad or 0)
            precio_unitario = float(d.precio or 0)
            subtotal = float(d.subtotal or 0)

            filas += f"""
                <tr>
                    <td class="txt">{titulo}</td>
                    <td class="num">{cantidad}</td>
                    <td class="num">{self._fmt_money(precio_unitario)}</td>
                    <td class="num">{self._fmt_money(subtotal)}</td>
                </tr>
            """

        fecha = escape(self._fmt_fecha(venta.fecha))
        cliente = escape(str(getattr(venta, "cliente", "") or "-"))
        correo = escape(str(getattr(venta, "correo", "") or "-"))
        telefono = escape(str(getattr(venta, "telefono", "") or "-"))
        vendedor = escape(str(getattr(venta, "vendedor", "") or "-"))
        forma_pago = escape(str(getattr(venta, "forma_pago", "") or "-"))
        total = self._fmt_money(getattr(venta, "total", 0))

        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: "DejaVu Sans", Arial, sans-serif;
                    font-size: 11pt;
                    color: #1F1F1F;
                    margin: 0;
                    padding: 0;
                }}

                .page {{
                    width: 100%;
                }}

                .header {{
                    text-align: center;
                    margin-bottom: 16px;
                }}

                .brand {{
                    font-size: 18pt;
                    font-weight: bold;
                    letter-spacing: 1px;
                }}

                .title {{
                    font-size: 13pt;
                    font-weight: bold;
                    margin-top: 4px;
                }}

                .sub {{
                    font-size: 9pt;
                    color: #5B5B5B;
                    margin-top: 2px;
                }}

                .line {{
                    border-top: 1px solid #E7E1D8;
                    margin: 12px 0;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    table-layout: fixed;
                }}

                .info {{
                    margin-bottom: 4px;
                }}

                .info td {{
                    padding: 4px 0;
                    vertical-align: top;
                    word-wrap: break-word;
                }}

                .info .label {{
                    width: 14%;
                    font-weight: bold;
                }}

                .info .value {{
                    width: 36%;
                }}

                .items thead th {{
                    text-align: left;
                    font-size: 10pt;
                    border-bottom: 1px solid #1F1F1F;
                    padding: 8px 8px 6px 8px;
                }}

                .items td {{
                    border-bottom: 1px dotted #DED6CC;
                    padding: 8px 8px;
                    vertical-align: top;
                    word-wrap: break-word;
                }}

                .txt {{
                    word-break: break-word;
                }}

                .num {{
                    text-align: right;
                    white-space: nowrap;
                }}

                .summary {{
                    margin-top: 16px;
                    width: 100%;
                    border-collapse: collapse;
                }}

                .summary td {{
                    padding: 4px 8px;
                }}

                .summary .label {{
                    width: 82%;
                    text-align: right;
                    font-weight: bold;
                    font-size: 12pt;
                }}

                .summary .value {{
                    width: 18%;
                    text-align: right;
                    font-size: 13pt;
                    font-weight: bold;
                    white-space: nowrap;
                }}

                .footer {{
                    margin-top: 22px;
                    text-align: center;
                    font-size: 9pt;
                    color: #5B5B5B;
                }}
            </style>
        </head>
        <body>
            <div class="page">
                <div class="header">
                    <div class="brand">GALERÍA DE ARTE</div>
                    <div class="title">NOTA DE VENTA</div>
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
                            <th style="width: 52%;">Pintura</th>
                            <th style="width: 12%; text-align:right;">Cant.</th>
                            <th style="width: 18%; text-align:right;">P.U.</th>
                            <th style="width: 18%; text-align:right;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas}
                    </tbody>
                </table>

                <table class="summary">
                    <tr>
                        <td class="label">TOTAL:</td>
                        <td class="value">{total}</td>
                    </tr>
                </table>

                <div class="footer">
                    Gracias por su compra. Conserve este comprobante.
                </div>
            </div>
        </body>
        </html>
        """

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
        self.btn_preview.setEnabled(False)

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

    def _fmt_fecha(self, valor):
        if valor is None:
            return "-"
        try:
            return valor.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(valor)

    def _fmt_money(self, valor):
        try:
            return f"${float(valor):,.2f}"
        except Exception:
            return "$0.00"
