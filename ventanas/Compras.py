from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import List, Optional, Tuple

from config.conexion import obtener_conexion
from ventanas.Proveedores import ProveedoresWindow
from ventanas.Artistas import ArtistasVentana
from ventanas.Pinturas import PinturasVentana

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


class ComprasRepo:
    def fetch_all(self) -> List[Tuple[int, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_compra, ISNULL(p.nombre, '') AS proveedor, c.fecha "
                "FROM Compras c "
                "LEFT JOIN Proveedores p ON c.id_proveedor = p.id_proveedor "
                "ORDER BY c.id_compra",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                cid = int(r[0])
                proveedor = str(r[1]) if r[1] else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] else ""
                result.append((cid, proveedor, fecha))
            return result

    def fetch_by_id(self, compra_id: int) -> List[Tuple[int, str, str, int]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_compra, ISNULL(p.nombre, '') AS proveedor, c.fecha, c.id_proveedor "
                "FROM Compras c "
                "LEFT JOIN Proveedores p ON c.id_proveedor = p.id_proveedor "
                "WHERE c.id_compra = ?",
                (compra_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                cid = int(r[0])
                proveedor = str(r[1]) if r[1] else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] else ""
                id_proveedor = int(r[3]) if r[3] is not None else 0
                result.append((cid, proveedor, fecha, id_proveedor))
            return result

    def search_by_proveedor(self, texto: str) -> List[Tuple[int, str, str]]:
        like = f"%{texto}%"
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT c.id_compra, ISNULL(p.nombre, '') AS proveedor, c.fecha "
                "FROM Compras c "
                "LEFT JOIN Proveedores p ON c.id_proveedor = p.id_proveedor "
                "WHERE ISNULL(p.nombre, '') LIKE ? "
                "ORDER BY c.id_compra",
                (like,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                cid = int(r[0])
                proveedor = str(r[1]) if r[1] else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] else ""
                result.append((cid, proveedor, fecha))
            return result

    def search_by_detail_name(self, texto: str, campo: str) -> List[Tuple[int, str, str]]:
        like = f"%{texto}%"
        if campo == "Artista":
            where_clause = "ISNULL(a.nombre, '') LIKE ?"
        else:
            where_clause = "ISNULL(pn.titulo, '') LIKE ?"

        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                f"SELECT DISTINCT c.id_compra, ISNULL(pr.nombre, '') AS proveedor, c.fecha "
                f"FROM Compras c "
                f"LEFT JOIN Proveedores pr ON c.id_proveedor = pr.id_proveedor "
                f"INNER JOIN DetalleCompra d ON c.id_compra = d.id_compra "
                f"LEFT JOIN Pinturas pn ON d.id_pintura = pn.id_pintura "
                f"LEFT JOIN Artistas a ON pn.id_artista = a.id_artista "
                f"WHERE {where_clause} "
                f"ORDER BY c.id_compra",
                (like,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                cid = int(r[0])
                proveedor = str(r[1]) if r[1] else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] else ""
                result.append((cid, proveedor, fecha))
            return result

    def insert(self, id_proveedor: int, fecha: str) -> int:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Compras (id_proveedor, fecha) "
                "VALUES (?, ?); SELECT SCOPE_IDENTITY()",
                (id_proveedor, fecha),
            )
            cur.nextset()
            new_id = int(cur.fetchone()[0])
            conn.commit()
            return new_id

    def update(self, compra_id: int, id_proveedor: int, fecha: str) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Compras SET id_proveedor = ?, fecha = ? WHERE id_compra = ?",
                (id_proveedor, fecha, compra_id),
            )
            conn.commit()

    def delete(self, compra_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleCompra WHERE id_compra = ?", (compra_id,))
            _exec(cur, "DELETE FROM Compras WHERE id_compra = ?", (compra_id,))
            conn.commit()


class DetalleCompraRepo:
    def fetch_by_compra(self, compra_id: int) -> List[Tuple[int, str, str, int, float, int]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT d.id_detalle, ISNULL(p.titulo, '') AS titulo, "
                "ISNULL(a.nombre, '') AS artista, "
                "d.cantidad, d.precio, d.id_pintura "
                "FROM DetalleCompra d "
                "LEFT JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "WHERE d.id_compra = ? "
                "ORDER BY d.id_detalle",
                (compra_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_detalle = int(r[0])
                titulo = str(r[1]) if r[1] else ""
                artista = str(r[2]) if r[2] else ""
                cantidad = int(r[3]) if r[3] is not None else 0
                precio = float(r[4]) if r[4] is not None else 0.0
                id_pintura = int(r[5]) if r[5] is not None else 0
                result.append((id_detalle, titulo, artista, cantidad, precio, id_pintura))
            return result


class ProveedoresRepo:
    def fetch_all_for_combo(self) -> List[Tuple[int, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "SELECT id_proveedor, ISNULL(nombre, '') FROM Proveedores ORDER BY nombre")
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]) if r[1] is not None else "") for r in rows]


class ArtistasRepo:
    def fetch_all_for_combo(self) -> List[Tuple[int, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "SELECT id_artista, ISNULL(nombre, '') FROM Artistas ORDER BY nombre")
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]) if r[1] is not None else "") for r in rows]


class PinturasRepo:
    def fetch_all_for_combo(self) -> List[Tuple[int, str, str, float]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT p.id_pintura, ISNULL(p.titulo, ''), ISNULL(a.nombre, ''), ISNULL(p.precio, 0) "
                "FROM Pinturas p "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "ORDER BY p.titulo",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                result.append(
                    (
                        int(r[0]),
                        str(r[1]) if r[1] is not None else "",
                        str(r[2]) if r[2] is not None else "",
                        float(r[3]) if r[3] is not None else 0.0,
                    )
                )
            return result

    def fetch_by_artista_for_combo(self, id_artista: int) -> List[Tuple[int, str, str, float]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT p.id_pintura, ISNULL(p.titulo, ''), ISNULL(a.nombre, ''), ISNULL(p.precio, 0) "
                "FROM Pinturas p "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "WHERE p.id_artista = ? "
                "ORDER BY p.titulo",
                (id_artista,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                result.append(
                    (
                        int(r[0]),
                        str(r[1]) if r[1] is not None else "",
                        str(r[2]) if r[2] is not None else "",
                        float(r[3]) if r[3] is not None else 0.0,
                    )
                )
            return result


class InventarioRepo:
    def get_disponible(self, id_pintura: int) -> int:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT ISNULL(SUM(cantidad), 0) FROM Inventario WHERE id_pintura = ?",
                (id_pintura,),
            )
            row = cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0

    def get_disponible_cursor(self, cur, id_pintura: int) -> int:
        _exec(
            cur,
            "SELECT ISNULL(SUM(cantidad), 0) FROM Inventario WHERE id_pintura = ?",
            (id_pintura,),
        )
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def agregar_cursor(self, cur, id_pintura: int, cantidad: int) -> None:
        restante = int(cantidad)

        _exec(
            cur,
            "SELECT id_inventario, cantidad FROM Inventario WHERE id_pintura = ? ORDER BY id_inventario",
            (id_pintura,),
        )
        rows = cur.fetchall()

        if rows:
            id_inventario, cant_actual = rows[0]
            nueva = int(cant_actual) + restante
            _exec(
                cur,
                "UPDATE Inventario SET cantidad = ? WHERE id_inventario = ?",
                (nueva, int(id_inventario)),
            )
        else:
            _exec(
                cur,
                "INSERT INTO Inventario (id_pintura, cantidad) VALUES (?, ?)",
                (id_pintura, restante),
            )

    def restar_cursor(self, cur, id_pintura: int, cantidad: int) -> None:
        restante = int(cantidad)

        _exec(
            cur,
            "SELECT id_inventario, cantidad FROM Inventario WHERE id_pintura = ? AND cantidad > 0 ORDER BY id_inventario",
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
            raise RuntimeError(f"No hay suficiente inventario para la pintura ID {id_pintura}.")


class ComprasVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.ventana_proveedores = None
        self.ventana_artistas = None
        self.ventana_pinturas = None

        self.setWindowTitle("Gestión de Compras")
        self.setMinimumSize(1800, 820)

        self.repo = ComprasRepo()
        self.detalle_repo = DetalleCompraRepo()
        self.proveedor_repo = ProveedoresRepo()
        self.artista_repo = ArtistasRepo()
        self.pintura_repo = PinturasRepo()
        self.inventario_repo = InventarioRepo()

        self.current_id: Optional[int] = None
        # (id_pintura, titulo, artista, cantidad, precio, subtotal)
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

        title = QLabel("Gestión de Compras")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        row_proveedor = QHBoxLayout()
        row_proveedor.setSpacing(12)
        row_proveedor.addStretch(1)

        lbl_proveedor = QLabel("Proveedor:")
        lbl_proveedor.setObjectName("MutedLabel")
        self.cmbProveedor = QComboBox()
        self.cmbProveedor.setObjectName("Combo")
        self.cmbProveedor.setFixedWidth(300)

        self.btnAdministrarProveedores = self._button(
            "Administrar proveedores", self.abrir_proveedores, wide=True
        )
        self.btnAdministrarProveedores.setFixedWidth(200)

        row_proveedor.addWidget(lbl_proveedor)
        row_proveedor.addWidget(self.cmbProveedor)
        row_proveedor.addWidget(self.btnAdministrarProveedores)
        row_proveedor.addStretch(1)
        card_layout.addLayout(row_proveedor)

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

        row_detalle = QHBoxLayout()
        row_detalle.setSpacing(12)
        row_detalle.addStretch(1)

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
        self.cmbPintura.setFixedWidth(340)

        self.btnAdministrarPinturas = self._button("Administrar pinturas", self.abrir_pinturas, wide=True)
        self.btnAdministrarPinturas.setFixedWidth(190)

        lbl_cantidad = QLabel("Cantidad:")
        lbl_cantidad.setObjectName("MutedLabel")
        self.spnCantidad = QSpinBox()
        self.spnCantidad.setObjectName("SpinBox")
        self.spnCantidad.setMinimum(1)
        self.spnCantidad.setMaximum(999999)
        self.spnCantidad.setFixedWidth(100)

        lbl_precio = QLabel("Precio:")
        lbl_precio.setObjectName("MutedLabel")
        self.txtPrecio = QLineEdit()
        self.txtPrecio.setObjectName("txtPrecio")
        self.txtPrecio.setFixedWidth(120)

        self.btnAgregarLinea = self._button("Agregar línea", self.on_add_line)

        row_detalle.addWidget(lbl_artista)
        row_detalle.addWidget(self.cmbArtista)
        row_detalle.addWidget(self.btnAdministrarArtistas)
        row_detalle.addSpacing(14)
        row_detalle.addWidget(lbl_pintura)
        row_detalle.addWidget(self.cmbPintura)
        row_detalle.addWidget(self.btnAdministrarPinturas)
        row_detalle.addSpacing(10)
        row_detalle.addWidget(lbl_cantidad)
        row_detalle.addWidget(self.spnCantidad)
        row_detalle.addSpacing(10)
        row_detalle.addWidget(lbl_precio)
        row_detalle.addWidget(self.txtPrecio)
        row_detalle.addWidget(self.btnAgregarLinea)
        row_detalle.addStretch(1)
        card_layout.addLayout(row_detalle)

        detail_frame = QFrame()
        detail_frame.setObjectName("TableFrame")
        df = QVBoxLayout(detail_frame)
        df.setContentsMargins(10, 10, 10, 10)

        self.detail_table = QTableWidget(0, 5)
        self.detail_table.setObjectName("Table")
        self.detail_table.setHorizontalHeaderLabels(["Pintura", "Artista", "Cantidad", "Precio", ""])
        self.detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.verticalHeader().setVisible(False)
        dh = self.detail_table.horizontalHeader()
        dh.setSectionResizeMode(0, QHeaderView.Stretch)
        dh.setSectionResizeMode(1, QHeaderView.Stretch)
        dh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        dh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        dh.setSectionResizeMode(4, QHeaderView.Fixed)
        self.detail_table.setColumnWidth(4, 50)
        self.detail_table.setMaximumHeight(190)

        df.addWidget(self.detail_table)
        card_layout.addWidget(detail_frame)

        row_totals = QHBoxLayout()
        row_totals.addStretch(1)
        totals_widget = QWidget()
        totals_layout = QVBoxLayout(totals_widget)
        totals_layout.setSpacing(4)
        totals_layout.setContentsMargins(0, 0, 0, 0)
        self.lblTotal = QLabel("Total: $0.00")
        self.lblTotal.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        totals_layout.addWidget(self.lblTotal)
        row_totals.addWidget(totals_widget)
        card_layout.addLayout(row_totals)

        row_actions = QHBoxLayout()
        row_actions.setSpacing(12)
        row_actions.addStretch(1)
        self.btnGuardar = self._button("Guardar Compra", self.on_guardar, wide=True)
        self.btnNueva = self._button("Nueva Compra", self.on_nueva, wide=True)
        self.btnEliminar = self._button("Eliminar Compra", self.on_eliminar, wide=True)
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
        lbl_buscar = QLabel("Buscar por ID:")
        lbl_buscar.setObjectName("MutedLabel")
        self.txtBuscarID = QLineEdit()
        self.txtBuscarID.setObjectName("SearchBox")
        self.txtBuscarID.setFixedWidth(160)
        self.btnBuscarID = self._button("Buscar ID", self.on_buscar_id)
        self.btnMostrarTodas = self._button("Mostrar todas", self.on_mostrar_todas, wide=True)
        row_buscar.addWidget(lbl_buscar)
        row_buscar.addWidget(self.txtBuscarID)
        row_buscar.addWidget(self.btnBuscarID)
        row_buscar.addWidget(self.btnMostrarTodas)
        row_buscar.addStretch(1)
        card_layout.addLayout(row_buscar)

        row_buscar_proveedor = QHBoxLayout()
        row_buscar_proveedor.setSpacing(12)
        row_buscar_proveedor.addStretch(1)
        lbl_buscar_proveedor = QLabel("Buscar proveedor:")
        lbl_buscar_proveedor.setObjectName("MutedLabel")
        self.txtBuscarProveedor = QLineEdit()
        self.txtBuscarProveedor.setObjectName("SearchBox")
        self.txtBuscarProveedor.setFixedWidth(260)
        self.btnBuscarProveedor = self._button("Buscar proveedor", self.on_buscar_proveedor, wide=True)
        row_buscar_proveedor.addWidget(lbl_buscar_proveedor)
        row_buscar_proveedor.addWidget(self.txtBuscarProveedor)
        row_buscar_proveedor.addWidget(self.btnBuscarProveedor)
        row_buscar_proveedor.addStretch(1)
        card_layout.addLayout(row_buscar_proveedor)

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

        compras_frame = QFrame()
        compras_frame.setObjectName("TableFrame")
        cf = QVBoxLayout(compras_frame)
        cf.setContentsMargins(10, 10, 10, 10)

        self.compras_table = QTableWidget(0, 3)
        self.compras_table.setObjectName("Table")
        self.compras_table.setHorizontalHeaderLabels(["ID", "Proveedor", "Fecha"])
        self.compras_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.compras_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.compras_table.verticalHeader().setVisible(False)
        ch = self.compras_table.horizontalHeader()
        ch.setSectionResizeMode(QHeaderView.Stretch)
        self.compras_table.itemSelectionChanged.connect(self.on_compra_selected)

        cf.addWidget(self.compras_table)
        card_layout.addWidget(compras_frame)

        row_bottom = QHBoxLayout()
        row_bottom.addStretch(1)
        self.btnSalir = self._button("Salir", self.close, wide=True)
        row_bottom.addWidget(self.btnSalir)
        row_bottom.addStretch(1)
        card_layout.addLayout(row_bottom)

        main.addWidget(card)
        self.setStyleSheet(self._stylesheet())

        self._load_proveedores_combo()
        self._load_artistas_combo()
        self._load_pinturas_combo(None)
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

    def _load_proveedores_combo(self) -> None:
        self.cmbProveedor.clear()
        try:
            proveedores = self.proveedor_repo.fetch_all_for_combo()
            self.cmbProveedor.addItem("-- Seleccionar proveedor --", None)
            for id_proveedor, nombre in proveedores:
                self.cmbProveedor.addItem(nombre, id_proveedor)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _load_artistas_combo(self) -> None:
        self.cmbArtista.blockSignals(True)
        self.cmbArtista.clear()
        self.cmbArtista.addItem("Cualquier Artista", None)
        try:
            artistas = self.artista_repo.fetch_all_for_combo()
            for id_artista, nombre in artistas:
                self.cmbArtista.addItem(nombre, id_artista)
        except Exception as e:
            self._show_error("Error BD", str(e))
        self.cmbArtista.setCurrentIndex(0)
        self.cmbArtista.blockSignals(False)

    def _load_pinturas_combo(self, id_artista: Optional[int] = None) -> None:
        self.cmbPintura.clear()
        try:
            if id_artista is None:
                pinturas = self.pintura_repo.fetch_all_for_combo()
            else:
                pinturas = self.pintura_repo.fetch_by_artista_for_combo(id_artista)

            self.cmbPintura.addItem("-- Seleccionar pintura --", None)
            for id_pintura, titulo, artista, precio in pinturas:
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

    def _recalculate_total(self) -> None:
        total = sum(line[5] for line in self._detail_lines)
        self.lblTotal.setText(f"Total: ${total:.2f}")

    def _refresh_detail_table(self) -> None:
        self.detail_table.setRowCount(0)
        for idx, (id_pintura, titulo, artista, cantidad, precio, subtotal) in enumerate(self._detail_lines):
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)

            it_titulo = QTableWidgetItem(titulo)
            it_titulo.setFlags(it_titulo.flags() & ~Qt.ItemIsEditable)

            it_artista = QTableWidgetItem(artista)
            it_artista.setFlags(it_artista.flags() & ~Qt.ItemIsEditable)

            it_cantidad = QTableWidgetItem(str(cantidad))
            it_cantidad.setFlags(it_cantidad.flags() & ~Qt.ItemIsEditable)

            it_precio = QTableWidgetItem(f"${precio:.2f}")
            it_precio.setFlags(it_precio.flags() & ~Qt.ItemIsEditable)

            self.detail_table.setItem(row, 0, it_titulo)
            self.detail_table.setItem(row, 1, it_artista)
            self.detail_table.setItem(row, 2, it_cantidad)
            self.detail_table.setItem(row, 3, it_precio)

            btn_quitar = QPushButton("X")
            btn_quitar.setObjectName("Btn")
            btn_quitar.setCursor(Qt.PointingHandCursor)
            btn_quitar.setFixedSize(30, 26)
            btn_quitar.clicked.connect(lambda checked=False, i=idx: self.on_remove_line(i))
            self.detail_table.setCellWidget(row, 4, btn_quitar)

        self._recalculate_total()

    def clear_form(self) -> None:
        self.current_id = None
        if self.cmbProveedor.count() > 0:
            self.cmbProveedor.setCurrentIndex(0)

        self.cmbArtista.blockSignals(True)
        if self.cmbArtista.count() > 0:
            self.cmbArtista.setCurrentIndex(0)
        self.cmbArtista.blockSignals(False)

        self._load_pinturas_combo(None)

        if self.cmbPintura.count() > 0:
            self.cmbPintura.setCurrentIndex(0)

        self.spnCantidad.setValue(1)
        self.txtPrecio.clear()
        self.dateFecha.setDate(QDate.currentDate())
        self._detail_lines.clear()
        self._refresh_detail_table()
        self.compras_table.clearSelection()
        self.btnEliminar.setEnabled(False)

        self.txtBuscarID.clear()
        self.txtBuscarProveedor.clear()
        self.txtBuscarDetalle.clear()
        self.cmbBuscarDetalle.setCurrentIndex(0)

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, str]]) -> None:
        self.compras_table.setRowCount(0)
        for r, (cid, proveedor, fecha) in enumerate(rows):
            self.compras_table.insertRow(r)

            it_id = QTableWidgetItem(str(cid))
            it_id.setFlags(it_id.flags() & ~Qt.ItemIsEditable)

            it_prov = QTableWidgetItem(proveedor)
            it_prov.setFlags(it_prov.flags() & ~Qt.ItemIsEditable)

            it_fecha = QTableWidgetItem(fecha)
            it_fecha.setFlags(it_fecha.flags() & ~Qt.ItemIsEditable)

            self.compras_table.setItem(r, 0, it_id)
            self.compras_table.setItem(r, 1, it_prov)
            self.compras_table.setItem(r, 2, it_fecha)

    def on_add_line(self) -> None:
        data = self.cmbPintura.currentData()
        if data is None:
            self._show_error("Validación", "Selecciona una pintura.")
            return

        if self.cmbProveedor.currentData() is None:
            self._show_error("Validación", "Selecciona un proveedor.")
            return

        id_pintura, titulo, artista, precio_combo = data
        cantidad = self.spnCantidad.value()

        raw_precio = self.txtPrecio.text().strip()
        if raw_precio:
            try:
                precio = float(raw_precio)
            except ValueError:
                self._show_error("Validación", "El precio debe ser numérico.")
                return
        else:
            precio = float(precio_combo)

        if cantidad <= 0:
            self._show_error("Validación", "La cantidad debe ser mayor que cero.")
            return

        for i, (pid, t, a, cant, p_unit, sub) in enumerate(self._detail_lines):
            if pid == id_pintura:
                nueva_cantidad = cant + cantidad
                nuevo_subtotal = nueva_cantidad * precio
                self._detail_lines[i] = (pid, t, a, nueva_cantidad, precio, nuevo_subtotal)
                self._refresh_detail_table()
                self.spnCantidad.setValue(1)
                self.txtPrecio.clear()
                return

        subtotal = cantidad * precio
        self._detail_lines.append((id_pintura, titulo, artista, cantidad, precio, subtotal))
        self._refresh_detail_table()
        self.spnCantidad.setValue(1)
        self.txtPrecio.clear()

    def on_remove_line(self, index: int) -> None:
        if 0 <= index < len(self._detail_lines):
            self._detail_lines.pop(index)
            self._refresh_detail_table()

    def _get_form_values(self) -> Tuple[Optional[int], str]:
        id_proveedor = self.cmbProveedor.currentData()
        fecha = self.dateFecha.date().toString("yyyy-MM-dd")
        return id_proveedor, fecha

    def on_guardar(self) -> None:
        id_proveedor, fecha = self._get_form_values()

        if id_proveedor is None:
            self._show_error("Validación", "Selecciona un proveedor.")
            return
        if not self._detail_lines:
            self._show_error("Validación", "Agrega al menos una línea de detalle.")
            return

        try:
            with db() as conn:
                cur = conn.cursor()

                if self.current_id is None:
                    _exec(
                        cur,
                        "INSERT INTO Compras (id_proveedor, fecha) VALUES (?, ?); SELECT SCOPE_IDENTITY()",
                        (id_proveedor, fecha),
                    )
                    cur.nextset()
                    compra_id = int(cur.fetchone()[0])

                else:
                    old_rows = self.detalle_repo.fetch_by_compra(self.current_id)
                    for _, _, _, cantidad, _, id_pintura in old_rows:
                        self.inventario_repo.restar_cursor(cur, id_pintura, cantidad)

                    _exec(
                        cur,
                        "UPDATE Compras SET id_proveedor = ?, fecha = ? WHERE id_compra = ?",
                        (id_proveedor, fecha, self.current_id),
                    )
                    _exec(cur, "DELETE FROM DetalleCompra WHERE id_compra = ?", (self.current_id,))
                    compra_id = self.current_id

                for id_pintura, titulo, artista, cantidad, precio, subtotal in self._detail_lines:
                    _exec(
                        cur,
                        "INSERT INTO DetalleCompra (id_compra, id_pintura, cantidad, precio) "
                        "VALUES (?, ?, ?, ?)",
                        (compra_id, id_pintura, cantidad, precio),
                    )
                    self.inventario_repo.agregar_cursor(cur, id_pintura, cantidad)

                conn.commit()

            self.load_all()
            self.clear_form()

        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_nueva(self) -> None:
        self.clear_form()

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona una compra de la tabla.")
            return

        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar la compra ID {self.current_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return

        try:
            with db() as conn:
                cur = conn.cursor()

                old_rows = self.detalle_repo.fetch_by_compra(self.current_id)
                for _, _, _, cantidad, _, id_pintura in old_rows:
                    self.inventario_repo.restar_cursor(cur, id_pintura, cantidad)

                _exec(cur, "DELETE FROM DetalleCompra WHERE id_compra = ?", (self.current_id,))
                _exec(cur, "DELETE FROM Compras WHERE id_compra = ?", (self.current_id,))
                conn.commit()

            self.load_all()
            self.clear_form()

        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_compra_selected(self) -> None:
        items = self.compras_table.selectedItems()
        if not items:
            return

        row = items[0].row()
        cid = int(self.compras_table.item(row, 0).text())

        try:
            rows = self.repo.fetch_by_id(cid)
            if not rows:
                return

            _, proveedor, fecha, id_proveedor = rows[0]
            self.current_id = cid

            idx = self.cmbProveedor.findData(id_proveedor)
            if idx >= 0:
                self.cmbProveedor.setCurrentIndex(idx)

            if fecha:
                qd = QDate.fromString(fecha, "yyyy-MM-dd")
                if qd.isValid():
                    self.dateFecha.setDate(qd)
            else:
                self.dateFecha.setDate(QDate.currentDate())

            self._detail_lines.clear()
            detail_rows = self.detalle_repo.fetch_by_compra(cid)
            for _, titulo, artista, cantidad, precio, id_pintura in detail_rows:
                subtotal = cantidad * precio
                self._detail_lines.append((id_pintura, titulo, artista, cantidad, precio, subtotal))

            self._refresh_detail_table()
            self.btnEliminar.setEnabled(True)

            if self._detail_lines:
                primer_artista = self._detail_lines[0][2]
                if primer_artista:
                    idx_art = self.cmbArtista.findText(primer_artista)
                    if idx_art >= 0:
                        self.cmbArtista.setCurrentIndex(idx_art)

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
            display_rows = [(r[0], r[1], r[2]) for r in rows]
            if display_rows:
                self.populate_table(display_rows)
            else:
                self.populate_table([])
                QMessageBox.information(self, "Resultado", "No se encontró ninguna compra con ese ID.")
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_buscar_proveedor(self) -> None:
        texto = self.txtBuscarProveedor.text().strip()
        if not texto:
            self.load_all()
            return

        try:
            rows = self.repo.search_by_proveedor(texto)
            if rows:
                self.populate_table(rows)
            else:
                self.populate_table([])
                QMessageBox.information(
                    self,
                    "Resultado",
                    "No se encontraron compras con ese proveedor.",
                )
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
                self.populate_table(rows)
            else:
                self.populate_table([])
                QMessageBox.information(
                    self,
                    "Resultado",
                    f"No se encontraron compras por {campo.lower()} con ese texto.",
                )
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_mostrar_todas(self) -> None:
        self.txtBuscarID.clear()
        self.txtBuscarProveedor.clear()
        self.txtBuscarDetalle.clear()
        self.cmbBuscarDetalle.setCurrentIndex(0)
        self.load_all()
        self.clear_form()

    def abrir_proveedores(self) -> None:
        if self.ventana_proveedores is None:
            self.ventana_proveedores = ProveedoresWindow(self)

        self.hide()
        self.ventana_proveedores.show()
        self.ventana_proveedores.raise_()
        self.ventana_proveedores.activateWindow()

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


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ComprasVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
