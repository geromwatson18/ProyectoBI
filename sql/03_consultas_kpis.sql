-- ============================================================================
-- Proyecto BI "Las Salsas de Lucho" - 03 CONSULTAS ANALITICAS (KPIs)
-- Responden las 5 preguntas de negocio. Ejecutar en la base dimensional (dw).
-- Sintaxis PostgreSQL.
-- ============================================================================
SET search_path TO dw;

-- KPIs globales -------------------------------------------------------------
SELECT
  SUM(monto_neto)                              AS ingreso_neto,
  SUM(monto_bruto)                             AS ingreso_bruto,
  SUM(descuento_monto)                         AS descuentos,
  SUM(costo_total)                             AS costo_ventas,
  SUM(margen_bruto)                            AS margen_bruto,
  ROUND(100.0*SUM(margen_bruto)/SUM(monto_neto),1) AS margen_pct,
  SUM(cantidad)                                AS unidades,
  COUNT(DISTINCT id_venta)                     AS facturas,
  ROUND(SUM(monto_neto)/COUNT(DISTINCT id_venta),0) AS ticket_promedio
FROM fact_ventas;

-- PN1: mix de producto y baja rotacion (Pareto) -----------------------------
SELECT p.nombre_producto, p.es_estrella,
       SUM(f.monto_neto)  AS ingreso,
       SUM(f.cantidad)    AS unidades,
       SUM(f.margen_bruto) AS margen,
       ROUND(100.0*SUM(f.monto_neto)/SUM(SUM(f.monto_neto)) OVER (),1) AS pct_ingreso
FROM fact_ventas f JOIN dim_producto p ON f.sk_producto=p.sk_producto
GROUP BY p.nombre_producto, p.es_estrella
ORDER BY ingreso DESC;

-- PN2: rentabilidad por canal y evolucion mensual ---------------------------
SELECT c.nombre_canal,
       SUM(f.monto_neto) AS ingreso,
       SUM(f.margen_bruto) AS margen,
       ROUND(100.0*SUM(f.margen_bruto)/SUM(f.monto_neto),1) AS margen_pct
FROM fact_ventas f JOIN dim_canal c ON f.sk_canal=c.sk_canal
GROUP BY c.nombre_canal ORDER BY ingreso DESC;

SELECT t.anio, t.mes, c.nombre_canal, SUM(f.monto_neto) AS ingreso
FROM fact_ventas f
JOIN dim_tiempo t ON f.sk_tiempo=t.sk_tiempo
JOIN dim_canal  c ON f.sk_canal=c.sk_canal
GROUP BY t.anio, t.mes, c.nombre_canal
ORDER BY t.anio, t.mes;

-- PN3: estacionalidad (promedio diario por mes para comparar de forma justa) -
SELECT t.anio, t.mes, t.nombre_mes,
       SUM(f.monto_neto)                                  AS ingreso_mes,
       ROUND(SUM(f.monto_neto)/COUNT(DISTINCT t.fecha),0) AS ingreso_prom_dia
FROM fact_ventas f JOIN dim_tiempo t ON f.sk_tiempo=t.sk_tiempo
GROUP BY t.anio, t.mes, t.nombre_mes
ORDER BY t.anio, t.mes;

-- PN4: impacto de promociones sobre volumen y margen ------------------------
SELECT pm.nombre_promocion, pm.aplica_promo,
       COUNT(*)            AS lineas,
       SUM(f.cantidad)     AS unidades,
       SUM(f.monto_neto)   AS ingreso,
       ROUND(100.0*SUM(f.descuento_monto)/NULLIF(SUM(f.monto_bruto),0),1) AS tasa_descuento,
       ROUND(100.0*SUM(f.margen_bruto)/SUM(f.monto_neto),1) AS margen_pct
FROM fact_ventas f JOIN dim_promocion pm ON f.sk_promocion=pm.sk_promocion
GROUP BY pm.nombre_promocion, pm.aplica_promo
ORDER BY ingreso DESC;

-- PN5 (exploratoria): concentracion de clientes y geografia -----------------
SELECT cl.nombre_cliente, cl.tipo_cliente, cl.provincia,
       SUM(f.monto_neto) AS ingreso,
       ROUND(100.0*SUM(f.monto_neto)/SUM(SUM(f.monto_neto)) OVER (),2) AS pct
FROM fact_ventas f JOIN dim_cliente cl ON f.sk_cliente=cl.sk_cliente
GROUP BY cl.nombre_cliente, cl.tipo_cliente, cl.provincia
ORDER BY ingreso DESC LIMIT 15;

-- Rotacion de inventario por producto ---------------------------------------
SELECT p.nombre_producto, p.es_estrella,
       ROUND(AVG(fi.rotacion_mes),2)   AS rotacion_prom,
       ROUND(AVG(fi.dias_inventario),0) AS dias_inventario,
       ROUND(AVG(fi.existencia_final),0) AS stock_prom
FROM fact_inventario fi JOIN dim_producto p ON fi.sk_producto=p.sk_producto
GROUP BY p.nombre_producto, p.es_estrella
ORDER BY rotacion_prom DESC;
