# -*- coding: utf-8 -*-
"""Genera los graficos analiticos del informe a partir del DWH."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","etl"))
os.environ.setdefault("BI_BACKEND","sqlite")
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from utils import get_engine

OUT=os.getenv("CHARTS_OUT","/tmp/charts"); os.makedirs(OUT,exist_ok=True)
dw=get_engine("dw")
def q(s): return pd.read_sql(s,dw)
col = lambda x,_: f"₡{x/1e6:.1f}M"
AZUL="#2471A3"; ROJO="#C0392B"; NAR="#E67E22"; VERDE="#229954"; GRIS="#85929E"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.grid":True,
                     "grid.alpha":0.3,"axes.spines.top":False,"axes.spines.right":False})

# 1 - Pareto de productos
p=q("""SELECT pr.nombre_producto n, pr.es_estrella e, SUM(f.monto_neto) ing
 FROM fact_ventas f JOIN dim_producto pr ON f.sk_producto=pr.sk_producto
 GROUP BY pr.nombre_producto,pr.es_estrella ORDER BY ing DESC""")
p["acum"]=100*p.ing.cumsum()/p.ing.sum()
fig,ax=plt.subplots(figsize=(9,4.5))
colores=[ROJO if e==1 else GRIS for e in p.e]
ax.bar(range(len(p)),p.ing,color=colores)
ax.set_xticks(range(len(p))); ax.set_xticklabels(p.n,rotation=40,ha="right",fontsize=8)
ax.yaxis.set_major_formatter(FuncFormatter(col)); ax.set_ylabel("Ingreso neto")
ax2=ax.twinx(); ax2.plot(range(len(p)),p.acum,color=AZUL,marker="o",lw=2)
ax2.set_ylabel("% acumulado",color=AZUL); ax2.set_ylim(0,105); ax2.grid(False)
ax2.axhline(80,ls="--",color=AZUL,alpha=.5)
ax.set_title("PN1 · Pareto de productos: las 3 salsas estrella concentran ~85% del ingreso")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=ROJO,label="Estrella"),Patch(color=GRIS,label="Baja rotación")],
          loc="center right",frameon=False)
plt.tight_layout(); plt.savefig(f"{OUT}/01_pareto_productos.png",dpi=130); plt.close()

# 2 - Canal: ingreso y margen
c=q("""SELECT c.nombre_canal n, SUM(f.monto_neto) ing,
 100.0*SUM(f.margen_bruto)/SUM(f.monto_neto) mg
 FROM fact_ventas f JOIN dim_canal c ON f.sk_canal=c.sk_canal
 GROUP BY c.nombre_canal ORDER BY ing DESC""")
fig,ax=plt.subplots(figsize=(8,4.2))
b=ax.bar(c.n,c.ing,color=[AZUL,NAR,VERDE,GRIS])
ax.yaxis.set_major_formatter(FuncFormatter(col)); ax.set_ylabel("Ingreso neto")
for i,(v,m) in enumerate(zip(c.ing,c.mg)):
    ax.text(i,v,f"  margen {m:.0f}%",ha="center",va="bottom",fontsize=9)
ax.set_title("PN2 · Ingreso por canal — el Mayoreo (~80 puntos de venta) aporta ~91% del ingreso")
plt.tight_layout(); plt.savefig(f"{OUT}/02_canal.png",dpi=130); plt.close()

# 3 - Estacionalidad mensual (ingreso promedio diario)
s=q("""SELECT t.anio a, t.mes m, SUM(f.monto_neto) ing, COUNT(DISTINCT t.fecha) d
 FROM fact_ventas f JOIN dim_tiempo t ON f.sk_tiempo=t.sk_tiempo
 GROUP BY t.anio,t.mes ORDER BY t.anio,t.mes""")
s["prom_dia"]=s.ing/s.d; s["lbl"]=s.a.astype(str).str[2:]+"-"+s.m.astype(str).str.zfill(2)
fig,ax=plt.subplots(figsize=(10,4.2))
ax.plot(s.lbl,s.prom_dia,color=AZUL,marker="o",lw=2)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f"₡{x/1e3:.0f}K"))
ax.set_ylabel("Ingreso promedio diario"); ax.set_xlabel("Año-Mes")
for i,r in s.iterrows():
    if r.m in (11,12): ax.axvspan(i-0.5,i+0.5,color=ROJO,alpha=0.10)
ax.set_xticklabels(s.lbl,rotation=45,ha="right",fontsize=8)
ax.set_title("PN3 · Estacionalidad: picos en nov–dic (sombreado) y mitad de año")
plt.tight_layout(); plt.savefig(f"{OUT}/03_estacionalidad.png",dpi=130); plt.close()

# 4 - Promociones
pr=q("""SELECT pm.nombre_promocion n, SUM(f.monto_neto) ing,
 100.0*SUM(f.margen_bruto)/SUM(f.monto_neto) mg
 FROM fact_ventas f JOIN dim_promocion pm ON f.sk_promocion=pm.sk_promocion
 GROUP BY pm.nombre_promocion ORDER BY ing DESC""")
fig,ax=plt.subplots(figsize=(8.5,4.2))
ax.barh(pr.n,pr.mg,color=[VERDE if m>=60 else (NAR if m>=56 else ROJO) for m in pr.mg])
ax.set_xlabel("Margen neto (%)"); ax.invert_yaxis()
for i,m in enumerate(pr.mg): ax.text(m,i,f" {m:.1f}%",va="center",fontsize=9)
ax.set_title("PN4 · Margen por tipo de promoción — 'Liquidación lenta' erosiona el margen")
plt.tight_layout(); plt.savefig(f"{OUT}/04_promociones.png",dpi=130); plt.close()

# 5 - Concentracion de clientes (Pareto mayoristas)
cl=q("""SELECT cl.nombre_cliente n, SUM(f.monto_neto) ing
 FROM fact_ventas f JOIN dim_cliente cl ON f.sk_cliente=cl.sk_cliente
 WHERE cl.tipo_cliente='Mayorista'
 GROUP BY cl.nombre_cliente ORDER BY ing DESC""")
fig,ax=plt.subplots(figsize=(9,4.2))
ax.bar(range(len(cl)),cl.ing,color=NAR)
ax.set_xticks(range(len(cl))); ax.set_xticklabels(cl.n,rotation=40,ha="right",fontsize=8)
ax.yaxis.set_major_formatter(FuncFormatter(col)); ax.set_ylabel("Ingreso neto")
ax.set_title("PN5 · Distribución del ingreso entre ~80 puntos de venta (base diversificada)")
plt.tight_layout(); plt.savefig(f"{OUT}/05_clientes.png",dpi=130); plt.close()

# 6 - Rotacion inventario
ri=q("""SELECT pr.nombre_producto n, pr.es_estrella e, AVG(fi.rotacion_mes) rot,
 AVG(fi.dias_inventario) dias
 FROM fact_inventario fi JOIN dim_producto pr ON fi.sk_producto=pr.sk_producto
 GROUP BY pr.nombre_producto,pr.es_estrella ORDER BY rot DESC""")
fig,ax=plt.subplots(figsize=(9,4.5))
ax.bar(range(len(ri)),ri.rot,color=[ROJO if e==1 else GRIS for e in ri.e])
ax.set_xticks(range(len(ri))); ax.set_xticklabels(ri.n,rotation=40,ha="right",fontsize=8)
ax.set_ylabel("Rotación mensual promedio")
ax.set_title("Rotación de inventario: estrella ~0.83 vs baja rotación ~0.12 (sobrestock)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=ROJO,label="Estrella"),Patch(color=GRIS,label="Baja rotación")],frameon=False)
plt.tight_layout(); plt.savefig(f"{OUT}/06_rotacion.png",dpi=130); plt.close()

# 7 - Calidad de datos
import sys
ql=pd.read_csv(os.path.join(os.path.dirname(__file__),"..","..","evidencia","etl_logs","reporte_calidad.csv"))
ql=ql[ql.hallazgo.str.contains("nula|<= 0|atipica|duplicada|inexistente",case=False)]
fig,ax=plt.subplots(figsize=(9,4))
ax.barh(ql.hallazgo,ql.registros,color=AZUL)
ax.invert_yaxis(); ax.set_xlabel("Registros afectados")
for i,v in enumerate(ql.registros): ax.text(v,i,f" {v}",va="center")
ax.set_title("Problemas de calidad detectados (pre-ETL) y tratados por R1–R10")
plt.tight_layout(); plt.savefig(f"{OUT}/07_calidad.png",dpi=130); plt.close()
print("Graficos generados en",OUT)
