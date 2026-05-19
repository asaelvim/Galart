"""
Initializes the SQLite database for Galart.
Creates all tables and inserts seed data if the database is new.
"""
import sqlite3


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS UsuarioTipo (
    id_tipo   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    usuario    TEXT NOT NULL UNIQUE,
    contraseña TEXT NOT NULL,
    email      TEXT,
    telefono   TEXT,
    id_tipo    INTEGER REFERENCES UsuarioTipo(id_tipo),
    activo     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    correo     TEXT,
    telefono   TEXT
);

CREATE TABLE IF NOT EXISTS Proveedores (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL,
    telefono     TEXT,
    correo       TEXT,
    direccion    TEXT
);

CREATE TABLE IF NOT EXISTS Vendedores (
    id_vendedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    correo      TEXT,
    telefono    TEXT,
    activo      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Artistas (
    id_artista INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    biografia  TEXT,
    pais       TEXT
);

CREATE TABLE IF NOT EXISTS Tecnicas (
    id_tecnica INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Pinturas (
    id_pintura INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo     TEXT NOT NULL,
    precio     REAL NOT NULL DEFAULT 0,
    id_artista INTEGER REFERENCES Artistas(id_artista),
    id_tecnica INTEGER REFERENCES Tecnicas(id_tecnica)
);

CREATE TABLE IF NOT EXISTS Inventario (
    id_inventario INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pintura    INTEGER NOT NULL REFERENCES Pinturas(id_pintura),
    cantidad      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Cotizaciones (
    id_cotizacion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente    INTEGER REFERENCES Clientes(id_cliente),
    id_vendedor   INTEGER REFERENCES Vendedores(id_vendedor),
    fecha         TEXT NOT NULL,
    subtotal      REAL NOT NULL DEFAULT 0,
    iva           REAL NOT NULL DEFAULT 0,
    total         REAL NOT NULL DEFAULT 0,
    concretada    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS DetalleCotizacion (
    id_detalle       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cotizacion    INTEGER NOT NULL REFERENCES Cotizaciones(id_cotizacion),
    id_pintura       INTEGER REFERENCES Pinturas(id_pintura),
    cantidad         INTEGER NOT NULL DEFAULT 1,
    precio_unitario  REAL NOT NULL DEFAULT 0,
    subtotal         REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Ventas (
    id_venta    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente  INTEGER REFERENCES Clientes(id_cliente),
    id_vendedor INTEGER REFERENCES Vendedores(id_vendedor),
    fecha       TEXT NOT NULL,
    total       REAL NOT NULL DEFAULT 0,
    forma_pago  TEXT
);

CREATE TABLE IF NOT EXISTS DetalleVenta (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta   INTEGER NOT NULL REFERENCES Ventas(id_venta),
    id_pintura INTEGER REFERENCES Pinturas(id_pintura),
    cantidad   INTEGER NOT NULL DEFAULT 1,
    subtotal   REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Compras (
    id_compra    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_proveedor INTEGER REFERENCES Proveedores(id_proveedor),
    fecha        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS DetalleCompra (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_compra  INTEGER NOT NULL REFERENCES Compras(id_compra),
    id_pintura INTEGER REFERENCES Pinturas(id_pintura),
    cantidad   INTEGER NOT NULL DEFAULT 1,
    precio     REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Exhibicion (
    id_exhibicion INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL,
    fecha_inicio  TEXT,
    fecha_fin     TEXT,
    hora_inicio   TEXT,
    hora_fin      TEXT
);

CREATE TABLE IF NOT EXISTS DetalleExhibicion (
    id_detalle    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_exhibicion INTEGER NOT NULL REFERENCES Exhibicion(id_exhibicion),
    id_pintura    INTEGER REFERENCES Pinturas(id_pintura)
);

CREATE TABLE IF NOT EXISTS AperturaCaja (
    id_apertura INTEGER PRIMARY KEY AUTOINCREMENT,
    id_vendedor INTEGER REFERENCES Vendedores(id_vendedor),
    monto       REAL NOT NULL DEFAULT 0,
    fecha       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS CierreCaja (
    id_cierre      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_vendedor    INTEGER REFERENCES Vendedores(id_vendedor),
    fecha          TEXT NOT NULL,
    totalEfectivo  REAL NOT NULL DEFAULT 0,
    totalVoucher   REAL NOT NULL DEFAULT 0,
    montoTotal     REAL NOT NULL DEFAULT 0
);
"""

SEED = """
INSERT OR IGNORE INTO UsuarioTipo (id_tipo, nombre) VALUES (1, 'Administrador');
INSERT OR IGNORE INTO UsuarioTipo (id_tipo, nombre) VALUES (2, 'Vendedor');

INSERT OR IGNORE INTO Usuarios (id_usuario, nombre, usuario, contraseña, email, telefono, id_tipo, activo)
VALUES (1, 'Administrador', 'admin', 'admin123', 'admin@galart.com', '5500000000', 1, 1);

INSERT OR IGNORE INTO Artistas (id_artista, nombre, biografia, pais)
VALUES (1, 'Frida Kahlo', 'Pintora mexicana conocida por sus autorretratos y obras influenciadas por el folclore mexicano.', 'México');

INSERT OR IGNORE INTO Artistas (id_artista, nombre, biografia, pais)
VALUES (2, 'Diego Rivera', 'Muralista mexicano, una de las figuras más influyentes del arte latinoamericano.', 'México');

INSERT OR IGNORE INTO Artistas (id_artista, nombre, biografia, pais)
VALUES (3, 'Remedios Varo', 'Pintora surrealista de origen español nacionalizada mexicana.', 'México');

INSERT OR IGNORE INTO Artistas (id_artista, nombre, biografia, pais)
VALUES (4, 'Rufino Tamayo', 'Pintor mexicano conocido por su síntesis entre el arte prehispánico y las corrientes modernas.', 'México');

INSERT OR IGNORE INTO Tecnicas (id_tecnica, nombre) VALUES (1, 'Óleo');
INSERT OR IGNORE INTO Tecnicas (id_tecnica, nombre) VALUES (2, 'Acuarela');
INSERT OR IGNORE INTO Tecnicas (id_tecnica, nombre) VALUES (3, 'Acrílico');
INSERT OR IGNORE INTO Tecnicas (id_tecnica, nombre) VALUES (4, 'Grabado');
INSERT OR IGNORE INTO Tecnicas (id_tecnica, nombre) VALUES (5, 'Pastel');

INSERT OR IGNORE INTO Pinturas (id_pintura, titulo, precio, id_artista, id_tecnica)
VALUES (1, 'Autorretrato con collar de espinas', 12500.00, 1, 1);

INSERT OR IGNORE INTO Pinturas (id_pintura, titulo, precio, id_artista, id_tecnica)
VALUES (2, 'Las dos Fridas', 45000.00, 1, 1);

INSERT OR IGNORE INTO Pinturas (id_pintura, titulo, precio, id_artista, id_tecnica)
VALUES (3, 'Sueño de una tarde dominical', 38000.00, 2, 1);

INSERT OR IGNORE INTO Pinturas (id_pintura, titulo, precio, id_artista, id_tecnica)
VALUES (4, 'Naturaleza muerta con loro', 18500.00, 2, 1);

INSERT OR IGNORE INTO Pinturas (id_pintura, titulo, precio, id_artista, id_tecnica)
VALUES (5, 'Exploración de las fuentes del río Orinoco', 22000.00, 3, 1);

INSERT OR IGNORE INTO Pinturas (id_pintura, titulo, precio, id_artista, id_tecnica)
VALUES (6, 'Sandías', 9800.00, 4, 3);

INSERT OR IGNORE INTO Inventario (id_pintura, cantidad) VALUES (1, 2);
INSERT OR IGNORE INTO Inventario (id_pintura, cantidad) VALUES (2, 1);
INSERT OR IGNORE INTO Inventario (id_pintura, cantidad) VALUES (3, 3);
INSERT OR IGNORE INTO Inventario (id_pintura, cantidad) VALUES (4, 2);
INSERT OR IGNORE INTO Inventario (id_pintura, cantidad) VALUES (5, 1);
INSERT OR IGNORE INTO Inventario (id_pintura, cantidad) VALUES (6, 4);

INSERT OR IGNORE INTO Clientes (id_cliente, nombre, correo, telefono)
VALUES (1, 'María González', 'maria@ejemplo.com', '5511111111');

INSERT OR IGNORE INTO Clientes (id_cliente, nombre, correo, telefono)
VALUES (2, 'Carlos Martínez', 'carlos@ejemplo.com', '5522222222');

INSERT OR IGNORE INTO Clientes (id_cliente, nombre, correo, telefono)
VALUES (3, 'Ana López', 'ana@ejemplo.com', '5533333333');

INSERT OR IGNORE INTO Proveedores (id_proveedor, nombre, telefono, correo, direccion)
VALUES (1, 'Arte y Enmarcados SA', '5544444444', 'ventas@arteenmarcados.com', 'Av. Insurgentes 100, CDMX');

INSERT OR IGNORE INTO Proveedores (id_proveedor, nombre, telefono, correo, direccion)
VALUES (2, 'Materiales Plásticos del Norte', '5555555555', 'info@matplasticos.com', 'Blvd. Díaz Ordaz 200, MTY');

INSERT OR IGNORE INTO Vendedores (id_vendedor, nombre, correo, telefono, activo)
VALUES (1, 'Luis Hernández', 'luis@galart.com', '5566666666', 1);

INSERT OR IGNORE INTO Vendedores (id_vendedor, nombre, correo, telefono, activo)
VALUES (2, 'Sofía Ramírez', 'sofia@galart.com', '5577777777', 1);
"""


def init_db(db_path: str) -> None:
    """Create tables and insert seed data if database is new."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.executescript(SCHEMA)
        # Only seed if the UsuarioTipo table is empty
        cur.execute("SELECT COUNT(*) FROM UsuarioTipo")
        if cur.fetchone()[0] == 0:
            cur.executescript(SEED)
        conn.commit()
    finally:
        conn.close()
