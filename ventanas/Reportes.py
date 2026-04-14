from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget
from modulos.ItemMenu import ItemMenu
from modulos.Fondo import Fondo
from modulos.Carta import Carta
from modulos.PaletaColores import *
from ventanas.NotaVentas import NotaVentasVentana

class ReporteSimpleVentana(QMainWindow):
    def __init__(self, titulo_reporte, ventana_padre=None):
        super().__init__(ventana_padre)
        self.ventana_padre = ventana_padre
        self.setWindowTitle(titulo_reporte)
        self.setMinimumSize(QSize(520, 360))

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(1)

        card = Carta()
        card.setFixedSize(520, 360)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)
        main.addLayout(wrap)

        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(30, 24, 30, 24)
        content.setSpacing(14)

        lbl_titulo = QLabel(titulo_reporte)
        lbl_titulo.setAlignment(Qt.AlignHCenter)
        lbl_titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.DemiBold))
        lbl_titulo.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(lbl_titulo)

        lbl_info = QLabel("Aquí irá el formulario, consulta o gráfico de este reporte.")
        lbl_info.setAlignment(Qt.AlignHCenter)
        lbl_info.setWordWrap(True)
        lbl_info.setFont(QFont("Segoe UI", 11))
        lbl_info.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(lbl_info)

        content.addStretch(1)

        btn_regresar = QPushButton("Cerrar")
        btn_regresar.setCursor(Qt.PointingHandCursor)
        btn_regresar.setFixedHeight(40)
        btn_regresar.setFont(QFont("Segoe UI", 12))
        btn_regresar.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {PRIMARIO};
                border: 1px solid {BORDE};
                border-radius: 10px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {PRIMARIO};
                color: white;
            }}
        """)
        btn_regresar.clicked.connect(self.close)
        content.addWidget(btn_regresar, alignment=Qt.AlignHCenter)

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)


class ReportesVentana(QMainWindow):
    def __init__(self, ventana_principal=None):
        super().__init__(ventana_principal)
        self.ventana_principal = ventana_principal

        self.setWindowTitle("Reportes")
        self.setMinimumSize(QSize(590, 829))

        self.ventana_reporte_actual = None

        root = Fondo()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(3)

        card = Carta()
        card.setFixedSize(590, 909)

        card_wrap = QHBoxLayout()
        card_wrap.addStretch(1)
        card_wrap.addWidget(card)
        card_wrap.addStretch(1)
        main.addLayout(card_wrap)

        main.addStretch(1)

        content = QVBoxLayout(card)
        content.setContentsMargins(42, 36, 42, 30)
        content.setSpacing(14)

        lbl_title = QLabel("Reportes")
        lbl_title.setAlignment(Qt.AlignHCenter)
        lbl_title.setFont(QFont("Segoe UI", 28, QFont.Weight.DemiBold))
        lbl_title.setStyleSheet(f"color: {TEXTO};")
        content.addWidget(lbl_title)

        lbl_sub = QLabel("Selecciona el tipo de reporte que deseas consultar")
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

        botones = [
            ("Ventas por periodo", self.abrir_ventas_por_periodo),
            ("Pinturas populares", self.abrir_pinturas_populares),
            ("Inventario", self.abrir_inventario),
            ("Compras por proveedor", self.abrir_compras_por_proveedor),
            ("Ventas por cliente", self.abrir_ventas_por_cliente),
            ("Ventas por mes", self.abrir_ventas_por_mes),
            ("Facturas", self.abrir_facturas),
            ("Nota de ventas", self.abrir_nota_de_ventas),
        ]

        self.menu_items = []
        content.addSpacing(6)
        for texto, accion in botones:
            item = ItemMenu(texto)
            self.menu_items.append(item)
            content.addWidget(item)
            content.addSpacing(ESPACIADO_BOTON)

            item.button.clicked.connect(accion)

        content.addStretch(1)

        btn_back = QPushButton("Regresar")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setFixedHeight(40)
        btn_back.setFont(QFont("Segoe UI", 13))
        btn_back.setStyleSheet(f"""
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
        btn_back.clicked.connect(self.regresar)
        content.addWidget(btn_back, alignment=Qt.AlignHCenter)

    def regresar(self):
        self.hide()
        if self.ventana_principal is not None:
            self.ventana_principal.show()
            self.ventana_principal.raise_()
            self.ventana_principal.activateWindow()

    def abrir_reporte(self, titulo):
        self.ventana_reporte_actual = ReporteSimpleVentana(titulo, self)
        self.hide()
        self.ventana_reporte_actual.show()
        self.ventana_reporte_actual.raise_()
        self.ventana_reporte_actual.activateWindow()

    def abrir_ventas_por_periodo(self):
        self.abrir_reporte("Ventas por periodo")

    def abrir_pinturas_populares(self):
        self.abrir_reporte("Pinturas populares")

    def abrir_inventario(self):
        self.abrir_reporte("Inventario")

    def abrir_compras_por_proveedor(self):
        self.abrir_reporte("Compras por proveedor")

    def abrir_ventas_por_cliente(self):
        self.abrir_reporte("Ventas por cliente")

    def abrir_ventas_por_mes(self):
        self.abrir_reporte("Ventas por mes")

    def abrir_facturas(self):
        self.abrir_reporte("Facturas")

    def abrir_nota_de_ventas(self):
        self.ventana_reporte_actual = NotaVentasVentana(self.ventana_principal.conexion, self)
        self.hide()
        self.ventana_reporte_actual.show()
        self.ventana_reporte_actual.raise_()
        self.ventana_reporte_actual.activateWindow()
