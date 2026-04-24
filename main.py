import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from config.conexion import obtener_conexion
from ventanas.Login import LoginVentana
from ventanas.VentanaPrincipal import VentanaPrincipal

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    login = LoginVentana()
    if login.exec() == QDialog.Accepted:
        conexion = obtener_conexion()
        if conexion is None:
            QMessageBox.critical(None, "Error", "No se pudo conectar a la base de datos.")
            sys.exit(1)

        w = VentanaPrincipal(conexion, login.usuario_actual)
        w.show()
        sys.exit(app.exec())

    sys.exit(0)
