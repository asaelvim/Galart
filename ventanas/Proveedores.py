"""
Pantalla: Gestión de Proveedores (Paleta Opción A - Minimal Luxe)
UI en PySide6 + tabla conectada a BD vía config/conexion.py (obtener_conexion)

Requisitos:
  pip install PySide6

Estructura esperada:
  - main_proveedores.py   (este archivo)
  - config/conexion.py    (tu conexión a BD)

config/conexion.py debe exponer:
  def obtener_conexion(): -> retorna conexión DB-API (pyodbc), con conn.cursor(), conn.commit()

Tabla esperada en BD: Proveedores
Columnas (como mínimo):
  id_proveedor (PK), nombre, telefono, correo, direccion

Ejecuta:
  python main_proveedores.py
"""

from __future__ import annotations

import re
import sys
from contextlib import contextmanager
from typing import List, Optional, Tuple

from config.conexion import obtener_conexion

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


# =========================
# Validación de correo electrónico
# =========================
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+(\.[a-zA-Z0-9\-]+)*\.[a-zA-Z]{2,}$")

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


def _exec(cur, sql: str, params=()):
    """Ejecuta SQL usando placeholders '?' (compatibles con pyodbc)."""
    cur.execute(sql, params)


# =========================
# Repositorio (CRUD)
# =========================
class ProveedoresRepo:
    TABLE = "Proveedores"

    def fetch_all(self) -> List[Tuple[int, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_proveedor, nombre, telefono, correo, direccion "
                "FROM Proveedores ORDER BY id_proveedor"
            )
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4])) for r in rows]

    def fetch_by_id(self, proveedor_id: int) -> List[Tuple[int, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_proveedor, nombre, telefono, correo, direccion "
                "FROM Proveedores WHERE id_proveedor = ?",
                (proveedor_id,),
            )
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4])) for r in rows]

    def search_by_name(self, nombre: str) -> List[Tuple[int, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            like = f"%{nombre}%"
            _exec(
                cur,
                "SELECT id_proveedor, nombre, telefono, correo, direccion "
                "FROM Proveedores WHERE nombre LIKE ? ORDER BY id_proveedor",
                (like,),
            )
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4])) for r in rows]

    def insert(self, nombre: str, telefono: str, correo: str, direccion: str) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Proveedores (nombre, telefono, correo, direccion) VALUES (?, ?, ?, ?)",
                (nombre, telefono, correo, direccion),
            )
            conn.commit()

    def update(
        self, proveedor_id: int, nombre: str, telefono: str, correo: str, direccion: str
    ) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Proveedores SET nombre = ?, telefono = ?, correo = ?, direccion = ? "
                "WHERE id_proveedor = ?",
                (nombre, telefono, correo, direccion, proveedor_id),
            )
            conn.commit()

    def delete(self, proveedor_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM Proveedores WHERE id_proveedor = ?", (proveedor_id,))
            conn.commit()


# =========================
# UI
# =========================
class ProveedoresWindow(QMainWindow):
    def __init__(self, ventana_principal):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de proveedores")
        self.setMinimumSize(940, 660)

        self.repo = ProveedoresRepo()
        self.current_id: Optional[int] = None

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(14)

        # Card contenedora
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 18)
        card_layout.setSpacing(12)

        # Título
        title = QLabel("Gestión de proveedores")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # === Fila 1: inputs (Nombre / Teléfono / Correo) ===
        row1 = QHBoxLayout()
        row1.setSpacing(22)
        row1.addStretch(1)
        row1.addLayout(self._labeled_edit("Nombre:", "txtNombre", width=190))
        row1.addLayout(self._labeled_edit("Teléfono:", "txtTelefono", width=190))
        row1.addLayout(self._labeled_edit("Correo:", "txtCorreo", width=190))
        row1.addStretch(1)

        card_layout.addLayout(row1)

        # === Fila 2: Dirección + CRUD ===
        row2 = QHBoxLayout()
        row2.setSpacing(18)
        row2.addStretch(1)
        row2.addLayout(self._labeled_edit("Dirección:", "txtDireccion", width=350))

        self.btnAgregar = self._button("Agregar", self.on_agregar, width=150)
        self.btnEditar = self._button("Editar", self.on_editar, width=150)
        self.btnEliminar = self._button("Eliminar", self.on_eliminar, width=150)

        row2.addWidget(self.btnAgregar)
        row2.addWidget(self.btnEditar)
        row2.addWidget(self.btnEliminar)
        row2.addStretch(1)

        card_layout.addLayout(row2)

        # === Fila 3: Buscar por nombre ===
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        lblBuscarNom = QLabel("Buscar por nombre:")
        lblBuscarNom.setObjectName("MutedLabel")

        self.txtBuscarNombre = QLineEdit()
        self.txtBuscarNombre.setObjectName("SearchBox")
        self.txtBuscarNombre.setFixedWidth(360)

        self.btnBuscarNombre = self._button("Buscar", self.on_buscar_nombre, width=140)
        self.btnMostrarTodos = self._button("Mostrar Todos", self.on_mostrar_todos, width=180)

        row3.addStretch(1)
        row3.addWidget(lblBuscarNom)
        row3.addWidget(self.txtBuscarNombre)
        row3.addWidget(self.btnBuscarNombre)
        row3.addWidget(self.btnMostrarTodos)
        row3.addStretch(1)

        card_layout.addLayout(row3)

        # Línea separadora (como en tu imagen)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("Separator")
        card_layout.addWidget(sep)

        # === Fila 4: Buscar por ID + Mostrar ID (Combo) ===
        row4 = QHBoxLayout()
        row4.setSpacing(14)

        lblBuscarID = QLabel("Buscar por ID:")
        lblBuscarID.setObjectName("MutedLabel")

        self.txtBuscarID = QLineEdit()
        self.txtBuscarID.setObjectName("SearchBox")
        self.txtBuscarID.setFixedWidth(260)

        self.btnBuscarID = self._button("Buscar", self.on_buscar_id, width=140)

        self.cboMostrarID = QComboBox()
        self.cboMostrarID.setObjectName("Combo")
        self.cboMostrarID.setFixedWidth(210)
        self.cboMostrarID.currentIndexChanged.connect(self.on_combo_id_changed)

        row4.addStretch(1)
        row4.addWidget(lblBuscarID)
        row4.addWidget(self.txtBuscarID)
        row4.addWidget(self.btnBuscarID)
        row4.addWidget(self.cboMostrarID)
        row4.addStretch(1)

        card_layout.addLayout(row4)

        # === Validadores de campos ===
        validator_letras = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
        )
        validator_numeros = QRegularExpressionValidator(
            QRegularExpression(r"^[0-9]+$")
        )
        validator_direccion = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s#\-.,]+$")
        )
        validator_correo = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-Z0-9_.+\-@]+$")
        )
        self.txtNombre.setValidator(validator_letras)
        self.txtTelefono.setValidator(validator_numeros)
        self.txtCorreo.setValidator(validator_correo)
        self.txtDireccion.setValidator(validator_direccion)
        self.txtBuscarID.setValidator(validator_numeros)
        self.txtBuscarNombre.setValidator(validator_letras)

        # === Tabla (contenedor con borde redondeado) ===
        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        tf = QVBoxLayout(table_frame)
        tf.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Correo", "Dirección"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.itemSelectionChanged.connect(self.on_row_selected)

        tf.addWidget(self.table)
        card_layout.addWidget(table_frame)

        # === Botón Salir ===
        row_bottom = QHBoxLayout()
        row_bottom.addStretch(1)
        self.btnSalir = self._button("Salir", self.close, width=220)
        row_bottom.addWidget(self.btnSalir)
        row_bottom.addStretch(1)
        card_layout.addLayout(row_bottom)

        main.addWidget(card)

        # Estilos (Minimal Luxe)
        self.setStyleSheet(self._stylesheet())

        # Cargar datos
        self.load_all()
    def closeEvent(self, event):
        if self.ventana_principal is not None:
            self.ventana_principal.show()
        event.accept()
    # ---------- UI helpers ----------
    def _labeled_edit(self, label: str, obj_name: str, width: int) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setSpacing(8)

        lbl = QLabel(label)
        lbl.setObjectName("MutedLabel")

        edit = QLineEdit()
        edit.setObjectName(obj_name)
        edit.setFixedWidth(width)

        lay.addWidget(lbl)
        lay.addWidget(edit)

        setattr(self, obj_name, edit)
        return lay

    def _button(self, text: str, handler, width: int = 110) -> QPushButton:
        b = QPushButton(text)
        b.setObjectName("Btn")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(handler)
        b.setFixedWidth(width)
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

    def clear_form(self) -> None:
        self.current_id = None
        self.txtNombre.clear()
        self.txtTelefono.clear()
        self.txtCorreo.clear()
        self.txtDireccion.clear()
        self.table.clearSelection()

    def _get_form_values(self) -> Tuple[str, str, str, str]:
        nombre = self.txtNombre.text().strip()
        telefono = self.txtTelefono.text().strip()
        correo = self.txtCorreo.text().strip()
        direccion = self.txtDireccion.text().strip()
        return nombre, telefono, correo, direccion

    # ---------- Tabla / carga ----------
    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
            self.refresh_id_combo(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, str, str, str]]) -> None:
        self.table.setRowCount(0)
        for r, (pid, nombre, telefono, correo, direccion) in enumerate(rows):
            self.table.insertRow(r)

            it_id = QTableWidgetItem(str(pid))
            it_nom = QTableWidgetItem(nombre)
            it_tel = QTableWidgetItem(telefono)
            it_cor = QTableWidgetItem(correo)
            it_dir = QTableWidgetItem(direccion)

            for it in (it_id, it_nom, it_tel, it_cor, it_dir):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_nom)
            self.table.setItem(r, 2, it_tel)
            self.table.setItem(r, 3, it_cor)
            self.table.setItem(r, 4, it_dir)

    def refresh_id_combo(self, rows: List[Tuple[int, str, str, str, str]]) -> None:
        self.cboMostrarID.blockSignals(True)
        self.cboMostrarID.clear()
        self.cboMostrarID.addItem("Mostrar ID", None)
        for (pid, _, _, _, _) in rows:
            self.cboMostrarID.addItem(str(pid), pid)
        self.cboMostrarID.setCurrentIndex(0)
        self.cboMostrarID.blockSignals(False)

    # ---------- Eventos ----------
    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return

        row = items[0].row()
        pid = int(self.table.item(row, 0).text())

        try:
            data = self.repo.fetch_by_id(pid)
            if not data:
                return
            pid, nombre, telefono, correo, direccion = data[0]
            self.current_id = pid
            self.txtNombre.setText(nombre)
            self.txtTelefono.setText(telefono)
            self.txtCorreo.setText(correo)
            self.txtDireccion.setText(direccion)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_mostrar_todos(self) -> None:
        self.txtBuscarNombre.clear()
        self.txtBuscarID.clear()
        self.clear_form()
        self.load_all()

    def on_buscar_nombre(self) -> None:
        nombre = self.txtBuscarNombre.text().strip()
        if not nombre:
            self.load_all()
            return
        try:
            rows = self.repo.search_by_name(nombre)
            self.populate_table(rows)
            self.refresh_id_combo(rows)
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_buscar_id(self) -> None:
        raw = self.txtBuscarID.text().strip()
        if not raw:
            self._show_error("Validación", "Escribe un ID para buscar.")
            return
        try:
            pid = int(raw)
        except ValueError:
            self._show_error("Validación", "El ID debe ser numérico.")
            return

        try:
            rows = self.repo.fetch_by_id(pid)
            self.populate_table(rows)
            self.refresh_id_combo(rows if rows else [])
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_combo_id_changed(self) -> None:
        pid = self.cboMostrarID.currentData()
        if pid is None:
            return
        try:
            rows = self.repo.fetch_by_id(int(pid))
            self.populate_table(rows)
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_agregar(self) -> None:
        nombre, telefono, correo, direccion = self._get_form_values()
        if not nombre or not telefono or not correo or not direccion:
            self._show_error("Validación", "Completa Nombre, Teléfono, Correo y Dirección.")
            return
        if not _EMAIL_RE.match(correo):
            self._show_error("Validación", "El correo no tiene un formato válido (ejemplo: usuario@dominio.com).")
            return
        try:
            self.repo.insert(nombre, telefono, correo, direccion)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_editar(self) -> None:
        if self.current_id is None:
            self._show_error("Editar", "Selecciona un proveedor de la tabla.")
            return
        nombre, telefono, correo, direccion = self._get_form_values()
        if not nombre or not telefono or not correo or not direccion:
            self._show_error("Validación", "Completa Nombre, Teléfono, Correo y Dirección.")
            return
        if not _EMAIL_RE.match(correo):
            self._show_error("Validación", "El correo no tiene un formato válido (ejemplo: usuario@dominio.com).")
            return
        try:
            self.repo.update(self.current_id, nombre, telefono, correo, direccion)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona un proveedor de la tabla.")
            return

        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar el proveedor ID {self.current_id}?",
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


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ProveedoresWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
