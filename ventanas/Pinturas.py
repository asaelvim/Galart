from __future__ import annotations

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


class PinturasRepo:
    TABLE = "Pinturas"

    def fetch_all(self) -> List[Tuple[int, str, float, int, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT p.id_pintura, p.titulo, p.precio, p.id_artista, "
                "ISNULL(a.nombre, '') as artista_nombre "
                "FROM Pinturas p "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "ORDER BY p.id_pintura",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                pid = int(r[0])
                titulo = str(r[1]) if r[1] is not None else ""
                precio = float(r[2]) if r[2] is not None else 0.0
                id_artista = int(r[3]) if r[3] is not None else 0
                artista_nombre = str(r[4]) if r[4] is not None else ""
                result.append((pid, titulo, precio, id_artista, artista_nombre))
            return result

    def fetch_by_id(self, pintura_id: int) -> List[Tuple[int, str, float, int, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT p.id_pintura, p.titulo, p.precio, p.id_artista, "
                "ISNULL(a.nombre, '') as artista_nombre "
                "FROM Pinturas p "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "WHERE p.id_pintura = ?",
                (pintura_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                pid = int(r[0])
                titulo = str(r[1]) if r[1] is not None else ""
                precio = float(r[2]) if r[2] is not None else 0.0
                id_artista = int(r[3]) if r[3] is not None else 0
                artista_nombre = str(r[4]) if r[4] is not None else ""
                result.append((pid, titulo, precio, id_artista, artista_nombre))
            return result

    def search_by_title(self, titulo: str) -> List[Tuple[int, str, float, int, str]]:
        with db() as conn:
            cur = conn.cursor()
            like = f"%{titulo}%"
            _exec(
                cur,
                "SELECT p.id_pintura, p.titulo, p.precio, p.id_artista, "
                "ISNULL(a.nombre, '') as artista_nombre "
                "FROM Pinturas p "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "WHERE p.titulo LIKE ? ORDER BY p.id_pintura",
                (like,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                pid = int(r[0])
                titulo_val = str(r[1]) if r[1] is not None else ""
                precio = float(r[2]) if r[2] is not None else 0.0
                id_artista = int(r[3]) if r[3] is not None else 0
                artista_nombre = str(r[4]) if r[4] is not None else ""
                result.append((pid, titulo_val, precio, id_artista, artista_nombre))
            return result

    def insert(self, titulo: str, precio: float, id_artista: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Pinturas (titulo, precio, id_artista) VALUES (?, ?, ?)",
                (titulo, precio, id_artista),
            )
            conn.commit()

    def update(self, pintura_id: int, titulo: str, precio: float, id_artista: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Pinturas SET titulo = ?, precio = ?, id_artista = ? "
                "WHERE id_pintura = ?",
                (titulo, precio, id_artista, pintura_id),
            )
            conn.commit()

    def delete(self, pintura_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM Pinturas WHERE id_pintura = ?", (pintura_id,))
            conn.commit()


# =========================
# UI Principal para PINTURAS
# =========================
class PinturasVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de Pinturas")
        self.setFixedSize(940, 660)

        self.repo = PinturasRepo()
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
        title = QLabel("Gestión de Pinturas")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # === Fila Titulo + botón Agregar ===
        row_titulo = QHBoxLayout()
        row_titulo.setSpacing(12)
        row_titulo.addStretch(1)
        lbl_titulo = QLabel("Titulo:")
        lbl_titulo.setObjectName("MutedLabel")
        self.txtTitulo = QLineEdit()
        self.txtTitulo.setObjectName("txtTitulo")
        self.txtTitulo.setFixedWidth(460)
        self.btnAgregar = self._button("Agregar", self.on_agregar)
        row_titulo.addWidget(lbl_titulo)
        row_titulo.addWidget(self.txtTitulo)
        row_titulo.addWidget(self.btnAgregar)
        row_titulo.addStretch(1)
        card_layout.addLayout(row_titulo)

        # === Fila Precio + botón Editar ===
        row_precio = QHBoxLayout()
        row_precio.setSpacing(12)
        row_precio.addStretch(1)
        lbl_precio = QLabel("Precio:")
        lbl_precio.setObjectName("MutedLabel")
        self.txtPrecio = QLineEdit()
        self.txtPrecio.setObjectName("txtPrecio")
        self.txtPrecio.setFixedWidth(460)
        self.btnEditar = self._button("Editar", self.on_editar)
        row_precio.addWidget(lbl_precio)
        row_precio.addWidget(self.txtPrecio)
        row_precio.addWidget(self.btnEditar)
        row_precio.addStretch(1)
        card_layout.addLayout(row_precio)

        # === Fila Artista + botón Eliminar ===
        row_artista = QHBoxLayout()
        row_artista.setSpacing(12)
        row_artista.addStretch(1)
        lbl_artista = QLabel("Artista:")
        lbl_artista.setObjectName("MutedLabel")
        self.cboArtista = QComboBox()
        self.cboArtista.setObjectName("Combo")
        self.cboArtista.setFixedWidth(460)
        self.btnEliminar = self._button("Eliminar", self.on_eliminar)
        row_artista.addWidget(lbl_artista)
        row_artista.addWidget(self.cboArtista)
        row_artista.addWidget(self.btnEliminar)
        row_artista.addStretch(1)
        card_layout.addLayout(row_artista)

        # === Fila Buscar por titulo ===
        row_buscar = QHBoxLayout()
        row_buscar.setSpacing(12)
        row_buscar.addStretch(1)
        lbl_buscar = QLabel("Buscar por titulo:")
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

        # === Validadores de campos ===
        validator_titulo = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s]+$")
        )
        validator_precio = QRegularExpressionValidator(
            QRegularExpression(r"^[0-9]*\.?[0-9]*$")
        )
        validator_numeros = QRegularExpressionValidator(
            QRegularExpression(r"^[0-9]+$")
        )
        self.txtTitulo.setValidator(validator_titulo)
        self.txtPrecio.setValidator(validator_precio)
        self.txtBuscarID.setValidator(validator_numeros)
        self.txtBuscar.setValidator(validator_titulo)

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

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(["ID", "Titulo", "Precio", "Artista"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 360)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        self.table.horizontalHeader().setStretchLastSection(True)

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

        self._load_artistas_combo()
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

    def _load_artistas_combo(self) -> None:
        """Carga la lista de artistas en el ComboBox."""
        self.cboArtista.blockSignals(True)
        self.cboArtista.clear()
        self.cboArtista.addItem("-- Seleccionar artista --", None)
        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(cur, "SELECT id_artista, nombre FROM Artistas ORDER BY nombre")
                rows = cur.fetchall()
                for r in rows:
                    self.cboArtista.addItem(str(r[1]), int(r[0]))
        except Exception:
            pass
        self.cboArtista.setCurrentIndex(0)
        self.cboArtista.blockSignals(False)

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
        self.txtTitulo.clear()
        self.txtPrecio.clear()
        self.cboArtista.setCurrentIndex(0)
        self.table.clearSelection()

    def _get_form_values(self) -> Tuple[str, str, Optional[int]]:
        titulo = self.txtTitulo.text().strip()
        precio = self.txtPrecio.text().strip()
        artista_id = self.cboArtista.currentData()
        return titulo, precio, artista_id

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, float, int, str]]) -> None:
        self.table.setRowCount(0)
        for r, (pid, titulo, precio, id_artista, artista_nombre) in enumerate(rows):
            self.table.insertRow(r)
            it_id = QTableWidgetItem(str(pid))
            it_id.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            it_titulo = QTableWidgetItem(titulo)
            it_precio = QTableWidgetItem(f"{precio:.2f}")
            it_artista = QTableWidgetItem(artista_nombre)
            for it in (it_id, it_titulo, it_precio, it_artista):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_titulo)
            self.table.setItem(r, 2, it_precio)
            self.table.setItem(r, 3, it_artista)

    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        pid = int(self.table.item(row, 0).text())
        try:
            rows = self.repo.fetch_by_id(pid)
            if rows:
                _, titulo, precio, id_artista, _ = rows[0]
                self.current_id = pid
                self.txtTitulo.setText(titulo)
                self.txtPrecio.setText(f"{precio:.2f}")
                index = self.cboArtista.findData(id_artista)
                if index >= 0:
                    self.cboArtista.setCurrentIndex(index)
        except Exception:
            self.current_id = pid
            self.txtTitulo.setText(self.table.item(row, 1).text())
            self.txtPrecio.setText(self.table.item(row, 2).text())
            artista_text = self.table.item(row, 3).text()
            idx = self.cboArtista.findText(artista_text)
            if idx >= 0:
                self.cboArtista.setCurrentIndex(idx)

    def on_mostrar_todos(self) -> None:
        self.txtBuscar.clear()
        self.txtBuscarID.clear()
        self.load_all()
        self.clear_form()

    def on_buscar(self) -> None:
        titulo = self.txtBuscar.text().strip()
        if not titulo:
            self.load_all()
            return
        try:
            rows = self.repo.search_by_title(titulo)
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
            pid = int(raw)
        except ValueError:
            self._show_error("Validación", "El ID debe ser numérico.")
            return
        try:
            rows = self.repo.fetch_by_id(pid)
            if rows:
                _, titulo, precio, id_artista, _ = rows[0]
                self.populate_table(rows)
                self.current_id = pid
                self.txtTitulo.setText(titulo)
                self.txtPrecio.setText(f"{precio:.2f}")
                index = self.cboArtista.findData(id_artista)
                if index >= 0:
                    self.cboArtista.setCurrentIndex(index)
            else:
                self.populate_table([])
                self.clear_form()
                QMessageBox.information(self, "Resultado", "No se encontró ninguna pintura con ese ID.")
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_agregar(self) -> None:
        titulo, precio_str, artista_id = self._get_form_values()
        if not titulo:
            self._show_error("Validación", "El campo Titulo es obligatorio.")
            return
        try:
            precio = float(precio_str)
        except ValueError:
            self._show_error("Validación", "El campo Precio debe ser numérico.")
            return
        if artista_id is None:
            self._show_error("Validación", "Selecciona un artista.")
            return
        try:
            self.repo.insert(titulo, precio, artista_id)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_editar(self) -> None:
        if self.current_id is None:
            self._show_error("Editar", "Selecciona una pintura de la tabla.")
            return
        titulo, precio_str, artista_id = self._get_form_values()
        if not titulo:
            self._show_error("Validación", "El campo Titulo es obligatorio.")
            return
        try:
            precio = float(precio_str)
        except ValueError:
            self._show_error("Validación", "El campo Precio debe ser numérico.")
            return
        if artista_id is None:
            self._show_error("Validación", "Selecciona un artista.")
            return
        try:
            self.repo.update(self.current_id, titulo, precio, artista_id)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_eliminar(self) -> None:
        if self.current_id is None:
            self._show_error("Eliminar", "Selecciona una pintura de la tabla.")
            return
        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar la pintura ID {self.current_id}?",
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
    w = PinturasVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
