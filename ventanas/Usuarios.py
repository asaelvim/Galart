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
    QCheckBox,
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


def _exec(cur, sql, params=()):
    """Ejecuta SQL usando placeholders '?' (compatibles con pyodbc)."""
    cur.execute(sql, params)


class UsuariosRepo:
    TABLE = "Usuarios"

    def fetch_all(self) -> List[Tuple[int, str, str, str, str, str, Optional[int], str, bool]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT u.id_usuario, u.nombre, u.usuario, u.contraseña, u.email, u.telefono, "
                "u.id_tipo, t.nombre, u.activo "
                "FROM Usuarios u "
                "LEFT JOIN UsuarioTipo t ON u.id_tipo = t.id_tipo "
                "ORDER BY u.id_usuario"
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                result.append(
                    (
                        int(r[0]),
                        str(r[1]) if r[1] is not None else "",
                        str(r[2]) if r[2] is not None else "",
                        str(r[3]) if r[3] is not None else "",
                        str(r[4]) if r[4] is not None else "",
                        str(r[5]) if r[5] is not None else "",
                        int(r[6]) if r[6] is not None else None,
                        str(r[7]) if r[7] is not None else "",
                        bool(r[8]) if r[8] is not None else False,
                    )
                )
            return result

    def fetch_by_id(self, usuario_id: int) -> List[Tuple[int, str, str, str, str, str, Optional[int], str, bool]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT u.id_usuario, u.nombre, u.usuario, u.contraseña, u.email, u.telefono, "
                "u.id_tipo, t.nombre, u.activo "
                "FROM Usuarios u "
                "LEFT JOIN UsuarioTipo t ON u.id_tipo = t.id_tipo "
                "WHERE u.id_usuario = ?",
                (usuario_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                result.append(
                    (
                        int(r[0]),
                        str(r[1]) if r[1] is not None else "",
                        str(r[2]) if r[2] is not None else "",
                        str(r[3]) if r[3] is not None else "",
                        str(r[4]) if r[4] is not None else "",
                        str(r[5]) if r[5] is not None else "",
                        int(r[6]) if r[6] is not None else None,
                        str(r[7]) if r[7] is not None else "",
                        bool(r[8]) if r[8] is not None else False,
                    )
                )
            return result

    def search_by_name(self, nombre: str) -> List[Tuple[int, str, str, str, str, str, Optional[int], str, bool]]:
        with db() as conn:
            cur = conn.cursor()
            like = f"%{nombre}%"
            _exec(
                cur,
                "SELECT u.id_usuario, u.nombre, u.usuario, u.contraseña, u.email, u.telefono, "
                "u.id_tipo, t.nombre, u.activo "
                "FROM Usuarios u "
                "LEFT JOIN UsuarioTipo t ON u.id_tipo = t.id_tipo "
                "WHERE u.nombre LIKE ? "
                "ORDER BY u.id_usuario",
                (like,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                result.append(
                    (
                        int(r[0]),
                        str(r[1]) if r[1] is not None else "",
                        str(r[2]) if r[2] is not None else "",
                        str(r[3]) if r[3] is not None else "",
                        str(r[4]) if r[4] is not None else "",
                        str(r[5]) if r[5] is not None else "",
                        int(r[6]) if r[6] is not None else None,
                        str(r[7]) if r[7] is not None else "",
                        bool(r[8]) if r[8] is not None else False,
                    )
                )
            return result

    def fetch_tipos(self) -> List[Tuple[int, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "SELECT id_tipo, nombre FROM UsuarioTipo ORDER BY nombre")
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]) if r[1] is not None else "") for r in rows]

    def insert(
        self,
        nombre: str,
        usuario: str,
        contrasena: str,
        email: str,
        telefono: str,
        id_tipo: Optional[int],
        activo: bool,
    ) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Usuarios (nombre, usuario, contraseña, email, telefono, id_tipo, activo) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nombre, usuario, contrasena, email, telefono, id_tipo, int(activo)),
            )
            conn.commit()

    def update(
        self,
        usuario_id: int,
        nombre: str,
        usuario: str,
        contrasena: str,
        email: str,
        telefono: str,
        id_tipo: Optional[int],
        activo: bool,
    ) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Usuarios "
                "SET nombre = ?, usuario = ?, contraseña = ?, email = ?, telefono = ?, id_tipo = ?, activo = ? "
                "WHERE id_usuario = ?",
                (nombre, usuario, contrasena, email, telefono, id_tipo, int(activo), usuario_id),
            )
            conn.commit()

    def delete(self, usuario_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM Usuarios WHERE id_usuario = ?", (usuario_id,))
            conn.commit()


class UsuariosVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de Usuarios")
        self.setFixedSize(1100, 680)

        self.repo = UsuariosRepo()
        self.current_id: Optional[int] = None
        self._block_open_detail = False
        self._tipos: List[Tuple[int, str]] = []

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
        card_layout.setSpacing(12)

        title = QLabel("Gestión de Usuarios")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # Inputs row 1
        row1 = QHBoxLayout()
        row1.setSpacing(18)
        row1.addStretch(1)
        row1.addLayout(self._labeled_edit("Nombre:", "txtNombre", width=180))
        row1.addLayout(self._labeled_edit("Usuario:", "txtUsuario", width=150))
        row1.addLayout(self._labeled_edit("Contraseña:", "txtContrasena", width=150))
        self.txtContrasena.setEchoMode(QLineEdit.Password)
        row1.addStretch(1)
        card_layout.addLayout(row1)

        # Inputs row 2
        row2 = QHBoxLayout()
        row2.setSpacing(18)
        row2.addStretch(1)
        row2.addLayout(self._labeled_edit("Email:", "txtEmail", width=200))
        row2.addLayout(self._labeled_edit("Teléfono:", "txtTelefono", width=110))

        tipo_layout = QHBoxLayout()
        tipo_layout.setSpacing(8)
        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setObjectName("MutedLabel")
        self.cmbTipo = QComboBox()
        self.cmbTipo.setObjectName("Combo")
        self.cmbTipo.setFixedWidth(160)
        tipo_layout.addWidget(lbl_tipo)
        tipo_layout.addWidget(self.cmbTipo)
        row2.addLayout(tipo_layout)

        activo_layout = QHBoxLayout()
        activo_layout.setSpacing(8)
        lbl_activo = QLabel("Activo:")
        lbl_activo.setObjectName("MutedLabel")
        self.chkActivo = QCheckBox()
        activo_layout.addWidget(lbl_activo)
        activo_layout.addWidget(self.chkActivo)
        row2.addLayout(activo_layout)

        row2.addStretch(1)
        card_layout.addLayout(row2)

        # CRUD buttons
        row3 = QHBoxLayout()
        row3.addStretch(1)
        self.btnAgregar = self._button("Agregar", self.on_agregar)
        self.btnEditar = self._button("Editar", self.on_editar)
        self.btnEliminar = self._button("Eliminar", self.on_eliminar)
        row3.addWidget(self.btnAgregar)
        row3.addWidget(self.btnEditar)
        row3.addWidget(self.btnEliminar)
        row3.addStretch(1)
        card_layout.addLayout(row3)

        # Search by name
        row4 = QHBoxLayout()
        row4.setSpacing(12)
        lbl_buscar = QLabel("Buscar por nombre:")
        lbl_buscar.setObjectName("MutedLabel")
        self.txtBuscar = QLineEdit()
        self.txtBuscar.setObjectName("SearchBox")
        self.txtBuscar.setFixedWidth(280)
        self.btnBuscar = self._button("Buscar", self.on_buscar)
        self.btnMostrar = self._button("Mostrar Todos", self.on_mostrar_todos)
        row4.addStretch(1)
        row4.addWidget(lbl_buscar)
        row4.addWidget(self.txtBuscar)
        row4.addWidget(self.btnBuscar)
        row4.addWidget(self.btnMostrar)
        row4.addStretch(1)
        card_layout.addLayout(row4)

        # Search by ID
        row5 = QHBoxLayout()
        row5.setSpacing(12)
        lbl_buscar_id = QLabel("Buscar por ID:")
        lbl_buscar_id.setObjectName("MutedLabel")
        self.txtBuscarID = QLineEdit()
        self.txtBuscarID.setObjectName("SearchBox")
        self.txtBuscarID.setFixedWidth(160)
        self.btnBuscarID = self._button("Buscar ID", self.on_buscar_id)
        row5.addStretch(1)
        row5.addWidget(lbl_buscar_id)
        row5.addWidget(self.txtBuscarID)
        row5.addWidget(self.btnBuscarID)
        row5.addStretch(1)
        card_layout.addLayout(row5)

        # Validadores
        validator_letras = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
        )
        validator_numeros = QRegularExpressionValidator(
            QRegularExpression(r"^[0-9]+$")
        )
        validator_email = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-Z0-9_.+\-@]+$")
        )
        self.txtNombre.setValidator(validator_letras)
        self.txtTelefono.setValidator(validator_numeros)
        self.txtEmail.setValidator(validator_email)
        self.txtBuscarID.setValidator(validator_numeros)
        self.txtBuscar.setValidator(validator_letras)

        # Table
        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        tf = QVBoxLayout(table_frame)
        tf.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Usuario", "Email", "Teléfono", "Tipo", "Activo"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.table.cellClicked.connect(self.on_table_clicked)

        tf.addWidget(self.table)
        card_layout.addWidget(table_frame)

        # Bottom button
        row_bottom = QHBoxLayout()
        row_bottom.addStretch(1)
        self.btnSalir = self._button("Salir", self.close, wide=True)
        row_bottom.addWidget(self.btnSalir)
        row_bottom.addStretch(1)
        card_layout.addLayout(row_bottom)

        main.addWidget(card)
        self.setStyleSheet(self._stylesheet())

        self._cargar_tipos()
        self.load_all()

    def closeEvent(self, event):
        if self.ventana_principal is not None:
            self.ventana_principal.show()
        event.accept()

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
        QLineEdit, QComboBox {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 6px 10px;
            color: {TEXT};
        }}
        QLineEdit:focus, QComboBox:focus {{
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

    def _show_error(self, title: str, msg: str) -> None:
        QMessageBox.critical(self, title, msg)

    def _cargar_tipos(self) -> None:
        try:
            self._tipos = self.repo.fetch_tipos()
            self.cmbTipo.clear()
            self.cmbTipo.addItem("", None)
            for tipo_id, nombre in self._tipos:
                self.cmbTipo.addItem(nombre, tipo_id)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def _set_tipo_por_id(self, tipo_id: Optional[int]) -> None:
        if tipo_id is None:
            self.cmbTipo.setCurrentIndex(0)
            return
        index = self.cmbTipo.findData(tipo_id)
        self.cmbTipo.setCurrentIndex(index if index >= 0 else 0)

    def _get_tipo_id_seleccionado(self) -> Optional[int]:
        value = self.cmbTipo.currentData()
        if value in ("", None):
            return None
        return int(value)

    def clear_form(self) -> None:
        self.current_id = None
        self.txtNombre.clear()
        self.txtUsuario.clear()
        self.txtContrasena.clear()
        self.txtEmail.clear()
        self.txtTelefono.clear()
        self._set_tipo_por_id(None)
        self.chkActivo.setChecked(False)
        self.table.clearSelection()

    def _get_form_values(self) -> Tuple[str, str, str, str, str, Optional[int], bool]:
        nombre = self.txtNombre.text().strip()
        usuario = self.txtUsuario.text().strip()
        contrasena = self.txtContrasena.text().strip()
        email = self.txtEmail.text().strip()
        telefono = self.txtTelefono.text().strip()
        id_tipo = self._get_tipo_id_seleccionado()
        activo = bool(self.chkActivo.isChecked())
        return nombre, usuario, contrasena, email, telefono, id_tipo, activo

    def _cargar_formulario_desde_id(self, usuario_id: int) -> None:
        rows = self.repo.fetch_by_id(usuario_id)
        if not rows:
            return
        uid, nombre, usuario, contrasena, email, telefono, id_tipo, _, activo = rows[0]
        self.current_id = uid
        self.txtNombre.setText(nombre)
        self.txtUsuario.setText(usuario)
        self.txtContrasena.setText(contrasena)
        self.txtEmail.setText(email)
        self.txtTelefono.setText(telefono)
        self._set_tipo_por_id(id_tipo)
        self.chkActivo.setChecked(bool(activo))

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, str, str, str, str, Optional[int], str, bool]]) -> None:
        self.table.setRowCount(0)
        for r, (uid, nombre, usuario, _, email, telefono, _, tipo, activo) in enumerate(rows):
            self.table.insertRow(r)
            it_id = QTableWidgetItem(str(uid))
            it_id.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            it_nombre = QTableWidgetItem(nombre)
            it_usuario = QTableWidgetItem(usuario)
            it_email = QTableWidgetItem(email)
            it_tel = QTableWidgetItem(telefono)
            it_tipo = QTableWidgetItem(tipo)
            it_activo = QTableWidgetItem("Sí" if activo else "No")
            for it in (it_id, it_nombre, it_usuario, it_email, it_tel, it_tipo, it_activo):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_nombre)
            self.table.setItem(r, 2, it_usuario)
            self.table.setItem(r, 3, it_email)
            self.table.setItem(r, 4, it_tel)
            self.table.setItem(r, 5, it_tipo)
            self.table.setItem(r, 6, it_activo)

    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        uid = int(self.table.item(row, 0).text())
        try:
            self._cargar_formulario_desde_id(uid)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_table_clicked(self, row: int, col: int) -> None:
        if self._block_open_detail:
            return
        try:
            int(self.table.item(row, 0).text())
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
            uid = int(raw)
        except ValueError:
            self._show_error("Validación", "El ID debe ser numérico.")
            return
        try:
            rows = self.repo.fetch_by_id(uid)
            self._block_open_detail = True
            self.populate_table(rows)
            self._block_open_detail = False
            if rows:
                self._cargar_formulario_desde_id(uid)
            else:
                self.clear_form()
                QMessageBox.information(self, "Resultado", "No se encontró ningún usuario con ese ID.")
        except Exception as e:
            self._block_open_detail = False
            self._show_error("Error BD", str(e))

    def on_agregar(self) -> None:
        nombre, usuario, contrasena, email, telefono, id_tipo, activo = self._get_form_values()
        if not nombre or not usuario or not contrasena or not email:
            self._show_error("Validación", "Completa Nombre, Usuario, Contraseña y Email.")
            return
        if not _EMAIL_RE.match(email):
            self._show_error("Validación", "El email no tiene un formato válido (ejemplo: usuario@dominio.com).")
            return
        try:
            self.repo.insert(nombre, usuario, contrasena, email, telefono, id_tipo, activo)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_editar(self) -> None:
        if self.current_id is None:
            self._show_error("Editar", "Selecciona un usuario de la tabla.")
            return
        nombre, usuario, contrasena, email, telefono, id_tipo, activo = self._get_form_values()
        if not nombre or not usuario or not contrasena or not email:
            self._show_error("Validación", "Completa Nombre, Usuario, Contraseña y Email.")
            return
        if not _EMAIL_RE.match(email):
            self._show_error("Validación", "El email no tiene un formato válido (ejemplo: usuario@dominio.com).")
            return
        try:
            self.repo.update(self.current_id, nombre, usuario, contrasena, email, telefono, id_tipo, activo)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona un usuario de la tabla.")
            return
        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar el usuario ID {self.current_id}?",
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
    w = UsuariosVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
