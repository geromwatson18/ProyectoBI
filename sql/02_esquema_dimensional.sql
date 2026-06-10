-- ============================================================================
-- Proyecto BI "Las Salsas de Lucho"
-- 02 - ESQUEMA DIMENSIONAL (modelo estrella, constelacion de 2 hechos) PostgreSQL
-- ----------------------------------------------------------------------------
-- Almacen analitico. Ejecutar en la base de datos: salsas_dw
-- Dimensiones conformadas: dim_tiempo y dim_producto se comparten entre los
-- dos hechos (fact_ventas y fact_inventario).
-- Todas las dimensiones usan LLAVE SUBROGADA (sk_*) independiente de la llave
-- de negocio. Se incluyen miembros "No identificado" (inferred members).
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS dw;
SET search_path TO dw;

DROP TABLE IF EXISTS dw.fact_ventas       CASCADE;
DROP TABLE IF EXISTS dw.fact_inventario   CASCADE;
DROP TABLE IF EXISTS dw.dim_tiempo        CASCADE;
DROP TABLE IF EXISTS dw.dim_producto      CASCADE;
DROP TABLE IF EXISTS dw.dim_cliente       CASCADE;
DROP TABLE IF EXISTS dw.dim_canal         CASCADE;
DROP TABLE IF EXISTS dw.dim_vendedor      CASCADE;
DROP TABLE IF EXISTS dw.dim_promocion     CASCADE;

-- ----------------------------- DIMENSIONES ---------------------------------
CREATE TABLE dw.dim_tiempo (
    sk_tiempo        INTEGER PRIMARY KEY,   -- AAAAMMDD
    fecha            DATE NOT NULL,
    anio             INTEGER,
    semestre         INTEGER,
    trimestre        INTEGER,
    mes              INTEGER,
    nombre_mes       VARCHAR(12),
    semana_anio      INTEGER,
    dia              INTEGER,
    dia_semana       INTEGER,
    nombre_dia       VARCHAR(12),
    es_fin_semana    BOOLEAN,
    temporada        VARCHAR(20)            -- Alta / Media / Baja
);

CREATE TABLE dw.dim_producto (
    sk_producto      SERIAL PRIMARY KEY,    -- llave subrogada
    id_producto      INTEGER,               -- llave de negocio
    nombre_producto  VARCHAR(120),
    categoria        VARCHAR(60),
    presentacion_ml  INTEGER,
    rango_precio     VARCHAR(20),           -- Economico / Medio / Premium
    es_estrella      BOOLEAN,
    precio_lista     NUMERIC(12,2),
    costo_unitario   NUMERIC(12,2)
);

CREATE TABLE dw.dim_cliente (
    sk_cliente       SERIAL PRIMARY KEY,
    id_cliente       INTEGER,
    nombre_cliente   VARCHAR(120),
    tipo_cliente     VARCHAR(30),           -- Minorista / Mayorista
    provincia        VARCHAR(60),           -- homologada
    region           VARCHAR(30),           -- GAM / Costera / Otra
    antiguedad_meses INTEGER,
    segmento_cliente VARCHAR(30)            -- Nuevo / Recurrente / Frecuente / Inactivo
);

CREATE TABLE dw.dim_canal (
    sk_canal         SERIAL PRIMARY KEY,
    id_canal         INTEGER,
    nombre_canal     VARCHAR(60),           -- homologado
    tipo_canal       VARCHAR(30)            -- Directo / Indirecto / Digital
);

CREATE TABLE dw.dim_vendedor (
    sk_vendedor      SERIAL PRIMARY KEY,
    id_vendedor      INTEGER,
    nombre_vendedor  VARCHAR(120),
    puesto           VARCHAR(60)
);

CREATE TABLE dw.dim_promocion (
    sk_promocion     SERIAL PRIMARY KEY,
    id_promocion     INTEGER,
    nombre_promocion VARCHAR(60),
    descuento_pct    NUMERIC(5,2),
    aplica_promo     BOOLEAN
);

-- ------------------------------- HECHOS ------------------------------------
-- Grano: una linea de detalle de factura (producto x venta).
CREATE TABLE dw.fact_ventas (
    sk_venta_linea   BIGSERIAL PRIMARY KEY,
    sk_tiempo        INTEGER REFERENCES dw.dim_tiempo(sk_tiempo),
    sk_producto      INTEGER REFERENCES dw.dim_producto(sk_producto),
    sk_cliente       INTEGER REFERENCES dw.dim_cliente(sk_cliente),
    sk_canal         INTEGER REFERENCES dw.dim_canal(sk_canal),
    sk_vendedor      INTEGER REFERENCES dw.dim_vendedor(sk_vendedor),
    sk_promocion     INTEGER REFERENCES dw.dim_promocion(sk_promocion),
    id_venta         INTEGER,               -- degenerate dimension (num. factura)
    cantidad         NUMERIC(12,2),
    precio_unitario  NUMERIC(12,2),
    monto_bruto      NUMERIC(14,2),
    descuento_monto  NUMERIC(14,2),
    monto_neto       NUMERIC(14,2),
    costo_total      NUMERIC(14,2),
    margen_bruto     NUMERIC(14,2)
);

-- Grano: snapshot mensual de inventario por producto.
CREATE TABLE dw.fact_inventario (
    sk_inventario       BIGSERIAL PRIMARY KEY,
    sk_tiempo           INTEGER REFERENCES dw.dim_tiempo(sk_tiempo),
    sk_producto         INTEGER REFERENCES dw.dim_producto(sk_producto),
    existencia_inicial  INTEGER,
    entradas            INTEGER,
    salidas             INTEGER,
    existencia_final    INTEGER,
    costo_inventario    NUMERIC(14,2),
    rotacion_mes        NUMERIC(10,4),      -- salidas / existencia promedio
    dias_inventario     NUMERIC(10,2)       -- 30 / rotacion
);

CREATE INDEX IF NOT EXISTS ix_fv_tiempo   ON dw.fact_ventas(sk_tiempo);
CREATE INDEX IF NOT EXISTS ix_fv_producto ON dw.fact_ventas(sk_producto);
CREATE INDEX IF NOT EXISTS ix_fv_cliente  ON dw.fact_ventas(sk_cliente);
CREATE INDEX IF NOT EXISTS ix_fi_tiempo   ON dw.fact_inventario(sk_tiempo);
CREATE INDEX IF NOT EXISTS ix_fi_producto ON dw.fact_inventario(sk_producto);
