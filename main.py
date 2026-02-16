import sys
from PySide6.QtWidgets import QApplication
from ventanas.VentanaPrincipal import VentanaPrincipal
from config.conexion import obtener_conexion

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 🔥 Crear conexión a SQL Server
    conexion = obtener_conexion()

    # Pasarla a la ventana principal
    w = VentanaPrincipal(conexion)
    w.show()

    sys.exit(app.exec())

