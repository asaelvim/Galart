from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor, QFont
from modulos.PaletaColores import *

class BotonMenu(QPushButton):
    def __init__(self, text: str, active: bool = False):
        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(ALTURA_BOTON)

        self.setFont(QFont("Segoe UI", 12))
        self.setFocusPolicy(Qt.NoFocus)
        self.setAutoDefault(False)
        self.setDefault(False)

        self.setObjectName("MenuButtonActive" if active else "MenuButton")

        self.setStyleSheet(self._style())

    def _style(self) -> str:
        return f"""
            QPushButton#MenuButton {{
                background: {FONDO_BOTON};
                color: {TEXTO_BOTON};
                border: 1px solid {BORDE_BOTON};
                border-radius: 10px;
                text-align: left;
                padding-left: 26px;
            }}

            QPushButton#MenuButtonActive {{
                background: {FONDO_ACTIVO};
                color: {TEXTO_ACTIVO};
                border: 1px solid {BORDE_BOTON};
                border-radius: 10px;
                text-align: left;
                padding-left: 26px;
            }}
        """
