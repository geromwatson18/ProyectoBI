# Diccionario de datos — Modelo dimensional `dw`
Proyecto BI · Las Salsas de Lucho

Convenciones: **PK** llave primaria · **FK** llave foránea · **BK** llave de negocio · **DD** dimensión degenerada · SK = llave subrogada.

## Dimensión `dim_tiempo` (conformada)
Granularidad: un día. Cubre 2024-01-01 a 2025-12-31.

| Columna | Tipo | Descripción |
|---|---|---|
| sk_tiempo | INTEGER (PK) | Llave subrogada con formato AAAAMMDD. |
| fecha | DATE | Fecha calendario. |
| anio | INTEGER | Año (2024, 2025). |
| semestre | INTEGER | 1 o 2. |
| trimestre | INTEGER | 1 a 4. |
| mes | INTEGER | 1 a 12. |
| nombre_mes | VARCHAR | Nombre del mes en español. |
| semana_anio | INTEGER | Semana ISO del año. |
| dia | INTEGER | Día del mes. |
| dia_semana | INTEGER | 1=Lunes … 7=Domingo. |
| nombre_dia | VARCHAR | Nombre del día. |
| es_fin_semana | BOOLEAN | Verdadero para sábado/domingo. |
| temporada | VARCHAR | Alta (nov–dic), Media (abr, jul), Baja (resto). |

## Dimensión `dim_producto` (conformada)
| Columna | Tipo | Descripción |
|---|---|---|
| sk_producto | SERIAL (PK) | Llave subrogada. |
| id_producto | INTEGER (BK) | Código del producto en el sistema operacional. |
| nombre_producto | VARCHAR | Nombre homologado del producto. |
| categoria | VARCHAR | Picantes / Aderezos / Especialidad Gourmet. |
| presentacion_ml | INTEGER | Tamaño del envase (200 ml, uniforme para todas las salsas). |
| rango_precio | VARCHAR | Rango de precio derivado; con precio uniforme de ₡3.000 todas caen en "Medio". |
| es_estrella | BOOLEAN | Producto de alta rotación (las 3 salsas insignia). |
| precio_lista | NUMERIC | Precio de venta de lista (₡3.000, uniforme para todas las salsas). |
| costo_unitario | NUMERIC | Costo unitario de producción. |

## Dimensión `dim_cliente`
| Columna | Tipo | Descripción |
|---|---|---|
| sk_cliente | SERIAL (PK) | Llave subrogada. Incluye miembro -1 "No identificado". |
| id_cliente | INTEGER (BK) | Código del cliente (-1 = inferido). |
| nombre_cliente | VARCHAR | Nombre/razón social. |
| tipo_cliente | VARCHAR | Minorista / Mayorista / No identificado. |
| provincia | VARCHAR | Provincia homologada (7 provincias de CR). |
| region | VARCHAR | GAM / Costera / Otra. |
| antiguedad_meses | INTEGER | Meses desde el registro (nulos imputados por mediana). |
| segmento_cliente | VARCHAR | Nuevo / Recurrente / Frecuente / Inactivo (RFM simplificado). |

## Dimensión `dim_canal`
| Columna | Tipo | Descripción |
|---|---|---|
| sk_canal | SERIAL (PK) | Llave subrogada. Incluye miembro "No identificado". |
| id_canal | INTEGER (BK) | Código de canal. |
| nombre_canal | VARCHAR | Tienda física / Feria del agricultor / Mayoreo / En línea. |
| tipo_canal | VARCHAR | Directo / Indirecto / Digital. |

## Dimensión `dim_vendedor`
| Columna | Tipo | Descripción |
|---|---|---|
| sk_vendedor | SERIAL (PK) | Llave subrogada. |
| id_vendedor | INTEGER (BK) | Código del vendedor. |
| nombre_vendedor | VARCHAR | Nombre del colaborador. |
| puesto | VARCHAR | Rol (Propietario, Ventas, Ferias). |

## Dimensión `dim_promocion`
| Columna | Tipo | Descripción |
|---|---|---|
| sk_promocion | SERIAL (PK) | Llave subrogada. |
| id_promocion | INTEGER (BK) | Código de promoción. |
| nombre_promocion | VARCHAR | Tipo de promoción aplicada. |
| descuento_pct | NUMERIC | Porcentaje de descuento asociado. |
| aplica_promo | BOOLEAN | Falso para "Sin promoción". |

## Hecho `fact_ventas`
Granularidad: **una línea de detalle de factura** (un producto dentro de una venta).

| Columna | Tipo | Descripción |
|---|---|---|
| sk_venta_linea | BIGSERIAL (PK) | Llave subrogada de la línea. |
| sk_tiempo | INTEGER (FK) | → dim_tiempo. |
| sk_producto | INTEGER (FK) | → dim_producto. |
| sk_cliente | INTEGER (FK) | → dim_cliente. |
| sk_canal | INTEGER (FK) | → dim_canal. |
| sk_vendedor | INTEGER (FK) | → dim_vendedor. |
| sk_promocion | INTEGER (FK) | → dim_promocion. |
| id_venta | INTEGER (DD) | Número de factura (dimensión degenerada). |
| cantidad | NUMERIC | Unidades vendidas (medida aditiva). |
| precio_unitario | NUMERIC | Precio unitario aplicado. |
| monto_bruto | NUMERIC | precio_unitario × cantidad. |
| descuento_monto | NUMERIC | Descuento en colones. |
| monto_neto | NUMERIC | monto_bruto − descuento_monto. |
| costo_total | NUMERIC | costo_unitario × cantidad. |
| margen_bruto | NUMERIC | monto_neto − costo_total. |

## Hecho `fact_inventario`
Granularidad: **snapshot mensual por producto**.

| Columna | Tipo | Descripción |
|---|---|---|
| sk_inventario | BIGSERIAL (PK) | Llave subrogada. |
| sk_tiempo | INTEGER (FK) | → dim_tiempo (primer día del mes de corte). |
| sk_producto | INTEGER (FK) | → dim_producto. |
| existencia_inicial | INTEGER | Stock al inicio del mes (semi-aditiva). |
| entradas | INTEGER | Unidades producidas/ingresadas. |
| salidas | INTEGER | Unidades despachadas. |
| existencia_final | INTEGER | Stock al cierre (semi-aditiva). |
| costo_inventario | NUMERIC | Valor del inventario al costo. |
| rotacion_mes | NUMERIC | salidas / existencia promedio. |
| dias_inventario | NUMERIC | 30 / rotacion_mes. |

## Catálogo de medidas / KPIs (≥ 12)
| # | Medida | Definición |
|---|---|---|
| 1 | Unidades vendidas | SUM(cantidad) |
| 2 | Ingreso bruto | SUM(monto_bruto) |
| 3 | Descuentos | SUM(descuento_monto) |
| 4 | Ingreso neto | SUM(monto_neto) |
| 5 | Costo de ventas | SUM(costo_total) |
| 6 | Margen bruto (₡) | SUM(margen_bruto) |
| 7 | Margen bruto (%) | SUM(margen_bruto)/SUM(monto_neto) |
| 8 | Número de facturas | COUNT(DISTINCT id_venta) |
| 9 | Ticket promedio | SUM(monto_neto)/facturas |
| 10 | Precio promedio de venta | SUM(monto_bruto)/SUM(cantidad) |
| 11 | Unidades por factura | SUM(cantidad)/facturas |
| 12 | Tasa de descuento (%) | SUM(descuento_monto)/SUM(monto_bruto) |
| 13 | Participación de producto (%) | ingreso del producto / ingreso total |
| 14 | Clientes activos | COUNT(DISTINCT sk_cliente) |
| 15 | Rotación de inventario | AVG(rotacion_mes) |
| 16 | Días de inventario | AVG(dias_inventario) |
| 17 | Valor de inventario | SUM(costo_inventario) |
