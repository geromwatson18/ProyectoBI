# -*- coding: utf-8 -*-
"""
Generador de la FUENTE OPERACIONAL sintetica de "Las Salsas de Lucho".

Calibracion del caso (parametros del negocio):
  * Cada salsa se VENDE a ~CRC 3.000 la botella de 200 ml (precio de lista).
  * ~80 PUNTOS DE VENTA (locales reales de Costa Rica) compran cada mes (mayoreo).
  * La UTILIDAD (margen bruto) objetivo es ~CRC 1,2 millones por mes.

Produce CSVs en data/raw/ que simulan la base transaccional real de la PYME,
incluyendo PROBLEMAS DE CALIDAD DE DATOS intencionales para que el ETL los trate.

Salida (modelo transaccional de origen):
  categorias.csv, productos.csv, clientes.csv, canales.csv, vendedores.csv,
  promociones.csv, ventas.csv, detalle_ventas.csv, movimientos_inventario.csv

Reproducible: semilla fija.
"""
import os, csv, random, datetime as dt
from collections import defaultdict
import numpy as np

random.seed(42); np.random.seed(42)
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.normpath(os.path.join(HERE, "..", "data", "raw"))
os.makedirs(RAW, exist_ok=True)

PRECIO = 3000          # CRC por botella de 200 ml (precio de venta, todas las salsas)
PRESENTACION = 200     # ml

def w(name, header, rows):
    p = os.path.join(RAW, name)
    with open(p, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f); wr.writerow(header); wr.writerows(rows)
    print(f"  {name:32s} {len(rows):6d} filas")

# ---------------------------------------------------------------------------
# 1) CATEGORIAS
# ---------------------------------------------------------------------------
categorias = [
    (1, "Picantes"),
    (2, "Aderezos"),
    (3, "Especialidad Gourmet"),
]
w("categorias.csv", ["id_categoria", "nombre_categoria"], categorias)

# ---------------------------------------------------------------------------
# 2) PRODUCTOS  (todas 200 ml, precio de venta CRC 3.000)
#    3 estrella (costo bajo -> margen alto) + 7 de baja rotacion (costo alto -> margen menor)
#    id, nombre, id_categoria, presentacion_ml, precio_lista, costo_unitario, estrella
# ---------------------------------------------------------------------------
productos = [
    # --- 3 ESTRELLA (alta rotacion, mejor margen) ---
    (101, "Salsa Picante Habanero Lucho", 1, PRESENTACION, PRECIO, 1150, 1),
    (102, "Chilero Criollo Lucho",        1, PRESENTACION, PRECIO, 1100, 1),
    (103, "Salsa de Ajo Lucho",           2, PRESENTACION, PRECIO, 1250, 1),
    # --- BAJA ROTACION (especialidad, costo alto -> margen menor) ---
    (104, "Salsa Mango-Habanero",         3, PRESENTACION, PRECIO, 1500, 0),
    (105, "Salsa BBQ Tamarindo",          3, PRESENTACION, PRECIO, 1480, 0),
    (106, "Salsa Chipotle Dulce",         1, PRESENTACION, PRECIO, 1420, 0),
    (107, "Salsa Verde Jalapeno",         1, PRESENTACION, PRECIO, 1350, 0),
    (108, "Aderezo Cilantro-Limon",       2, PRESENTACION, PRECIO, 1380, 0),
    (109, "Salsa Inferno Carolina Reaper",3, PRESENTACION, PRECIO, 1650, 0),
    (110, "Salsa Curry Tropical",         3, PRESENTACION, PRECIO, 1550, 0),
]
w("productos.csv",
  ["id_producto","nombre_producto","id_categoria","presentacion_ml","precio_lista","costo_unitario","es_estrella"],
  productos)

# ---------------------------------------------------------------------------
# 3) CANALES  (con variantes "sucias" de texto para homologar en ETL)
# ---------------------------------------------------------------------------
canales = [
    (1, "Tienda fisica"),
    (2, "Feria del agricultor"),
    (3, "Mayoreo"),
    (4, "En linea"),
]
w("canales.csv", ["id_canal","nombre_canal"], canales)

# ---------------------------------------------------------------------------
# 4) VENDEDORES
# ---------------------------------------------------------------------------
vendedores = [
    (1, "Luis 'Lucho' Mora",  "Propietario"),
    (2, "Carolina Vargas",    "Ventas"),
    (3, "Diego Soto",         "Ventas"),
    (4, "Maria Jose Rojas",   "Ferias"),
]
w("vendedores.csv", ["id_vendedor","nombre_vendedor","puesto"], vendedores)

# ---------------------------------------------------------------------------
# 5) PROMOCIONES
# ---------------------------------------------------------------------------
promociones = [
    (0, "Sin promocion",        0.00),
    (1, "Descuento mayoreo",    0.10),
    (2, "Combo feria 2x",       0.15),
    (3, "Temporada alta",       0.08),
    (4, "Liquidacion lenta",    0.25),
]
w("promociones.csv", ["id_promocion","nombre_promocion","descuento_pct"], promociones)

# ---------------------------------------------------------------------------
# 6) CLIENTES = PUNTOS DE VENTA reales de Costa Rica (mayoreo) + retail
#    Locales reales por canton/provincia. Se inyectan nulos y provincias sucias.
# ---------------------------------------------------------------------------
provincias_variantes = {
    "San Jose":  ["San Jose", "san jose", "SAN JOSE", "S.J.", " San Jose "],
    "Cartago":   ["Cartago", "cartago", "CARTAGO", " Cartago"],
    "Heredia":   ["Heredia", "heredia", "HEREDIA"],
    "Alajuela":  ["Alajuela", "alajuela", "ALAJUELA"],
    "Guanacaste":["Guanacaste", "guanacaste", "GUANACASTE"],
    "Puntarenas":["Puntarenas", "puntarenas"],
    "Limon":     ["Limon", "limon", "LIMON"],
}

# Puntos de venta (locales) reales de CR: (nombre, provincia). ~96 locales.
LOCALES = [
    # ---- San Jose (GAM) ----
    ("Pulperia La Esquina (Desamparados)", "San Jose"),
    ("Mini Super El Cruce (Aserri)", "San Jose"),
    ("Soda Dona Tere (San Pedro)", "San Jose"),
    ("Restaurante El Fogon (Escazu)", "San Jose"),
    ("Super Las Brisas (Hatillo)", "San Jose"),
    ("Abastecedor San Blas (Tibas)", "San Jose"),
    ("Soda La U (Montes de Oca)", "San Jose"),
    ("Minimercado Santa Ana Centro", "San Jose"),
    ("Pulperia Don Beto (Moravia)", "San Jose"),
    ("Macrobiotica Vida Sana (Curridabat)", "San Jose"),
    ("Restaurante Sabor Tico (Zapote)", "San Jose"),
    ("Verduleria El Mercadito (Pavas)", "San Jose"),
    ("Super Mora (Ciudad Colon)", "San Jose"),
    ("Soda El Parque (Goicoechea)", "San Jose"),
    ("Mini Super Alajuelita Centro", "San Jose"),
    ("Cafeteria Central (Perez Zeledon)", "San Jose"),
    ("Pulperia La Bendicion (Guadalupe)", "San Jose"),
    ("Restaurante Casa Vieja (Sabana)", "San Jose"),
    # ---- Alajuela ----
    ("Super El Ahorro (Alajuela Centro)", "Alajuela"),
    ("Pulperia La Amistad (San Ramon)", "Alajuela"),
    ("Mini Super Grecia", "Alajuela"),
    ("Soda Las Palmas (Atenas)", "Alajuela"),
    ("Abastecedor Naranjo Centro", "Alajuela"),
    ("Restaurante El Mirador (Poas)", "Alajuela"),
    ("Super Palmares", "Alajuela"),
    ("Minimercado Orotina", "Alajuela"),
    ("Pulperia El Progreso (Ciudad Quesada)", "Alajuela"),
    ("Verduleria Zarcero Fresco", "Alajuela"),
    ("Soda Sarchi Tipico", "Alajuela"),
    ("Mini Super Upala", "Alajuela"),
    ("Restaurante La Carreta (San Mateo)", "Alajuela"),
    # ---- Cartago ----
    ("Pulperia La Basilica (Cartago Centro)", "Cartago"),
    ("Mini Super Tres Rios (La Union)", "Cartago"),
    ("Soda El Volcan (Paraiso)", "Cartago"),
    ("Restaurante Turrialtico (Turrialba)", "Cartago"),
    ("Super Oreamuno", "Cartago"),
    ("Abastecedor El Guarco", "Cartago"),
    ("Verduleria Cervantes Fresco", "Cartago"),
    ("Pulperia Pacayas Centro", "Cartago"),
    ("Minimercado Cipreses", "Cartago"),
    ("Soda La Plaza (Tejar)", "Cartago"),
    ("Restaurante El Quijongo (Cot)", "Cartago"),
    # ---- Heredia ----
    ("Super Heredia Centro", "Heredia"),
    ("Pulperia Barva Vieja", "Heredia"),
    ("Mini Super San Rafael", "Heredia"),
    ("Soda La Estacion (San Joaquin)", "Heredia"),
    ("Abastecedor Belen", "Heredia"),
    ("Restaurante El Tigre Vestido (Santa Barbara)", "Heredia"),
    ("Verduleria Santo Domingo Fresco", "Heredia"),
    ("Minimercado Mercedes Norte", "Heredia"),
    ("Pulperia San Isidro Centro", "Heredia"),
    ("Soda Flores Tico", "Heredia"),
    # ---- Guanacaste ----
    ("Super Liberia Centro", "Guanacaste"),
    ("Pulperia Nicoya Vieja", "Guanacaste"),
    ("Mini Super Santa Cruz", "Guanacaste"),
    ("Soda La Guaria (Canas)", "Guanacaste"),
    ("Restaurante Marisco Azul (Filadelfia)", "Guanacaste"),
    ("Abastecedor Bagaces", "Guanacaste"),
    ("Minimercado Tilaran", "Guanacaste"),
    ("Pulperia La Cruz Centro", "Guanacaste"),
    ("Soda Playas del Coco", "Guanacaste"),
    ("Super Tamarindo Beach", "Guanacaste"),
    # ---- Puntarenas ----
    ("Marisqueria Mar Azul (Puntarenas)", "Puntarenas"),
    ("Pulperia El Roble (Esparza)", "Puntarenas"),
    ("Mini Super Quepos Centro", "Puntarenas"),
    ("Soda Jaco Beach (Garabito)", "Puntarenas"),
    ("Restaurante El Pescador (Golfito)", "Puntarenas"),
    ("Abastecedor Ciudad Cortes (Osa)", "Puntarenas"),
    ("Minimercado Ciudad Neily", "Puntarenas"),
    ("Pulperia Parrita Centro", "Puntarenas"),
    ("Super Buenos Aires", "Puntarenas"),
    ("Soda El Muelle (Caldera)", "Puntarenas"),
    # ---- Limon ----
    ("Pulperia Caribe (Limon Centro)", "Limon"),
    ("Mini Super Guapiles (Pococi)", "Limon"),
    ("Soda Calypso (Siquirres)", "Limon"),
    ("Restaurante Bribri Tipico (Talamanca)", "Limon"),
    ("Abastecedor Matina", "Limon"),
    ("Minimercado Guacimo", "Limon"),
    ("Super Cahuita Beach", "Limon"),
    ("Pulperia Puerto Viejo", "Limon"),
    ("Soda Estrada (Pueblo Nuevo)", "Limon"),
    ("Restaurante Miss Edith (Cahuita)", "Limon"),
    # ---- mayoristas adicionales para superar 80 activos/mes ----
    ("Distribuidora Tica de Abarrotes (Heredia)", "Heredia"),
    ("Comercializadora del Valle (Cartago)", "Cartago"),
    ("Mayorista La Economia (San Jose)", "San Jose"),
    ("Super Compro (Alajuela)", "Alajuela"),
    ("Distribuidora Pacifico (Puntarenas)", "Puntarenas"),
    ("Mayoreo del Caribe (Limon)", "Limon"),
    ("Abastecedor Pampa (Guanacaste)", "Guanacaste"),
    ("Comercial El Guapileno (Pococi)", "Limon"),
    ("Distribuidora San Carlos (Ciudad Quesada)", "Alajuela"),
    ("Super Mayoreo Curridabat", "San Jose"),
    ("Mercadito Organico (Santa Ana)", "San Jose"),
    ("Feria Verde (Aranjuez, San Jose)", "San Jose"),
    ("Feria del Agricultor de Heredia", "Heredia"),
    ("Feria del Agricultor de Cartago", "Cartago"),
]

clientes = []
# cliente 1 = consumidor final generico ("contado", retail en tienda/feria/linea)
clientes.append((1, "Cliente Contado", "Minorista", "San Jose", "", "Walk-in"))
cid = 2
locales_ids = []
for nm, prov in LOCALES:
    prov_txt = random.choice(provincias_variantes[prov])
    if random.random() < 0.11:
        freg = ""  # NULO intencional en fecha_registro
    else:
        start = dt.date(2021,1,1); end = dt.date(2025,6,1)
        freg = (start + dt.timedelta(days=random.randint(0,(end-start).days))).isoformat()
    clientes.append((cid, nm, "Mayorista", prov_txt, freg, "Comercio"))
    locales_ids.append(cid)
    cid += 1
# algunos minoristas con nombre (consumidores frecuentes en tienda/linea)
nombres_pila = ["Ana","Jose","Luis","Marta","Carlos","Sofia","Diego","Laura","Pedro","Karla",
                "Andres","Gabriela","Mauricio","Daniela","Esteban","Natalia","Rodrigo","Paula"]
apellidos = ["Mora","Jimenez","Rojas","Vargas","Castro","Soto","Chaves","Quiros","Mena","Solano"]
minoristas_ids = []
for _ in range(40):
    nm = f"{random.choice(nombres_pila)} {random.choice(apellidos)}"
    prov = random.choice(list(provincias_variantes.keys()))
    prov_txt = random.choice(provincias_variantes[prov])
    freg = "" if random.random() < 0.10 else \
        (dt.date(2023,1,1) + dt.timedelta(days=random.randint(0,1000))).isoformat()
    clientes.append((cid, nm, "Minorista", prov_txt, freg, "Consumidor"))
    minoristas_ids.append(cid)
    cid += 1
w("clientes.csv",
  ["id_cliente","nombre_cliente","tipo_cliente","provincia","fecha_registro","segmento_origen"],
  clientes)

# ---------------------------------------------------------------------------
# 7) VENTAS + DETALLE  (2 anios; mayoreo a ~80 locales/mes + retail diario)
# ---------------------------------------------------------------------------
canal_variantes = {
    1: ["Tienda fisica","tienda fisica","TIENDA FISICA","Tienda Fisica "," tienda  fisica"],
    2: ["Feria del agricultor","feria","Feria","FERIA DEL AGRICULTOR"],
    3: ["Mayoreo","mayoreo","MAYOREO","Venta mayoreo"],
    4: ["En linea","en linea","EN LINEA","Online","en  linea"],
}
nombre_prod_sucio = {
    101: ["Salsa Picante Habanero Lucho","SALSA PICANTE HABANERO LUCHO","salsa picante habanero lucho "],
    102: ["Chilero Criollo Lucho","chilero criollo lucho","Chilero Criollo  Lucho"],
    103: ["Salsa de Ajo Lucho","SALSA DE AJO LUCHO","salsa de ajo lucho"],
}
prod_ids   = [p[0] for p in productos]
precio_lst = {p[0]: p[4] for p in productos}
costo_unit = {p[0]: p[5] for p in productos}
estrella   = {p[0]: p[6] for p in productos}
nombre_prod= {p[0]: p[1] for p in productos}
# pesos de demanda: las 3 estrella concentran ventas
peso_prod = {pid: (50 if estrella[pid]==1 else 3) for pid in prod_ids}
peso_prod[101] = 50; peso_prod[102] = 42; peso_prod[103] = 38

ventas_rows = []
detalle_rows = []
venta_id = 1000
linea_global = 1

def estacion(m):
    if m in (11,12): return 1.6
    if m == 7:       return 1.25
    if m in (1,2):   return 0.8
    if m == 4:       return 1.1   # Semana Santa
    return 1.0

def nombre_linea(pid):
    if pid in nombre_prod_sucio and random.random() < 0.3:
        return random.choice(nombre_prod_sucio[pid])
    return nombre_prod[pid]

def costo_field(pid):
    return "" if random.random() < 0.04 else costo_unit[pid]

def agregar_factura(d, cliente, canal, promo, lineas):
    """lineas = lista de (pid, cantidad). Crea encabezado + detalle."""
    global venta_id, linea_global
    venta_id += 1
    canal_txt = random.choice(canal_variantes[canal])
    vendedor = random.choice([1,2,3,4])
    descp = promociones[promo][2]
    total = 0.0
    buf = []
    usados = set()
    for pid, cant in lineas:
        if pid in usados:
            continue
        usados.add(pid)
        precio = precio_lst[pid]
        if random.random() < 0.08:               # leve variacion de precio
            precio = int(precio * random.choice([0.95, 1.05]))
        bruto = precio * cant
        desc = round(bruto * descp, 2)
        buf.append([pid, nombre_linea(pid), cant, precio, bruto, desc, costo_field(pid)])
        total += (bruto - desc)
    if not buf:
        return
    ventas_rows.append([venta_id, d.isoformat(), cliente, canal, canal_txt, vendedor, promo, round(total,2)])
    for b in buf:
        detalle_rows.append([linea_global, venta_id] + b)
        linea_global += 1

# meses del periodo
meses = []
y, m = 2024, 1
while (y, m) <= (2025, 12):
    meses.append((y, m)); m += 1
    if m > 12: m = 1; y += 1

def dias_del_mes(y, m):
    ini = dt.date(y, m, 1)
    fin = dt.date(y + (m==12), (m % 12) + 1, 1)
    return [(ini + dt.timedelta(days=i)) for i in range((fin-ini).days)]

# --- (A) MAYOREO: ~80 puntos de venta activos por mes (compras distintas) ---
for (y, m) in meses:
    fac = estacion(m)
    dias = dias_del_mes(y, m)
    n_activos = int(round(np.random.normal(80, 1.5)))      # ~80 locales/mes
    n_activos = min(max(n_activos, 76), len(locales_ids))
    activos = random.sample(locales_ids, n_activos)
    for cli in activos:
        n_fact = 1 + (1 if random.random() < 0.30 else 0)  # 1-2 compras/mes
        for _ in range(int(round(n_fact * fac if fac>1 else n_fact))):
            d = random.choice(dias)
            promo = 1 if random.random() < 0.45 else (3 if (m in (11,12) and random.random()<0.3) else 0)
            n_lineas = random.choices([1,2,3], weights=[55,33,12])[0]
            lineas = []
            for _l in range(n_lineas):
                pid = random.choices(prod_ids, weights=[peso_prod[p] for p in prod_ids])[0]
                cant = random.choices([2,3,4,6,8], weights=[18,28,28,18,8])[0]
                lineas.append((pid, cant))
            agregar_factura(d, cli, 3, promo, lineas)

# --- (B) RETAIL diario: tienda fisica, feria, en linea (volumen pequeno) ---
for (y, m) in meses:
    fac = estacion(m)
    for d in dias_del_mes(y, m):
        wknd = 1.3 if d.weekday() in (5,6) else 1.0
        nfact = np.random.poisson(1.0 * fac * wknd)
        for _ in range(int(nfact)):
            canal = random.choices([1,2,4], weights=[50,30,20])[0]
            if canal == 1:
                cli = 1 if random.random() < 0.65 else random.choice(minoristas_ids)
            elif canal == 2:
                cli = 1 if random.random() < 0.85 else random.choice(minoristas_ids)
            else:
                cli = random.choice(minoristas_ids) if random.random() < 0.6 else 1
            promo = 2 if (canal==2 and random.random()<0.3) else \
                    (3 if (m in (11,12) and random.random()<0.2) else
                     (4 if random.random()<0.04 else 0))
            n_lineas = random.choices([1,2,3], weights=[62,28,10])[0]
            lineas = []
            for _l in range(n_lineas):
                pid = random.choices(prod_ids, weights=[peso_prod[p] for p in prod_ids])[0]
                cant = random.choices([1,2,3], weights=[70,22,8])[0]
                lineas.append((pid, cant))
            agregar_factura(d, cli, canal, promo, lineas)

# ---- INYECCION DE PROBLEMAS DE CALIDAD ----
ndup = max(20, int(len(detalle_rows)*0.005))
for _ in range(ndup):                       # a) duplicados exactos de lineas
    src = random.choice(detalle_rows)
    dup = src.copy(); dup[0] = linea_global; linea_global += 1
    detalle_rows.append(dup)
for _ in range(25):                          # b) outliers de cantidad (digitacion)
    r = random.choice(detalle_rows); r[4] = random.choice([999, 1500, 9999])
for _ in range(18):                          # c) cantidades cero / negativas
    r = random.choice(detalle_rows); r[4] = random.choice([0, -2, -1])
for _ in range(40):                          # d) canal_texto nulo en algunas ventas
    r = random.choice(ventas_rows); r[4] = ""
for _ in range(15):                          # e) cliente inexistente (FK rota)
    r = random.choice(ventas_rows); r[2] = 99999

w("ventas.csv",
  ["id_venta","fecha_venta","id_cliente","id_canal","canal_texto","id_vendedor","id_promocion","total_factura"],
  ventas_rows)
w("detalle_ventas.csv",
  ["id_linea","id_venta","id_producto","nombre_producto_texto","cantidad","precio_unitario","monto_bruto","descuento","costo_unitario"],
  detalle_rows)

# ---------------------------------------------------------------------------
# 8) MOVIMIENTOS DE INVENTARIO (snapshot mensual por producto)
# ---------------------------------------------------------------------------
salidas = defaultdict(int)
fecha_de_venta = {v[0]: v[1] for v in ventas_rows}
for d_ in detalle_rows:
    pid, cant, vid = d_[2], d_[4], d_[1]
    fecha = fecha_de_venta.get(vid)
    if fecha and isinstance(cant,(int,float)) and 0 < cant < 500:
        salidas[(pid, fecha[:7])] += int(cant)

inv_rows = []; inv_id = 1
existencias = {p[0]: random.randint(150, 500) for p in productos}
for pid in prod_ids:
    for (y, m) in meses:
        ym = f"{y:04d}-{m:02d}"
        ini = existencias[pid]
        sal = salidas.get((pid, ym), 0)
        objetivo = (sal*1.2) if estrella[pid]==1 else max(20, sal*1.5+30)
        ent = int(max(0, objetivo - (ini - sal)))
        fin = max(0, ini + ent - sal)
        existencias[pid] = fin
        inv_rows.append([inv_id, pid, ym+"-01", ini, ent, sal, fin, round(fin*costo_unit[pid],2)])
        inv_id += 1
w("movimientos_inventario.csv",
  ["id_mov","id_producto","fecha_corte","existencia_inicial","entradas","salidas","existencia_final","costo_inventario"],
  inv_rows)

# ---------------------------------------------------------------------------
# Resumen de calibracion (control interno; no se escribe a CSV)
# ---------------------------------------------------------------------------
margen_tot = 0.0; ingreso_tot = 0.0
for d_ in detalle_rows:
    pid, cant, _pre, bruto, desc = d_[2], d_[4], d_[5], d_[6], d_[7]
    if not isinstance(cant,(int,float)) or cant <= 0 or cant >= 500:
        continue
    neto = bruto - desc
    costo = costo_unit[pid] * cant
    ingreso_tot += neto; margen_tot += (neto - costo)
print("\nFuente operacional generada en data/raw/")
print(f"Ventas: {len(ventas_rows)} | lineas: {len(detalle_rows)} | clientes: {len(clientes)} | locales mayoreo: {len(locales_ids)}")
print(f"[CALIBRACION] ingreso/mes ~ CRC {ingreso_tot/24:,.0f} | utilidad/mes ~ CRC {margen_tot/24:,.0f} | margen ~ {100*margen_tot/ingreso_tot:.1f}%")
