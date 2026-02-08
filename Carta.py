from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect
from PaletaColores import *

class Carta(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            QFrame#Card {{
                background: {SUPERFICIE};
                border: 1px solid {BORDE};
                border-radius: 22px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 55))
        self.setGraphicsEffect(shadow)
