from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import List, Optional, Tuple

from config.conexion import obtener_conexion
from ventanas.Pinturas import PinturasVentana
from ventanas.Artistas import ArtistasVentana

from PySide6.QtCore import Qt, QDate, QTime, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
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
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
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
    cur.execute(sql, params)


def _fmt_date(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _fmt_time(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M:%S")
    return str(value)


def _to_qdate(value: str) -> QDate:
    qd = QDate.fromString(value, "yyyy-MM-dd")
    return qd if qd.isValid() else QDate.currentDate()


def _to_qtime(value: str) -> QTime:
    qt = QTime.fromString(value, "HH:mm:ss")
    if not qt.isValid():
        qt = QTime.fromString(value, "HH:mm")
    return qt if qt.isValid() else QTime.currentTime()


class ExhibicionesRepo:
    TABLE = "Exhibicion"

    def fetch_all(self) -> List[Tuple[int, str, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_exhibicion, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin "
                "FROM Exhibicion ORDER BY id_exhibicion",
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                eid = int(r[0])
                nombre = str(r[1]) if r[1] is not None else ""
                fecha_inicio = _fmt_date(r[2])
                fecha_fin = _fmt_date(r[3])
                hora_inicio = _fmt_time(r[4])
                hora_fin = _fmt_time(r[5])
                result.append((eid, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin))
            return result

    def fetch_by_id(self, exhibicion_id: int) -> List[Tuple[int, str, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT id_exhibicion, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin "
                "FROM Exhibicion WHERE id_exhibicion = ?",
                (exhibicion_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                eid = int(r[0])
                nombre = str(r[1]) if r[1] is not None else ""
                fecha_inicio = _fmt_date(r[2])
                fecha_fin = _fmt_date(r[3])
                hora_inicio = _fmt_time(r[4])
                hora_fin = _fmt_time(r[5])
                result.append((eid, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin))
            return result

    def search_by_name(self, nombre: str) -> List[Tuple[int, str, str, str, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            like = f"%{nombre}%"
            _exec(
                cur,
                "SELECT id_exhibicion, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin "
                "FROM Exhibicion WHERE nombre LIKE ? ORDER BY id_exhibicion",
                (like,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                eid = int(r[0])
                nom = str(r[1]) if r[1] is not None else ""
                fecha_inicio = _fmt_date(r[2])
                fecha_fin = _fmt_date(r[3])
                hora_inicio = _fmt_time(r[4])
                hora_fin = _fmt_time(r[5])
                result.append((eid, nom, fecha_inicio, fecha_fin, hora_inicio, hora_fin))
            return result

    def search(self, modo: str, texto: str) -> List[Tuple[int, str, str, str, str, str]]:
        like = f"%{texto}%"
        with db() as conn:
            cur = conn.cursor()

            if modo == "exhibicion":
                sql = (
                    "SELECT DISTINCT e.id_exhibicion, e.nombre, e.fecha_inicio, e.fecha_fin, e.hora_inicio, e.hora_fin "
                    "FROM Exhibicion e "
                    "WHERE e.nombre LIKE ? "
                    "ORDER BY e.id_exhibicion"
                )
                params = (like,)
            elif modo == "pintura":
                sql = (
                    "SELECT DISTINCT e.id_exhibicion, e.nombre, e.fecha_inicio, e.fecha_fin, e.hora_inicio, e.hora_fin "
                    "FROM Exhibicion e "
                    "INNER JOIN DetalleExhibicion d ON e.id_exhibicion = d.id_exhibicion "
                    "INNER JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                    "WHERE p.titulo LIKE ? "
                    "ORDER BY e.id_exhibicion"
                )
                params = (like,)
            else:  # artista
                sql = (
                    "SELECT DISTINCT e.id_exhibicion, e.nombre, e.fecha_inicio, e.fecha_fin, e.hora_inicio, e.hora_fin "
                    "FROM Exhibicion e "
                    "INNER JOIN DetalleExhibicion d ON e.id_exhibicion = d.id_exhibicion "
                    "INNER JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                    "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                    "WHERE COALESCE(a.nombre, '') LIKE ? "
                    "ORDER BY e.id_exhibicion"
                )
                params = (like,)

            _exec(cur, sql, params)
            rows = cur.fetchall()
            result = []
            for r in rows:
                eid = int(r[0])
                nombre = str(r[1]) if r[1] is not None else ""
                fecha_inicio = _fmt_date(r[2])
                fecha_fin = _fmt_date(r[3])
                hora_inicio = _fmt_time(r[4])
                hora_fin = _fmt_time(r[5])
                result.append((eid, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin))
            return result

    def insert(
        self,
        nombre: str,
        fecha_inicio: str,
        fecha_fin: Optional[str],
        hora_inicio: str,
        hora_fin: str,
    ) -> int:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO Exhibicion (nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin) "
                "VALUES (?, ?, ?, ?, ?)",
                (nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin),
            )
            new_id = cur.lastrowid
            conn.commit()
            return new_id

    def update(
        self,
        exhibicion_id: int,
        nombre: str,
        fecha_inicio: str,
        fecha_fin: Optional[str],
        hora_inicio: str,
        hora_fin: str,
    ) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "UPDATE Exhibicion SET nombre = ?, fecha_inicio = ?, fecha_fin = ?, hora_inicio = ?, hora_fin = ? "
                "WHERE id_exhibicion = ?",
                (nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin, exhibicion_id),
            )
            conn.commit()

    def delete(self, exhibicion_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleExhibicion WHERE id_exhibicion = ?", (exhibicion_id,))
            _exec(cur, "DELETE FROM Exhibicion WHERE id_exhibicion = ?", (exhibicion_id,))
            conn.commit()


class DetalleExhibicionRepo:
    def fetch_by_exhibicion(self, exhibicion_id: int) -> List[Tuple[int, int, str, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "SELECT d.id_detalle, d.id_pintura, COALESCE(p.titulo, '') AS titulo, "
                "COALESCE(a.nombre, '') AS artista "
                "FROM DetalleExhibicion d "
                "LEFT JOIN Pinturas p ON d.id_pintura = p.id_pintura "
                "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                "WHERE d.id_exhibicion = ? "
                "ORDER BY d.id_detalle",
                (exhibicion_id,),
            )
            rows = cur.fetchall()
            result = []
            for r in rows:
                id_detalle = int(r[0])
                id_pintura = int(r[1]) if r[1] is not None else 0
                titulo = str(r[2]) if r[2] is not None else ""
                artista = str(r[3]) if r[3] is not None else ""
                result.append((id_detalle, id_pintura, titulo, artista))
            return result

    def insert(self, id_exhibicion: int, id_pintura: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(
                cur,
                "INSERT INTO DetalleExhibicion (id_exhibicion, id_pintura) VALUES (?, ?)",
                (id_exhibicion, id_pintura),
            )
            conn.commit()

    def delete_by_exhibicion(self, exhibicion_id: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleExhibicion WHERE id_exhibicion = ?", (exhibicion_id,))
            conn.commit()

    def delete(self, id_detalle: int) -> None:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "DELETE FROM DetalleExhibicion WHERE id_detalle = ?", (id_detalle,))
            conn.commit()


class ArtistasRepo:
    def fetch_all_for_combo(self) -> List[Tuple[int, str]]:
        with db() as conn:
            cur = conn.cursor()
            _exec(cur, "SELECT id_artista, COALESCE(nombre, '') FROM Artistas ORDER BY nombre")
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]) if r[1] is not None else "") for r in rows]


class PinturasRepo:
    def fetch_all_for_combo(self, id_artista: Optional[int] = None) -> List[Tuple[int, str]]:
        with db() as conn:
            cur = conn.cursor()
            if id_artista is None:
                _exec(
                    cur,
                    "SELECT p.id_pintura, COALESCE(p.titulo, '') "
                    "FROM Pinturas p "
                    "ORDER BY p.titulo",
                )
            else:
                _exec(
                    cur,
                    "SELECT p.id_pintura, COALESCE(p.titulo, '') "
                    "FROM Pinturas p "
                    "WHERE p.id_artista = ? "
                    "ORDER BY p.titulo",
                    (id_artista,),
                )
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]) if r[1] is not None else "") for r in rows]


# =========================
# UI Principal para EXHIBICIONES
# =========================
class ExhibicionesVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.ventana_pinturas = None
        self.ventana_artistas = None

        self.setWindowTitle("Gestión de Exhibiciones")
        self.setMinimumSize(1500, 780)

        self.repo = ExhibicionesRepo()
        self.detalle_repo = DetalleExhibicionRepo()
        self.artistas_repo = ArtistasRepo()
        self.pinturas_repo = PinturasRepo()
        self.current_id: Optional[int] = None

        # (id_pintura, titulo)
        self._detail_lines: List[Tuple[int, str]] = []

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

        title = QLabel("Gestión de Exhibiciones")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(QFont("Segoe UI", 12))
        title.setObjectName("Title")
        card_layout.addWidget(title)

        # === Nombre ===
        row_nombre = QHBoxLayout()
        row_nombre.setSpacing(12)
        row_nombre.addStretch(1)
        lbl_nombre = QLabel("Nombre:")
        lbl_nombre.setObjectName("MutedLabel")
        self.txtNombre = QLineEdit()
        self.txtNombre.setObjectName("txtNombre")
        self.txtNombre.setFixedWidth(460)
        row_nombre.addWidget(lbl_nombre)
        row_nombre.addWidget(self.txtNombre)
        row_nombre.addStretch(1)
        card_layout.addLayout(row_nombre)

        # === Fechas ===
        row_fechas = QHBoxLayout()
        row_fechas.setSpacing(12)
        row_fechas.addStretch(1)

        lbl_inicio = QLabel("Fecha inicio:")
        lbl_inicio.setObjectName("MutedLabel")
        self.dateInicio = QDateEdit()
        self.dateInicio.setObjectName("dateInicio")
        self.dateInicio.setFixedWidth(190)
        self.dateInicio.setCalendarPopup(True)
        self.dateInicio.setDisplayFormat("yyyy-MM-dd")
        self.dateInicio.setDate(QDate.currentDate())

        lbl_fin = QLabel("Fecha fin:")
        lbl_fin.setObjectName("MutedLabel")
        self.dateFin = QDateEdit()
        self.dateFin.setObjectName("dateFin")
        self.dateFin.setFixedWidth(190)
        self.dateFin.setCalendarPopup(True)
        self.dateFin.setDisplayFormat("yyyy-MM-dd")
        self.dateFin.setDate(QDate.currentDate())

        row_fechas.addWidget(lbl_inicio)
        row_fechas.addWidget(self.dateInicio)
        row_fechas.addSpacing(20)
        row_fechas.addWidget(lbl_fin)
        row_fechas.addWidget(self.dateFin)
        row_fechas.addStretch(1)
        card_layout.addLayout(row_fechas)

        # === Horas ===
        row_horas = QHBoxLayout()
        row_horas.setSpacing(12)
        row_horas.addStretch(1)

        lbl_hora_inicio = QLabel("Hora inicio:")
        lbl_hora_inicio.setObjectName("MutedLabel")
        self.timeInicio = QTimeEdit()
        self.timeInicio.setObjectName("timeInicio")
        self.timeInicio.setFixedWidth(150)
        self.timeInicio.setDisplayFormat("HH:mm:ss")
        self.timeInicio.setTime(QTime.currentTime())

        lbl_hora_fin = QLabel("Hora fin:")
        lbl_hora_fin.setObjectName("MutedLabel")
        self.timeFin = QTimeEdit()
        self.timeFin.setObjectName("timeFin")
        self.timeFin.setFixedWidth(150)
        self.timeFin.setDisplayFormat("HH:mm:ss")
        self.timeFin.setTime(QTime.currentTime())

        row_horas.addWidget(lbl_hora_inicio)
        row_horas.addWidget(self.timeInicio)
        row_horas.addSpacing(20)
        row_horas.addWidget(lbl_hora_fin)
        row_horas.addWidget(self.timeFin)
        row_horas.addStretch(1)
        card_layout.addLayout(row_horas)

        # === Botones CRUD ===
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

        # === Separador ===
        sep1 = QFrame()
        sep1.setObjectName("Separator")
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        card_layout.addWidget(sep1)

        # === Filtros de artista / pinturas ===
        row_filtros = QHBoxLayout()
        row_filtros.setSpacing(12)
        row_filtros.addStretch(1)

        lbl_artista = QLabel("Artista:")
        lbl_artista.setObjectName("MutedLabel")
        self.cmbArtista = QComboBox()
        self.cmbArtista.setObjectName("Combo")
        self.cmbArtista.setFixedWidth(260)
        self.cmbArtista.currentIndexChanged.connect(self.on_artista_changed)

        self.btnAdministrarArtistas = self._button(
            "Administrar artistas", self.abrir_artistas, wide=True
        )
        self.btnAdministrarArtistas.setFixedWidth(180)

        lbl_pintura = QLabel("Pintura:")
        lbl_pintura.setObjectName("MutedLabel")
        self.cmbPintura = QComboBox()
        self.cmbPintura.setObjectName("Combo")
        self.cmbPintura.setFixedWidth(380)

        self.btnAdministrarPinturas = self._button(
            "Administrar pinturas", self.abrir_pinturas, wide=True
        )
        self.btnAdministrarPinturas.setFixedWidth(180)

        self.btnAgregarPintura = self._button("Agregar pintura", self.on_add_painting, wide=True)

        row_filtros.addWidget(lbl_artista)
        row_filtros.addWidget(self.cmbArtista)
        row_filtros.addWidget(self.btnAdministrarArtistas)
        row_filtros.addSpacing(16)
        row_filtros.addWidget(lbl_pintura)
        row_filtros.addWidget(self.cmbPintura)
        row_filtros.addWidget(self.btnAdministrarPinturas)
        row_filtros.addWidget(self.btnAgregarPintura)
        row_filtros.addStretch(1)
        card_layout.addLayout(row_filtros)

        detail_frame = QFrame()
        detail_frame.setObjectName("TableFrame")
        df = QVBoxLayout(detail_frame)
        df.setContentsMargins(10, 10, 10, 10)

        self.detail_table = QTableWidget(0, 3)
        self.detail_table.setObjectName("Table")
        self.detail_table.setHorizontalHeaderLabels(["Pintura", "Artista", ""])
        self.detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.verticalHeader().setVisible(False)
        detail_header = self.detail_table.horizontalHeader()
        detail_header.setSectionResizeMode(0, QHeaderView.Stretch)
        detail_header.setSectionResizeMode(1, QHeaderView.Stretch)
        detail_header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.detail_table.setColumnWidth(2, 60)
        self.detail_table.setMaximumHeight(220)

        df.addWidget(self.detail_table)
        card_layout.addWidget(detail_frame)

        # === Búsqueda ===
        row_buscar = QHBoxLayout()
        row_buscar.setSpacing(12)
        row_buscar.addStretch(1)

        lbl_buscar = QLabel("Buscar por:")
        lbl_buscar.setObjectName("MutedLabel")
        self.cmbBuscarPor = QComboBox()
        self.cmbBuscarPor.setObjectName("Combo")
        self.cmbBuscarPor.setFixedWidth(170)
        self.cmbBuscarPor.addItem("Exhibición", "exhibicion")
        self.cmbBuscarPor.addItem("Pintura", "pintura")
        self.cmbBuscarPor.addItem("Artista", "artista")

        lbl_texto = QLabel("Texto:")
        lbl_texto.setObjectName("MutedLabel")
        self.txtBuscar = QLineEdit()
        self.txtBuscar.setObjectName("SearchBox")
        self.txtBuscar.setFixedWidth(300)

        self.btnBuscar = self._button("Buscar", self.on_buscar)

        row_buscar.addWidget(lbl_buscar)
        row_buscar.addWidget(self.cmbBuscarPor)
        row_buscar.addWidget(lbl_texto)
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

        # === Validadores de campos ===
        validator_letras = QRegularExpressionValidator(
            QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
        )
        validator_numeros = QRegularExpressionValidator(
            QRegularExpression(r"^[0-9]+$")
        )
        self.txtNombre.setValidator(validator_letras)
        self.txtBuscar.setValidator(validator_letras)
        self.txtBuscarID.setValidator(validator_numeros)

        row_mostrar = QHBoxLayout()
        row_mostrar.addStretch(1)
        self.btnMostrarTodos = self._button("Mostrar todos", self.on_mostrar_todos, wide=True)
        row_mostrar.addWidget(self.btnMostrarTodos)
        row_mostrar.addStretch(1)
        card_layout.addLayout(row_mostrar)

        # === Tabla principal ===
        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        tf = QVBoxLayout(table_frame)
        tf.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, 6)
        self.table.setObjectName("Table")
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Fecha inicio", "Fecha fin", "Hora inicio", "Hora fin"]
        )
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
        self.btnSalir = self._button("Salir", self.close, wide=True)
        row_bottom.addWidget(self.btnSalir)
        row_bottom.addStretch(1)
        card_layout.addLayout(row_bottom)

        main.addWidget(card)
        self.setStyleSheet(self._stylesheet())

        self._load_artistas_combo()
        self._load_pinturas_combo(None)
        self.load_all()

    def closeEvent(self, event):
        if self.ventana_principal is not None:
            self.ventana_principal.show()
        event.accept()

    def actualizar_selects(self) -> None:
        artista_actual = self.cmbArtista.currentData()

        pintura_actual = None
        data_pintura = self.cmbPintura.currentData()
        if data_pintura is not None:
            pintura_actual = data_pintura[0]

        self._load_artistas_combo()

        idx_artista = self.cmbArtista.findData(artista_actual)
        if idx_artista >= 0:
            self.cmbArtista.setCurrentIndex(idx_artista)
        elif self.cmbArtista.count() > 0:
            self.cmbArtista.setCurrentIndex(0)

        id_artista = self.cmbArtista.currentData()
        self._load_pinturas_combo(id_artista if id_artista is not None else None)

        if pintura_actual is not None:
            for i in range(self.cmbPintura.count()):
                data = self.cmbPintura.itemData(i)
                if data is not None and data[0] == pintura_actual:
                    self.cmbPintura.setCurrentIndex(i)
                    break
        elif self.cmbPintura.count() > 0:
            self.cmbPintura.setCurrentIndex(0)

    def showEvent(self, event):
        super().showEvent(event)
        self.actualizar_selects()

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
        QDateEdit, QTimeEdit {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 6px 10px;
            color: {TEXT};
        }}
        QDateEdit:focus, QTimeEdit:focus {{
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

    def _load_artistas_combo(self) -> None:
        self.cmbArtista.blockSignals(True)
        self.cmbArtista.clear()
        self.cmbArtista.addItem("Cualquier Artista", None)

        try:
            artistas = self.artistas_repo.fetch_all_for_combo()
            for id_artista, nombre in artistas:
                self.cmbArtista.addItem(nombre, id_artista)
        except Exception as e:
            self._show_error("Error BD", str(e))

        self.cmbArtista.setCurrentIndex(0)
        self.cmbArtista.blockSignals(False)

    def _load_pinturas_combo(self, id_artista: Optional[int] = None) -> None:
        self.cmbPintura.clear()
        try:
            pinturas = self.pinturas_repo.fetch_all_for_combo(id_artista)
            self.cmbPintura.addItem("-- Seleccionar pintura --", None)
            for id_pintura, titulo in pinturas:
                self.cmbPintura.addItem(titulo, (id_pintura, titulo))
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_artista_changed(self) -> None:
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

    def _get_form_values(self) -> Tuple[str, str, str, str, str]:
        nombre = self.txtNombre.text().strip()
        fecha_inicio = self.dateInicio.date().toString("yyyy-MM-dd")
        fecha_fin = self.dateFin.date().toString("yyyy-MM-dd")
        hora_inicio = self.timeInicio.time().toString("HH:mm:ss")
        hora_fin = self.timeFin.time().toString("HH:mm:ss")
        return nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin

    def _refresh_detail_table(self) -> None:
        self.detail_table.setRowCount(0)
        for idx, (id_pintura, titulo, artista) in enumerate(self._detail_lines):
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)

            it_titulo = QTableWidgetItem(titulo)
            it_titulo.setFlags(it_titulo.flags() & ~Qt.ItemIsEditable)
            it_artista = QTableWidgetItem(artista)
            it_artista.setFlags(it_artista.flags() & ~Qt.ItemIsEditable)

            self.detail_table.setItem(row, 0, it_titulo)
            self.detail_table.setItem(row, 1, it_artista)

            btn_quitar = QPushButton("X")
            btn_quitar.setObjectName("Btn")
            btn_quitar.setCursor(Qt.PointingHandCursor)
            btn_quitar.setFixedSize(30, 26)
            btn_quitar.clicked.connect(lambda checked=False, i=idx: self.on_remove_painting(i))
            self.detail_table.setCellWidget(row, 2, btn_quitar)

    def _set_detail_from_db(self, exhibicion_id: int) -> None:
        self._detail_lines.clear()
        rows = self.detalle_repo.fetch_by_exhibicion(exhibicion_id)
        for _, id_pintura, titulo, artista in rows:
            self._detail_lines.append((id_pintura, titulo, artista))
        self._refresh_detail_table()

    def clear_form(self) -> None:
        self.current_id = None
        self.txtNombre.clear()
        self.dateInicio.setDate(QDate.currentDate())
        self.dateFin.setDate(QDate.currentDate())
        self.timeInicio.setTime(QTime.currentTime())
        self.timeFin.setTime(QTime.currentTime())
        self.cmbArtista.setCurrentIndex(0)
        self._load_pinturas_combo(None)
        self.cmbPintura.setCurrentIndex(0)
        self._detail_lines.clear()
        self._refresh_detail_table()
        self.table.clearSelection()

    def load_all(self) -> None:
        try:
            rows = self.repo.fetch_all()
            self.populate_table(rows)
        except Exception as e:
            self._show_error("Error BD", str(e))

    def populate_table(self, rows: List[Tuple[int, str, str, str, str, str]]) -> None:
        self.table.setRowCount(0)
        for r, (eid, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin) in enumerate(rows):
            self.table.insertRow(r)

            it_id = QTableWidgetItem(str(eid))
            it_id.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            it_nombre = QTableWidgetItem(nombre)
            it_inicio = QTableWidgetItem(fecha_inicio)
            it_fin = QTableWidgetItem(fecha_fin)
            it_h_inicio = QTableWidgetItem(hora_inicio)
            it_h_fin = QTableWidgetItem(hora_fin)

            for it in (it_id, it_nombre, it_inicio, it_fin, it_h_inicio, it_h_fin):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, it_nombre)
            self.table.setItem(r, 2, it_inicio)
            self.table.setItem(r, 3, it_fin)
            self.table.setItem(r, 4, it_h_inicio)
            self.table.setItem(r, 5, it_h_fin)

    def on_row_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return

        row = items[0].row()
        eid = int(self.table.item(row, 0).text())

        try:
            rows = self.repo.fetch_by_id(eid)
            if rows:
                _, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin = rows[0]
                self.current_id = eid
                self.txtNombre.setText(nombre)

                self.dateInicio.setDate(_to_qdate(fecha_inicio) if fecha_inicio else QDate.currentDate())
                self.dateFin.setDate(_to_qdate(fecha_fin) if fecha_fin else QDate.currentDate())
                self.timeInicio.setTime(_to_qtime(hora_inicio) if hora_inicio else QTime.currentTime())
                self.timeFin.setTime(_to_qtime(hora_fin) if hora_fin else QTime.currentTime())

                self._set_detail_from_db(eid)
        except Exception:
            self.current_id = eid
            self.txtNombre.setText(self.table.item(row, 1).text())

            fi = self.table.item(row, 2).text()
            ff = self.table.item(row, 3).text()
            hi = self.table.item(row, 4).text()
            hf = self.table.item(row, 5).text()

            if fi:
                self.dateInicio.setDate(_to_qdate(fi))
            if ff:
                self.dateFin.setDate(_to_qdate(ff))
            if hi:
                self.timeInicio.setTime(_to_qtime(hi))
            if hf:
                self.timeFin.setTime(_to_qtime(hf))

    def on_mostrar_todos(self) -> None:
        self.txtBuscar.clear()
        self.txtBuscarID.clear()
        self.load_all()
        self.clear_form()

    def on_buscar(self) -> None:
        texto = self.txtBuscar.text().strip()
        if not texto:
            self.load_all()
            return

        modo = self.cmbBuscarPor.currentData()
        if modo not in ("exhibicion", "pintura", "artista"):
            modo = "exhibicion"

        try:
            rows = self.repo.search(modo, texto)
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
                self.populate_table(rows)
                _, nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin = rows[0]
                self.current_id = eid
                self.txtNombre.setText(nombre)
                if fecha_inicio:
                    self.dateInicio.setDate(_to_qdate(fecha_inicio))
                if fecha_fin:
                    self.dateFin.setDate(_to_qdate(fecha_fin))
                if hora_inicio:
                    self.timeInicio.setTime(_to_qtime(hora_inicio))
                if hora_fin:
                    self.timeFin.setTime(_to_qtime(hora_fin))
                self._set_detail_from_db(eid)
            else:
                self.populate_table([])
                self.clear_form()
                QMessageBox.information(self, "Resultado", "No se encontró ninguna exhibición con ese ID.")
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_add_painting(self) -> None:
        data = self.cmbPintura.currentData()
        if data is None:
            self._show_error("Validación", "Selecciona una pintura.")
            return

        id_pintura, titulo = data

        if any(pid == id_pintura for pid, _, _ in self._detail_lines):
            self._show_error("Validación", "Esa pintura ya está agregada a la exhibición.")
            return

        artista = ""
        for i in range(self.cmbPintura.count()):
            current = self.cmbPintura.itemData(i)
            if current and current[0] == id_pintura:
                artista = self.cmbPintura.itemText(i)
                break

        if " - " in artista:
            artista = ""

        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(
                    cur,
                    "SELECT COALESCE(a.nombre, '') "
                    "FROM Pinturas p "
                    "LEFT JOIN Artistas a ON p.id_artista = a.id_artista "
                    "WHERE p.id_pintura = ?",
                    (id_pintura,),
                )
                row = cur.fetchone()
                artista = str(row[0]) if row and row[0] is not None else ""
        except Exception:
            artista = ""

        self._detail_lines.append((id_pintura, titulo, artista))
        self._refresh_detail_table()
        self.cmbPintura.setCurrentIndex(0)

    def on_remove_painting(self, index: int) -> None:
        if 0 <= index < len(self._detail_lines):
            self._detail_lines.pop(index)
            self._refresh_detail_table()

    def _validate_form(self) -> Optional[str]:
        nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin = self._get_form_values()

        if not nombre:
            return "El campo Nombre es obligatorio."

        if self.dateFin.date() < self.dateInicio.date():
            return "La fecha fin no puede ser menor que la fecha inicio."

        if self.dateInicio.date() == self.dateFin.date() and self.timeFin.time() < self.timeInicio.time():
            return "La hora fin no puede ser menor que la hora inicio cuando la fecha es la misma."

        if not self._detail_lines:
            return "Agrega al menos una pintura al detalle de exhibición."

        return None

    def on_agregar(self) -> None:
        error = self._validate_form()
        if error:
            self._show_error("Validación", error)
            return

        nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin = self._get_form_values()

        try:
            with db() as conn:
                cur = conn.cursor()

                _exec(
                    cur,
                    "INSERT INTO Exhibicion (nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin),
                )
                new_id = cur.lastrowid

                for id_pintura, _titulo, _artista in self._detail_lines:
                    _exec(
                        cur,
                        "INSERT INTO DetalleExhibicion (id_exhibicion, id_pintura) VALUES (?, ?)",
                        (new_id, id_pintura),
                    )

                conn.commit()

            self.load_all()
            self.clear_form()
        except Exception as e:
            self._show_error("Error BD", str(e))

    def on_editar(self) -> None:
        if self.current_id is None:
            self._show_error("Editar", "Selecciona una exhibición de la tabla.")
            return

        error = self._validate_form()
        if error:
            self._show_error("Validación", error)
            return

        nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin = self._get_form_values()

        try:
            with db() as conn:
                cur = conn.cursor()

                _exec(
                    cur,
                    "UPDATE Exhibicion SET nombre = ?, fecha_inicio = ?, fecha_fin = ?, hora_inicio = ?, hora_fin = ? "
                    "WHERE id_exhibicion = ?",
                    (nombre, fecha_inicio, fecha_fin, hora_inicio, hora_fin, self.current_id),
                )

                _exec(
                    cur,
                    "DELETE FROM DetalleExhibicion WHERE id_exhibicion = ?",
                    (self.current_id,),
                )

                for id_pintura, _titulo, _artista in self._detail_lines:
                    _exec(
                        cur,
                        "INSERT INTO DetalleExhibicion (id_exhibicion, id_pintura) VALUES (?, ?)",
                        (self.current_id, id_pintura),
                    )

                conn.commit()

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

    def abrir_pinturas(self) -> None:
        if self.ventana_pinturas is None:
            self.ventana_pinturas = PinturasVentana(self)

        self.hide()
        self.ventana_pinturas.show()
        self.ventana_pinturas.raise_()
        self.ventana_pinturas.activateWindow()

    def abrir_artistas(self) -> None:
        if self.ventana_artistas is None:
            self.ventana_artistas = ArtistasVentana(self)

        self.hide()
        self.ventana_artistas.show()
        self.ventana_artistas.raise_()
        self.ventana_artistas.activateWindow()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ExhibicionesVentana()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
