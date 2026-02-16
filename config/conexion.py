import pyodbc

def obtener_conexion():
    servidor = "localhost"
    puerto = 1433
    base_datos = "Galart"
    usuario = "sa"
    password = "pruebaBD123"

    cadena = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={servidor},{puerto};"
        f"DATABASE={base_datos};"
        f"UID={usuario};"
        f"PWD={password};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )

    try:
        conexion = pyodbc.connect(cadena)
        return conexion
    except Exception as e:
        print("Error de conexión:", e)
        raise


