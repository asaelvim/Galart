from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import List, Optional, Tuple
from datetime import datetime

from config.conexion import obtener_conexion

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDateEdit,
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


class ExhibicionesRepo:
    TABLE = "Exhibicion"

    def fetch_all(self) -> List[Tuple[int, str, str]]:
        """Retorna (id_columna, nombre, fecha_str)."""
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_columna, nombre, fecha "
                "FROM Exhibicion ORDER BY id_columna"
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                eid = int(r[0])
                nombre = str(r[1]) if r[1] is not None else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] is not None else ""
                result.append((eid, nombre, fecha))
            return result

    def fetch_by_id(self, exhibicion_id: int) -> List[Tuple[int, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_columna, nombre, fecha "
                "FROM Exhibicion WHERE id_columna = ?",
                (exhibicion_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                eid = int(r[0])
                nombre = str(r[1]) if r[1] is not None else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] is not None else ""
                result.append((eid, nombre, fecha))
            return result

    def search_by_name(self, nombre: str) -> List[Tuple[int, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            like = f"%{nombre}%"
            _exec(
                cur,
                "SELECT id_columna, nombre, fecha "
                "FROM Exhibicion WHERE nombre LIKE ? ORDER BY id_columna",
                (like,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                eid = int(r[0])
                nom = str(r[1]) if r[1] is not None else ""
                fecha = r[2].strftime("%Y-%m-%d") if r[2] is not None else ""
                result.append((eid, nom, fecha))
            return result

    def insert(self, nombre: str, fecha: str) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Exhibicion (nombre, fecha) VALUES (?, ?)",
                (nombre, fecha),
            )
            conn.commit()

    def update(self, exhibicion_id: int, nombre: str, fecha: str) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Exhibicion SET nombre = ?, fecha = ? "
                "WHERE id_columna = ?",
                (nombre, fecha, exhibicion_id),
            )
            conn.commit()

    def delete(self, exhibicion_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM Exhibicion WHERE id_columna = ?", (exhibicion_id,))
            conn.commit()


# =========================
# UI Principal para EXHIBICIONES
# =========================
class ExhibicionesVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de Exhibiciones")
        self.setFixedSize(940, 660)

        self.repo = ExhibicionesRepo()
        self.current_id: Optional[int] = None

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

        # Título
        title = QLabel("Gestión de Exhibiciones")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # === Fila Nombre + botón Agregar ===
        row_nombre = QHBoxLayout()
        row_nombre.setSpacing(12)
        row_nombre.addStretch(1)
        lbl_nombre = QLabel("Nombre:")
        lbl_nombre.setObjectName("MutedLabel")
        self.txtNombre = QLineEdit()
        self.txtNombre.setObjectName("txtNombre")
        self.txtNombre.setFixedWidth(460)
        self.btnAgregar = self._button("Agregar", self.on_agregar)
        row_nombre.addWidget(lbl_nombre)
        row_nombre.addWidget(self.txtNombre)
        row_nombre.addWidget(self.btnAgregar)
        row_nombre.addStretch(1)
        card_layout.addLayout(row_nombre)

        # === Fila Fecha + botón Editar ===
        row_fecha = QHBoxLayout()
        row_fecha.setSpacing(12)
        row_fecha.addStretch(1)
        lbl_fecha = QLabel("Fecha:")
        lbl_fecha.setObjectName("MutedLabel")
        self.dateFecha = QDateEdit()
        self.dateFecha.setObjectName("dateFecha")
        self.dateFecha.setFixedWidth(460)
        self.dateFecha.setCalendarPopup(True)
        self.dateFecha.setDisplayFormat("yyyy-MM-dd")
        self.dateFecha.setDate(QDate.currentDate())
        self.btnEditar = self._button("Editar", self.on_editar)
        row_fecha.addWidget(lbl_fecha)
        row_fecha.addWidget(self.dateFecha)
        row_fecha.addWidget(self.btnEditar)
        row_fecha.addStretch(1)
        card_layout.addLayout(row_fecha)

        # === Fila con Eliminar (alineado con los otros botones) ===
        row_eliminar = QHBoxLayout()
        row_eliminar.setSpacing(12)
        row_eliminar.addStretch(1)
        spacer_label = QWidget()
        spacer_label.setFixedWidth(50)
        spacer_input = QWidget()
        spacer_input.setFixedWidth(460)
        self.btnEliminar = self._button("Eliminar", self.on_eliminar)
        row_eliminar.addWidget(spacer_label)
        row_eliminar.addWidget(spacer_input)
        row_eliminar.addWidget(self.btnEliminar)
        row_eliminar.addStretch(1)
        card_layout.addLayout(row_eliminar)

        # === Fila Buscar por nombre ===
        row_buscar = QHBoxLayout()
        row_buscar.setSpacing(12)
        row_buscar.addStretch(1)
        lbl_buscar = QLabel("Buscar por nombre:")
        lbl_buscar.setObjectName("MutedLabel")
        self.txtBuscar = QLineEdit()
        self.txtBuscar.setObjectName("SearchBox")
        self.txtBuscar.setFixedWidth(300)
        self.btnBuscar = self._button("Buscar", self.on_buscar)
        row_buscar.addWidget(lbl_buscar)
        row_buscar.addWidget(self.txtBuscar)
        row_buscar.addWidget(self.btnBuscar)
        row_buscar.addStretch(1)
        card_layout.addLayout(row_buscar)

        # === Fila Buscar por ID ===
        row_buscar_id = QHBoxLayout()
        row_buscar_id.setSpacing(12)
        row_buscar_id.addStretch(1)
        lbl_buscar_id = QLabel("Buscar por ID:")
        lbl_buscar_id.setObjectName("MutedLabel")
        self.txtBuscarID = QLineEdit()
        self.txtBuscarID.setObjectName("SearchBox")
        self.txtBuscarID.setFixedWidth(160)
        self.btnBuscarID = self._button("Buscar ID", self.on_buscar_id)
        row_buscar_id.addWidget(lbl_buscar_id)
        row_buscar_id.addWidget(self.txtBuscarID)
        row_buscar_id.addWidget(self.btnBuscarID)
        row_buscar_id.addStretch(1)
        card_layout.addLayout(row_buscar_id)

        # === Botón Mostrar todos centrado ===
        row_mostrar = QHBoxLayout()
        row_mostrar.addStretch(1)
        self.btnMostrarTodos = self._button("Mostrar todos", self.on_mostrar_todos, wide=True)
        row_mostrar.addWidget(self.btnMostrarTodos)
        row_mostrar.addStretch(1)
        card_layout.addLayout(row_mostrar)

        # === Tabla ===
        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        tf = QVBoxLayout(table_frame)
        tf.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, 3)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Fecha"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.itemSelectionChanged.connect(self.on_row_selected)

        tf.addWidget(self.table)
        card_layout.addWidget(table_frame)

        # === Botón Salir centrado abajo ===
        row_bottom = QHBoxLayout()
        row_bottom.addStretch(1)
        self.btnSalir = self._button("Salir", self.close, wide=True)
        row_bottom.addWidget(self.btnSalir)
        row_bottom.addStretch(1)
        card_layout.addLayout(row_bottom)

        main.addWidget(card)
        self.setStyleSheet(self._stylesheet())

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
        self.dateFecha.setDate(QDate.currentDate())
        self.table.clearSelection()

    def _get_form_values(self) -> Tuple[str, str]:
        nombre = self.txtNombre.text().strip()
        fecha_str = self.dateFecha.date().toString("yyyy-MM-dd")
        return nombre, fecha_str

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, str]]) -> None:
        self.table.setRowCount(0)
        for r, (eid, nombre, fecha) in enumerate(rows):
            self.table.insertRow(r)
            it_id = QTableWidgetItem(str(eid))
            it_id.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            it_nombre = QTableWidgetItem(nombre)
            it_fecha = QTableWidgetItem(fecha)
            for it in (it_id, it_nombre, it_fecha):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_nombre)
            self.table.setItem(r, 2, it_fecha)

    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        eid = int(self.table.item(row, 0).text())
        try:
            rows = self.repo.fetch_by_id(eid)
            if rows:
                _, nombre, fecha = rows[0]
                self.current_id = eid
                self.txtNombre.setText(nombre)
                if fecha:
                    self.dateFecha.setDate(QDate.fromString(fecha, "yyyy-MM-dd"))
                else:
                    self.dateFecha.setDate(QDate.currentDate())
        except Exception:
            self.current_id = eid
            self.txtNombre.setText(self.table.item(row, 1).text())
            fecha = self.table.item(row, 2).text()
            if fecha:
                self.dateFecha.setDate(QDate.fromString(fecha, "yyyy-MM-dd"))
            else:
                self.dateFecha.setDate(QDate.currentDate())

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
            self.populate_table(rows)
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_buscar_id(self) -> None:
        raw = self.txtBuscarID.text().strip()
        if not raw:
            self._show_error("Validación", "Escribe un ID para buscar.")
            return
        try:
            eid = int(raw)
        except ValueError:
            self._show_error("Validación", "El ID debe ser numérico.")
            return
        try:
            rows = self.repo.fetch_by_id(eid)
            if rows:
                _, nombre, fecha = rows[0]
                self.populate_table(rows)
                self.current_id = eid
                self.txtNombre.setText(nombre)
                if fecha:
                    self.dateFecha.setDate(QDate.fromString(fecha, "yyyy-MM-dd"))
                else:
                    self.dateFecha.setDate(QDate.currentDate())
            else:
                self.populate_table([])
                self.clear_form()
                QMessageBox.information(self, "Resultado", "No se encontró ninguna exhibición con ese ID.")
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_agregar(self) -> None:
        nombre, fecha = self._get_form_values()
        if not nombre:
            self._show_error("Validación", "El campo Nombre es obligatorio.")
            return
        try:
            self.repo.insert(nombre, fecha)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_editar(self) -> None:
        if self.current_id is None:
            self._show_error("Editar", "Selecciona una exhibición de la tabla.")
            return
        nombre, fecha = self._get_form_values()
        if not nombre:
            self._show_error("Validación", "El campo Nombre es obligatorio.")
            return
        try:
            self.repo.update(self.current_id, nombre, fecha)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona una exhibición de la tabla.")
            return
        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar la exhibición ID {self.current_id}?",
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
    w = ExhibicionesVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
