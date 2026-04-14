from __future__ import annotations

from contextlib import contextmanager
from config.conexion import obtener_conexion

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor
from PySide6.QtWidgets import (
    QDialog, QFrame, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget
)

from ventanas.RecuperarContrasena import RecuperarContrasenaVentana

BG = "#F7F4EF"
SURFACE = "#FFFFFF"
BORDER = "#E7E1D8"
TEXT = "#2A2A2A"
MUTED = "#5B5B5B"
PRIMARY = "#111827"
GOLD = "#C8A24A"

BTN_BG = "#111827"
BTN_TEXT = "#FFFFFF"


@contextmanager
def db():
    conn = obtener_conexion()
    if conn is None:
        raise RuntimeError("No se pudo conectar a la base de datos.")
    try:
        yield conn
    finally:
        conn.close()


def _exec(cur, sql, params=()):
    cur.execute(sql, params)


class LoginVentana(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.usuario_actual = None

        self.setWindowTitle("Login")
        self.setFixedSize(620, 560)
        self.setModal(True)

        root = QWidget()
        root.setObjectName("Root")
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(root)

        main = QVBoxLayout(root)
        main.setAlignment(Qt.AlignCenter)
        main.setSpacing(20)

        card = QFrame()
        card.setObjectName("Card")

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(16)

        # TITULO
        lbl_title = QLabel("Galería de Arte")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFont(QFont("Segoe UI", 30, QFont.Bold))
        lbl_title.setObjectName("Title")

        lbl_sub = QLabel("Inicia sesión")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setFont(QFont("Segoe UI", 13))
        lbl_sub.setObjectName("MutedLabel")

        # INPUTS
        self.txtUsuario = QLineEdit()
        self.txtUsuario.setPlaceholderText("Usuario")
        self.txtUsuario.setFixedWidth(320)
        self.txtUsuario.setFixedHeight(46)

        self.txtContrasena = QLineEdit()
        self.txtContrasena.setPlaceholderText("Contraseña")
        self.txtContrasena.setEchoMode(QLineEdit.Password)
        self.txtContrasena.setFixedWidth(320)
        self.txtContrasena.setFixedHeight(46)

        # BOTONES
        self.btnEntrar = QPushButton("Entrar")
        self.btnEntrar.setFixedWidth(320)
        self.btnEntrar.setFixedHeight(48)

        self.btnSalir = QPushButton("Salir")
        self.btnSalir.setFixedWidth(320)
        self.btnSalir.setFixedHeight(40)

        self.btnEntrar.clicked.connect(self.autenticar)
        self.btnSalir.clicked.connect(self.reject)

        # AGREGAR AL LAYOUT
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_sub)
        card_layout.addSpacing(10)

        card_layout.addWidget(self.txtUsuario, alignment=Qt.AlignCenter)
        card_layout.addWidget(self.txtContrasena, alignment=Qt.AlignCenter)

        # ENLACE "¿Olvidaste tu contraseña?"
        self.lbl_olvide = QLabel("¿Olvidaste tu contraseña?")
        self.lbl_olvide.setAlignment(Qt.AlignCenter)
        self.lbl_olvide.setObjectName("OlvideLink")
        self.lbl_olvide.setCursor(QCursor(Qt.PointingHandCursor))
        self.lbl_olvide.mousePressEvent = self._abrir_recuperar_contrasena
        card_layout.addWidget(self.lbl_olvide, alignment=Qt.AlignCenter)

        card_layout.addSpacing(10)

        card_layout.addWidget(self.btnEntrar, alignment=Qt.AlignCenter)
        card_layout.addWidget(self.btnSalir, alignment=Qt.AlignCenter)

        main.addWidget(card)

        self.setStyleSheet(self._stylesheet())

        self.txtUsuario.returnPressed.connect(self.autenticar)
        self.txtContrasena.returnPressed.connect(self.autenticar)

    def _stylesheet(self):

        return f"""
        QWidget#Root {{
            background: {BG};
            font-family: "Segoe UI";
        }}

        QFrame#Card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 20px;
            padding: 40px;
        }}

        QLabel#Title {{
            color: {TEXT};
        }}

        QLabel#MutedLabel {{
            color: {MUTED};
            font-size: 12pt;
        }}

        QLabel#OlvideLink {{
            color: {GOLD};
            font-size: 10pt;
            text-decoration: underline;
        }}

        QLineEdit {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 10px 14px;
            font-size: 13pt;
            color: {TEXT};
        }}

        QLineEdit::placeholder {{
            color: #9A9A9A;
        }}

        QLineEdit:focus {{
            border: 2px solid {GOLD};
            background: #FFFFFF;
        }}

        QPushButton {{
            border-radius: 12px;
            font-size: 13pt;
            font-weight: 600;
            color: #000000;
        }}

        """

    def _abrir_recuperar_contrasena(self, event=None):
        dialogo = RecuperarContrasenaVentana(self)
        dialogo.exec()

    def _show_error(self, title, msg):
        QMessageBox.critical(self, title, msg)

    def autenticar(self):

        usuario = self.txtUsuario.text().strip()
        contrasena = self.txtContrasena.text().strip()

        if not usuario or not contrasena:
            self._show_error("Validación", "Escribe usuario y contraseña.")
            return

        try:

            with db() as conn:
                cur = conn.cursor()

                _exec(
                    cur,
                    """SELECT u.id_usuario, u.nombre, u.usuario, u.id_tipo, t.nombre
                       FROM Usuarios u
                       LEFT JOIN UsuarioTipo t ON u.id_tipo = t.id_tipo
                       WHERE u.usuario=? AND u.contraseña=? AND u.activo=1""",
                    (usuario, contrasena),
                )

                row = cur.fetchone()

                if not row:
                    self._show_error("Acceso denegado", "Usuario o contraseña incorrectos.")
                    return

                self.usuario_actual = {
                    "id_usuario": row[0],
                    "nombre": row[1],
                    "usuario": row[2],
                    "id_tipo": row[3],
                    "tipo_nombre": row[4],
                }

                self.accept()

        except Exception as e:
            self._show_error("Error BD", str(e))
