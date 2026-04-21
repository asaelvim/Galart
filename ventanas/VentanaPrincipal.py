from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame 

from modulos.Fondo import Fondo
from modulos.Carta import Carta
from modulos.PaletaColores import *
from modulos.ItemMenu import ItemMenu
from ventanas.Clientes import ClientesVentana
from ventanas.Proveedores import ProveedoresWindow
from ventanas.Vendedores import VendedoresVentana
from ventanas.Artistas import ArtistasVentana
from ventanas.Pinturas import PinturasVentana
from ventanas.Exhibiciones import ExhibicionesVentana
from ventanas.Cotizaciones import CotizacionesVentana
from ventanas.Ventas import VentasVentana
from ventanas.Compras import ComprasVentana
from ventanas.Reportes import ReportesVentana
from ventanas.CorteCaja import CorteCajaVentana

class VentanaPrincipal(QMainWindow):
    def __init__(self, conexion, usuario_actual=None):
        super().__init__()

        self.conexion = conexion
        self.usuario_actual = usuario_actual
        self.ventana_clientes = None
        self.ventana_proveedores = None
        self.ventana_vendedores = None
        self.ventana_artistas = None
        self.ventana_pinturas = None
        self.ventana_exhibiciones = None
        self.ventana_cotizaciones = None
        self.ventana_ventas = None
        self.ventana_compras = None
        self.ventana_reportes = None
        self.ventana_corte_caja = None
        self.ventana_usuarios = None

        cursor = self.conexion.cursor()
        cursor.execute("SELECT DB_NAME()")
        print("Conectado a:", cursor.fetchone()[0])
        self.setWindowTitle("Galería de Arte")
        self.setMinimumSize(QSize(590, 829))

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
        content.setSpacing(10)

        row_config = QHBoxLayout()
        btn_corte_caja = QPushButton("💰")
        btn_corte_caja.setCursor(Qt.PointingHandCursor)
        btn_corte_caja.setFixedSize(36, 36)
        btn_corte_caja.setFont(QFont("Segoe UI", 20, QFont.Weight.DemiBold))
        btn_corte_caja.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {DESACTIVADO};
                border: none;
            }}
            QPushButton:hover {{
                color: {ACENTO};
            }}
        """)
        btn_corte_caja.clicked.connect(self.abrir_corte_caja)
        row_config.addWidget(btn_corte_caja)
        row_config.addStretch(1)
        if self._es_admin():
            btn_config = QPushButton("⚙")
            btn_config.setCursor(Qt.PointingHandCursor)
            btn_config.setFixedSize(36, 36)
            btn_config.setFont(QFont("Segoe UI", 20, QFont.Weight.DemiBold))
            btn_config.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {DESACTIVADO};
                    border: none;
                }}
                QPushButton:hover {{
                    color: {ACENTO};
                }}
            """)
            btn_config.clicked.connect(self.abrir_usuarios)
            row_config.addWidget(btn_config)
        content.addLayout(row_config)

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

        self.lbl_sesion = QLabel(self._texto_sesion())
        self.lbl_sesion.setAlignment(Qt.AlignHCenter)
        self.lbl_sesion.setFont(QFont("Segoe UI", 10))
        self.lbl_sesion.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(self.lbl_sesion)

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
            "Gestión de Exhibiciones",
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
            if t == "Gestión de Clientes":
                it.button.clicked.connect(self.abrir_clientes)
            if t == "Gestión de Proveedores":
                it.button.clicked.connect(self.abrir_proveedores)
            if t == "Gestión de Vendedores":
                it.button.clicked.connect(self.abrir_vendedores)
            if t == "Gestión de Artistas":
                it.button.clicked.connect(self.abrir_artistas)
            if t == "Gestión de Pinturas":
                it.button.clicked.connect(self.abrir_pinturas)
            if t == "Gestión de Exhibiciones":
                it.button.clicked.connect(self.abrir_exhibiciones)
            if t == "Cotizaciones":
                it.button.clicked.connect(self.abrir_cotizaciones)
            if t == "Gestión de Ventas":
                it.button.clicked.connect(self.abrir_ventas)
            if t == "Gestión de Compras":
                it.button.clicked.connect(self.abrir_compras)
            if t == "Reportes":
                it.button.clicked.connect(self.abrir_reportes)

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


    def abrir_clientes(self):
        if self.ventana_clientes is None:
            self.ventana_clientes = ClientesVentana(self)

        self.hide()
        self.ventana_clientes.show()
        self.ventana_clientes.raise_()
        self.ventana_clientes.activateWindow()

    def abrir_proveedores(self):
        if self.ventana_proveedores is None:
            self.ventana_proveedores = ProveedoresWindow(self)

        self.hide()
        self.ventana_proveedores.show()
        self.ventana_proveedores.raise_()
        self.ventana_proveedores.activateWindow()

    def abrir_vendedores(self):
        if self.ventana_vendedores is None:
            self.ventana_vendedores = VendedoresVentana(self)

        self.hide()
        self.ventana_vendedores.show()
        self.ventana_vendedores.raise_()
        self.ventana_vendedores.activateWindow()

    def abrir_artistas(self):
        if self.ventana_artistas is None:
            self.ventana_artistas = ArtistasVentana(self)

        self.hide()
        self.ventana_artistas.show()
        self.ventana_artistas.raise_()
        self.ventana_artistas.activateWindow()

    def abrir_pinturas(self):
        if self.ventana_pinturas is None:
            self.ventana_pinturas = PinturasVentana(self)
        self.hide()
        self.ventana_pinturas.show()
        self.ventana_pinturas.raise_()
        self.ventana_pinturas.activateWindow()

    def abrir_exhibiciones(self):
        if self.ventana_exhibiciones is None:
            self.ventana_exhibiciones = ExhibicionesVentana(self)
        self.hide()
        self.ventana_exhibiciones.show()
        self.ventana_exhibiciones.raise_()
        self.ventana_exhibiciones.activateWindow()

    def abrir_cotizaciones(self):
        if self.ventana_cotizaciones is None:
            self.ventana_cotizaciones = CotizacionesVentana(self)
        self.hide()
        self.ventana_cotizaciones.show()
        self.ventana_cotizaciones.raise_()
        self.ventana_cotizaciones.activateWindow()

    def abrir_ventas(self):
        if self.ventana_ventas is None:
            self.ventana_ventas = VentasVentana(self)
        self.hide()
        self.ventana_ventas.show()
        self.ventana_ventas.raise_()
        self.ventana_ventas.activateWindow()

    def abrir_compras(self):
        if self.ventana_compras is None:
            self.ventana_compras = ComprasVentana(self)
        self.hide()
        self.ventana_compras.show()
        self.ventana_compras.raise_()
        self.ventana_compras.activateWindow()

    def abrir_reportes(self):
        if self.ventana_reportes is None:
            self.ventana_reportes = ReportesVentana(self)

        self.hide()
        self.ventana_reportes.show()
        self.ventana_reportes.raise_()
        self.ventana_reportes.activateWindow()

    def abrir_corte_caja(self):
        if self.ventana_corte_caja is None:
            self.ventana_corte_caja = CorteCajaVentana(self.conexion, self)
        else:
            self.ventana_corte_caja.recargar()
        self.hide()
        self.ventana_corte_caja.show()
        self.ventana_corte_caja.raise_()
        self.ventana_corte_caja.activateWindow()

    def abrir_usuarios(self):
        from ventanas.Usuarios import UsuariosVentana
        if self.ventana_usuarios is None:
            self.ventana_usuarios = UsuariosVentana(self)
        self.hide()
        self.ventana_usuarios.show()
        self.ventana_usuarios.raise_()
        self.ventana_usuarios.activateWindow()

    def _texto_sesion(self) -> str:
        if not self.usuario_actual:
            return "Sesión: invitado"
        nombre = self.usuario_actual.get("nombre", "")
        usuario = self.usuario_actual.get("usuario", "")
        tipo = self.usuario_actual.get("tipo_nombre", "")
        return f"Sesión: {nombre} ({usuario}) - {tipo}"

    def _es_admin(self) -> bool:
        if not self.usuario_actual:
            return False
        tipo = self.usuario_actual.get("tipo_nombre", "") or ""
        return tipo.strip().lower() == "administrador"
    def showEvent(self, event):
        if hasattr(self, "lbl_sesion"):
            self.lbl_sesion.setText(self._texto_sesion())
        super().showEvent(event)
