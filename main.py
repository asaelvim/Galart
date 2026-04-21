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

        try:
            cursor = conexion.cursor()
            cursor.execute(
                """
                INSERT INTO AperturaCaja (monto, fecha)
                SELECT ?, GETDATE()
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM AperturaCaja
                    WHERE CAST(fecha AS DATE) = CAST(GETDATE() AS DATE)
                )
                """,
                (0,),
            )
            conexion.commit()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Error",
                f"No se pudo inicializar la apertura de caja en la base de datos:\n{e}",
            )
            sys.exit(1)

        w = VentanaPrincipal(conexion, login.usuario_actual)
        w.show()
        sys.exit(app.exec())

    sys.exit(0)
