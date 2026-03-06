from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import List, Optional, Tuple

from config.conexion import obtener_conexion

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
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


class VendedoresRepo:
    TABLE = "Vendedores"

    def fetch_all(self) -> List[Tuple[int, str, str, str, bool]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_vendedor, nombre, correo, telefono, activo "
                "FROM Vendedores ORDER BY id_vendedor"
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                vid = int(r[0])
                nombre = str(r[1]) if r[1] is not None else ""
                correo = str(r[2]) if r[2] is not None else ""
                telefono = str(r[3]) if r[3] is not None else ""
                activo = bool(r[4]) if r[4] is not None else False
                result.append((vid, nombre, correo, telefono, activo))
            return result

    def fetch_by_id(self, vendedor_id: int) -> List[Tuple[int, str, str, str, bool]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_vendedor, nombre, correo, telefono, activo "
                "FROM Vendedores WHERE id_vendedor = ?",
                (vendedor_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                vid = int(r[0])
                nombre = str(r[1]) if r[1] is not None else ""
                correo = str(r[2]) if r[2] is not None else ""
                telefono = str(r[3]) if r[3] is not None else ""
                activo = bool(r[4]) if r[4] is not None else False
                result.append((vid, nombre, correo, telefono, activo))
            return result

    def search_by_name(self, nombre: str) -> List[Tuple[int, str, str, str, bool]]:
        with db() as conn:
            cur = conn.cursor()
            like = f"%{nombre}%"
            _exec(
                cur,
                "SELECT id_vendedor, nombre, correo, telefono, activo "
                "FROM Vendedores WHERE nombre LIKE ? ORDER BY id_vendedor",
                (like,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                vid = int(r[0])
                nombre = str(r[1]) if r[1] is not None else ""
                correo = str(r[2]) if r[2] is not None else ""
                telefono = str(r[3]) if r[3] is not None else ""
                activo = bool(r[4]) if r[4] is not None else False
                result.append((vid, nombre, correo, telefono, activo))
            return result

    def insert(self, nombre: str, correo: str, telefono: str, activo: bool) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Vendedores (nombre, correo, telefono, activo) VALUES (?, ?, ?, ?)",
                (nombre, correo, telefono, int(activo)),
            )
            conn.commit()

    def update(self, vendedor_id: int, nombre: str, correo: str, telefono: str, activo: bool) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Vendedores "
                "SET nombre = ?, correo = ?, telefono = ?, activo = ? "
                "WHERE id_vendedor = ?",
                (nombre, correo, telefono, int(activo), vendedor_id),
            )
            conn.commit()

    def delete(self, vendedor_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM Vendedores WHERE id_vendedor = ?", (vendedor_id,))
            conn.commit()


# =========================
# Ventana detalle (PLACEHOLDER)
# =========================
class VendedorDetalleDialog(QDialog):
    def __init__(self, vendedor_id: int, nombre: str, correo: str, telefono: str, activo: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Vendedor ID {vendedor_id}")
        self.setFixedSize(380, 260)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(18, 18, 18, 18)
        self.layout().setSpacing(12)

        title = QLabel(f"Vendedor ID {vendedor_id}")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        self.layout().addWidget(title)

        info = QLabel(
            f"ID: {vendedor_id}\n\n"
            f"Nombre: {nombre}\n"
            f"Correo: {correo}\n"
            f"Teléfono: {telefono}\n"
            f"Activo: {'Sí' if activo else 'No'}"
        )
        info.setAlignment(Qt.AlignHCenter)
        self.layout().addWidget(info)

        btn = QPushButton("Cerrar")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.accept)
        btn.setFixedHeight(34)
        btn.setObjectName("Btn")
        self.layout().addWidget(btn, alignment=Qt.AlignHCenter)

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
# UI Principal para VENDEDORES
# =========================
class VendedoresVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de Vendedores")
        self.setFixedSize(980, 660)

        self.repo = VendedoresRepo()
        self.current_id: Optional[int] = None
        self._block_open_detail = False

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

        title = QLabel("Gestión de Vendedores")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # Inputs row
        row1 = QHBoxLayout()
        row1.setSpacing(18)
        row1.addStretch(1)
        row1.addLayout(self._labeled_edit("Nombre:", "txtNombre", width=220))
        row1.addLayout(self._labeled_edit("Correo:", "txtCorreo", width=300))
        row1.addLayout(self._labeled_edit("Teléfono:", "txtTelefono", width=140))

        # Activo checkbox
        ch_layout = QHBoxLayout()
        ch_layout.setSpacing(8)
        lbl_act = QLabel("Activo:")
        lbl_act.setObjectName("MutedLabel")
        self.chkActivo = QCheckBox()
        ch_layout.addWidget(lbl_act)
        ch_layout.addWidget(self.chkActivo)
        ch_layout.addStretch(1)
        row1.addLayout(ch_layout)
        row1.addStretch(1)

        card_layout.addLayout(row1)

        # CRUD buttons
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

        # Search by name
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        lblBuscar = QLabel("Buscar por nombre:")
        lblBuscar.setObjectName("MutedLabel")
        self.txtBuscar = QLineEdit()
        self.txtBuscar.setObjectName("SearchBox")
        self.txtBuscar.setFixedWidth(280)
        self.btnBuscar = self._button("Buscar", self.on_buscar)
        self.btnMostrar = self._button("Mostrar Todos", self.on_mostrar_todos)
        row3.addStretch(1)
        row3.addWidget(lblBuscar)
        row3.addWidget(self.txtBuscar)
        row3.addWidget(self.btnBuscar)
        row3.addWidget(self.btnMostrar)
        row3.addStretch(1)
        card_layout.addLayout(row3)

        # Search by ID
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

        # Table
        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        tf = QVBoxLayout(table_frame)
        tf.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Correo", "Teléfono", "Activo"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 260)
        self.table.setColumnWidth(2, 320)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 70)

        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.table.cellClicked.connect(self.on_table_clicked)
        self.table.horizontalHeader().setStretchLastSection(True)

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

        # Load data
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

    # Helpers
    def _show_error(self, title: str, msg: str) -> None:
        QMessageBox.critical(self, title, msg)

    def clear_form(self) -> None:
        self.current_id = None
        self.txtNombre.clear()
        self.txtCorreo.clear()
        self.txtTelefono.clear()
        self.chkActivo.setChecked(False)
        self.table.clearSelection()

    def _get_form_values(self) -> Tuple[str, str, str, bool]:
        nombre = self.txtNombre.text().strip()
        correo = self.txtCorreo.text().strip()
        telefono = self.txtTelefono.text().strip()
        activo = bool(self.chkActivo.isChecked())
        return nombre, correo, telefono, activo

    # Load / populate
    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, str, str, bool]]) -> None:
        self.table.setRowCount(0)
        for r, (vid, nombre, correo, telefono, activo) in enumerate(rows):
            self.table.insertRow(r)
            it_id = QTableWidgetItem(str(vid))
            it_id.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            it_nom = QTableWidgetItem(nombre)
            it_cor = QTableWidgetItem(correo)
            it_tel = QTableWidgetItem(telefono)
            it_act = QTableWidgetItem("Sí" if activo else "No")
            for it in (it_id, it_nom, it_cor, it_tel, it_act):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_nom)
            self.table.setItem(r, 2, it_cor)
            self.table.setItem(r, 3, it_tel)
            self.table.setItem(r, 4, it_act)

    # Events
    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        vid = int(self.table.item(row, 0).text())
        nombre = self.table.item(row, 1).text()
        correo = self.table.item(row, 2).text()
        telefono = self.table.item(row, 3).text()
        activo_text = self.table.item(row, 4).text()
        activo = True if activo_text == "Sí" else False
        self.current_id = vid
        self.txtNombre.setText(nombre)
        self.txtCorreo.setText(correo)
        self.txtTelefono.setText(telefono)
        self.chkActivo.setChecked(activo)

    def on_table_clicked(self, row: int, col: int) -> None:
        if self._block_open_detail:
            return
        try:
            vid = int(self.table.item(row, 0).text())
            nombre = self.table.item(row, 1).text()
            correo = self.table.item(row, 2).text()
            telefono = self.table.item(row, 3).text()
            activo = True if self.table.item(row, 4).text() == "Sí" else False
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
            vid = int(raw)
        except ValueError:
            self._show_error("Validación", "El ID debe ser numérico.")
            return
        try:
            rows = self.repo.fetch_by_id(vid)
            self._block_open_detail = True
            self.populate_table(rows)
            self._block_open_detail = False
            if rows:
                vid, nombre, correo, telefono, activo = rows[0]
                self.current_id = vid
                self.txtNombre.setText(nombre)
                self.txtCorreo.setText(correo)
                self.txtTelefono.setText(telefono)
                self.chkActivo.setChecked(bool(activo))
            else:
                self.clear_form()
                QMessageBox.information(self, "Resultado", "No se encontró ningún vendedor con ese ID.")
        except Exception as e:
            self._block_open_detail = False
            self._show_error("Error BD", str(e))

    def on_agregar(self) -> None:
        nombre, correo, telefono, activo = self._get_form_values()
        if not nombre or not correo or not telefono:
            self._show_error("Validación", "Completa Nombre, Correo y Teléfono.")
            return
        try:
            self.repo.insert(nombre, correo, telefono, activo)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_editar(self) -> None:
        if self.current_id is None:
            self._show_error("Editar", "Selecciona un vendedor de la tabla.")
            return
        nombre, correo, telefono, activo = self._get_form_values()
        if not nombre or not correo or not telefono:
            self._show_error("Validación", "Completa Nombre, Correo y Teléfono.")
            return
        try:
            self.repo.update(self.current_id, nombre, correo, telefono, activo)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona un vendedor de la tabla.")
            return
        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar el vendedor ID {self.current_id}?",
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
    w = VendedoresVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
