# -*- coding: utf-8 -*-
"""Genera los diagramas del modelo operacional y dimensional (graphviz)."""
import os
from graphviz import Digraph
HERE=os.path.dirname(os.path.abspath(__file__))
OUT="/tmp/diag"; os.makedirs(OUT,exist_ok=True)

# ---------------- MODELO OPERACIONAL (transaccional) ----------------
op=Digraph("operacional", format="png")
op.attr(rankdir="LR", bgcolor="white", fontname="Helvetica")
op.attr("node", shape="record", style="filled", fillcolor="#FDEBD0",
        color="#B9770E", fontname="Helvetica", fontsize="10")

tablas={
 "categorias":"categorias|id_categoria (PK)\\lnombre_categoria\\l",
 "productos":"productos|id_producto (PK)\\lnombre_producto\\lid_categoria (FK)\\lpresentacion_ml\\lprecio_lista\\lcosto_unitario\\les_estrella\\l",
 "clientes":"clientes|id_cliente (PK)\\lnombre_cliente\\ltipo_cliente\\lprovincia\\lfecha_registro\\lsegmento_origen\\l",
 "canales":"canales|id_canal (PK)\\lnombre_canal\\l",
 "vendedores":"vendedores|id_vendedor (PK)\\lnombre_vendedor\\lpuesto\\l",
 "promociones":"promociones|id_promocion (PK)\\lnombre_promocion\\ldescuento_pct\\l",
 "ventas":"ventas|id_venta (PK)\\lfecha_venta\\lid_cliente (FK)\\lid_canal (FK)\\lid_vendedor (FK)\\lid_promocion (FK)\\ltotal_factura\\l",
 "detalle_ventas":"detalle_ventas|id_linea (PK)\\lid_venta (FK)\\lid_producto (FK)\\lcantidad\\lprecio_unitario\\lmonto_bruto\\ldescuento\\lcosto_unitario\\l",
 "movimientos_inventario":"movimientos_inventario|id_mov (PK)\\lid_producto (FK)\\lfecha_corte\\lexistencia_inicial\\lentradas\\lsalidas\\lexistencia_final\\lcosto_inventario\\l",
}
for k,v in tablas.items(): op.node(k,v)
op.edge("ventas","clientes"); op.edge("ventas","canales"); op.edge("ventas","vendedores")
op.edge("ventas","promociones"); op.edge("detalle_ventas","ventas")
op.edge("detalle_ventas","productos"); op.edge("productos","categorias")
op.edge("movimientos_inventario","productos")
op.render(os.path.join(OUT,"modelo_operacional"), cleanup=False)
print("modelo_operacional.png OK")

# ---------------- MODELO DIMENSIONAL (estrella / constelacion) ----------------
dm=Digraph("dimensional", format="png")
dm.attr(rankdir="LR", bgcolor="white", fontname="Helvetica", nodesep="0.5", ranksep="1.0")
dm.attr("node", shape="record", fontname="Helvetica", fontsize="10")

def dim(name,label): dm.node(name,label,style="filled",fillcolor="#D6EAF8",color="#2471A3")
def fact(name,label): dm.node(name,label,style="filled",fillcolor="#FADBD8",color="#C0392B")

dim("dim_tiempo","dim_tiempo (conformada)|sk_tiempo (PK)\\lfecha, anio, semestre\\ltrimestre, mes, nombre_mes\\lsemana_anio, dia\\les_fin_semana, temporada\\l")
dim("dim_producto","dim_producto (conformada)|sk_producto (PK)\\lid_producto (BK)\\lnombre_producto, categoria\\lpresentacion_ml, rango_precio\\les_estrella\\lprecio_lista, costo_unitario\\l")
dim("dim_cliente","dim_cliente|sk_cliente (PK)\\lid_cliente (BK)\\lnombre, tipo_cliente\\lprovincia, region\\lantiguedad_meses\\lsegmento_cliente\\l")
dim("dim_canal","dim_canal|sk_canal (PK)\\lid_canal (BK)\\lnombre_canal\\ltipo_canal\\l")
dim("dim_vendedor","dim_vendedor|sk_vendedor (PK)\\lid_vendedor (BK)\\lnombre_vendedor, puesto\\l")
dim("dim_promocion","dim_promocion|sk_promocion (PK)\\lid_promocion (BK)\\lnombre_promocion\\ldescuento_pct, aplica_promo\\l")

fact("fact_ventas","fact_ventas|sk_venta_linea (PK)|FK: sk_tiempo, sk_producto,\\lsk_cliente, sk_canal,\\lsk_vendedor, sk_promocion\\lid_venta (DD)|--- MEDIDAS ---\\lcantidad, precio_unitario\\lmonto_bruto, descuento_monto\\lmonto_neto, costo_total\\lmargen_bruto\\l")
fact("fact_inventario","fact_inventario|sk_inventario (PK)|FK: sk_tiempo, sk_producto|--- MEDIDAS ---\\lexistencia_inicial, entradas\\lsalidas, existencia_final\\lcosto_inventario\\lrotacion_mes, dias_inventario\\l")

for d in ["dim_tiempo","dim_producto","dim_cliente","dim_canal","dim_vendedor","dim_promocion"]:
    dm.edge("fact_ventas",d)
dm.edge("fact_inventario","dim_tiempo"); dm.edge("fact_inventario","dim_producto")
dm.render(os.path.join(OUT,"modelo_dimensional"), cleanup=False)
print("modelo_dimensional.png OK")
