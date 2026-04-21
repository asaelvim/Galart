from datetime import datetime
from html import escape

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMessageBox, QInputDialog
)

from modulos.Fondo import Fondo
from modulos.Carta import Carta
from modulos.PaletaColores import BORDE, DESACTIVADO, FONDO_B, TEXTO_BOTON
from ventanas.Reportes import (
    _VENTANA_STYLE, _BTN_PDF_STYLE, _BTN_PREVIEW_STYLE, _BTN_VOLVER_STYLE,
    _PDF_CSS, _make_tabla, _tabla_item, _guardar_pdf, _vista_previa_pdf, _fmt_money
)


MAX_OPENING_AMOUNT = 999999999.99


def _fmt_fecha(valor):
    if valor is None:
        return "-"
    try:
        return valor.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(valor)


class CorteCajaVentana(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre
        self._id_apertura = None
        self._monto_apertura = 0.0
        self._fecha_apertura = None
        self._total_ventas = 0.0
        self._total_general = 0.0
        self._datos_ventas = []

        self.setWindowTitle("Corte de Caja")
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

        titulo = QLabel("Corte de Caja")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        content.addWidget(titulo)

        subtitulo = QLabel("Resumen de operaciones del día")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(linea)

        fila_apertura = QHBoxLayout()
        self.lbl_apertura = QLabel("Monto de apertura: $0.00")
        self.lbl_apertura.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        fila_apertura.addWidget(self.lbl_apertura)
        fila_apertura.addStretch(1)

        btn_editar = QPushButton("Editar")
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.setFixedHeight(36)
        btn_editar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        btn_editar.setStyleSheet(_BTN_PREVIEW_STYLE)
        btn_editar.clicked.connect(self.editar_apertura)
        fila_apertura.addWidget(btn_editar)
        content.addLayout(fila_apertura)

        self.tabla = _make_tabla(["ID", "Cliente", "Vendedor", "Forma de Pago", "Total"])
        content.addWidget(self.tabla)

        self.lbl_total = QLabel("Total del día (apertura + ventas): $0.00")
        self.lbl_total.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.lbl_total.setStyleSheet(
            f"color: {TEXTO_BOTON}; background: {FONDO_B}; border: 1px solid {BORDE};"
            f" border-radius: 8px; padding: 6px 10px;"
        )
        content.addWidget(self.lbl_total, alignment=Qt.AlignRight)

        acciones = QHBoxLayout()
        acciones.addStretch(1)

        self.btn_preview = QPushButton("Vista Previa")
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        self.btn_preview.setFixedHeight(40)
        self.btn_preview.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_preview.setStyleSheet(_BTN_PREVIEW_STYLE)
        self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self.vista_previa_pdf)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        btn_cerrar_caja = QPushButton("🔒 Cerrar Caja")
        btn_cerrar_caja.setCursor(Qt.PointingHandCursor)
        btn_cerrar_caja.setFixedHeight(40)
        btn_cerrar_caja.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        btn_cerrar_caja.setStyleSheet(_BTN_PDF_STYLE)
        btn_cerrar_caja.clicked.connect(self.cerrar_caja)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        acciones.addWidget(self.btn_preview)
        acciones.addSpacing(8)
        acciones.addWidget(self.btn_pdf)
        acciones.addSpacing(8)
        acciones.addWidget(btn_cerrar_caja)
        acciones.addSpacing(8)
        acciones.addWidget(btn_volver)
        content.addLayout(acciones)

        self.recargar()

    def _asegurar_apertura_hoy(self):
        cursor = self.conexion.cursor()
        cursor.execute(
            """
            INSERT INTO AperturaCaja (monto, fecha)
            SELECT ?, GETDATE()
            WHERE NOT EXISTS (
                SELECT 1
                FROM AperturaCaja
                WHERE CAST(fecha AS DATE) = CAST(GETDATE() AS DATE)
            )
            """,
            (0,),
        )
        self.conexion.commit()

        cursor.execute(
            """
            SELECT TOP 1 id_apertura, monto, fecha
            FROM AperturaCaja
            WHERE CAST(fecha AS DATE) = CAST(GETDATE() AS DATE)
            ORDER BY id_apertura DESC
            """
        )
        return cursor.fetchone()

    def recargar(self):
        try:
            apertura = self._asegurar_apertura_hoy()
            self._id_apertura = apertura.id_apertura if apertura else None
            self._monto_apertura = float((apertura.monto if apertura else 0) or 0)
            self._fecha_apertura = apertura.fecha if apertura else None

            cursor = self.conexion.cursor()
            cursor.execute(
                """
                SELECT v.id_venta, c.nombre AS cliente, ven.nombre AS vendedor,
                       v.forma_pago, v.total
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                LEFT JOIN Vendedores ven ON ven.id_vendedor = v.id_vendedor
                WHERE CAST(v.fecha AS DATE) = CAST(GETDATE() AS DATE)
                ORDER BY v.fecha
                """
            )
            filas = cursor.fetchall()
            self._datos_ventas = filas

            self.tabla.setRowCount(0)
            self._total_ventas = 0.0
            for fila in filas:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                valores = [
                    fila.id_venta,
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
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (valor, align) in enumerate(zip(valores, aligns)):
                    self.tabla.setItem(row, col, _tabla_item(valor, align))
                self._total_ventas += float(fila.total or 0)

            self._total_general = self._monto_apertura + self._total_ventas
            self.lbl_apertura.setText(f"Monto de apertura: {_fmt_money(self._monto_apertura)}")
            self.lbl_total.setText(
                f"Total del día (apertura + ventas): {_fmt_money(self._total_general)}"
            )
            hay_datos = bool(self._datos_ventas)
            self.btn_pdf.setEnabled(hay_datos)
            self.btn_preview.setEnabled(hay_datos)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el corte de caja:\n{e}")

    def editar_apertura(self):
        monto, ok = QInputDialog.getDouble(
            self,
            "Editar monto de apertura",
            "Monto de apertura:",
            self._monto_apertura,
            0.0,
            MAX_OPENING_AMOUNT,
            2,
        )
        if not ok:
            return
        try:
            if self._id_apertura is None:
                apertura = self._asegurar_apertura_hoy()
                self._id_apertura = apertura.id_apertura if apertura else None
            if self._id_apertura is None:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo obtener un registro de apertura de caja para actualizar.",
                )
                return
            cursor = self.conexion.cursor()
            cursor.execute(
                "UPDATE AperturaCaja SET monto = ? WHERE id_apertura = ?",
                (monto, self._id_apertura),
            )
            self.conexion.commit()
            self.recargar()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el monto de apertura:\n{e}")

    def _armar_html(self):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        filas_html = ""
        for fila in self._datos_ventas:
            filas_html += f"""
                <tr>
                    <td class="num">{escape(str(fila.id_venta))}</td>
                    <td class="txt">{escape(str(fila.cliente or ""))}</td>
                    <td class="txt">{escape(str(fila.vendedor or ""))}</td>
                    <td class="txt">{escape(str(fila.forma_pago or ""))}</td>
                    <td class="num">{escape(_fmt_money(fila.total))}</td>
                </tr>"""

        return f"""
        <html><head><style>{_PDF_CSS}</style></head><body>
        <div class="page">
            <div class="header">
                <div class="brand">GALERÍA DE ARTE</div>
                <div class="title">CORTE DE CAJA</div>
                <div class="sub">Fecha: {escape(fecha_hoy)}</div>
            </div>
            <div class="line"></div>
            <table class="info">
                <tr>
                    <td class="label">Monto apertura:</td>
                    <td class="value">{escape(_fmt_money(self._monto_apertura))}</td>
                    <td class="label">Fecha:</td>
                    <td class="value">{escape(_fmt_fecha(self._fecha_apertura))}</td>
                </tr>
            </table>
            <div class="line"></div>
            <table class="items">
                <thead>
                    <tr>
                        <th style="width:10%; text-align:right;">ID</th>
                        <th style="width:26%;">Cliente</th>
                        <th style="width:24%;">Vendedor</th>
                        <th style="width:20%;">Forma de Pago</th>
                        <th style="width:20%; text-align:right;">Total</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
            <table class="summary">
                <tr>
                    <td class="label">TOTAL VENTAS:</td>
                    <td class="value">{escape(_fmt_money(self._total_ventas))}</td>
                </tr>
                <tr>
                    <td class="label">MONTO APERTURA:</td>
                    <td class="value">{escape(_fmt_money(self._monto_apertura))}</td>
                </tr>
                <tr>
                    <td class="label">TOTAL GENERAL:</td>
                    <td class="value">{escape(_fmt_money(self._total_general))}</td>
                </tr>
            </table>
            <div class="footer">Reporte generado por Sistema Galería de Arte</div>
        </div>
        </body></html>"""

    def exportar_pdf(self):
        fecha_hoy = datetime.now().strftime("%Y%m%d")
        _guardar_pdf(
            self,
            "Corte de Caja",
            f"corte_caja_{fecha_hoy}.pdf",
            self._armar_html(),
        )

    def vista_previa_pdf(self):
        fecha_hoy = datetime.now().strftime("%Y%m%d")
        _vista_previa_pdf(
            self,
            "Corte de Caja",
            f"corte_caja_{fecha_hoy}.pdf",
            self._armar_html(),
        )

    def cerrar_caja(self):
        respuesta = QMessageBox.question(
            self,
            "Confirmar cierre de caja",
            f"Se registrará el cierre con un monto total de {_fmt_money(self._total_general)}.\n"
            "¿Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            cursor = self.conexion.cursor()
            cursor.execute(
                """
                INSERT INTO CierreCaja (montoTotal, fecha)
                SELECT ?, GETDATE()
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM CierreCaja
                    WHERE CAST(fecha AS DATE) = CAST(GETDATE() AS DATE)
                )
                """,
                (self._total_general,),
            )
            filas_insertadas = cursor.rowcount
            if filas_insertadas == 0:
                QMessageBox.warning(self, "Aviso", "Ya existe un cierre de caja registrado para hoy.")
                return
            self.conexion.commit()
            QMessageBox.information(self, "Listo", "Cierre de caja registrado correctamente.")
            self.recargar()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el cierre de caja:\n{e}")

    def regresar(self):
        if self.ventana_padre:
            self.ventana_padre.show()
        self.close()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.ventana_corte_caja = None
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)
