"""
Pantalla: Gestión de Clientes (Paleta Opción A - Minimal Luxe)
UI en PySide6 + tabla conectada a BD vía config/conexion.py (obtener_conexion)

Incluye:
- CRUD
- Buscar por nombre
- Buscar por ID
- Al dar click en una fila de la tabla: abre ventana de detalle (placeholder)

Requisitos:
  pip install PySide6

Estructura esperada:
  - main_clientes.py   (este archivo)
  - config/conexion.py (tu conexión a BD)

Tabla esperada en BD: Clientes
  columnas: id_cliente (PK), nombre, correo, telefono

Ejecuta:
  python main_clientes.py
"""

from __future__ import annotations

import re
import sys
from contextlib import contextmanager
from typing import List, Optional, Tuple

from config.conexion import obtener_conexion
from modulos.PdfUtils import guardar_pdf, vista_previa_pdf, html_tabla_widget

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
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


def _exec(cur, sql, params=()):
    """Ejecuta SQL usando placeholders '?' (compatibles con pyodbc)."""
    cur.execute(sql, params)


class ClientesRepo:
    TABLE = "Clientes"

    def fetch_all(self) -> List[Tuple[int, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_cliente, nombre, correo, telefono "
                "FROM Clientes ORDER BY id_cliente"
            )
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]), str(r[2]), str(r[3])) for r in rows]

    def fetch_by_id(self, cliente_id: int) -> List[Tuple[int, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_cliente, nombre, correo, telefono "
                "FROM Clientes WHERE id_cliente = ?",
                (cliente_id,),
            )
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]), str(r[2]), str(r[3])) for r in rows]

    def search_by_name(self, nombre: str) -> List[Tuple[int, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            like = f"%{nombre}%"
            _exec(
                cur,
                "SELECT id_cliente, nombre, correo, telefono "
                "FROM Clientes WHERE nombre LIKE ? ORDER BY id_cliente",
                (like,),
            )
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]), str(r[2]), str(r[3])) for r in rows]

    def insert(self, nombre: str, correo: str, telefono: str) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Clientes (nombre, correo, telefono) VALUES (?, ?, ?)",
                (nombre, correo, telefono),
            )
            conn.commit()

    def update(self, cliente_id: int, nombre: str, correo: str, telefono: str) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Clientes "
                "SET nombre = ?, correo = ?, telefono = ? "
                "WHERE id_cliente = ?",
                (nombre, correo, telefono, cliente_id),
            )
            conn.commit()

    def delete(self, cliente_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM Clientes WHERE id_cliente = ?", (cliente_id,))
            conn.commit()


# =========================
# Ventana detalle (PLACEHOLDER)
# (Luego tú me pides el código real. Aquí solo existe para que el código de Clientes ya quede terminado)
# =========================
class ClienteDetalleDialog(QDialog):
    def __init__(self, cliente_id: int, nombre: str, correo: str, telefono: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Cliente ID {cliente_id}")
        self.setMinimumSize(360, 240)

        root = QWidget()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(18, 18, 18, 18)
        self.layout().setSpacing(12)

        title = QLabel(f"Cliente ID {cliente_id}")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        self.layout().addWidget(title)

        info = QLabel(
            f"ID: {cliente_id}\n\n"
            f"Nombre: {nombre}\n"
            f"Correo: {correo}\n"
            f"Teléfono: {telefono}"
        )
        info.setAlignment(Qt.AlignHCenter)
        self.layout().addWidget(info)

        btn = QPushButton("Cerrar")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.accept)
        btn.setFixedHeight(34)
        btn.setObjectName("Btn")
        self.layout().addWidget(btn, alignment=Qt.AlignHCenter)

        # mismo estilo
        self.setStyleSheet(f"""
        QDialog {{
            background: {BG};
            color: {TEXT};
            font-family: "Segoe UI";
            font-size: 10pt;
        }}
        QPushButton#Btn {{
            background: {BTN_BG};
            color: {BTN_TEXT};
            border: 1px solid {BTN_BORDER};
            border-radius: 9px;
            padding: 6px 16px;
        }}
        QPushButton#Btn:hover {{
            border: 1px solid {GOLD};
            background: {BG};
        }}
        QPushButton#Btn:pressed {{
            background: #EFE7DD;
        }}
        """)


# =========================
# UI Principal
# =========================
class ClientesVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de Clientes")
        self.setMinimumSize(900, 660)

        self.repo = ClientesRepo()
        self.current_id: Optional[int] = None

        # Para evitar abrir 2 veces con selección programática
        self._block_open_detail = False

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
        title = QLabel("Gestión de Clientes")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # === Fila 1: inputs ===
        row1 = QHBoxLayout()
        row1.setSpacing(18)
        row1.addStretch(1)
        row1.addLayout(self._labeled_edit("Nombre:", "txtNombre", width=190))
        row1.addLayout(self._labeled_edit("Correo:", "txtCorreo", width=260))
        row1.addLayout(self._labeled_edit("Teléfono:", "txtTelefono", width=120))
        row1.addStretch(1)

        card_layout.addLayout(row1)

        # === Fila 2: botones CRUD ===
        row2 = QHBoxLayout()
        row2.addStretch(1)

        self.btnAgregar = self._button("Agregar", self.on_agregar)
        self.btnEditar = self._button("Editar", self.on_editar)
        self.btnEliminar = self._button("Eliminar", self.on_eliminar)

        row2.addWidget(self.btnAgregar)
        row2.addWidget(self.btnEditar)
        row2.addWidget(self.btnEliminar)

        row2.addStretch(1)
        card_layout.addLayout(row2)

        # === Fila 3: búsqueda por nombre ===
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        lblBuscar = QLabel("Buscar por nombre:")
        lblBuscar.setObjectName("MutedLabel")

        self.txtBuscar = QLineEdit()
        self.txtBuscar.setObjectName("SearchBox")
        self.txtBuscar.setFixedWidth(260)

        self.btnBuscar = self._button("Buscar", self.on_buscar)
        self.btnMostrar = self._button("Mostrar Todos", self.on_mostrar_todos)

        row3.addStretch(1)
        row3.addWidget(lblBuscar)
        row3.addWidget(self.txtBuscar)
        row3.addWidget(self.btnBuscar)
        row3.addWidget(self.btnMostrar)
        row3.addStretch(1)

        card_layout.addLayout(row3)

        # === Fila 4: búsqueda por ID ===
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        lblBuscarID = QLabel("Buscar por ID:")
        lblBuscarID.setObjectName("MutedLabel")

        self.txtBuscarID = QLineEdit()
        self.txtBuscarID.setObjectName("SearchBox")
        self.txtBuscarID.setFixedWidth(160)

        self.btnBuscarID = self._button("Buscar ID", self.on_buscar_id)

        row4.addStretch(1)
        row4.addWidget(lblBuscarID)
        row4.addWidget(self.txtBuscarID)
        row4.addWidget(self.btnBuscarID)
        row4.addStretch(1)

        card_layout.addLayout(row4)

        # === Validadores de campos ===
        validator_letras = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
        )
        validator_numeros = QRegularExpressionValidator(
            QRegularExpression(r"^[0-9]+$")
        )
        validator_telefono = QRegularExpressionValidator(
            QRegularExpression(r"^\d{0,10}$")
        )
        validator_correo = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-Z0-9_.+\-@]+$")
        )
        self.txtNombre.setValidator(validator_letras)
        self.txtTelefono.setValidator(validator_telefono)
        self.txtCorreo.setValidator(validator_correo)
        self.txtBuscarID.setValidator(validator_numeros)
        self.txtBuscar.setValidator(validator_letras)

        # === Tabla (contenedor con borde redondeado) ===
        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        tf = QVBoxLayout(table_frame)
        tf.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Correo", "Teléfono"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # IMPORTANTE:
        # - itemSelectionChanged solo llena el formulario
        # - cellClicked abre la ventana detalle (cuando el usuario da click)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.table.cellClicked.connect(self.on_table_clicked)

        tf.addWidget(self.table)
        card_layout.addWidget(table_frame)

        # === Botón Salir ===
        row_bottom = QHBoxLayout()
        row_bottom.addStretch(1)
        self.btnVistaPrevia = self._button("Vista Previa", self.vista_previa_pdf, wide=True)
        row_bottom.addWidget(self.btnVistaPrevia)
        row_bottom.addSpacing(8)
        self.btnExportarPDF = self._button("Exportar PDF", self.exportar_pdf, wide=True)
        row_bottom.addWidget(self.btnExportarPDF)
        row_bottom.addSpacing(8)
        self.btnSalir = self._button("Salir", self.close, wide=True)
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

    def exportar_pdf(self) -> None:
        guardar_pdf(self, "Gestión de Clientes", "clientes.pdf",
                    html_tabla_widget(self.table, "LISTADO DE CLIENTES"))

    def vista_previa_pdf(self) -> None:
        vista_previa_pdf(self, "Gestión de Clientes", "clientes.pdf",
                         html_tabla_widget(self.table, "LISTADO DE CLIENTES"))

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

    # =========================
    # Helpers UI
    # =========================
    def _show_error(self, title: str, msg: str) -> None:
        QMessageBox.critical(self, title, msg)

    def clear_form(self) -> None:
        self.current_id = None
        self.txtNombre.clear()
        self.txtCorreo.clear()
        self.txtTelefono.clear()
        self.table.clearSelection()

    def _get_form_values(self) -> Tuple[str, str, str]:
        nombre = self.txtNombre.text().strip()
        correo = self.txtCorreo.text().strip()
        telefono = self.txtTelefono.text().strip()
        return nombre, correo, telefono

    # =========================
    # Carga / Tabla
    # =========================
    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, str, str]]) -> None:
        self.table.setRowCount(0)
        for r, (cid, nombre, correo, telefono) in enumerate(rows):
            self.table.insertRow(r)

            it_id = QTableWidgetItem(str(cid))
            it_id.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            it_nom = QTableWidgetItem(nombre)
            it_cor = QTableWidgetItem(correo)
            it_tel = QTableWidgetItem(telefono)

            for it in (it_id, it_nom, it_cor, it_tel):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_nom)
            self.table.setItem(r, 2, it_cor)
            self.table.setItem(r, 3, it_tel)

    # =========================
    # Eventos
    # =========================
    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return

        row = items[0].row()
        cid = int(self.table.item(row, 0).text())
        nombre = self.table.item(row, 1).text()
        correo = self.table.item(row, 2).text()
        telefono = self.table.item(row, 3).text()

        self.current_id = cid
        self.txtNombre.setText(nombre)
        self.txtCorreo.setText(correo)
        self.txtTelefono.setText(telefono)

    def on_table_clicked(self, row: int, col: int) -> None:
        """
        Abre la ventana detalle SOLO cuando el usuario hace click.
        (No se abre cuando la selección cambia por código.)
        """
        if self._block_open_detail:
            return

        try:
            cid = int(self.table.item(row, 0).text())
            nombre = self.table.item(row, 1).text()
            correo = self.table.item(row, 2).text()
            telefono = self.table.item(row, 3).text()
        except Exception:
            return


    def on_mostrar_todos(self) -> None:
        self.txtBuscar.clear()
        self.txtBuscarID.clear()
        self.load_all()
        self.clear_form()

    def on_buscar(self) -> None:
        nombre = self.txtBuscar.text().strip()
        if not nombre:
            self.load_all()
            return
        try:
            rows = self.repo.search_by_name(nombre)
            self._block_open_detail = True
            self.populate_table(rows)
            self._block_open_detail = False
            self.clear_form()
        except Exception as e:
            self._block_open_detail = False
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
            self._block_open_detail = True
            self.populate_table(rows)
            self._block_open_detail = False

            if rows:
                cid, nombre, correo, telefono = rows[0]
                self.current_id = cid
                self.txtNombre.setText(nombre)
                self.txtCorreo.setText(correo)
                self.txtTelefono.setText(telefono)
            else:
                self.clear_form()
                QMessageBox.information(self, "Resultado", "No se encontró ningún cliente con ese ID.")
        except Exception as e:
            self._block_open_detail = False
            self._show_error("Error BD", str(e))

    def on_agregar(self) -> None:
        nombre, correo, telefono = self._get_form_values()
        if not nombre or not correo or not telefono:
            self._show_error("Validación", "Completa Nombre, Correo y Teléfono.")
            return
        if len(telefono) != 10:
            self._show_error("Validación", "El teléfono debe tener exactamente 10 dígitos.")
            return
        if not _EMAIL_RE.match(correo):
            self._show_error("Validación", "El correo no tiene un formato válido (ejemplo: usuario@dominio.com).")
            return
        try:
            self.repo.insert(nombre, correo, telefono)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_editar(self) -> None:
        if self.current_id is None:
            self._show_error("Editar", "Selecciona un cliente de la tabla.")
            return
        nombre, correo, telefono = self._get_form_values()
        if not nombre or not correo or not telefono:
            self._show_error("Validación", "Completa Nombre, Correo y Teléfono.")
            return
        if len(telefono) != 10:
            self._show_error("Validación", "El teléfono debe tener exactamente 10 dígitos.")
            return
        if not _EMAIL_RE.match(correo):
            self._show_error("Validación", "El correo no tiene un formato válido (ejemplo: usuario@dominio.com).")
            return
        try:
            self.repo.update(self.current_id, nombre, correo, telefono)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona un cliente de la tabla.")
            return
        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar el cliente ID {self.current_id}?",
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
    w = ClientesVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
