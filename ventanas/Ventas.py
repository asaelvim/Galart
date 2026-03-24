from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import List, Optional, Tuple

from config.conexion import obtener_conexion

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
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
# Repositorio Ventas
# =========================
class VentasRepo:
    def fetch_all(self) -> List[Tuple[int, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT v.id_venta, "
                "ISNULL(cl.nombre, '') AS cliente, "
                "v.fecha, v.total "
                "FROM Ventas v "
                "LEFT JOIN Clientes cl ON v.id_cliente = cl.id_cliente "
                "ORDER BY v.id_venta",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                vid = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] else ""
                total = f"{float(r[3]):.2f}" if r[3] is not None else "0.00"
                result.append((vid, cliente, fecha, total))
            return result

    def fetch_by_id(self, venta_id: int) -> List[Tuple]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT v.id_venta, "
                "ISNULL(cl.nombre, '') AS cliente, "
                "v.fecha, v.total, v.id_cliente "
                "FROM Ventas v "
                "LEFT JOIN Clientes cl ON v.id_cliente = cl.id_cliente "
                "WHERE v.id_venta = ?",
                (venta_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                vid = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] else ""
                total = f"{float(r[3]):.2f}" if r[3] is not None else "0.00"
                id_cliente = int(r[4]) if r[4] is not None else 0
                result.append((vid, cliente, fecha, total, id_cliente))
            return result

    def insert(self, id_cliente: int, fecha: str, total: float) -> int:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Ventas (id_cliente, fecha, total) "
                "VALUES (?, ?, ?); SELECT SCOPE_IDENTITY()",
                (id_cliente, fecha, total),
            )
            cur.nextset()
            new_id = int(cur.fetchone()[0])
            conn.commit()
            return new_id

    def update(self, venta_id: int, id_cliente: int, fecha: str, total: float) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Ventas SET id_cliente = ?, fecha = ?, total = ? WHERE id_venta = ?",
                (id_cliente, fecha, total, venta_id),
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
    def fetch_by_venta(self, venta_id: int) -> List[Tuple[int, str, int, str, int]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT d.id_detalle, ISNULL(p.titulo, '') AS titulo, "
                "d.cantidad, d.subtotal, d.id_pintura "
                "FROM DetalleVenta d "
                "LEFT JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                "WHERE d.id_venta = ? "
                "ORDER BY d.id_detalle",
                (venta_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_detalle = int(r[0])
                titulo = str(r[1]) if r[1] else ""
                cantidad = int(r[2])
                subtotal = f"{float(r[3]):.2f}" if r[3] is not None else "0.00"
                id_pintura = int(r[4]) if r[4] is not None else 0
                result.append((id_detalle, titulo, cantidad, subtotal, id_pintura))
            return result


# =========================
# Repositorio Cotizaciones
# =========================
class CotizacionesImportRepo:
    def fetch_all(self) -> List[Tuple[int, str, str, str, int]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_cotizacion, "
                "ISNULL(cl.nombre, '') AS cliente, "
                "c.fecha, c.total, c.id_cliente "
                "FROM Cotizaciones c "
                "LEFT JOIN Clientes cl ON c.id_cliente = cl.id_cliente "
                "ORDER BY c.id_cotizacion",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_cotizacion = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] else ""
                total = f"{float(r[3]):.2f}" if r[3] is not None else "0.00"
                id_cliente = int(r[4]) if r[4] is not None else 0
                result.append((id_cotizacion, cliente, fecha, total, id_cliente))
            return result

    def fetch_by_id(self, cotizacion_id: int) -> List[Tuple[int, str, str, str, int]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_cotizacion, "
                "ISNULL(cl.nombre, '') AS cliente, "
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
                fecha = r[2].strftime("%Y-%m-%d") if r[2] else ""
                total = f"{float(r[3]):.2f}" if r[3] is not None else "0.00"
                id_cliente = int(r[4]) if r[4] is not None else 0
                result.append((id_cotizacion, cliente, fecha, total, id_cliente))
            return result

    def fetch_detalle(self, cotizacion_id: int) -> List[Tuple[int, str, int, float, float]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT d.id_pintura, ISNULL(p.titulo, '') AS titulo, "
                "d.cantidad, d.precio_unitario, d.subtotal "
                "FROM DetalleCotizacion d "
                "LEFT JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                "WHERE d.id_cotizacion = ? "
                "ORDER BY d.id_detalle",
                (cotizacion_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_pintura = int(r[0])
                titulo = str(r[1]) if r[1] else ""
                cantidad = int(r[2]) if r[2] is not None else 0
                precio_unitario = float(r[3]) if r[3] is not None else 0.0
                subtotal = float(r[4]) if r[4] is not None else 0.0
                result.append((id_pintura, titulo, cantidad, precio_unitario, subtotal))
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
            "SELECT ISNULL(SUM(cantidad), 0) "
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
            "SELECT TOP 1 id_inventario, cantidad "
            "FROM Inventario "
            "WHERE id_pintura = ? "
            "ORDER BY id_inventario",
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
        self.setWindowTitle("Gestión de Ventas")
        self.setMinimumSize(1020, 740)

        self.repo = VentasRepo()
        self.detalle_repo = DetalleVentaRepo()
        self.cotizacion_repo = CotizacionesImportRepo()
        self.inventario_repo = InventarioRepo()

        self.current_id: Optional[int] = None
        # (id_pintura, titulo, cantidad, precio_unitario, subtotal_linea)
        self._detail_lines: List[Tuple[int, str, int, float, float]] = []

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

        # Cliente
        row_cliente = QHBoxLayout()
        row_cliente.setSpacing(12)
        row_cliente.addStretch(1)
        lbl_cliente = QLabel("Cliente:")
        lbl_cliente.setObjectName("MutedLabel")
        self.cmbCliente = QComboBox()
        self.cmbCliente.setObjectName("Combo")
        self.cmbCliente.setFixedWidth(260)
        row_cliente.addWidget(lbl_cliente)
        row_cliente.addWidget(self.cmbCliente)
        row_cliente.addStretch(1)
        card_layout.addLayout(row_cliente)

        # Cotización
        row_cot = QHBoxLayout()
        row_cot.setSpacing(12)
        row_cot.addStretch(1)
        lbl_cot = QLabel("Cotización:")
        lbl_cot.setObjectName("MutedLabel")
        self.cmbCotizacion = QComboBox()
        self.cmbCotizacion.setObjectName("Combo")
        self.cmbCotizacion.setFixedWidth(340)
        self.btnImportarCotizacion = self._button("Importar cotización", self.on_import_cotizacion, wide=True)
        row_cot.addWidget(lbl_cot)
        row_cot.addWidget(self.cmbCotizacion)
        row_cot.addWidget(self.btnImportarCotizacion)
        row_cot.addStretch(1)
        card_layout.addLayout(row_cot)

        # Fecha
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

        # Agregar línea
        row_line = QHBoxLayout()
        row_line.setSpacing(12)
        row_line.addStretch(1)
        lbl_pintura = QLabel("Pintura:")
        lbl_pintura.setObjectName("MutedLabel")
        self.cmbPintura = QComboBox()
        self.cmbPintura.setObjectName("Combo")
        self.cmbPintura.setFixedWidth(340)
        lbl_cantidad = QLabel("Cantidad:")
        lbl_cantidad.setObjectName("MutedLabel")
        self.spnCantidad = QSpinBox()
        self.spnCantidad.setObjectName("SpinBox")
        self.spnCantidad.setMinimum(1)
        self.spnCantidad.setMaximum(99999)
        self.spnCantidad.setFixedWidth(90)
        self.btnAgregarLinea = self._button("Agregar línea", self.on_add_line)
        row_line.addWidget(lbl_pintura)
        row_line.addWidget(self.cmbPintura)
        row_line.addSpacing(10)
        row_line.addWidget(lbl_cantidad)
        row_line.addWidget(self.spnCantidad)
        row_line.addWidget(self.btnAgregarLinea)
        row_line.addStretch(1)
        card_layout.addLayout(row_line)

        # Tabla detalle
        detail_frame = QFrame()
        detail_frame.setObjectName("TableFrame")
        df = QVBoxLayout(detail_frame)
        df.setContentsMargins(10, 10, 10, 10)

        self.detail_table = QTableWidget(0, 4)
        self.detail_table.setObjectName("Table")
        self.detail_table.setHorizontalHeaderLabels(["Pintura", "Cantidad", "Subtotal", ""])
        self.detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.verticalHeader().setVisible(False)
        detail_header = self.detail_table.horizontalHeader()
        detail_header.setSectionResizeMode(0, QHeaderView.Stretch)
        detail_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        detail_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        detail_header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.detail_table.setColumnWidth(3, 50)
        self.detail_table.setMaximumHeight(180)

        df.addWidget(self.detail_table)
        card_layout.addWidget(detail_frame)

        # Totales
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

        # Botones acción
        row_actions = QHBoxLayout()
        row_actions.setSpacing(12)
        row_actions.addStretch(1)
        self.btnGuardar = self._button("Guardar Venta", self.on_guardar, wide=True)
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

        # Buscar
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

        # Tabla ventas
        ventas_frame = QFrame()
        ventas_frame.setObjectName("TableFrame")
        vf = QVBoxLayout(ventas_frame)
        vf.setContentsMargins(10, 10, 10, 10)

        self.ventas_table = QTableWidget(0, 4)
        self.ventas_table.setObjectName("Table")
        self.ventas_table.setHorizontalHeaderLabels(["ID", "Cliente", "Fecha", "Total"])
        self.ventas_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ventas_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ventas_table.verticalHeader().setVisible(False)
        ventas_header = self.ventas_table.horizontalHeader()
        ventas_header.setSectionResizeMode(QHeaderView.Stretch)

        self.ventas_table.itemSelectionChanged.connect(self.on_venta_selected)
        vf.addWidget(self.ventas_table)
        card_layout.addWidget(ventas_frame)

        # Salir
        row_bottom = QHBoxLayout()
        row_bottom.addStretch(1)
        self.btnSalir = self._button("Salir", self.close, wide=True)
        row_bottom.addWidget(self.btnSalir)
        row_bottom.addStretch(1)
        card_layout.addLayout(row_bottom)

        main.addWidget(card)
        self.setStyleSheet(self._stylesheet())

        self._load_clientes_combo()
        self._load_pinturas_combo()
        self._load_cotizaciones_combo()
        self.load_all()

    def closeEvent(self, event):
        if self.ventana_principal is not None:
            self.ventana_principal.show()
        event.accept()

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

    def _load_clientes_combo(self) -> None:
        self.cmbCliente.clear()
        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(cur, "SELECT id_cliente, ISNULL(nombre, '') FROM Clientes ORDER BY nombre")
                rows = cur.fetchall()
                for r in rows:
                    self.cmbCliente.addItem(str(r[1]), r[0])
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _load_pinturas_combo(self) -> None:
        self.cmbPintura.clear()
        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(cur, "SELECT id_pintura, ISNULL(titulo, ''), ISNULL(precio, 0) FROM Pinturas ORDER BY titulo")
                rows = cur.fetchall()
                self.cmbPintura.addItem("-- Seleccionar pintura --", None)
                for r in rows:
                    id_pintura = int(r[0])
                    titulo = str(r[1]) if r[1] is not None else ""
                    precio = float(r[2]) if r[2] is not None else 0.0
                    self.cmbPintura.addItem(f"{titulo} - ${precio:.2f}", (id_pintura, titulo, precio))
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _load_cotizaciones_combo(self) -> None:
        self.cmbCotizacion.clear()
        try:
            cotizaciones = self.cotizacion_repo.fetch_all()
            self.cmbCotizacion.addItem("-- Seleccionar cotización --", None)
            for id_cotizacion, cliente, fecha, total, id_cliente in cotizaciones:
                texto = f"#{id_cotizacion} | {cliente} | {fecha} | ${total}"
                self.cmbCotizacion.addItem(texto, (id_cotizacion, id_cliente, fecha))
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _recalculate_totals(self) -> None:
        subtotal = sum(line[4] for line in self._detail_lines)
        self.lblSubtotal.setText(f"Subtotal: ${subtotal:.2f}")
        self.lblTotal.setText(f"Total: ${subtotal:.2f}")

    def _cantidad_solicitada_por_pintura(self, id_pintura: int, lines=None) -> int:
        lines = self._detail_lines if lines is None else lines
        return sum(cantidad for pid, _, cantidad, _, _ in lines if pid == id_pintura)

    def _validar_existencias_lineas(self, lines) -> bool:
        acumuladas = {}
        for id_pintura, _, cantidad, _, _ in lines:
            acumuladas[id_pintura] = acumuladas.get(id_pintura, 0) + cantidad

        for id_pintura, solicitada in acumuladas.items():
            disponible = self.inventario_repo.get_disponible(id_pintura)
            if solicitada > disponible:
                titulo = next((t for pid, t, _, _, _ in lines if pid == id_pintura), f"ID {id_pintura}")
                self._show_error(
                    "Existencias insuficientes",
                    f"La pintura '{titulo}' solo tiene {disponible} en inventario.\n"
                    f"Se están solicitando {solicitada}."
                )
                return False
        return True

    def _validar_existencias_lineas_cursor(self, cur, lines) -> bool:
        acumuladas = {}
        for id_pintura, _, cantidad, _, _ in lines:
            acumuladas[id_pintura] = acumuladas.get(id_pintura, 0) + cantidad

        for id_pintura, solicitada in acumuladas.items():
            disponible = self.inventario_repo.get_disponible_cursor(cur, id_pintura)
            if solicitada > disponible:
                titulo = next((t for pid, t, _, _, _ in lines if pid == id_pintura), f"ID {id_pintura}")
                self._show_error(
                    "Existencias insuficientes",
                    f"La pintura '{titulo}' solo tiene {disponible} en inventario.\n"
                    f"Se están solicitando {solicitada}."
                )
                return False
        return True

    def _refresh_detail_table(self) -> None:
        self.detail_table.setRowCount(0)
        for idx, (id_pintura, titulo, cantidad, precio_unitario, subtotal_linea) in enumerate(self._detail_lines):
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)
            self.detail_table.setItem(row, 0, QTableWidgetItem(titulo))
            self.detail_table.setItem(row, 1, QTableWidgetItem(str(cantidad)))
            self.detail_table.setItem(row, 2, QTableWidgetItem(f"${subtotal_linea:.2f}"))
            btn_quitar = QPushButton("X")
            btn_quitar.setObjectName("Btn")
            btn_quitar.setCursor(Qt.PointingHandCursor)
            btn_quitar.setFixedSize(30, 26)
            btn_quitar.clicked.connect(lambda checked=False, i=idx: self.on_remove_line(i))
            self.detail_table.setCellWidget(row, 3, btn_quitar)
        self._recalculate_totals()

    def clear_form(self) -> None:
        self.current_id = None
        if self.cmbCliente.count() > 0:
            self.cmbCliente.setCurrentIndex(0)
        if self.cmbCotizacion.count() > 0:
            self.cmbCotizacion.setCurrentIndex(0)
        self.dateFecha.setDate(QDate.currentDate())
        self._detail_lines.clear()
        self._refresh_detail_table()
        self.ventas_table.clearSelection()
        self.btnEliminar.setEnabled(False)

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_ventas_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_ventas_table(self, rows: List[Tuple]) -> None:
        self.ventas_table.setRowCount(0)
        for r, data in enumerate(rows):
            vid, cliente, fecha, total = data[:4]
            self.ventas_table.insertRow(r)
            for col, val in enumerate([str(vid), cliente, fecha, total]):
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

        id_pintura, titulo, precio = data
        cantidad = self.spnCantidad.value()

        if self._cantidad_solicitada_por_pintura(id_pintura) + cantidad > self.inventario_repo.get_disponible(id_pintura):
            disponible = self.inventario_repo.get_disponible(id_pintura)
            solicitada = self._cantidad_solicitada_por_pintura(id_pintura) + cantidad
            self._show_error(
                "Existencias insuficientes",
                f"La pintura '{titulo}' solo tiene {disponible} en inventario.\n"
                f"Estás intentando pedir {solicitada}."
            )
            return

        for i, (pid, t, cant, p_unit, sub) in enumerate(self._detail_lines):
            if pid == id_pintura:
                nueva_cantidad = cant + cantidad
                nuevo_subtotal = nueva_cantidad * p_unit
                self._detail_lines[i] = (pid, t, nueva_cantidad, p_unit, nuevo_subtotal)
                self._refresh_detail_table()
                return

        subtotal_linea = precio * cantidad
        self._detail_lines.append((id_pintura, titulo, cantidad, precio, subtotal_linea))
        self._refresh_detail_table()

    def on_remove_line(self, index: int) -> None:
        if 0 <= index < len(self._detail_lines):
            self._detail_lines.pop(index)
            self._refresh_detail_table()

    def on_import_cotizacion(self) -> None:
        data = self.cmbCotizacion.currentData()
        if data is None:
            self._show_error("Validación", "Selecciona una cotización.")
            return

        id_cotizacion, id_cliente, fecha_cotizacion = data

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

            if not self._validar_existencias_lineas(detalle):
                return

            self._detail_lines = list(detalle)
            self._refresh_detail_table()

            idx = self.cmbCliente.findData(id_cliente)
            if idx >= 0:
                self.cmbCliente.setCurrentIndex(idx)

            if fecha_cotizacion:
                qd = QDate.fromString(fecha_cotizacion, "yyyy-MM-dd")
                if qd.isValid():
                    self.dateFecha.setDate(qd)

            self.current_id = None
            self.btnEliminar.setEnabled(False)

        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_guardar(self) -> None:
        if self.cmbCliente.count() == 0 or self.cmbCliente.currentData() is None:
            self._show_error("Validación", "Selecciona un cliente.")
            return
        if not self._detail_lines:
            self._show_error("Validación", "Agrega al menos una línea de detalle.")
            return

        id_cliente = self.cmbCliente.currentData()
        fecha = self.dateFecha.date().toString("yyyy-MM-dd")
        total = sum(line[4] for line in self._detail_lines)

        try:
            with db() as conn:
                cur = conn.cursor()

                if self.current_id is None:
                    if not self._validar_existencias_lineas_cursor(cur, self._detail_lines):
                        conn.rollback()
                        return

                    _exec(
                        cur,
                        "INSERT INTO Ventas (id_cliente, fecha, total) "
                        "VALUES (?, ?, ?); SELECT SCOPE_IDENTITY()",
                        (id_cliente, fecha, total),
                    )
                    cur.nextset()
                    venta_id = int(cur.fetchone()[0])

                else:
                    old_rows = self.detalle_repo.fetch_by_venta(self.current_id)
                    for _, _, cantidad, _, id_pintura in old_rows:
                        self.inventario_repo.restaurar_cursor(cur, id_pintura, cantidad)

                    if not self._validar_existencias_lineas_cursor(cur, self._detail_lines):
                        conn.rollback()
                        return

                    _exec(
                        cur,
                        "UPDATE Ventas SET id_cliente = ?, fecha = ?, total = ? WHERE id_venta = ?",
                        (id_cliente, fecha, total, self.current_id),
                    )
                    _exec(cur, "DELETE FROM DetalleVenta WHERE id_venta = ?", (self.current_id,))
                    venta_id = self.current_id

                for (id_pintura, titulo, cantidad, precio_unitario, subtotal_linea) in self._detail_lines:
                    _exec(
                        cur,
                        "INSERT INTO DetalleVenta (id_venta, id_pintura, cantidad, subtotal) "
                        "VALUES (?, ?, ?, ?)",
                        (venta_id, id_pintura, cantidad, subtotal_linea),
                    )
                    self.inventario_repo.descontar_cursor(cur, id_pintura, cantidad)

                conn.commit()

            self.load_all()
            self.clear_form()

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
                for _, _, cantidad, _, id_pintura in old_rows:
                    self.inventario_repo.restaurar_cursor(cur, id_pintura, cantidad)

                _exec(cur, "DELETE FROM DetalleVenta WHERE id_venta = ?", (self.current_id,))
                _exec(cur, "DELETE FROM Ventas WHERE id_venta = ?", (self.current_id,))
                conn.commit()

            self.load_all()
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

            _, cliente, fecha, total, id_cliente = rows[0]
            self.current_id = vid

            idx = self.cmbCliente.findData(id_cliente)
            if idx >= 0:
                self.cmbCliente.setCurrentIndex(idx)

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
            for _, titulo, cantidad, subtotal_d, id_pintura in detail_rows:
                precio_unitario = float(subtotal_d) / cantidad if cantidad else 0.0
                self._detail_lines.append((
                    id_pintura,
                    titulo,
                    cantidad,
                    precio_unitario,
                    float(subtotal_d),
                ))

            self._refresh_detail_table()
            self.btnEliminar.setEnabled(True)

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
            display_rows = [(r[0], r[1], r[2], r[3]) for r in rows]
            if display_rows:
                self.populate_ventas_table(display_rows)
            else:
                self.populate_ventas_table([])
                QMessageBox.information(self, "Resultado", "No se encontró ninguna venta con ese ID.")
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_mostrar_todas(self) -> None:
        self.txtBuscarID.clear()
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
