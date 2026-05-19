"""
inicializar_bd.py
-----------------
Ejecuta database/setup.sql contra la instancia SQL Server configurada
en config/conexion.py y crea/puebla la base de datos Galart desde cero.

Uso:
    python database/inicializar_bd.py

Requisitos:
    - pyodbc instalado  (pip install pyodbc)
    - ODBC Driver 18 for SQL Server instalado en el equipo
    - SQL Server accesible en localhost:1433 con el usuario 'sa'
"""

from __future__ import annotations

import os
import re
import sys

import pyodbc


# ------------------------------------------------------------------ #
#  Configuración de conexión (debe coincidir con config/conexion.py)  #
# ------------------------------------------------------------------ #
SERVIDOR = "localhost"
PUERTO = 1433
USUARIO_SA = "sa"
PASSWORD_SA = "pruebaBD123"
BASE_DATOS = "Galart"


def _conectar(base_datos: str = "master") -> pyodbc.Connection:
    """Abre una conexión pyodbc al servidor indicado."""
    cadena = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVIDOR},{PUERTO};"
        f"DATABASE={base_datos};"
        f"UID={USUARIO_SA};"
        f"PWD={PASSWORD_SA};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(cadena, autocommit=True)


def _dividir_batches(sql: str) -> list[str]:
    """Divide el script en lotes separados por GO (insensible a mayúsculas)."""
    batches = re.split(r"^\s*GO\s*$", sql, flags=re.IGNORECASE | re.MULTILINE)
    return [b.strip() for b in batches if b.strip()]


def inicializar() -> None:
    script_path = os.path.join(os.path.dirname(__file__), "setup.sql")

    if not os.path.exists(script_path):
        print(f"[ERROR] No se encontró el script: {script_path}")
        sys.exit(1)

    with open(script_path, encoding="utf-8") as f:
        sql_completo = f.read()

    batches = _dividir_batches(sql_completo)
    total = len(batches)

    print(f"Galart — Inicialización de base de datos")
    print(f"Conectando a {SERVIDOR}:{PUERTO} …")

    try:
        conn = _conectar("master")
    except Exception as exc:
        print(f"[ERROR] No se pudo conectar a SQL Server:\n  {exc}")
        print("\nVerifica que:")
        print("  • SQL Server esté corriendo en localhost:1433")
        print("  • Las credenciales de 'sa' sean correctas")
        print("  • ODBC Driver 18 for SQL Server esté instalado")
        sys.exit(1)

    print(f"Conexión exitosa. Ejecutando {total} lotes SQL …\n")

    errores = 0
    for i, batch in enumerate(batches, start=1):
        preview = batch.splitlines()[0][:80]
        try:
            conn.execute(batch)
            print(f"  [{i:>3}/{total}] OK  — {preview}")
        except pyodbc.Error as exc:
            # Ignorar "database already exists" y errores equivalentes
            estado = exc.args[0] if exc.args else ""
            mensaje = str(exc)
            if any(code in mensaje for code in ("01000", "42S01", "1801", "2714")):
                print(f"  [{i:>3}/{total}] --  (ya existe, se omite) — {preview}")
            else:
                print(f"  [{i:>3}/{total}] ERR — {preview}")
                print(f"         {mensaje}")
                errores += 1

    conn.close()

    print()
    if errores == 0:
        print("✔  Base de datos inicializada correctamente.")
        print()
        print("  Credenciales de acceso por defecto:")
        print("    Usuario:    admin")
        print("    Contraseña: admin123")
    else:
        print(f"⚠  Finalizado con {errores} error(es). Revisa los mensajes anteriores.")
        sys.exit(1)


if __name__ == "__main__":
    inicializar()
