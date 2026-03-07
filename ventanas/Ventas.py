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
    """Ejecuta SQL usando placeholders '?' (compatibles con pyodbc)."""
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

    def insert(self, id_venta: int, id_pintura: int, cantidad: int, subtotal: float) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO DetalleVenta (id_venta, id_pintura, cantidad, subtotal) "
                "VALUES (?, ?, ?, ?)",
                (id_venta, id_pintura, cantidad, subtotal),
            )
            conn.commit()

    def delete_by_venta(self, venta_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleVenta WHERE id_venta = ?", (venta_id,))
            conn.commit()

    def delete(self, id_detalle: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleVenta WHERE id_detalle = ?", (id_detalle,))
            conn.commit()


# =========================
# UI Principal para VENTAS
# =========================
class VentasVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de Ventas")
        self.setFixedSize(1000, 700)

        self.repo = VentasRepo()
        self.detalle_repo = DetalleVentaRepo()
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

        # Título
        title = QLabel("Gestión de Ventas")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # === Fila Cliente ===
        row_cv = QHBoxLayout()
        row_cv.setSpacing(12)
        row_cv.addStretch(1)
        lbl_cliente = QLabel("Cliente:")
        lbl_cliente.setObjectName("MutedLabel")
        self.cmbCliente = QComboBox()
        self.cmbCliente.setObjectName("Combo")
        self.cmbCliente.setFixedWidth(260)
        row_cv.addWidget(lbl_cliente)
        row_cv.addWidget(self.cmbCliente)
        row_cv.addStretch(1)
        card_layout.addLayout(row_cv)

        # === Fila Fecha ===
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

        # === Separador ===
        sep1 = QFrame()
        sep1.setObjectName("Separator")
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        card_layout.addWidget(sep1)

        # === Fila agregar línea de detalle ===
        row_line = QHBoxLayout()
        row_line.setSpacing(12)
        row_line.addStretch(1)
        lbl_pintura = QLabel("Pintura:")
        lbl_pintura.setObjectName("MutedLabel")
        self.cmbPintura = QComboBox()
        self.cmbPintura.setObjectName("Combo")
        self.cmbPintura.setFixedWidth(320)
        lbl_cantidad = QLabel("Cantidad:")
        lbl_cantidad.setObjectName("MutedLabel")
        self.spnCantidad = QSpinBox()
        self.spnCantidad.setObjectName("SpinBox")
        self.spnCantidad.setMinimum(1)
        self.spnCantidad.setMaximum(999)
        self.spnCantidad.setFixedWidth(80)
        self.btnAgregarLinea = self._button("Agregar línea", self.on_add_line)
        row_line.addWidget(lbl_pintura)
        row_line.addWidget(self.cmbPintura)
        row_line.addSpacing(10)
        row_line.addWidget(lbl_cantidad)
        row_line.addWidget(self.spnCantidad)
        row_line.addWidget(self.btnAgregarLinea)
        row_line.addStretch(1)
        card_layout.addLayout(row_line)

        # === Tabla de detalles ===
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
        detail_header.setSectionResizeMode(QHeaderView.Stretch)
        detail_header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.detail_table.setColumnWidth(3, 50)
        self.detail_table.setMaximumHeight(160)

        df.addWidget(self.detail_table)
        card_layout.addWidget(detail_frame)

        # === Totales ===
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

        # === Botones de acción ===
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

        # === Separador ===
        sep2 = QFrame()
        sep2.setObjectName("Separator")
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        card_layout.addWidget(sep2)

        # === Fila búsqueda ===
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

        # === Tabla de ventas ===
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

        # === Botón Salir ===
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
                for r in rows:
                    id_pintura = int(r[0])
                    titulo = str(r[1])
                    precio = float(r[2]) if r[2] is not None else 0.0
                    self.cmbPintura.addItem(f"{titulo} - ${precio:.2f}", (id_pintura, precio))
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _recalculate_totals(self) -> None:
        subtotal = sum(line[4] for line in self._detail_lines)
        self.lblSubtotal.setText(f"Subtotal: ${subtotal:.2f}")
        self.lblTotal.setText(f"Total: ${subtotal:.2f}")

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
            btn_quitar.clicked.connect(lambda checked, i=idx: self.on_remove_line(i))
            self.detail_table.setCellWidget(row, 3, btn_quitar)
        self._recalculate_totals()

    def clear_form(self) -> None:
        self.current_id = None
        if self.cmbCliente.count() > 0:
            self.cmbCliente.setCurrentIndex(0)
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
        id_pintura, precio = data
        titulo = self.cmbPintura.currentText()
        cantidad = self.spnCantidad.value()
        subtotal_linea = precio * cantidad
        self._detail_lines.append((id_pintura, titulo, cantidad, precio, subtotal_linea))
        self._refresh_detail_table()

    def on_remove_line(self, index: int) -> None:
        if 0 <= index < len(self._detail_lines):
            self._detail_lines.pop(index)
            self._refresh_detail_table()

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
            if self.current_id is None:
                new_id = self.repo.insert(id_cliente, fecha, total)
                for (id_pintura, titulo, cantidad, precio_unitario, subtotal_linea) in self._detail_lines:
                    self.detalle_repo.insert(new_id, id_pintura, cantidad, subtotal_linea)
            else:
                self.repo.update(self.current_id, id_cliente, fecha, total)
                self.detalle_repo.delete_by_venta(self.current_id)
                for (id_pintura, titulo, cantidad, precio_unitario, subtotal_linea) in self._detail_lines:
                    self.detalle_repo.insert(self.current_id, id_pintura, cantidad, subtotal_linea)
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
            self.repo.delete(self.current_id)
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
            data = rows[0]
            _, cliente, fecha, total, id_cliente = data

            self.current_id = vid

            # Seleccionar cliente en combo
            idx = self.cmbCliente.findData(id_cliente)
            if idx >= 0:
                self.cmbCliente.setCurrentIndex(idx)

            # Setear fecha
            if fecha:
                self.dateFecha.setDate(QDate.fromString(fecha, "yyyy-MM-dd"))
            else:
                self.dateFecha.setDate(QDate.currentDate())

            # Cargar detalles
            self._detail_lines.clear()
            detail_rows = self.detalle_repo.fetch_by_venta(vid)
            for (id_detalle, titulo, cantidad, subtotal_d, id_pintura) in detail_rows:
                # Recover precio_unitario from combo data if available, else derive from subtotal/cantidad
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
