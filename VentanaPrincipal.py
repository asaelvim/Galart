from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame 

from Fondo import Fondo
from Carta import Carta
from PaletaColores import *
from ItemMenu import ItemMenu

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Galería de Arte")
        self.setFixedSize(QSize(590, 829))

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(3)

        card = Carta()
        card.setFixedSize(590, 829)

        card_wrap = QHBoxLayout()
        card_wrap.addStretch(1)
        card_wrap.addWidget(card)
        card_wrap.addStretch(1)
        main.addLayout(card_wrap)

        main.addStretch(1)


        content = QVBoxLayout(card)
        content.setContentsMargins(42, 36, 42, 30)
        content.setSpacing(14)

        lbl_title = QLabel("Galería de Arte")
        lbl_title.setAlignment(Qt.AlignHCenter)
        lbl_title.setFont(QFont("Segoe UI", 28, QFont.Weight.DemiBold))
        lbl_title.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(lbl_title)

        lbl_sub = QLabel("Sistema de Ventas de Pinturas de Arte")
        lbl_sub.setAlignment(Qt.AlignHCenter)
        lbl_sub.setFont(QFont("Segoe UI", 12))
        lbl_sub.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(lbl_sub)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {BORDE}; border: none;")
        content.addWidget(line)

        content.addSpacing(6)

        items = [
            "Gestión de Clientes",
            "Gestión de Proveedores",
            "Gestión de Vendedores",
            "Gestión de Pinturas",
            "Gestión de Artistas",
            "Cotizaciones",
            "Gestión de Ventas",
            "Gestión de Compras",
            "Reportes",
        ]
        
        self.menu_items = []

        for i, t in enumerate(items):
            it = ItemMenu(t)
            self.menu_items.append(it)
            content.addWidget(it)
            content.addSpacing(ESPACIADO_BOTON)

        content.addStretch(1)


        btn_exit = QPushButton("Salir")
        btn_exit.setCursor(Qt.PointingHandCursor)
        btn_exit.setFixedHeight(40)
        btn_exit.setFont(QFont("Segoe UI", 13))
        btn_exit.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {DESACTIVADO};
                border: none;
            }}
            QPushButton:hover {{
                color: {PRIMARIO};
                text-decoration: underline;
            }}
        """)

        btn_exit.clicked.connect(QApplication.instance().quit)

        content.addWidget(btn_exit, alignment=Qt.AlignHCenter)
