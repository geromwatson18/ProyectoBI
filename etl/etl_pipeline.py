# -*- coding: utf-8 -*-
"""
PASO 3 del pipeline: ETL DIMENSIONAL.
Extrae desde la base OPERACIONAL, aplica las reglas de transformacion R1..R10 y
carga el modelo estrella en la base DWH. Reproducible y trazable.

Reglas de transformacion no triviales:
  R1  Construccion de dim_tiempo (derivacion de calendario + temporada).
  R2  Generacion de llaves subrogadas (SK) en todas las dimensiones.
  R3  Homologacion/normalizacion de catalogos (provincia, canal, producto).
  R4  Calculo de antiguedad del cliente (manejo de nulos por mediana).
  R5  Clasificacion/segmentacion de clientes (RFM simplificado).
  R6  Deteccion y tratamiento de valores atipicos (regla IQR).
  R7  Deduplicacion de lineas de venta por clave natural.
  R8  Derivacion de medidas (monto_neto, costo, margen) + validacion de signos.
  R9  Validacion de integridad referencial (inferred members "No identificado").
  R10 Tratamiento de nulos y estandarizacion de formatos (fechas, moneda).
"""
import os, unicodedata, datetime as dt
import numpy as np
import pandas as pd
import config
from utils import get_engine, get_logger

log = get_logger("03_etl_dimensional")
bitacora = []   # (regla, descripcion, registros_afectados)
def reg(regla, desc, n):
    bitacora.append((regla, desc, int(n)))
    log.info("%-4s | %-55s | %6d", regla, desc, int(n))

# ---------------------------------------------------------------- helpers ---
def quita_acentos(s):
    if pd.isna(s): return s
    return "".join(c for c in unicodedata.normalize("NFKD", str(s))
                   if not unicodedata.combining(c))

def limpia_texto(s):
    if pd.isna(s) or str(s).strip() == "": return None
    s = " ".join(str(s).split())          # colapsa espacios
    return s.strip()

# ============================ R1: DIM_TIEMPO ===============================
MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto",
         "Setiembre","Octubre","Noviembre","Diciembre"]
DIAS  = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"]

def construir_dim_tiempo():
    ini = dt.date.fromisoformat(config.FECHA_INICIO_DIM_TIEMPO)
    fin = dt.date.fromisoformat(config.FECHA_FIN_DIM_TIEMPO)
    filas = []
    d = ini
    while d <= fin:
        mes = d.month
        temporada = ("Alta" if mes in (11,12) else
                     "Media" if mes in (4,7) else "Baja")
        filas.append(dict(
            sk_tiempo=int(d.strftime("%Y%m%d")), fecha=d.isoformat(),
            anio=d.year, semestre=1 if mes<=6 else 2,
            trimestre=(mes-1)//3+1, mes=mes, nombre_mes=MESES[mes-1],
            semana_anio=int(d.strftime("%V")), dia=d.day,
            dia_semana=d.weekday()+1, nombre_dia=DIAS[d.weekday()],
            es_fin_semana=d.weekday()>=5, temporada=temporada))
        d += dt.timedelta(days=1)
    df = pd.DataFrame(filas)
    reg("R1", "dim_tiempo construida (dias de calendario)", len(df))
    return df

# ====================== R3 homologacion catalogos ==========================
MAPA_REGION = {  # provincia -> region
    "San Jose":"GAM","Cartago":"GAM","Heredia":"GAM","Alajuela":"GAM",
    "Guanacaste":"Costera","Puntarenas":"Costera","Limon":"Costera"}

def homologa_provincia(s):
    s = quita_acentos(limpia_texto(s) or "")
    s = s.upper().replace(".","").replace(" ","")
    tabla = {"SANJOSE":"San Jose","SJ":"San Jose","CARTAGO":"Cartago",
             "HEREDIA":"Heredia","ALAJUELA":"Alajuela","GUANACASTE":"Guanacaste",
             "PUNTARENAS":"Puntarenas","LIMON":"Limon"}
    return tabla.get(s, "Otra")

def homologa_canal(texto, id_canal):
    t = quita_acentos(limpia_texto(texto) or "").lower().replace(" ","")
    if "tienda" in t: return "Tienda fisica"
    if "feria"  in t: return "Feria del agricultor"
    if "mayoreo" in t: return "Mayoreo"
    if "linea" in t or "online" in t: return "En linea"
    # respaldo por id_canal
    m = {"1":"Tienda fisica","2":"Feria del agricultor","3":"Mayoreo","4":"En linea"}
    return m.get(str(id_canal), config.MIEMBRO_NO_IDENTIFICADO)

TIPO_CANAL = {"Tienda fisica":"Directo","Feria del agricultor":"Directo",
              "Mayoreo":"Indirecto","En linea":"Digital",
              config.MIEMBRO_NO_IDENTIFICADO:"No identificado"}

def main():
    op = get_engine("op"); dw = get_engine("dw")
    log.info("=== ETL DIMENSIONAL  op=%s -> dw=%s ===", op.url, dw.url)

    # ---------------- EXTRACT ----------------
    categorias = pd.read_sql("SELECT * FROM categorias", op)
    productos  = pd.read_sql("SELECT * FROM productos", op)
    canales    = pd.read_sql("SELECT * FROM canales", op)
    vendedores = pd.read_sql("SELECT * FROM vendedores", op)
    promos     = pd.read_sql("SELECT * FROM promociones", op)
    clientes   = pd.read_sql("SELECT * FROM clientes", op)
    ventas     = pd.read_sql("SELECT * FROM ventas", op)
    detalle    = pd.read_sql("SELECT * FROM detalle_ventas", op)
    inventario = pd.read_sql("SELECT * FROM movimientos_inventario", op)
    log.info("Extraidas %d ventas, %d lineas, %d clientes",
             len(ventas), len(detalle), len(clientes))

    # tipados numericos (R10)
    categorias["id_categoria"]=pd.to_numeric(categorias["id_categoria"],errors="coerce")
    canales["id_canal"]=pd.to_numeric(canales["id_canal"],errors="coerce")
    for c in ["id_producto","id_categoria","presentacion_ml"]:
        productos[c] = pd.to_numeric(productos[c], errors="coerce")
    for c in ["precio_lista","costo_unitario"]:
        productos[c] = pd.to_numeric(productos[c], errors="coerce")
    productos["es_estrella"] = pd.to_numeric(productos["es_estrella"], errors="coerce").fillna(0)
    detalle["id_venta"]=pd.to_numeric(detalle["id_venta"],errors="coerce")
    detalle["id_producto"]=pd.to_numeric(detalle["id_producto"],errors="coerce")
    for c in ["cantidad","precio_unitario","monto_bruto","descuento","costo_unitario"]:
        detalle[c]=pd.to_numeric(detalle[c],errors="coerce")
    ventas["id_venta"]=pd.to_numeric(ventas["id_venta"],errors="coerce")
    ventas["id_cliente"]=pd.to_numeric(ventas["id_cliente"],errors="coerce")
    ventas["id_canal"]=pd.to_numeric(ventas["id_canal"],errors="coerce")
    ventas["id_vendedor"]=pd.to_numeric(ventas["id_vendedor"],errors="coerce")
    ventas["id_promocion"]=pd.to_numeric(ventas["id_promocion"],errors="coerce")
    ventas["fecha_venta"]=pd.to_datetime(ventas["fecha_venta"],errors="coerce")
    reg("R10","Tipado/estandarizacion de formatos (fechas y moneda)", len(detalle)+len(ventas))

    # ============== DIM_TIEMPO (R1) ==============
    dim_tiempo = construir_dim_tiempo()

    # ============== DIM_PRODUCTO (R2,R3) ==============
    prod = productos.merge(categorias, on="id_categoria", how="left")
    prod["nombre_producto"] = prod["nombre_producto"].map(limpia_texto)
    # rango de precio (binning)
    prod["rango_precio"] = pd.cut(prod["precio_lista"],
        bins=[0,2400,3000,99999], labels=["Economico","Medio","Premium"])
    dim_producto = pd.DataFrame({
        "id_producto": prod["id_producto"],
        "nombre_producto": prod["nombre_producto"],
        "categoria": prod["nombre_categoria"].map(limpia_texto),
        "presentacion_ml": prod["presentacion_ml"],
        "rango_precio": prod["rango_precio"].astype(str),
        "es_estrella": prod["es_estrella"].astype(int).astype(bool),
        "precio_lista": prod["precio_lista"],
        "costo_unitario": prod["costo_unitario"],
    }).reset_index(drop=True)
    dim_producto.insert(0,"sk_producto", range(1,len(dim_producto)+1))   # R2
    reg("R2","Llaves subrogadas dim_producto", len(dim_producto))
    reg("R3","Homologacion de nombres de producto", len(dim_producto))

    # ============== DIM_CANAL (R2,R3) ==============
    canales_norm = canales.copy()
    canales_norm["nombre_canal"] = canales_norm.apply(
        lambda r: homologa_canal(r["nombre_canal"], r["id_canal"]), axis=1)
    # agregar miembro No identificado
    dim_canal = canales_norm[["id_canal","nombre_canal"]].copy()
    dim_canal["id_canal"]=pd.to_numeric(dim_canal["id_canal"],errors="coerce")
    dim_canal = pd.concat([dim_canal, pd.DataFrame(
        [{"id_canal":-1,"nombre_canal":config.MIEMBRO_NO_IDENTIFICADO}])], ignore_index=True)
    dim_canal["tipo_canal"]=dim_canal["nombre_canal"].map(TIPO_CANAL).fillna("No identificado")
    dim_canal.insert(0,"sk_canal", range(1,len(dim_canal)+1))
    reg("R3","Homologacion de canal + miembro No identificado", len(dim_canal))

    # ============== DIM_VENDEDOR / DIM_PROMOCION (R2) ==============
    dim_vendedor = vendedores.copy()
    dim_vendedor["id_vendedor"]=pd.to_numeric(dim_vendedor["id_vendedor"])
    dim_vendedor.insert(0,"sk_vendedor",range(1,len(dim_vendedor)+1))

    dim_promocion = promos.copy()
    dim_promocion["id_promocion"]=pd.to_numeric(dim_promocion["id_promocion"])
    dim_promocion["descuento_pct"]=pd.to_numeric(dim_promocion["descuento_pct"])
    dim_promocion["aplica_promo"]=dim_promocion["id_promocion"]!=0
    dim_promocion.insert(0,"sk_promocion",range(1,len(dim_promocion)+1))
    reg("R2","Llaves subrogadas dim_vendedor/dim_promocion",
        len(dim_vendedor)+len(dim_promocion))

    # ============== DIM_CLIENTE (R3,R4,R5,R9,R10) ==============
    cli = clientes.copy()
    cli["id_cliente"]=pd.to_numeric(cli["id_cliente"],errors="coerce")
    cli["nombre_cliente"]=cli["nombre_cliente"].map(limpia_texto)
    cli["tipo_cliente"]=cli["tipo_cliente"].map(limpia_texto)
    cli["provincia"]=cli["provincia"].map(homologa_provincia)           # R3
    cli["region"]=cli["provincia"].map(MAPA_REGION).fillna("Otra")
    # R4: antiguedad en meses, imputando nulos por mediana
    freg = pd.to_datetime(cli["fecha_registro"], errors="coerce")
    hoy = pd.Timestamp("2025-12-31")
    ant = ((hoy - freg).dt.days/30.44)
    n_nulos = ant.isna().sum()
    ant = ant.fillna(ant.median()).round().astype(int)
    cli["antiguedad_meses"]=ant
    reg("R4", "Antiguedad de cliente (nulos imputados por mediana)", n_nulos)

    # R5: segmentacion por recencia/frecuencia (RFM simplificado)
    v_cli = ventas.dropna(subset=["id_cliente"]).copy()
    fr = v_cli.groupby("id_cliente")["id_venta"].nunique().rename("frecuencia")
    rec = v_cli.groupby("id_cliente")["fecha_venta"].max().rename("ult_compra")
    seg = pd.concat([fr,rec],axis=1).reset_index()
    seg["dias_recencia"]=(hoy-seg["ult_compra"]).dt.days
    def segmenta(row):
        if pd.isna(row["frecuencia"]): return "Nuevo"
        if row["dias_recencia"]>180: return "Inactivo"
        if row["frecuencia"]>=20: return "Frecuente"
        if row["frecuencia"]>=5:  return "Recurrente"
        return "Nuevo"
    seg["segmento_cliente"]=seg.apply(segmenta,axis=1)
    cli = cli.merge(seg[["id_cliente","segmento_cliente"]],on="id_cliente",how="left")
    cli["segmento_cliente"]=cli["segmento_cliente"].fillna("Nuevo")
    reg("R5","Segmentacion de clientes (RFM simplificado)", len(cli))

    dim_cliente = cli[["id_cliente","nombre_cliente","tipo_cliente","provincia",
                       "region","antiguedad_meses","segmento_cliente"]].copy()
    # R9: miembro No identificado para FKs rotas
    dim_cliente = pd.concat([dim_cliente, pd.DataFrame([{
        "id_cliente":-1,"nombre_cliente":config.MIEMBRO_NO_IDENTIFICADO,
        "tipo_cliente":"No identificado","provincia":"Otra","region":"Otra",
        "antiguedad_meses":0,"segmento_cliente":"No identificado"}])],ignore_index=True)
    dim_cliente.insert(0,"sk_cliente",range(1,len(dim_cliente)+1))

    # ====================== HECHO: FACT_VENTAS ======================
    df = detalle.merge(ventas, on="id_venta", how="left", suffixes=("","_v"))
    n0=len(df)
    # R7: deduplicacion por clave natural
    df = df.drop_duplicates(subset=["id_venta","id_producto","cantidad","precio_unitario"])
    reg("R7","Deduplicacion de lineas de venta", n0-len(df))
    # R8 validacion de signos: descartar cantidades <=0
    n_neg=(df["cantidad"]<=0).sum()
    df = df[df["cantidad"]>0]
    reg("R8","Lineas con cantidad <=0 descartadas (devoluciones mal registradas)", n_neg)

    # homologar canal por fila (texto sucio / nulo) -- necesario para R6 por canal
    df["canal_norm"]=df.apply(lambda r: homologa_canal(r.get("canal_texto"), r.get("id_canal")),axis=1)

    # R6 deteccion de outliers POR CANAL (regla IQR dentro de cada canal: el
    # menudeo vende 1-3 unidades y el mayoreo 6-36; un umbral global confundiria
    # ventas legitimas de mayoreo con errores. Se evalua por grupo).
    def tope_iqr(s):
        q1,q3 = s.quantile([.25,.75]); return q3 + config.UMBRAL_OUTLIER_IQR*(q3-q1)
    topes = df.groupby("canal_norm")["cantidad"].transform(tope_iqr)
    # piso de seguridad: nunca marcar como atipico una compra <= 50 unidades
    topes = topes.clip(lower=50)
    mask_out = df["cantidad"] > topes
    n_out = int(mask_out.sum())
    df = df[~mask_out]
    reg("R6", "Outliers de cantidad descartados (IQR por canal, piso 50 uds)", n_out)

    # R10: recomputo monto_bruto = precio*cantidad (homologa inconsistencias)
    df["monto_bruto"]= (df["precio_unitario"]*df["cantidad"]).round(2)
    # descuento ya viene como monto; recalcular neto
    df["descuento"]=df["descuento"].fillna(0)
    df["monto_neto"]=(df["monto_bruto"]-df["descuento"]).round(2)
    # R8: costo nulo -> imputar desde catalogo de productos
    costo_cat = dim_producto.set_index("id_producto")["costo_unitario"]
    n_costo_nulo = df["costo_unitario"].isna().sum()
    df["costo_unitario"]=df["costo_unitario"].fillna(df["id_producto"].map(costo_cat))
    reg("R8","Costo unitario nulo imputado desde catalogo", n_costo_nulo)
    df["costo_total"]=(df["costo_unitario"]*df["cantidad"]).round(2)
    df["margen_bruto"]=(df["monto_neto"]-df["costo_total"]).round(2)

    # mapeo de canal homologado a llave subrogada
    canal_sk = dim_canal.set_index("nombre_canal")["sk_canal"]
    df["sk_canal"]=df["canal_norm"].map(canal_sk).fillna(
        int(dim_canal.loc[dim_canal["nombre_canal"]==config.MIEMBRO_NO_IDENTIFICADO,"sk_canal"].iloc[0]))

    # R9 integridad referencial cliente
    cli_sk = dim_cliente.set_index("id_cliente")["sk_cliente"]
    sk_cli_noid = int(dim_cliente.loc[dim_cliente["id_cliente"]==-1,"sk_cliente"].iloc[0])
    n_orphan=(~df["id_cliente"].isin(cli_sk.index)).sum()
    df["sk_cliente"]=df["id_cliente"].map(cli_sk).fillna(sk_cli_noid).astype(int)
    reg("R9","Lineas con cliente inexistente -> miembro No identificado", n_orphan)

    prod_sk = dim_producto.set_index("id_producto")["sk_producto"]
    df["sk_producto"]=df["id_producto"].map(prod_sk)
    df = df.dropna(subset=["sk_producto"])
    df["sk_producto"]=df["sk_producto"].astype(int)

    vend_sk = dim_vendedor.set_index("id_vendedor")["sk_vendedor"]
    df["sk_vendedor"]=df["id_vendedor"].map(vend_sk).fillna(1).astype(int)
    promo_sk = dim_promocion.set_index("id_promocion")["sk_promocion"]
    df["sk_promocion"]=df["id_promocion"].map(promo_sk).fillna(1).astype(int)
    df["sk_tiempo"]=df["fecha_venta"].dt.strftime("%Y%m%d").astype("Int64")
    df = df.dropna(subset=["sk_tiempo"])

    fact_ventas = df[["sk_tiempo","sk_producto","sk_cliente","sk_canal","sk_vendedor",
                      "sk_promocion","id_venta","cantidad","precio_unitario","monto_bruto",
                      "descuento","monto_neto","costo_total","margen_bruto"]].copy()
    fact_ventas = fact_ventas.rename(columns={"descuento":"descuento_monto"})
    fact_ventas.insert(0,"sk_venta_linea",range(1,len(fact_ventas)+1))
    reg("R8","fact_ventas: medidas derivadas (neto, costo, margen)", len(fact_ventas))

    # ====================== HECHO: FACT_INVENTARIO ======================
    inv = inventario.copy()
    for c in ["existencia_inicial","entradas","salidas","existencia_final","costo_inventario"]:
        inv[c]=pd.to_numeric(inv[c],errors="coerce")
    inv["id_producto"]=pd.to_numeric(inv["id_producto"],errors="coerce")
    inv["fecha_corte"]=pd.to_datetime(inv["fecha_corte"],errors="coerce")
    inv["existencia_prom"]=((inv["existencia_inicial"]+inv["existencia_final"])/2).replace(0,np.nan)
    inv["rotacion_mes"]=(inv["salidas"]/inv["existencia_prom"]).round(4).fillna(0)
    inv["dias_inventario"]=(30/inv["rotacion_mes"].replace(0,np.nan)).round(2).fillna(999)
    inv["sk_producto"]=inv["id_producto"].map(prod_sk)
    inv["sk_tiempo"]=inv["fecha_corte"].dt.strftime("%Y%m%d").astype("Int64")
    fact_inventario = inv.dropna(subset=["sk_producto","sk_tiempo"])[
        ["sk_tiempo","sk_producto","existencia_inicial","entradas","salidas",
         "existencia_final","costo_inventario","rotacion_mes","dias_inventario"]].copy()
    fact_inventario["sk_producto"]=fact_inventario["sk_producto"].astype(int)
    fact_inventario.insert(0,"sk_inventario",range(1,len(fact_inventario)+1))
    reg("R1","fact_inventario: rotacion y dias de inventario derivados", len(fact_inventario))

    # ---------------- LOAD ----------------
    def carga(nombre, dframe):
        dframe.to_sql(nombre, dw, if_exists="replace", index=False)
        log.info("Cargada dw.%-16s %6d filas", nombre, len(dframe))

    carga("dim_tiempo", dim_tiempo)
    carga("dim_producto", dim_producto)
    carga("dim_cliente", dim_cliente)
    carga("dim_canal", dim_canal)
    carga("dim_vendedor", dim_vendedor)
    carga("dim_promocion", dim_promocion)
    carga("fact_ventas", fact_ventas)
    carga("fact_inventario", fact_inventario)

    # bitacora de ETL
    bit = pd.DataFrame(bitacora, columns=["regla","descripcion","registros_afectados"])
    bit.to_csv(os.path.join(config.LOG_DIR,"bitacora_etl.csv"), index=False)
    log.info("ETL finalizado. fact_ventas=%d, fact_inventario=%d",
             len(fact_ventas), len(fact_inventario))
    return fact_ventas, fact_inventario

if __name__ == "__main__":
    main()
