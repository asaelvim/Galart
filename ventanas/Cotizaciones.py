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
# Repositorio Cotizaciones
# =========================
class CotizacionesRepo:

    def fetch_all(self) -> List[Tuple[int, str, str, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_cotizacion, "
                "ISNULL(cl.nombre, '') AS cliente, "
                "ISNULL(v.nombre, '') AS vendedor, "
                "c.fecha, c.subtotal, c.iva, c.total "
                "FROM Cotizaciones c "
                "LEFT JOIN Clientes cl ON c.id_cliente = cl.id_cliente "
                "LEFT JOIN Vendedores v ON c.id_vendedor = v.id_vendedor "
                "ORDER BY c.id_cotizacion",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                cid = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                vendedor = str(r[2]) if r[2] else ""
                fecha = r[3].strftime("%Y-%m-%d") if r[3] else ""
                subtotal = f"{float(r[4]):.2f}" if r[4] is not None else "0.00"
                iva = f"{float(r[5]):.2f}" if r[5] is not None else "0.00"
                total = f"{float(r[6]):.2f}" if r[6] is not None else "0.00"
                result.append((cid, cliente, vendedor, fecha, subtotal, iva, total))
            return result

    def fetch_by_id(self, cotizacion_id: int) -> List[Tuple[int, str, str, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_cotizacion, "
                "ISNULL(cl.nombre, '') AS cliente, "
                "ISNULL(v.nombre, '') AS vendedor, "
                "c.fecha, c.subtotal, c.iva, c.total, "
                "c.id_cliente, c.id_vendedor "
                "FROM Cotizaciones c "
                "LEFT JOIN Clientes cl ON c.id_cliente = cl.id_cliente "
                "LEFT JOIN Vendedores v ON c.id_vendedor = v.id_vendedor "
                "WHERE c.id_cotizacion = ?",
                (cotizacion_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                cid = int(r[0])
                cliente = str(r[1]) if r[1] else ""
                vendedor = str(r[2]) if r[2] else ""
                fecha = r[3].strftime("%Y-%m-%d") if r[3] else ""
                subtotal = f"{float(r[4]):.2f}" if r[4] is not None else "0.00"
                iva = f"{float(r[5]):.2f}" if r[5] is not None else "0.00"
                total = f"{float(r[6]):.2f}" if r[6] is not None else "0.00"
                id_cliente = int(r[7]) if r[7] is not None else 0
                id_vendedor = int(r[8]) if r[8] is not None else 0
                result.append((cid, cliente, vendedor, fecha, subtotal, iva, total, id_cliente, id_vendedor))
            return result

    def insert(self, id_cliente: int, id_vendedor: Optional[int], fecha: str,
               subtotal: float, iva: float, total: float) -> int:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Cotizaciones (id_cliente, id_vendedor, fecha, subtotal, iva, total) "
                "VALUES (?, ?, ?, ?, ?, ?); SELECT SCOPE_IDENTITY()",
                (id_cliente, id_vendedor, fecha, subtotal, iva, total),
            )
            cur.nextset()
            new_id = int(cur.fetchone()[0])
            conn.commit()
            return new_id

    def update(self, cotizacion_id: int, id_cliente: int, id_vendedor: Optional[int],
               fecha: str, subtotal: float, iva: float, total: float) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Cotizaciones SET id_cliente = ?, id_vendedor = ?, fecha = ?, "
                "subtotal = ?, iva = ?, total = ? WHERE id_cotizacion = ?",
                (id_cliente, id_vendedor, fecha, subtotal, iva, total, cotizacion_id),
            )
            conn.commit()

    def delete(self, cotizacion_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleCotizacion WHERE id_cotizacion = ?", (cotizacion_id,))
            _exec(cur, "DELETE FROM Cotizaciones WHERE id_cotizacion = ?", (cotizacion_id,))
            conn.commit()


# =========================
# Repositorio DetalleCotizacion
# =========================
class DetalleCotizacionRepo:

    def fetch_by_cotizacion(self, cotizacion_id: int) -> List[Tuple[int, str, int, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT d.id_detalle, ISNULL(p.titulo, '') AS titulo, "
                "d.cantidad, d.precio_unitario, d.subtotal, d.id_pintura "
                "FROM DetalleCotizacion d "
                "LEFT JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                "WHERE d.id_cotizacion = ? "
                "ORDER BY d.id_detalle",
                (cotizacion_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_detalle = int(r[0])
                titulo = str(r[1]) if r[1] else ""
                cantidad = int(r[2])
                precio_unitario = f"{float(r[3]):.2f}" if r[3] is not None else "0.00"
                subtotal = f"{float(r[4]):.2f}" if r[4] is not None else "0.00"
                id_pintura = int(r[5]) if r[5] is not None else 0
                result.append((id_detalle, titulo, cantidad, precio_unitario, subtotal, id_pintura))
            return result

    def insert(self, id_cotizacion: int, id_pintura: int, cantidad: int,
               precio_unitario: float, subtotal: float) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO DetalleCotizacion (id_cotizacion, id_pintura, cantidad, precio_unitario, subtotal) "
                "VALUES (?, ?, ?, ?, ?)",
                (id_cotizacion, id_pintura, cantidad, precio_unitario, subtotal),
            )
            conn.commit()

    def delete_by_cotizacion(self, cotizacion_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleCotizacion WHERE id_cotizacion = ?", (cotizacion_id,))
            conn.commit()

    def delete(self, id_detalle: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleCotizacion WHERE id_detalle = ?", (id_detalle,))
            conn.commit()

class InventarioRepo:
    def get_disponible(self, id_pintura: int) -> int:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT ISNULL(SUM(cantidad), 0) "
                "FROM Inventario "
                "WHERE id_pintura = ?",
                (id_pintura,),
            )
            row = cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0

# =========================
# UI Principal para COTIZACIONES
# =========================
class CotizacionesVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de Cotizaciones")
        self.setMinimumSize(1000, 780)

        self.repo = CotizacionesRepo()
        self.detalle_repo = DetalleCotizacionRepo()
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

        # Título
        title = QLabel("Gestión de Cotizaciones")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # === Fila Cliente + Vendedor ===
        row_cv = QHBoxLayout()
        row_cv.setSpacing(12)
        row_cv.addStretch(1)
        lbl_cliente = QLabel("Cliente:")
        lbl_cliente.setObjectName("MutedLabel")
        self.cmbCliente = QComboBox()
        self.cmbCliente.setObjectName("Combo")
        self.cmbCliente.setFixedWidth(260)
        lbl_vendedor = QLabel("Vendedor:")
        lbl_vendedor.setObjectName("MutedLabel")
        self.cmbVendedor = QComboBox()
        self.cmbVendedor.setObjectName("Combo")
        self.cmbVendedor.setFixedWidth(260)
        row_cv.addWidget(lbl_cliente)
        row_cv.addWidget(self.cmbCliente)
        row_cv.addSpacing(20)
        row_cv.addWidget(lbl_vendedor)
        row_cv.addWidget(self.cmbVendedor)
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

        self.detail_table = QTableWidget(0, 5)
        self.detail_table.setObjectName("Table")
        self.detail_table.setHorizontalHeaderLabels(["Pintura", "Cantidad", "Precio Unitario", "Subtotal", ""])
        self.detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.verticalHeader().setVisible(False)
        detail_header = self.detail_table.horizontalHeader()
        detail_header.setSectionResizeMode(QHeaderView.Stretch)
        detail_header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.detail_table.setColumnWidth(4, 50)
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
        self.lblIva = QLabel("IVA (16%): $0.00")
        self.lblIva.setObjectName("MutedLabel")
        self.lblTotal = QLabel("Total: $0.00")
        self.lblTotal.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        totals_layout.addWidget(self.lblSubtotal)
        totals_layout.addWidget(self.lblIva)
        totals_layout.addWidget(self.lblTotal)
        row_totals.addWidget(totals_widget)
        card_layout.addLayout(row_totals)

        # === Botones de acción ===
        row_actions = QHBoxLayout()
        row_actions.setSpacing(12)
        row_actions.addStretch(1)
        self.btnGuardar = self._button("Guardar Cotización", self.on_guardar, wide=True)
        self.btnNueva = self._button("Nueva Cotización", self.on_nueva, wide=True)
        self.btnEliminar = self._button("Eliminar Cotización", self.on_eliminar, wide=True)
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

        # === Tabla de cotizaciones ===
        cot_frame = QFrame()
        cot_frame.setObjectName("TableFrame")
        cf = QVBoxLayout(cot_frame)
        cf.setContentsMargins(10, 10, 10, 10)

        self.cot_table = QTableWidget(0, 7)
        self.cot_table.setObjectName("Table")
        self.cot_table.setHorizontalHeaderLabels(["ID", "Cliente", "Vendedor", "Fecha", "Subtotal", "IVA", "Total"])
        self.cot_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cot_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cot_table.verticalHeader().setVisible(False)
        cot_header = self.cot_table.horizontalHeader()
        cot_header.setSectionResizeMode(QHeaderView.Stretch)

        self.cot_table.itemSelectionChanged.connect(self.on_cotizacion_selected)

        cf.addWidget(self.cot_table)
        card_layout.addWidget(cot_frame)

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
        self._load_vendedores_combo()
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

    def _load_vendedores_combo(self) -> None:
        self.cmbVendedor.clear()
        self.cmbVendedor.addItem("(Sin vendedor)", None)
        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(cur, "SELECT id_vendedor, ISNULL(nombre, '') FROM Vendedores WHERE ISNULL(activo, 1) = 1 ORDER BY nombre")
                rows = cur.fetchall()
                for r in rows:
                    self.cmbVendedor.addItem(str(r[1]), r[0])
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
        iva = subtotal * 0.16
        total = subtotal + iva
        self.lblSubtotal.setText(f"Subtotal: ${subtotal:.2f}")
        self.lblIva.setText(f"IVA (16%): ${iva:.2f}")
        self.lblTotal.setText(f"Total: ${total:.2f}")

    def _cantidad_solicitada_por_pintura(self, id_pintura: int) -> int:
        return sum(cantidad for pid, _, cantidad, _, _ in self._detail_lines if pid == id_pintura)

    def _validar_existencia_para_agregar(self, id_pintura: int, cantidad_nueva: int) -> bool:
        disponible = self.inventario_repo.get_disponible(id_pintura)
        solicitada_total = self._cantidad_solicitada_por_pintura(id_pintura) + cantidad_nueva

        if solicitada_total > disponible:
            titulo = next(
                (t for pid, t, _, _, _ in self._detail_lines if pid == id_pintura),
                f"ID {id_pintura}"
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

        for id_pintura, _, cantidad, _, _ in self._detail_lines:
            acumuladas[id_pintura] = acumuladas.get(id_pintura, 0) + cantidad

        for id_pintura, solicitada in acumuladas.items():
            disponible = self.inventario_repo.get_disponible(id_pintura)
            if solicitada > disponible:
                titulo = next(
                    (t for pid, t, _, _, _ in self._detail_lines if pid == id_pintura),
                    f"ID {id_pintura}"
                )
                self._show_error(
                    "Existencias insuficientes",
                    f"La pintura '{titulo}' tiene {disponible} en inventario.\n"
                    f"En la cotización estás solicitando {solicitada}."
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
            self.detail_table.setItem(row, 2, QTableWidgetItem(f"${precio_unitario:.2f}"))
            self.detail_table.setItem(row, 3, QTableWidgetItem(f"${subtotal_linea:.2f}"))
            btn_quitar = QPushButton("X")
            btn_quitar.setObjectName("Btn")
            btn_quitar.setCursor(Qt.PointingHandCursor)
            btn_quitar.setFixedSize(30, 26)
            btn_quitar.clicked.connect(lambda checked, i=idx: self.on_remove_line(i))
            self.detail_table.setCellWidget(row, 4, btn_quitar)
        self._recalculate_totals()

    def clear_form(self) -> None:
        self.current_id = None
        if self.cmbCliente.count() > 0:
            self.cmbCliente.setCurrentIndex(0)
        if self.cmbVendedor.count() > 0:
            self.cmbVendedor.setCurrentIndex(0)
        self.dateFecha.setDate(QDate.currentDate())
        self._detail_lines.clear()
        self._refresh_detail_table()
        self.cot_table.clearSelection()
        self.btnEliminar.setEnabled(False)

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_cotizaciones_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_cotizaciones_table(self, rows: List[Tuple]) -> None:
        self.cot_table.setRowCount(0)
        for r, data in enumerate(rows):
            cid, cliente, vendedor, fecha, subtotal, iva, total = data[:7]
            self.cot_table.insertRow(r)
            for col, val in enumerate([str(cid), cliente, vendedor, fecha, subtotal, iva, total]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.cot_table.setItem(r, col, item)

    def on_add_line(self) -> None:
        if self.cmbPintura.count() == 0:
            self._show_error("Validación", "No hay pinturas disponibles.")
            return

        data = self.cmbPintura.currentData()
        if data is None:
            self._show_error("Validación", "Selecciona una pintura.")
            return

        id_pintura, precio = data
        cantidad = self.spnCantidad.value()

        if not self._validar_existencia_para_agregar(id_pintura, cantidad):
            return

        titulo = self.cmbPintura.currentText()

        # 🔎 Buscar si ya existe la pintura en la lista
        for i, (pid, t, cant, p_unit, sub) in enumerate(self._detail_lines):
            if pid == id_pintura:
                nueva_cantidad = cant + cantidad
                nuevo_subtotal = nueva_cantidad * p_unit

                self._detail_lines[i] = (
                    pid,
                    t,
                    nueva_cantidad,
                    p_unit,
                    nuevo_subtotal
                )

                self._refresh_detail_table()
                return

        # Si no existe, agregar nueva línea
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
        if self.cmbVendedor.count() == 0 or self.cmbVendedor.currentData() is None:
            self._show_error("Validación", "Selecciona un vendedor.")
            return
        if not self._detail_lines:
            self._show_error("Validación", "Agrega al menos una línea de detalle.")
            return

        # Validar existencias antes de guardar
        if not self._validar_existencias_totales():
            return

        id_cliente = self.cmbCliente.currentData()
        id_vendedor = self.cmbVendedor.currentData()
        fecha = self.dateFecha.date().toString("yyyy-MM-dd")

        subtotal = sum(line[4] for line in self._detail_lines)
        iva = subtotal * 0.16
        total = subtotal + iva

        try:
            with db() as conn:
                cur = conn.cursor()

                if self.current_id is None:
                    # Nueva cotización
                    _exec(
                        cur,
                        "INSERT INTO Cotizaciones (id_cliente, id_vendedor, fecha, subtotal, iva, total) "
                        "VALUES (?, ?, ?, ?, ?, ?); SELECT SCOPE_IDENTITY()",
                        (id_cliente, id_vendedor, fecha, subtotal, iva, total),
                    )
                    cur.nextset()
                    cotizacion_id = int(cur.fetchone()[0])
                else:
                    # Actualizar cotización existente
                    _exec(
                        cur,
                        "UPDATE Cotizaciones SET id_cliente = ?, id_vendedor = ?, fecha = ?, "
                        "subtotal = ?, iva = ?, total = ? WHERE id_cotizacion = ?",
                        (id_cliente, id_vendedor, fecha, subtotal, iva, total, self.current_id),
                    )
                    _exec(cur, "DELETE FROM DetalleCotizacion WHERE id_cotizacion = ?", (self.current_id,))
                    cotizacion_id = self.current_id

                # Guardar detalle
                for id_pintura, titulo, cantidad, precio_unitario, subtotal_linea in self._detail_lines:
                    _exec(
                        cur,
                        "INSERT INTO DetalleCotizacion (id_cotizacion, id_pintura, cantidad, precio_unitario, subtotal) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (cotizacion_id, id_pintura, cantidad, precio_unitario, subtotal_linea),
                    )

                conn.commit()

            self.load_all()
            self.clear_form()

        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_nueva(self) -> None:
        self.clear_form()

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona una cotización de la tabla.")
            return
        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar la cotización ID {self.current_id}?",
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

    def on_cotizacion_selected(self) -> None:
        items = self.cot_table.selectedItems()
        if not items:
            return
        row = items[0].row()
        cid = int(self.cot_table.item(row, 0).text())
        try:
            rows = self.repo.fetch_by_id(cid)
            if not rows:
                return
            data = rows[0]
            _, cliente, vendedor, fecha, subtotal, iva, total, id_cliente, id_vendedor = data

            self.current_id = cid

            # Seleccionar cliente en combo
            idx = self.cmbCliente.findData(id_cliente)
            if idx >= 0:
                self.cmbCliente.setCurrentIndex(idx)

            # Seleccionar vendedor en combo
            if id_vendedor:
                idx_v = self.cmbVendedor.findData(id_vendedor)
                if idx_v >= 0:
                    self.cmbVendedor.setCurrentIndex(idx_v)
            else:
                self.cmbVendedor.setCurrentIndex(0)

            # Setear fecha
            if fecha:
                self.dateFecha.setDate(QDate.fromString(fecha, "yyyy-MM-dd"))
            else:
                self.dateFecha.setDate(QDate.currentDate())

            # Cargar detalles
            self._detail_lines.clear()
            detail_rows = self.detalle_repo.fetch_by_cotizacion(cid)
            for (id_detalle, titulo, cantidad, precio_unitario, subtotal_d, id_pintura) in detail_rows:
                self._detail_lines.append((
                    id_pintura,
                    titulo,
                    cantidad,
                    float(precio_unitario),
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
            cid = int(raw)
        except ValueError:
            self._show_error("Validación", "El ID debe ser numérico.")
            return
        try:
            rows = self.repo.fetch_by_id(cid)
            display_rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows]
            if display_rows:
                self.populate_cotizaciones_table(display_rows)
            else:
                self.populate_cotizaciones_table([])
                QMessageBox.information(self, "Resultado", "No se encontró ninguna cotización con ese ID.")
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_mostrar_todas(self) -> None:
        self.txtBuscarID.clear()
        self.load_all()
        self.clear_form()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = CotizacionesVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
