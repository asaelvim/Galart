from __future__ import annotations

import urllib.parse
from contextlib import contextmanager

from config.conexion import obtener_conexion

from PySide6.QtCore import Qt, QUrl, QRegularExpression
from PySide6.QtGui import QDesktopServices, QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QDialog, QFrame, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget
)

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


class RecuperarContrasenaVentana(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Recuperar contraseña")
        self.setFixedSize(620, 460)
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

        # TÍTULO
        lbl_title = QLabel("Recuperar contraseña")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        lbl_title.setObjectName("Title")

        lbl_sub = QLabel("Ingresa tu usuario y número de teléfono\npara verificar tu identidad.")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setFont(QFont("Segoe UI", 11))
        lbl_sub.setObjectName("MutedLabel")

        # INPUTS
        self.txtUsuario = QLineEdit()
        self.txtUsuario.setPlaceholderText("Usuario")
        self.txtUsuario.setFixedWidth(320)
        self.txtUsuario.setFixedHeight(46)

        self.txtTelefono = QLineEdit()
        self.txtTelefono.setPlaceholderText("Teléfono (ej. 5512345678)")
        self.txtTelefono.setFixedWidth(320)
        self.txtTelefono.setFixedHeight(46)
        self.txtTelefono.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^\d{0,10}$"))
        )

        # BOTONES
        self.btnVerificar = QPushButton("Verificar")
        self.btnVerificar.setFixedWidth(320)
        self.btnVerificar.setFixedHeight(48)

        self.btnCancelar = QPushButton("Cancelar")
        self.btnCancelar.setFixedWidth(320)
        self.btnCancelar.setFixedHeight(40)

        self.btnVerificar.clicked.connect(self.verificar)
        self.btnCancelar.clicked.connect(self.reject)

        # AGREGAR AL LAYOUT
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_sub)
        card_layout.addSpacing(10)

        card_layout.addWidget(self.txtUsuario, alignment=Qt.AlignCenter)
        card_layout.addWidget(self.txtTelefono, alignment=Qt.AlignCenter)

        card_layout.addSpacing(10)

        card_layout.addWidget(self.btnVerificar, alignment=Qt.AlignCenter)
        card_layout.addWidget(self.btnCancelar, alignment=Qt.AlignCenter)

        main.addWidget(card)

        self.setStyleSheet(self._stylesheet())

        self.txtTelefono.returnPressed.connect(self.verificar)

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

        QLineEdit {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 10px 14px;
            font-size: 13pt;
            color: {TEXT};
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

    def verificar(self):
        usuario = self.txtUsuario.text().strip()
        telefono_ingresado = self.txtTelefono.text().strip()

        if not usuario or not telefono_ingresado:
            QMessageBox.warning(self, "Validación", "Por favor completa todos los campos.")
            return

        if len(telefono_ingresado) != 10:
            QMessageBox.warning(self, "Validación", "El teléfono debe tener exactamente 10 dígitos.")
            return

        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(
                    cur,
                    "SELECT telefono, contraseña FROM Usuarios WHERE usuario = ? AND activo = 1",
                    (usuario,),
                )
                fila = cur.fetchone()

                if not fila:
                    QMessageBox.warning(
                        self,
                        "Usuario no encontrado",
                        "No se encontró ningún usuario activo con ese nombre de usuario.",
                    )
                    return

                telefono_bd, contrasena = fila[0], fila[1]

                if not telefono_bd or not telefono_bd.strip():
                    QMessageBox.warning(
                        self,
                        "Sin teléfono registrado",
                        "Este usuario no tiene un número de teléfono registrado.",
                    )
                    return

                if telefono_ingresado.strip() != telefono_bd.strip():
                    QMessageBox.warning(
                        self,
                        "Teléfono incorrecto",
                        "El número de teléfono no coincide con el registrado.",
                    )
                    return

        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))
            return

        # Construir enlace de WhatsApp
        mensaje = f"Hola, tu contraseña de Galart es: {contrasena}"
        numero_limpio = ''.join(c for c in telefono_bd.strip() if c.isdigit())
        url = f"https://wa.me/{numero_limpio}?text={urllib.parse.quote(mensaje)}"

        QDesktopServices.openUrl(QUrl(url))

        QMessageBox.information(
            self,
            "WhatsApp",
            f"Se abrirá WhatsApp con tu contraseña. Si no se abre automáticamente, visita: {url}",
        )
        self.accept()
