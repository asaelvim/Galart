from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import List, Optional, Tuple

from config.conexion import obtener_conexion
from ventanas.Artistas import ArtistasVentana
from modulos.PdfUtils import guardar_pdf, vista_previa_pdf, html_tabla_widget

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
    QDialog,
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


class PinturasRepo:
    TABLE = "Pinturas"

    def fetch_all(self) -> List[Tuple[int, str, float, int, str, Optional[int], str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT p.id_pintura, p.titulo, p.precio, p.id_artista, "
                "ISNULL(a.nombre, '') as artista_nombre, "
                "p.id_tecnica, ISNULL(t.nombre, '') as tecnica_nombre "
                "FROM Pinturas p "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "LEFT JOIN Tecnicas t ON p.id_tecnica = t.id_tecnica "
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
                id_tecnica = int(r[5]) if r[5] is not None else None
                tecnica_nombre = str(r[6]) if r[6] is not None else ""
                result.append((pid, titulo, precio, id_artista, artista_nombre, id_tecnica, tecnica_nombre))
            return result

    def fetch_by_id(self, pintura_id: int) -> List[Tuple[int, str, float, int, str, Optional[int], str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT p.id_pintura, p.titulo, p.precio, p.id_artista, "
                "ISNULL(a.nombre, '') as artista_nombre, "
                "p.id_tecnica, ISNULL(t.nombre, '') as tecnica_nombre "
                "FROM Pinturas p "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "LEFT JOIN Tecnicas t ON p.id_tecnica = t.id_tecnica "
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
                id_tecnica = int(r[5]) if r[5] is not None else None
                tecnica_nombre = str(r[6]) if r[6] is not None else ""
                result.append((pid, titulo, precio, id_artista, artista_nombre, id_tecnica, tecnica_nombre))
            return result

    def search_by_title(self, titulo: str) -> List[Tuple[int, str, float, int, str, Optional[int], str]]:
        with db() as conn:
            cur = conn.cursor()
            like = f"%{titulo}%"
            _exec(
                cur,
                "SELECT p.id_pintura, p.titulo, p.precio, p.id_artista, "
                "ISNULL(a.nombre, '') as artista_nombre, "
                "p.id_tecnica, ISNULL(t.nombre, '') as tecnica_nombre "
                "FROM Pinturas p "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "LEFT JOIN Tecnicas t ON p.id_tecnica = t.id_tecnica "
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
                id_tecnica = int(r[5]) if r[5] is not None else None
                tecnica_nombre = str(r[6]) if r[6] is not None else ""
                result.append((pid, titulo_val, precio, id_artista, artista_nombre, id_tecnica, tecnica_nombre))
            return result

    def insert(self, titulo: str, precio: float, id_artista: int, id_tecnica: Optional[int] = None) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica) VALUES (?, ?, ?, ?)",
                (titulo, precio, id_artista, id_tecnica),
            )
            conn.commit()

    def update(self, pintura_id: int, titulo: str, precio: float, id_artista: int, id_tecnica: Optional[int] = None) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Pinturas SET titulo = ?, precio = ?, id_artista = ?, id_tecnica = ? "
                "WHERE id_pintura = ?",
                (titulo, precio, id_artista, id_tecnica, pintura_id),
            )
            conn.commit()

    def delete(self, pintura_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM Pinturas WHERE id_pintura = ?", (pintura_id,))
            conn.commit()


class TecnicasRepo:
    TABLE = "Tecnicas"

    def fetch_all(self) -> List[Tuple[int, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "SELECT id_tecnica, nombre FROM Tecnicas ORDER BY nombre")
            rows = cur.fetchall()
            result = []
            for r in rows:
                result.append((int(r[0]), str(r[1]) if r[1] is not None else ""))
            return result

    def insert(self, nombre: str) -> int:
        with db() as conn:
            cur = conn.cursor()

            _exec(cur, "SELECT TOP 1 id_tecnica FROM Tecnicas WHERE nombre = ?", (nombre,))
            existente = cur.fetchone()
            if existente is not None:
                raise RuntimeError("Ya existe una técnica con ese nombre.")

            _exec(cur, "INSERT INTO Tecnicas (nombre) VALUES (?)", (nombre,))
            conn.commit()

            _exec(
                cur,
                "SELECT TOP 1 id_tecnica FROM Tecnicas WHERE nombre = ? ORDER BY id_tecnica DESC",
                (nombre,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("No se pudo recuperar la técnica guardada.")
            return int(row[0])

    def delete(self, tecnica_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()

            _exec(
                cur,
                "SELECT COUNT(*) FROM Pinturas WHERE id_tecnica = ?",
                (tecnica_id,),
            )
            usados = cur.fetchone()
            cantidad = int(usados[0]) if usados else 0

            if cantidad > 0:
                raise RuntimeError("No se puede eliminar la técnica porque está asignada a una o más pinturas.")

            _exec(cur, "DELETE FROM Tecnicas WHERE id_tecnica = ?", (tecnica_id,))
            conn.commit()


class TecnicasVentana(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Administrar técnicas")
        self.setModal(True)
        self.setMinimumSize(640, 500)

        self.repo = TecnicasRepo()
        self.current_id: Optional[int] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Administrar técnicas")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        layout.addWidget(title)

        row_nombre = QHBoxLayout()
        row_nombre.setSpacing(12)
        row_nombre.addStretch(1)

        lbl_nombre = QLabel("Nombre:")
        lbl_nombre.setObjectName("MutedLabel")

        self.txtNombre = QLineEdit()
        self.txtNombre.setPlaceholderText("Escribe la técnica")
        self.txtNombre.setFixedWidth(320)
        self.txtNombre.setFixedHeight(34)

        validator_nombre = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
        )
        self.txtNombre.setValidator(validator_nombre)

        row_nombre.addWidget(lbl_nombre)
        row_nombre.addWidget(self.txtNombre)
        row_nombre.addStretch(1)
        layout.addLayout(row_nombre)

        row_botones = QHBoxLayout()
        row_botones.setSpacing(12)
        row_botones.addStretch(1)

        self.btnGuardar = QPushButton("Guardar")
        self.btnEliminar = QPushButton("Eliminar")
        self.btnLimpiar = QPushButton("Limpiar")

        for b in (self.btnGuardar, self.btnEliminar, self.btnLimpiar):
            b.setObjectName("Btn")
            b.setFixedWidth(110)
            b.setFixedHeight(34)

        self.btnGuardar.clicked.connect(self.on_guardar)
        self.btnEliminar.clicked.connect(self.on_eliminar)
        self.btnLimpiar.clicked.connect(self.clear_form)

        row_botones.addWidget(self.btnGuardar)
        row_botones.addWidget(self.btnEliminar)
        row_botones.addWidget(self.btnLimpiar)
        row_botones.addStretch(1)
        layout.addLayout(row_botones)

        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        tf = QVBoxLayout(table_frame)
        tf.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, 2)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_row_selected)

        tf.addWidget(self.table)
        layout.addWidget(table_frame)

        row_salir = QHBoxLayout()
        row_salir.addStretch(1)
        self.btnCerrar = QPushButton("Cerrar")
        self.btnCerrar.setObjectName("Btn")
        self.btnCerrar.setFixedWidth(120)
        self.btnCerrar.setFixedHeight(34)
        self.btnCerrar.clicked.connect(self.accept)
        row_salir.addWidget(self.btnCerrar)
        row_salir.addStretch(1)
        layout.addLayout(row_salir)

        self.setStyleSheet(f"""
            QDialog {{
                background: {BG};
                color: {TEXT};
                font-family: "Segoe UI";
                font-size: 10pt;
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
        """)

        self.load_all()

    def clear_form(self) -> None:
        self.current_id = None
        self.txtNombre.clear()
        self.table.clearSelection()

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str]]) -> None:
        self.table.setRowCount(0)
        for r, (tid, nombre) in enumerate(rows):
            self.table.insertRow(r)
            it_id = QTableWidgetItem(str(tid))
            it_nombre = QTableWidgetItem(nombre)
            for it in (it_id, it_nombre):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_nombre)

    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        self.current_id = int(self.table.item(row, 0).text())
        self.txtNombre.setText(self.table.item(row, 1).text())

    def on_guardar(self) -> None:
        nombre = self.txtNombre.text().strip()
        if not nombre:
            QMessageBox.critical(self, "Validación", "El nombre de la técnica es obligatorio.")
            return
        try:
            tecnica_id = self.repo.insert(nombre)
            self.load_all()
            self.clear_form()

            for i in range(self.table.rowCount()):
                if self.table.item(i, 0).text() == str(tecnica_id):
                    self.table.selectRow(i)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))

    def on_eliminar(self) -> None:
        if self.current_id is None:
            QMessageBox.critical(self, "Eliminar", "Selecciona una técnica de la tabla.")
            return

        r = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar la técnica ID {self.current_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return

        try:
            self.repo.delete(self.current_id)
            self.load_all()
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))


class PinturasVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.setWindowTitle("Gestión de Pinturas")
        self.setMinimumSize(940, 660)

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

        title = QLabel("Gestión de Pinturas")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        row_titulo = QHBoxLayout()
        row_titulo.setSpacing(12)
        row_titulo.addStretch(1)
        lbl_titulo = QLabel("Titulo:")
        lbl_titulo.setObjectName("MutedLabel")
        self.txtTitulo = QLineEdit()
        self.txtTitulo.setObjectName("txtTitulo")
        self.txtTitulo.setFixedWidth(460)
        validator_titulo = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.,\-']+$")
        )
        self.txtTitulo.setValidator(validator_titulo)
        row_titulo.addWidget(lbl_titulo)
        row_titulo.addWidget(self.txtTitulo)
        row_titulo.addStretch(1)
        card_layout.addLayout(row_titulo)

        row_precio = QHBoxLayout()
        row_precio.setSpacing(12)
        row_precio.addStretch(1)
        lbl_precio = QLabel("Precio:")
        lbl_precio.setObjectName("MutedLabel")
        self.txtPrecio = QLineEdit()
        self.txtPrecio.setObjectName("txtPrecio")
        self.txtPrecio.setFixedWidth(460)
        row_precio.addWidget(lbl_precio)
        row_precio.addWidget(self.txtPrecio)
        row_precio.addStretch(1)
        card_layout.addLayout(row_precio)

        row_artista = QHBoxLayout()
        row_artista.setSpacing(12)
        row_artista.addStretch(1)

        lbl_artista = QLabel("Artista:")
        lbl_artista.setObjectName("MutedLabel")

        self.cboArtista = QComboBox()
        self.cboArtista.setObjectName("Combo")
        self.cboArtista.setFixedWidth(360)

        self.btnAdministrarArtistas = self._button(
            "Administrar artistas", self.abrir_artistas, wide=True
        )
        self.btnAdministrarArtistas.setFixedWidth(180)

        row_artista.addWidget(lbl_artista)
        row_artista.addWidget(self.cboArtista)
        row_artista.addWidget(self.btnAdministrarArtistas)
        row_artista.addStretch(1)
        card_layout.addLayout(row_artista)

        row_tecnica = QHBoxLayout()
        row_tecnica.setSpacing(12)
        row_tecnica.addStretch(1)

        lbl_tecnica = QLabel("Técnica:")
        lbl_tecnica.setObjectName("MutedLabel")

        self.cboTecnica = QComboBox()
        self.cboTecnica.setObjectName("Combo")
        self.cboTecnica.setFixedWidth(360)

        self.btnAdministrarTecnicas = self._button(
            "Administrar técnicas", self.abrir_tecnicas, wide=True
        )
        self.btnAdministrarTecnicas.setFixedWidth(180)

        row_tecnica.addWidget(lbl_tecnica)
        row_tecnica.addWidget(self.cboTecnica)
        row_tecnica.addWidget(self.btnAdministrarTecnicas)
        row_tecnica.addStretch(1)

        card_layout.addLayout(row_tecnica)

        row_acciones = QHBoxLayout()
        row_acciones.setSpacing(12)
        row_acciones.addStretch(1)

        self.btnAgregar = self._button("Agregar", self.on_agregar)
        self.btnEditar = self._button("Editar", self.on_editar)
        self.btnEliminar = self._button("Eliminar", self.on_eliminar)

        row_acciones.addWidget(self.btnAgregar)
        row_acciones.addWidget(self.btnEditar)
        row_acciones.addWidget(self.btnEliminar)

        row_acciones.addStretch(1)
        card_layout.addLayout(row_acciones)

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

        validator_titulo = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.,\-']+$")
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

        row_mostrar = QHBoxLayout()
        row_mostrar.addStretch(1)
        self.btnMostrarTodos = self._button("Mostrar todos", self.on_mostrar_todos, wide=True)
        row_mostrar.addWidget(self.btnMostrarTodos)
        row_mostrar.addStretch(1)
        card_layout.addLayout(row_mostrar)

        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        tf = QVBoxLayout(table_frame)
        tf.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(["ID", "Titulo", "Precio", "Artista", "Técnica"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.itemSelectionChanged.connect(self.on_row_selected)

        tf.addWidget(self.table)
        card_layout.addWidget(table_frame)

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
        self.setStyleSheet(self._stylesheet())

        self._load_artistas_combo()
        self._load_tecnicas_combo()
        self.load_all()

    def closeEvent(self, event):
        if self.ventana_principal is not None:
            self.ventana_principal.show()
        event.accept()

    def exportar_pdf(self) -> None:
        guardar_pdf(self, "Gestión de Pinturas", "pinturas.pdf",
                    html_tabla_widget(self.table, "LISTADO DE PINTURAS"))

    def vista_previa_pdf(self) -> None:
        vista_previa_pdf(self, "Gestión de Pinturas", "pinturas.pdf",
                         html_tabla_widget(self.table, "LISTADO DE PINTURAS"))

    def showEvent(self, event):
        super().showEvent(event)
        self.actualizar_selects()

    def actualizar_selects(self) -> None:
        artista_actual = self.cboArtista.currentData()
        tecnica_actual = self.cboTecnica.currentData()

        self._load_artistas_combo()
        idx_artista = self.cboArtista.findData(artista_actual)
        if idx_artista >= 0:
            self.cboArtista.setCurrentIndex(idx_artista)
        elif self.cboArtista.count() > 0:
            self.cboArtista.setCurrentIndex(0)

        self._load_tecnicas_combo()
        idx_tecnica = self.cboTecnica.findData(tecnica_actual)
        if idx_tecnica >= 0:
            self.cboTecnica.setCurrentIndex(idx_tecnica)
        elif self.cboTecnica.count() > 0:
            self.cboTecnica.setCurrentIndex(0)

    def _button(self, text: str, handler, wide: bool = False) -> QPushButton:
        b = QPushButton(text)
        b.setObjectName("Btn")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(handler)
        b.setFixedWidth(170 if wide else 110)
        b.setFixedHeight(34)
        return b

    def _load_artistas_combo(self) -> None:
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

    def _load_tecnicas_combo(self) -> None:
        self.cboTecnica.blockSignals(True)
        self.cboTecnica.clear()
        self.cboTecnica.addItem("-- Seleccionar técnica --", None)
        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(cur, "SELECT id_tecnica, nombre FROM Tecnicas ORDER BY nombre")
                rows = cur.fetchall()
                for r in rows:
                    self.cboTecnica.addItem(str(r[1]), int(r[0]))
        except Exception:
            pass
        self.cboTecnica.setCurrentIndex(0)
        self.cboTecnica.blockSignals(False)

    def abrir_tecnicas(self) -> None:
        dlg = TecnicasVentana(self)
        dlg.exec()
        self.actualizar_selects()

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
        self.cboTecnica.setCurrentIndex(0)
        self.table.clearSelection()

    def _get_form_values(self) -> Tuple[str, str, Optional[int], Optional[int]]:
        titulo = self.txtTitulo.text().strip()
        precio = self.txtPrecio.text().strip()
        artista_id = self.cboArtista.currentData()
        tecnica_id = self.cboTecnica.currentData()
        return titulo, precio, artista_id, tecnica_id

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, float, int, str, Optional[int], str]]) -> None:
        self.table.setRowCount(0)
        for r, (pid, titulo, precio, id_artista, artista_nombre, id_tecnica, tecnica_nombre) in enumerate(rows):
            self.table.insertRow(r)
            it_id = QTableWidgetItem(str(pid))
            it_id.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            it_titulo = QTableWidgetItem(titulo)
            it_precio = QTableWidgetItem(f"{precio:.2f}")
            it_artista = QTableWidgetItem(artista_nombre)
            it_tecnica = QTableWidgetItem(tecnica_nombre)
            for it in (it_id, it_titulo, it_precio, it_artista, it_tecnica):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_titulo)
            self.table.setItem(r, 2, it_precio)
            self.table.setItem(r, 3, it_artista)
            self.table.setItem(r, 4, it_tecnica)

    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        pid = int(self.table.item(row, 0).text())
        try:
            rows = self.repo.fetch_by_id(pid)
            if rows:
                _, titulo, precio, id_artista, _, id_tecnica, _ = rows[0]
                self.current_id = pid
                self.txtTitulo.setText(titulo)
                self.txtPrecio.setText(f"{precio:.2f}")
                index = self.cboArtista.findData(id_artista)
                if index >= 0:
                    self.cboArtista.setCurrentIndex(index)
                index_t = self.cboTecnica.findData(id_tecnica)
                if index_t >= 0:
                    self.cboTecnica.setCurrentIndex(index_t)
                else:
                    self.cboTecnica.setCurrentIndex(0)
        except Exception:
            self.current_id = pid
            self.txtTitulo.setText(self.table.item(row, 1).text())
            self.txtPrecio.setText(self.table.item(row, 2).text())
            artista_text = self.table.item(row, 3).text()
            idx = self.cboArtista.findText(artista_text)
            if idx >= 0:
                self.cboArtista.setCurrentIndex(idx)
            tecnica_text = self.table.item(row, 4).text()
            idx_t = self.cboTecnica.findText(tecnica_text)
            if idx_t >= 0:
                self.cboTecnica.setCurrentIndex(idx_t)
            else:
                self.cboTecnica.setCurrentIndex(0)

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
                _, titulo, precio, id_artista, _, id_tecnica, _ = rows[0]
                self.populate_table(rows)
                self.current_id = pid
                self.txtTitulo.setText(titulo)
                self.txtPrecio.setText(f"{precio:.2f}")
                index = self.cboArtista.findData(id_artista)
                if index >= 0:
                    self.cboArtista.setCurrentIndex(index)
                index_t = self.cboTecnica.findData(id_tecnica)
                if index_t >= 0:
                    self.cboTecnica.setCurrentIndex(index_t)
                else:
                    self.cboTecnica.setCurrentIndex(0)
            else:
                self.populate_table([])
                self.clear_form()
                QMessageBox.information(self, "Resultado", "No se encontró ninguna pintura con ese ID.")
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_agregar(self) -> None:
        titulo, precio_str, artista_id, tecnica_id = self._get_form_values()
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
            self.repo.insert(titulo, precio, artista_id, tecnica_id)
            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_editar(self) -> None:
        if self.current_id is None:
            self._show_error("Editar", "Selecciona una pintura de la tabla.")
            return
        titulo, precio_str, artista_id, tecnica_id = self._get_form_values()
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
            self.repo.update(self.current_id, titulo, precio, artista_id, tecnica_id)
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

    def abrir_artistas(self) -> None:
        self.ventana_artistas = ArtistasVentana(self)
        self.hide()
        self.ventana_artistas.show()
        self.ventana_artistas.raise_()
        self.ventana_artistas.activateWindow()

    def abrir_tecnicas(self) -> None:
        dlg = TecnicasVentana(self)
        dlg.exec()
        self.actualizar_selects()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = PinturasVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
