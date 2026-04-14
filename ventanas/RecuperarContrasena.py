from __future__ import annotations

import smtplib
from contextlib import contextmanager
from email.mime.text import MIMEText

from config.conexion import obtener_conexion

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QFrame, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget
)

# Configurar con las credenciales reales del remitente antes de usar
SMTP_EMAIL = "tucorreo@gmail.com"
SMTP_PASSWORD = "tu_app_password"

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
        self.setFixedSize(620, 420)
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

        lbl_sub = QLabel("Ingresa tu nombre de usuario y te enviaremos\ntu contraseña al correo registrado.")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setFont(QFont("Segoe UI", 11))
        lbl_sub.setObjectName("MutedLabel")

        # INPUT
        self.txtUsuario = QLineEdit()
        self.txtUsuario.setPlaceholderText("Nombre de usuario")
        self.txtUsuario.setFixedWidth(320)
        self.txtUsuario.setFixedHeight(46)

        # BOTONES
        self.btnEnviar = QPushButton("Enviar correo")
        self.btnEnviar.setFixedWidth(320)
        self.btnEnviar.setFixedHeight(48)

        self.btnCancelar = QPushButton("Cancelar")
        self.btnCancelar.setFixedWidth(320)
        self.btnCancelar.setFixedHeight(40)

        self.btnEnviar.clicked.connect(self.enviar_correo)
        self.btnCancelar.clicked.connect(self.reject)

        # AGREGAR AL LAYOUT
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_sub)
        card_layout.addSpacing(10)

        card_layout.addWidget(self.txtUsuario, alignment=Qt.AlignCenter)

        card_layout.addSpacing(10)

        card_layout.addWidget(self.btnEnviar, alignment=Qt.AlignCenter)
        card_layout.addWidget(self.btnCancelar, alignment=Qt.AlignCenter)

        main.addWidget(card)

        self.setStyleSheet(self._stylesheet())

        self.txtUsuario.returnPressed.connect(self.enviar_correo)

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
            font-size: 11pt;
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

    def enviar_correo(self):
        usuario = self.txtUsuario.text().strip()

        if not usuario:
            QMessageBox.warning(self, "Validación", "Por favor ingresa tu nombre de usuario.")
            return

        try:
            with db() as conn:
                cur = conn.cursor()
                _exec(
                    cur,
                    "SELECT email, contraseña FROM Usuarios WHERE usuario = ? AND activo = 1",
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

                email, contrasena = fila[0], fila[1]

                if not email or not email.strip():
                    QMessageBox.warning(
                        self,
                        "Sin correo registrado",
                        "Este usuario no tiene un correo registrado.",
                    )
                    return

        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))
            return

        try:
            mensaje = MIMEText(
                f"Hola {usuario},\n\n"
                f"Tu contraseña de acceso a Galart es: {contrasena}\n\n"
                "Si no solicitaste este correo, ignóralo.\n\n"
                "— Equipo Galart",
                "plain",
                "utf-8",
            )
            mensaje["Subject"] = "Recuperación de contraseña - Galart"
            mensaje["From"] = SMTP_EMAIL
            mensaje["To"] = email.strip()

            with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
                servidor.ehlo()
                servidor.starttls()
                servidor.login(SMTP_EMAIL, SMTP_PASSWORD)
                servidor.sendmail(SMTP_EMAIL, email.strip(), mensaje.as_string())

        except Exception as e:
            QMessageBox.critical(self, "Error al enviar correo", str(e))
            return

        QMessageBox.information(
            self,
            "Correo enviado",
            "Se ha enviado la contraseña al correo registrado.",
        )
        self.accept()
