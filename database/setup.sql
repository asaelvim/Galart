-- =============================================================
--  Galart -- Script completo de base de datos
--  SQL Server 2019+
--  Uso: ejecutar contra la instancia destino con el usuario "sa"
--       (o cualquier login con permisos de CREATE DATABASE).
-- =============================================================

-- -------------------------------------------------------
-- 1. Crear / seleccionar base de datos
-- -------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = N'Galart')
    CREATE DATABASE Galart;
GO

USE Galart;
GO

-- -------------------------------------------------------
-- 2. Tablas de catálogo
-- -------------------------------------------------------

-- Tipos de usuario (Administrador, Vendedor, etc.)
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'UsuarioTipo')
CREATE TABLE UsuarioTipo (
    id_tipo   INT           IDENTITY(1,1) PRIMARY KEY,
    nombre    NVARCHAR(60)  NOT NULL
);
GO

-- Artistas
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Artistas')
CREATE TABLE Artistas (
    id_artista  INT            IDENTITY(1,1) PRIMARY KEY,
    nombre      NVARCHAR(120)  NOT NULL,
    biografia   NVARCHAR(MAX)  NULL,
    pais        NVARCHAR(80)   NULL
);
GO

-- Técnicas de pintura
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Tecnicas')
CREATE TABLE Tecnicas (
    id_tecnica  INT           IDENTITY(1,1) PRIMARY KEY,
    nombre      NVARCHAR(80)  NOT NULL
);
GO

-- Pinturas
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Pinturas')
CREATE TABLE Pinturas (
    id_pintura  INT             IDENTITY(1,1) PRIMARY KEY,
    titulo      NVARCHAR(200)   NOT NULL,
    precio      DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    id_artista  INT             NULL REFERENCES Artistas(id_artista),
    id_tecnica  INT             NULL REFERENCES Tecnicas(id_tecnica)
);
GO

-- Clientes
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Clientes')
CREATE TABLE Clientes (
    id_cliente  INT            IDENTITY(1,1) PRIMARY KEY,
    nombre      NVARCHAR(120)  NOT NULL,
    correo      NVARCHAR(120)  NULL,
    telefono    NVARCHAR(30)   NULL
);
GO

-- Proveedores
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Proveedores')
CREATE TABLE Proveedores (
    id_proveedor  INT            IDENTITY(1,1) PRIMARY KEY,
    nombre        NVARCHAR(120)  NOT NULL,
    telefono      NVARCHAR(30)   NULL,
    correo        NVARCHAR(120)  NULL,
    direccion     NVARCHAR(200)  NULL
);
GO

-- Vendedores
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Vendedores')
CREATE TABLE Vendedores (
    id_vendedor  INT            IDENTITY(1,1) PRIMARY KEY,
    nombre       NVARCHAR(120)  NOT NULL,
    correo       NVARCHAR(120)  NULL,
    telefono     NVARCHAR(30)   NULL,
    activo       BIT            NOT NULL DEFAULT 1
);
GO

-- Usuarios del sistema
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Usuarios')
CREATE TABLE Usuarios (
    id_usuario  INT            IDENTITY(1,1) PRIMARY KEY,
    nombre      NVARCHAR(120)  NOT NULL,
    usuario     NVARCHAR(60)   NOT NULL,
    [contraseña] NVARCHAR(60)  NOT NULL,
    email       NVARCHAR(120)  NULL,
    telefono    NVARCHAR(30)   NULL,
    id_tipo     INT            NULL REFERENCES UsuarioTipo(id_tipo),
    activo      BIT            NOT NULL DEFAULT 1
);
GO

-- -------------------------------------------------------
-- 3. Tablas de inventario y movimientos
-- -------------------------------------------------------

-- Inventario (stock por pintura)
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Inventario')
CREATE TABLE Inventario (
    id_inventario  INT  IDENTITY(1,1) PRIMARY KEY,
    id_pintura     INT  NOT NULL REFERENCES Pinturas(id_pintura),
    cantidad       INT  NOT NULL DEFAULT 0
);
GO

-- -------------------------------------------------------
-- 4. Ventas
-- -------------------------------------------------------

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Ventas')
CREATE TABLE Ventas (
    id_venta    INT             IDENTITY(1,1) PRIMARY KEY,
    id_cliente  INT             NULL REFERENCES Clientes(id_cliente),
    id_vendedor INT             NULL REFERENCES Vendedores(id_vendedor),
    fecha       DATE            NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    total       DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    forma_pago  NVARCHAR(30)    NULL
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'DetalleVenta')
CREATE TABLE DetalleVenta (
    id_detalle  INT             IDENTITY(1,1) PRIMARY KEY,
    id_venta    INT             NOT NULL REFERENCES Ventas(id_venta),
    id_pintura  INT             NOT NULL REFERENCES Pinturas(id_pintura),
    cantidad    INT             NOT NULL DEFAULT 1,
    subtotal    DECIMAL(12, 2)  NOT NULL DEFAULT 0
);
GO

-- -------------------------------------------------------
-- 5. Cotizaciones
-- -------------------------------------------------------

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Cotizaciones')
CREATE TABLE Cotizaciones (
    id_cotizacion  INT             IDENTITY(1,1) PRIMARY KEY,
    id_cliente     INT             NULL REFERENCES Clientes(id_cliente),
    id_vendedor    INT             NULL REFERENCES Vendedores(id_vendedor),
    fecha          DATE            NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    subtotal       DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    iva            DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    total          DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    concretada     BIT             NOT NULL DEFAULT 0
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'DetalleCotizacion')
CREATE TABLE DetalleCotizacion (
    id_detalle       INT             IDENTITY(1,1) PRIMARY KEY,
    id_cotizacion    INT             NOT NULL REFERENCES Cotizaciones(id_cotizacion),
    id_pintura       INT             NOT NULL REFERENCES Pinturas(id_pintura),
    cantidad         INT             NOT NULL DEFAULT 1,
    precio_unitario  DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    subtotal         DECIMAL(12, 2)  NOT NULL DEFAULT 0
);
GO

-- -------------------------------------------------------
-- 6. Compras a proveedores
-- -------------------------------------------------------

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Compras')
CREATE TABLE Compras (
    id_compra    INT   IDENTITY(1,1) PRIMARY KEY,
    id_proveedor INT   NULL REFERENCES Proveedores(id_proveedor),
    fecha        DATE  NOT NULL DEFAULT CAST(GETDATE() AS DATE)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'DetalleCompra')
CREATE TABLE DetalleCompra (
    id_detalle  INT             IDENTITY(1,1) PRIMARY KEY,
    id_compra   INT             NOT NULL REFERENCES Compras(id_compra),
    id_pintura  INT             NOT NULL REFERENCES Pinturas(id_pintura),
    cantidad    INT             NOT NULL DEFAULT 1,
    precio      DECIMAL(12, 2)  NOT NULL DEFAULT 0
);
GO

-- -------------------------------------------------------
-- 7. Exhibiciones
-- -------------------------------------------------------

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'Exhibicion')
CREATE TABLE Exhibicion (
    id_exhibicion  INT            IDENTITY(1,1) PRIMARY KEY,
    nombre         NVARCHAR(200)  NOT NULL,
    fecha_inicio   DATE           NULL,
    fecha_fin      DATE           NULL,
    hora_inicio    TIME           NULL,
    hora_fin       TIME           NULL
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'DetalleExhibicion')
CREATE TABLE DetalleExhibicion (
    id_detalle     INT  IDENTITY(1,1) PRIMARY KEY,
    id_exhibicion  INT  NOT NULL REFERENCES Exhibicion(id_exhibicion),
    id_pintura     INT  NOT NULL REFERENCES Pinturas(id_pintura)
);
GO

-- -------------------------------------------------------
-- 8. Caja
-- -------------------------------------------------------

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'AperturaCaja')
CREATE TABLE AperturaCaja (
    id_apertura  INT             IDENTITY(1,1) PRIMARY KEY,
    id_vendedor  INT             NOT NULL REFERENCES Vendedores(id_vendedor),
    monto        DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    fecha        DATETIME        NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'CierreCaja')
CREATE TABLE CierreCaja (
    id_cierre      INT             IDENTITY(1,1) PRIMARY KEY,
    id_vendedor    INT             NOT NULL REFERENCES Vendedores(id_vendedor),
    fecha          DATETIME        NOT NULL DEFAULT GETDATE(),
    totalEfectivo  DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    totalVoucher   DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    montoTotal     DECIMAL(12, 2)  NOT NULL DEFAULT 0
);
GO

-- =============================================================
--  DATOS INICIALES (seed)
-- =============================================================

-- -------------------------------------------------------
-- Tipos de usuario
-- -------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM UsuarioTipo WHERE nombre = N'Administrador')
    INSERT INTO UsuarioTipo (nombre) VALUES (N'Administrador');

IF NOT EXISTS (SELECT 1 FROM UsuarioTipo WHERE nombre = N'Vendedor')
    INSERT INTO UsuarioTipo (nombre) VALUES (N'Vendedor');

IF NOT EXISTS (SELECT 1 FROM UsuarioTipo WHERE nombre = N'Cajero')
    INSERT INTO UsuarioTipo (nombre) VALUES (N'Cajero');
GO

-- -------------------------------------------------------
-- Usuario administrador
--   usuario:    admin
--   contraseña: admin123
-- -------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE usuario = N'admin')
    INSERT INTO Usuarios (nombre, usuario, [contraseña], email, telefono, id_tipo, activo)
    SELECT N'Administrador', N'admin', N'admin123',
           N'admin@galart.com', N'5500000000',
           id_tipo, 1
    FROM UsuarioTipo WHERE nombre = N'Administrador';
GO

-- -------------------------------------------------------
-- Técnicas de pintura
-- -------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM Tecnicas WHERE nombre = N'Óleo')
    INSERT INTO Tecnicas (nombre) VALUES (N'Óleo');

IF NOT EXISTS (SELECT 1 FROM Tecnicas WHERE nombre = N'Acuarela')
    INSERT INTO Tecnicas (nombre) VALUES (N'Acuarela');

IF NOT EXISTS (SELECT 1 FROM Tecnicas WHERE nombre = N'Acrílico')
    INSERT INTO Tecnicas (nombre) VALUES (N'Acrílico');

IF NOT EXISTS (SELECT 1 FROM Tecnicas WHERE nombre = N'Fresco')
    INSERT INTO Tecnicas (nombre) VALUES (N'Fresco');

IF NOT EXISTS (SELECT 1 FROM Tecnicas WHERE nombre = N'Gouache')
    INSERT INTO Tecnicas (nombre) VALUES (N'Gouache');
GO

-- -------------------------------------------------------
-- Artistas
-- -------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM Artistas WHERE nombre = N'Diego Rivera')
    INSERT INTO Artistas (nombre, biografia, pais)
    VALUES (
        N'Diego Rivera',
        N'Muralista mexicano reconocido por sus obras monumentales que retratan la historia y cultura de México.',
        N'México'
    );

IF NOT EXISTS (SELECT 1 FROM Artistas WHERE nombre = N'Frida Kahlo')
    INSERT INTO Artistas (nombre, biografia, pais)
    VALUES (
        N'Frida Kahlo',
        N'Pintora mexicana conocida por sus autorretratos cargados de simbolismo y exploración de la identidad.',
        N'México'
    );

IF NOT EXISTS (SELECT 1 FROM Artistas WHERE nombre = N'Rufino Tamayo')
    INSERT INTO Artistas (nombre, biografia, pais)
    VALUES (
        N'Rufino Tamayo',
        N'Pintor mexicano que fusionó el arte prehispánico con influencias modernas europeas.',
        N'México'
    );

IF NOT EXISTS (SELECT 1 FROM Artistas WHERE nombre = N'José Clemente Orozco')
    INSERT INTO Artistas (nombre, biografia, pais)
    VALUES (
        N'José Clemente Orozco',
        N'Muralista mexicano de estilo expresionista, conocido por sus representaciones dramáticas de la Revolución.',
        N'México'
    );

IF NOT EXISTS (SELECT 1 FROM Artistas WHERE nombre = N'David Alfaro Siqueiros')
    INSERT INTO Artistas (nombre, biografia, pais)
    VALUES (
        N'David Alfaro Siqueiros',
        N'Muralista mexicano y activista político, pionero en el uso de nuevos materiales en el arte.',
        N'México'
    );
GO

-- -------------------------------------------------------
-- Pinturas (con stock en Inventario)
-- -------------------------------------------------------

-- Usamos variables para obtener los IDs recién insertados
DECLARE @id_diego     INT = (SELECT id_artista FROM Artistas WHERE nombre = N'Diego Rivera');
DECLARE @id_frida     INT = (SELECT id_artista FROM Artistas WHERE nombre = N'Frida Kahlo');
DECLARE @id_tamayo    INT = (SELECT id_artista FROM Artistas WHERE nombre = N'Rufino Tamayo');
DECLARE @id_orozco    INT = (SELECT id_artista FROM Artistas WHERE nombre = N'José Clemente Orozco');
DECLARE @id_siqueiros INT = (SELECT id_artista FROM Artistas WHERE nombre = N'David Alfaro Siqueiros');

DECLARE @id_oleo      INT = (SELECT id_tecnica FROM Tecnicas WHERE nombre = N'Óleo');
DECLARE @id_acuarela  INT = (SELECT id_tecnica FROM Tecnicas WHERE nombre = N'Acuarela');
DECLARE @id_acrilico  INT = (SELECT id_tecnica FROM Tecnicas WHERE nombre = N'Acrílico');
DECLARE @id_fresco    INT = (SELECT id_tecnica FROM Tecnicas WHERE nombre = N'Fresco');

-- Diego Rivera
IF NOT EXISTS (SELECT 1 FROM Pinturas WHERE titulo = N'Sueño de una tarde dominical en la Alameda Central')
BEGIN
    INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica)
    VALUES (N'Sueño de una tarde dominical en la Alameda Central', 85000.00, @id_diego, @id_fresco);
    INSERT INTO Inventario (id_pintura, cantidad)
    VALUES (SCOPE_IDENTITY(), 2);
END

IF NOT EXISTS (SELECT 1 FROM Pinturas WHERE titulo = N'Vendedora de flores')
BEGIN
    INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica)
    VALUES (N'Vendedora de flores', 42000.00, @id_diego, @id_oleo);
    INSERT INTO Inventario (id_pintura, cantidad)
    VALUES (SCOPE_IDENTITY(), 3);
END

-- Frida Kahlo
IF NOT EXISTS (SELECT 1 FROM Pinturas WHERE titulo = N'Las dos Fridas')
BEGIN
    INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica)
    VALUES (N'Las dos Fridas', 120000.00, @id_frida, @id_oleo);
    INSERT INTO Inventario (id_pintura, cantidad)
    VALUES (SCOPE_IDENTITY(), 1);
END

IF NOT EXISTS (SELECT 1 FROM Pinturas WHERE titulo = N'Autorretrato con collar de espinas')
BEGIN
    INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica)
    VALUES (N'Autorretrato con collar de espinas', 95000.00, @id_frida, @id_oleo);
    INSERT INTO Inventario (id_pintura, cantidad)
    VALUES (SCOPE_IDENTITY(), 1);
END

-- Rufino Tamayo
IF NOT EXISTS (SELECT 1 FROM Pinturas WHERE titulo = N'Perro aullando a la luna')
BEGIN
    INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica)
    VALUES (N'Perro aullando a la luna', 38000.00, @id_tamayo, @id_acrilico);
    INSERT INTO Inventario (id_pintura, cantidad)
    VALUES (SCOPE_IDENTITY(), 4);
END

IF NOT EXISTS (SELECT 1 FROM Pinturas WHERE titulo = N'Sandías')
BEGIN
    INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica)
    VALUES (N'Sandías', 27500.00, @id_tamayo, @id_acuarela);
    INSERT INTO Inventario (id_pintura, cantidad)
    VALUES (SCOPE_IDENTITY(), 5);
END

-- José Clemente Orozco
IF NOT EXISTS (SELECT 1 FROM Pinturas WHERE titulo = N'El hombre de fuego')
BEGIN
    INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica)
    VALUES (N'El hombre de fuego', 55000.00, @id_orozco, @id_fresco);
    INSERT INTO Inventario (id_pintura, cantidad)
    VALUES (SCOPE_IDENTITY(), 2);
END

-- David Alfaro Siqueiros
IF NOT EXISTS (SELECT 1 FROM Pinturas WHERE titulo = N'Nuestra imagen actual')
BEGIN
    INSERT INTO Pinturas (titulo, precio, id_artista, id_tecnica)
    VALUES (N'Nuestra imagen actual', 47000.00, @id_siqueiros, @id_acrilico);
    INSERT INTO Inventario (id_pintura, cantidad)
    VALUES (SCOPE_IDENTITY(), 3);
END
GO

-- -------------------------------------------------------
-- Vendedor de prueba (para probar caja y ventas)
-- -------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM Vendedores WHERE nombre = N'Vendedor Demo')
    INSERT INTO Vendedores (nombre, correo, telefono, activo)
    VALUES (N'Vendedor Demo', N'vendedor@galart.com', N'5511111111', 1);
GO

-- -------------------------------------------------------
-- Verificación rápida
-- -------------------------------------------------------
SELECT 'UsuarioTipo' AS tabla, COUNT(*) AS registros FROM UsuarioTipo
UNION ALL SELECT 'Usuarios',   COUNT(*) FROM Usuarios
UNION ALL SELECT 'Artistas',   COUNT(*) FROM Artistas
UNION ALL SELECT 'Tecnicas',   COUNT(*) FROM Tecnicas
UNION ALL SELECT 'Pinturas',   COUNT(*) FROM Pinturas
UNION ALL SELECT 'Inventario', COUNT(*) FROM Inventario
UNION ALL SELECT 'Vendedores', COUNT(*) FROM Vendedores;
GO
