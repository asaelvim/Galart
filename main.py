import sys
from PySide6.QtWidgets import QApplication
from ventanas.VentanaPrincipal import VentanaPrincipal
from config.conexion import obtener_conexion

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    conexion = obtener_conexion()

    w = VentanaPrincipal(conexion)
    w.show()

    sys.exit(app.exec())

