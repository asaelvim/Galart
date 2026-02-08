import sys
from PySide6.QtWidgets import QApplication
from ventanas.VentanaPrincipal import VentanaPrincipal

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = VentanaPrincipal()
    w.show()
    sys.exit(app.exec())
