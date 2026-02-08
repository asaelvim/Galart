import sys
from PySide6.QtWidgets import QApplication
from VentanaPrincipal import VentanaPrincipal

FONDO_A = "#F7F4EF"
FONDO_B = "#F2ECE4"
SUPERFICIE = "#FFFFFF"
BORDE = "#E7E1D8"
TEXTO = "#1F1F1F"
DESACTIVADO = "#5B5B5B"

PRIMARIO = "#111827"
ACENTO = "#C8A24A"

ALTURA_BOTON = 40
ESPACIADO_BOTON = 10
FONDO_BOTON = "#F6F1EA"
BORDE_BOTON = "#DED6CC"
TEXTO_BOTON = "#2A2A2A"
FONDO_ACTIVO = "#2F333A"
TEXTO_ACTIVO = "#FFFFFF"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = VentanaPrincipal()
    w.show()
    sys.exit(app.exec())
