-- ============================================================================
-- Proyecto BI "Las Salsas de Lucho"
-- 01 - ESQUEMA OPERACIONAL (fuente transaccional de origen)  -- PostgreSQL
-- ----------------------------------------------------------------------------
-- Replica la base transaccional real de la PYME. Es la FUENTE del proceso ETL.
-- Ejecutar en la base de datos: salsas_op
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS op;
SET search_path TO op;

DROP TABLE IF EXISTS op.detalle_ventas        CASCADE;
DROP TABLE IF EXISTS op.ventas                CASCADE;
DROP TABLE IF EXISTS op.movimientos_inventario CASCADE;
DROP TABLE IF EXISTS op.productos             CASCADE;
DROP TABLE IF EXISTS op.categorias            CASCADE;
DROP TABLE IF EXISTS op.clientes              CASCADE;
DROP TABLE IF EXISTS op.canales               CASCADE;
DROP TABLE IF EXISTS op.vendedores            CASCADE;
DROP TABLE IF EXISTS op.promociones           CASCADE;

CREATE TABLE op.categorias (
    id_categoria      INTEGER PRIMARY KEY,
    nombre_categoria  VARCHAR(60) NOT NULL
);

CREATE TABLE op.productos (
    id_producto       INTEGER PRIMARY KEY,
    nombre_producto   VARCHAR(120) NOT NULL,
    id_categoria      INTEGER REFERENCES op.categorias(id_categoria),
    presentacion_ml   INTEGER,
    precio_lista      NUMERIC(12,2),
    costo_unitario    NUMERIC(12,2),
    es_estrella       SMALLINT
);

CREATE TABLE op.canales (
    id_canal          INTEGER PRIMARY KEY,
    nombre_canal      VARCHAR(60) NOT NULL
);

CREATE TABLE op.vendedores (
    id_vendedor       INTEGER PRIMARY KEY,
    nombre_vendedor   VARCHAR(120) NOT NULL,
    puesto            VARCHAR(60)
);

CREATE TABLE op.promociones (
    id_promocion      INTEGER PRIMARY KEY,
    nombre_promocion  VARCHAR(60) NOT NULL,
    descuento_pct     NUMERIC(5,2)
);

CREATE TABLE op.clientes (
    id_cliente        INTEGER PRIMARY KEY,
    nombre_cliente    VARCHAR(120),
    tipo_cliente      VARCHAR(30),
    provincia         VARCHAR(60),      -- texto SUCIO (variantes a homologar)
    fecha_registro    VARCHAR(20),      -- puede venir NULA/vacia
    segmento_origen   VARCHAR(40)
);

CREATE TABLE op.ventas (
    id_venta          INTEGER PRIMARY KEY,
    fecha_venta       DATE,
    id_cliente        INTEGER,          -- puede apuntar a cliente inexistente (FK rota)
    id_canal          INTEGER,
    canal_texto       VARCHAR(60),      -- texto SUCIO / nulo
    id_vendedor       INTEGER REFERENCES op.vendedores(id_vendedor),
    id_promocion      INTEGER REFERENCES op.promociones(id_promocion),
    total_factura     NUMERIC(14,2)
);

CREATE TABLE op.detalle_ventas (
    id_linea               INTEGER PRIMARY KEY,
    id_venta               INTEGER REFERENCES op.ventas(id_venta),
    id_producto            INTEGER,
    nombre_producto_texto  VARCHAR(120), -- texto SUCIO a homologar
    cantidad               NUMERIC(12,2),-- puede ser 0/negativa/atipica
    precio_unitario        NUMERIC(12,2),
    monto_bruto            NUMERIC(14,2),
    descuento              NUMERIC(14,2),
    costo_unitario         NUMERIC(12,2) -- puede venir nulo
);

CREATE TABLE op.movimientos_inventario (
    id_mov               INTEGER PRIMARY KEY,
    id_producto          INTEGER REFERENCES op.productos(id_producto),
    fecha_corte          DATE,
    existencia_inicial   INTEGER,
    entradas             INTEGER,
    salidas              INTEGER,
    existencia_final     INTEGER,
    costo_inventario     NUMERIC(14,2)
);

CREATE INDEX IF NOT EXISTS ix_ventas_fecha   ON op.ventas(fecha_venta);
CREATE INDEX IF NOT EXISTS ix_detalle_venta  ON op.detalle_ventas(id_venta);
CREATE INDEX IF NOT EXISTS ix_detalle_prod   ON op.detalle_ventas(id_producto);
