# -*- coding: utf-8 -*-
"""
Dashboard analitico - Las Salsas de Lucho (Streamlit + Plotly).
6 vistas tematicas, segmentadores por anio/canal/categoria, y respuesta a las
5 preguntas de negocio. Lee del almacen dimensional (dw) via SQLAlchemy.

Ejecutar:  streamlit run dashboard/app.py
(usa la conexion definida en etl/config.py; export BI_BACKEND=sqlite para demo)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils import get_engine

st.set_page_config(page_title="BI · Las Salsas de Lucho", layout="wide",
                   page_icon="🌶️")
ROJO="#C0392B"; AZUL="#2471A3"; NAR="#E67E22"; VERDE="#229954"; GRIS="#85929E"

@st.cache_data(ttl=600)
def load():
    dw = get_engine("dw")
    fv = pd.read_sql("SELECT * FROM fact_ventas", dw)
    fi = pd.read_sql("SELECT * FROM fact_inventario", dw)
    dt = pd.read_sql("SELECT * FROM dim_tiempo", dw)
    dp = pd.read_sql("SELECT * FROM dim_producto", dw)
    dc = pd.read_sql("SELECT * FROM dim_cliente", dw)
    dca= pd.read_sql("SELECT * FROM dim_canal", dw)
    dv = pd.read_sql("SELECT * FROM dim_vendedor", dw)
    dpr= pd.read_sql("SELECT * FROM dim_promocion", dw)
    f = (fv.merge(dt,on="sk_tiempo").merge(dp,on="sk_producto")
           .merge(dc,on="sk_cliente").merge(dca,on="sk_canal")
           .merge(dv,on="sk_vendedor").merge(dpr,on="sk_promocion"))
    inv = fi.merge(dt,on="sk_tiempo").merge(dp,on="sk_producto")
    return f, inv

f, inv = load()

# -------- SEGMENTADORES (sidebar) --------
st.sidebar.title("🌶️ Las Salsas de Lucho")
st.sidebar.caption("Solución de Inteligencia de Negocios")
pagina = st.sidebar.radio("Navegación", [
    "1 · Resumen ejecutivo", "2 · Productos y rotación", "3 · Canales y vendedores",
    "4 · Estacionalidad", "5 · Promociones", "6 · Clientes y geografía"])
st.sidebar.markdown("---")
anios = sorted(f.anio.unique())
sel_anio = st.sidebar.multiselect("Año", anios, default=anios)
sel_canal= st.sidebar.multiselect("Canal", sorted(f.nombre_canal.unique()),
                                  default=sorted(f.nombre_canal.unique()))
sel_cat  = st.sidebar.multiselect("Categoría", sorted(f.categoria.unique()),
                                  default=sorted(f.categoria.unique()))
d = f[f.anio.isin(sel_anio) & f.nombre_canal.isin(sel_canal) & f.categoria.isin(sel_cat)]
di = inv[inv.anio.isin(sel_anio) & inv.categoria.isin(sel_cat)]

def kpi(c, label, val): c.metric(label, val)
def money(x): return f"₡{x/1e6:,.1f}M"

# ================= PAGINA 1 =================
if pagina.startswith("1"):
    st.title("Resumen ejecutivo")
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1,"Ingreso neto", money(d.monto_neto.sum()))
    kpi(c2,"Margen bruto", money(d.margen_bruto.sum()))
    kpi(c3,"Margen %", f"{100*d.margen_bruto.sum()/d.monto_neto.sum():.1f}%")
    kpi(c4,"Facturas", f"{d.id_venta.nunique():,}")
    kpi(c5,"Ticket prom.", f"₡{d.monto_neto.sum()/d.id_venta.nunique():,.0f}")
    a,b = st.columns(2)
    serie = d.groupby(["anio","mes"]).monto_neto.sum().reset_index()
    serie["periodo"]=serie.anio.astype(str)+"-"+serie.mes.astype(str).str.zfill(2)
    a.plotly_chart(px.line(serie,x="periodo",y="monto_neto",markers=True,
        title="Evolución mensual del ingreso neto",color_discrete_sequence=[AZUL]),use_container_width=True)
    canal=d.groupby("nombre_canal").monto_neto.sum().reset_index()
    b.plotly_chart(px.pie(canal,names="nombre_canal",values="monto_neto",hole=.45,
        title="Participación por canal"),use_container_width=True)
    a2,b2 = st.columns(2)
    topp=d.groupby("nombre_producto").monto_neto.sum().nlargest(5).reset_index()
    a2.plotly_chart(px.bar(topp,x="monto_neto",y="nombre_producto",orientation="h",
        title="Top 5 productos por ingreso",color_discrete_sequence=[ROJO]),use_container_width=True)
    seg=d.groupby("segmento_cliente").monto_neto.sum().reset_index()
    b2.plotly_chart(px.bar(seg,x="segmento_cliente",y="monto_neto",
        title="Ingreso por segmento de cliente",color_discrete_sequence=[VERDE]),use_container_width=True)

# ================= PAGINA 2 (PN1) =================
elif pagina.startswith("2"):
    st.title("Productos y rotación  ·  PN1")
    g=d.groupby(["nombre_producto","es_estrella"]).agg(
        ingreso=("monto_neto","sum"),unidades=("cantidad","sum"),
        margen=("margen_bruto","sum")).reset_index().sort_values("ingreso",ascending=False)
    g["margen_pct"]=100*g.margen/g.ingreso; g["acum"]=100*g.ingreso.cumsum()/g.ingreso.sum()
    a,b=st.columns(2)
    fig=go.Figure()
    fig.add_bar(x=g.nombre_producto,y=g.ingreso,marker_color=[ROJO if e else GRIS for e in g.es_estrella],name="Ingreso")
    fig.add_scatter(x=g.nombre_producto,y=g.acum,yaxis="y2",mode="lines+markers",name="% acum",line_color=AZUL)
    fig.update_layout(title="Pareto de productos",yaxis2=dict(overlaying="y",side="right",range=[0,105]))
    a.plotly_chart(fig,use_container_width=True)
    b.plotly_chart(px.bar(g,x="nombre_producto",y="margen_pct",title="Margen % por producto",
        color_discrete_sequence=[NAR]),use_container_width=True)
    a2,b2=st.columns(2)
    a2.plotly_chart(px.bar(g,x="nombre_producto",y="unidades",title="Unidades vendidas",
        color_discrete_sequence=[AZUL]),use_container_width=True)
    rot=di.groupby(["nombre_producto","es_estrella"]).agg(
        rotacion=("rotacion_mes","mean"),dias=("dias_inventario","mean")).reset_index()
    b2.plotly_chart(px.bar(rot.sort_values("rotacion",ascending=False),x="nombre_producto",y="rotacion",
        color="es_estrella",title="Rotación mensual de inventario"),use_container_width=True)
    st.subheader("Detalle (decisión de surtido)")
    st.dataframe(g.assign(clasificacion=g.es_estrella.map({1:"Estrella",0:"Baja rotación"})),
                 use_container_width=True)

# ================= PAGINA 3 (PN2) =================
elif pagina.startswith("3"):
    st.title("Canales y vendedores  ·  PN2")
    a,b=st.columns(2)
    c=d.groupby("nombre_canal").agg(ingreso=("monto_neto","sum"),
        margen=("margen_bruto","sum")).reset_index()
    c["margen_pct"]=100*c.margen/c.ingreso
    a.plotly_chart(px.bar(c,x="nombre_canal",y="ingreso",title="Ingreso por canal",
        color_discrete_sequence=[AZUL]),use_container_width=True)
    b.plotly_chart(px.bar(c,x="nombre_canal",y="margen_pct",title="Margen % por canal",
        color_discrete_sequence=[VERDE]),use_container_width=True)
    serie=d.groupby(["anio","mes","nombre_canal"]).monto_neto.sum().reset_index()
    serie["periodo"]=serie.anio.astype(str)+"-"+serie.mes.astype(str).str.zfill(2)
    st.plotly_chart(px.area(serie,x="periodo",y="monto_neto",color="nombre_canal",
        title="Evolución mensual del ingreso por canal"),use_container_width=True)
    a2,b2=st.columns(2)
    v=d.groupby("nombre_vendedor").monto_neto.sum().reset_index()
    a2.plotly_chart(px.bar(v,x="nombre_vendedor",y="monto_neto",title="Ingreso por vendedor",
        color_discrete_sequence=[NAR]),use_container_width=True)
    tc=d.groupby("tipo_canal").monto_neto.sum().reset_index()
    b2.plotly_chart(px.pie(tc,names="tipo_canal",values="monto_neto",hole=.4,
        title="Ingreso por tipo de canal"),use_container_width=True)

# ================= PAGINA 4 (PN3) =================
elif pagina.startswith("4"):
    st.title("Estacionalidad  ·  PN3")
    s=d.groupby(["anio","mes","nombre_mes"]).agg(ingreso=("monto_neto","sum"),
        dias=("fecha","nunique")).reset_index()
    s["prom_dia"]=s.ingreso/s.dias; s["periodo"]=s.anio.astype(str)+"-"+s.mes.astype(str).str.zfill(2)
    st.plotly_chart(px.line(s,x="periodo",y="prom_dia",markers=True,
        title="Ingreso promedio diario por mes (comparación justa)",
        color_discrete_sequence=[AZUL]),use_container_width=True)
    a,b=st.columns(2)
    tmp=d.groupby("temporada").monto_neto.sum().reset_index()
    a.plotly_chart(px.bar(tmp,x="temporada",y="monto_neto",title="Ingreso por temporada",
        color_discrete_sequence=[ROJO]),use_container_width=True)
    dow=d.groupby("nombre_dia").monto_neto.sum().reset_index()
    b.plotly_chart(px.bar(dow,x="nombre_dia",y="monto_neto",title="Ingreso por día de semana",
        color_discrete_sequence=[VERDE]),use_container_width=True)
    heat=d.pivot_table(index="nombre_mes",columns="anio",values="monto_neto",aggfunc="sum")
    st.plotly_chart(px.imshow(heat,text_auto=".2s",aspect="auto",
        title="Mapa de calor mes × año",color_continuous_scale="OrRd"),use_container_width=True)

# ================= PAGINA 5 (PN4) =================
elif pagina.startswith("5"):
    st.title("Promociones  ·  PN4")
    p=d.groupby("nombre_promocion").agg(ingreso=("monto_neto","sum"),
        unidades=("cantidad","sum"),margen=("margen_bruto","sum"),
        bruto=("monto_bruto","sum"),desc=("descuento_monto","sum")).reset_index()
    p["margen_pct"]=100*p.margen/p.ingreso; p["tasa_desc"]=100*p.desc/p.bruto
    a,b=st.columns(2)
    a.plotly_chart(px.bar(p,x="nombre_promocion",y="margen_pct",title="Margen % por promoción",
        color="margen_pct",color_continuous_scale="RdYlGn"),use_container_width=True)
    b.plotly_chart(px.bar(p,x="nombre_promocion",y="ingreso",title="Ingreso por promoción",
        color_discrete_sequence=[AZUL]),use_container_width=True)
    a2,b2=st.columns(2)
    a2.plotly_chart(px.scatter(p,x="tasa_desc",y="margen_pct",size="ingreso",text="nombre_promocion",
        title="Tasa de descuento vs margen"),use_container_width=True)
    ap=d.assign(grupo=d.aplica_promo.map({1:"Con promo",0:"Sin promo"})).groupby("grupo").agg(
        ingreso=("monto_neto","sum"),margen_pct=("margen_bruto",lambda x:100*x.sum()/d.loc[x.index,"monto_neto"].sum())).reset_index()
    b2.plotly_chart(px.bar(ap,x="grupo",y="ingreso",title="Con promo vs sin promo (ingreso)",
        color_discrete_sequence=[NAR]),use_container_width=True)
    st.dataframe(p.round(1),use_container_width=True)

# ================= PAGINA 6 (PN5) =================
else:
    st.title("Clientes y geografía  ·  PN5")
    a,b=st.columns(2)
    cl=d[d.tipo_cliente=="Mayorista"].groupby("nombre_cliente").monto_neto.sum().nlargest(10).reset_index()
    a.plotly_chart(px.bar(cl,x="monto_neto",y="nombre_cliente",orientation="h",
        title="Top mayoristas (concentración)",color_discrete_sequence=[NAR]),use_container_width=True)
    tc=d.groupby("tipo_cliente").monto_neto.sum().reset_index()
    b.plotly_chart(px.pie(tc,names="tipo_cliente",values="monto_neto",hole=.4,
        title="Ingreso: Minorista vs Mayorista"),use_container_width=True)
    a2,b2=st.columns(2)
    prov=d.groupby("provincia").monto_neto.sum().reset_index()
    a2.plotly_chart(px.bar(prov.sort_values("monto_neto"),x="monto_neto",y="provincia",orientation="h",
        title="Ingreso por provincia",color_discrete_sequence=[AZUL]),use_container_width=True)
    reg=d.groupby("region").monto_neto.sum().reset_index()
    b2.plotly_chart(px.pie(reg,names="region",values="monto_neto",hole=.4,
        title="Ingreso por región"),use_container_width=True)
    seg=d.groupby("segmento_cliente").agg(ingreso=("monto_neto","sum"),
        clientes=("sk_cliente","nunique")).reset_index()
    st.plotly_chart(px.bar(seg,x="segmento_cliente",y="ingreso",title="Ingreso por segmento RFM",
        color_discrete_sequence=[VERDE]),use_container_width=True)
