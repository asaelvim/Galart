# Galart — Sistema Gestor de Galería de Arte

Proyecto de Ingeniería de Software

---

## Requisitos previos

| Herramienta | Versión mínima |
|---|---|
| Python | 3.10+ |
| SQL Server | 2019+ (o Express) |
| ODBC Driver for SQL Server | 18 |

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/asaelvim/Galart.git
cd Galart
```

### 2. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 3. Configurar la conexión a SQL Server

Edita `config/conexion.py` si tu instancia de SQL Server usa credenciales distintas a las predeterminadas:

```
Servidor:   localhost
Puerto:     1433
Usuario:    sa
Contraseña: pruebaBD123
```

### 4. Inicializar la base de datos

Ejecuta el script de configuración desde la raíz del proyecto:

```bash
python database/inicializar_bd.py
```

Este script:
- Crea la base de datos `Galart` si no existe.
- Crea todas las tablas necesarias.
- Inserta los datos iniciales (catálogos, artistas, pinturas e inventario).

Al terminar verás la confirmación:

```
✔  Base de datos inicializada correctamente.

  Credenciales de acceso por defecto:
    Usuario:    admin
    Contraseña: admin123
```

> El script es idempotente: puedes volver a ejecutarlo sin perder datos existentes.

---

## Ejecución de la aplicación

```bash
python main.py
```

---

## Datos semilla incluidos

| Tabla | Registros |
|---|---|
| UsuarioTipo | 3 (Administrador, Vendedor, Cajero) |
| Usuarios | 1 (admin / admin123) |
| Artistas | 5 (Rivera, Kahlo, Tamayo, Orozco, Siqueiros) |
| Técnicas | 5 (Óleo, Acuarela, Acrílico, Fresco, Gouache) |
| Pinturas | 8 obras con precios de referencia |
| Inventario | Stock inicial por pintura |
| Vendedores | 1 vendedor demo |
