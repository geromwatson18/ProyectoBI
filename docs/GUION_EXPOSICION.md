# Guion de exposición — Las Salsas de Lucho
### Cómo entender el proyecto y cómo grabarte exponiéndolo

Este documento te explica **todo el proyecto en palabras sencillas** y te da un
**guion para grabarte** (≈15–18 min). Léelo una vez completo y luego usa la parte 3
como libreto.

---

## PARTE 1 · Entiende el proyecto en 5 minutos

**¿Qué es?** Una solución de *Inteligencia de Negocios* (BI) para una microempresa
ficticia-realista de salsas, "Las Salsas de Lucho". BI significa: tomar los datos
que el negocio ya genera (ventas, inventario) y convertirlos en información que
ayuda a decidir.

**El caso (los números que pediste):**

- Cada salsa se vende en botella de **200 ml a ₡3.000**.
- El negocio vende sobre todo por **mayoreo a ~80 puntos de venta** (locales reales
  de CR: pulperías, mini súper, sodas, restaurantes) cada mes.
- Genera **≈₡2,03 millones de ingreso al mes** y una **utilidad (ganancia) de
  ≈₡1,17 millones al mes** (margen ≈57,6 %).

**La cadena de la solución (esto es lo más importante que debes saber explicar):**

```
Fuente operacional  →   ETL   →   Modelo dimensional   →   Tablero
(datos crudos)      (limpieza)   (datos ordenados)        (gráficos)
```

1. **Fuente operacional**: los datos crudos del negocio (9 tablas: ventas, detalle,
   clientes, productos, inventario…), con errores reales (nulos, duplicados, textos
   mal escritos). Están en `data/raw/` como CSV.
2. **ETL** (Extraer–Transformar–Cargar): un programa en **Python** que lee esos
   datos, los **limpia y transforma** con 10 reglas, y los carga ordenados. Está en
   `etl/`. Se ejecuta con un solo comando.
3. **Modelo dimensional** (esquema estrella): la forma "ordenada" de guardar los
   datos para analizarlos. Tiene **2 tablas de hechos** (`fact_ventas`,
   `fact_inventario`) y **6 dimensiones** (tiempo, producto, cliente, canal,
   vendedor, promoción). Definido en `sql/`.
4. **Tablero** (dashboard): la app visual en **Streamlit + Plotly** con 6 vistas y
   gráficos que responden las preguntas del negocio. Está en `dashboard/app.py`.

**Las 5 preguntas de negocio que el proyecto responde:**

- **PN1** ¿Qué productos venden y cuáles rotan poco? → 3 salsas estrella = **85 %** del ingreso.
- **PN2** ¿Qué canal es más rentable? → Mayoreo = **91 %** del ingreso.
- **PN3** ¿Cómo es la estacionalidad? → picos en **nov–dic**, piso en ene–feb.
- **PN4** ¿Las promociones ayudan o dañan? → "Liquidación lenta" baja el margen a **45,6 %**.
- **PN5** (exploratoria) ¿Dependemos de pocos clientes? → **No**; el riesgo es de
  canal (todo es mayoreo) y de surtido (todo son 3 productos).

---

## PARTE 2 · Cada pieza, explicada para que la defiendas

> El profesor evaluará que **entiendas las decisiones**, no que leas. Esto te prepara.

**¿Por qué Python para el ETL y no Power BI?** Porque el enunciado exige una
herramienta de ETL **distinta** de Power BI/Tableau. Python (pandas + SQLAlchemy)
permite reglas de limpieza complejas y es 100 % reproducible: cualquiera corre un
comando y obtiene el mismo resultado.

**¿Qué es una "regla de transformación no trivial"?** No es solo copiar un dato; es
transformarlo con lógica de negocio. Tenemos 10 (R1–R10). Ejemplos para mencionar:
- **R1** — construir la *dimensión de tiempo* (de cada fecha derivamos año, mes,
  trimestre, temporada).
- **R3** — *homologar catálogos*: "MAYOREO", "mayoreo", "Venta mayoreo" → todo a un
  único valor limpio "Mayoreo".
- **R6** — *detectar outliers*: una venta de 9.999 botellas es un error de digitación
  y se descarta.
- **R8** — recalcular **margen** = ingreso neto − costo, e imputar costos faltantes.
- **R9** — si una venta apunta a un cliente que no existe, se reasigna a "No identificado".

**¿Qué es el esquema estrella y la "granularidad"?** La tabla de hechos guarda los
números (cantidad, monto, margen) al nivel más fino: **una línea de factura**. Las
dimensiones guardan los "para describir" (qué producto, qué cliente, qué fecha).
Granularidad = "cada fila representa una línea de venta de un producto".

**¿Qué son las llaves subrogadas?** Un ID propio del almacén (1, 2, 3…) independiente
del ID del sistema original. Sirve para no depender del sistema de origen.

**Calidad de datos**: ANTES de transformar, el programa `calidad_datos.py` cuenta los
problemas (16 fechas nulas, 40 canales vacíos, 24 duplicados, etc.) y deja un reporte
en `evidencia/etl_logs/`. Eso demuestra trazabilidad.

**¿De dónde salen los datos?** Son **sintéticos y anonimizados**, generados con una
semilla fija (`etl/generar_fuente_operacional.py`) para que el caso sea reproducible
y no exponga datos reales. (Ver "Lo que falta por hacer" al final.)

---

## PARTE 3 · Libreto para grabar (slide por slide)

> Abre `presentacion/Presentacion_Las_Salsas_de_Lucho.pptx`. Habla natural, no leas
> palabra por palabra. Tiempos aproximados entre paréntesis.

**Slide 1 — Portada (20 s).**
"Buenas, somos el grupo ___. Presentamos nuestra solución de Inteligencia de Negocios
para Las Salsas de Lucho, una PYME de salsas artesanales."

**Slide 2 — La organización (1 min).**
"Las Salsas de Lucho es una microempresa de Cartago. Vende botellas de 200 ml a
₡3.000. Su canal principal es el mayoreo: surte a unos 80 locales en todo el país.
Llevan las ventas en hojas de cálculo, lo que genera errores de datos."

**Slide 3 — Problema y preguntas (1.5 min).**
"El dueño decide por intuición. No sabe qué productos y canales le dejan ganancia, ni
cuánto inventario lento acumula. Definimos 5 preguntas de negocio que guían todo el
proyecto." (Léelas brevemente.)

**Slide 4 — Arquitectura (1.5 min).**
"La solución sigue una cadena: la fuente operacional pasa por un ETL en Python, llega
a un modelo dimensional en estrella, y se visualiza en un tablero. Usamos Python para
el ETL porque el curso pide una herramienta distinta de Power BI, y porque es
totalmente reproducible."

**Slide 5 — Fuente operacional (1.5 min).**
"La fuente tiene 9 tablas relacionadas con 2 años de historia: 3.655 ventas, 5.055
líneas de detalle, 137 clientes… A propósito incluye errores reales para que el ETL
los corrija." (Señala el diagrama del modelo de origen.)

**Slide 6 — Modelo dimensional (2 min).**
"Diseñamos un esquema estrella con 2 hechos: fact_ventas, al nivel de línea de
factura, y fact_inventario, un snapshot mensual por producto. Comparten las
dimensiones de tiempo y producto (dimensiones conformadas). Todo con llaves
subrogadas y una dimensión de tiempo obligatoria." (Explica granularidad con tus
palabras de la Parte 2.)

**Slide 7 — ETL, 10 reglas (2 min).**
"El ETL aplica 10 reglas no triviales." Menciona 3 o 4: dim_tiempo, homologación de
catálogos, detección de outliers, cálculo de margen. "Todo queda registrado en
bitácoras; el resultado son 4.989 líneas de venta limpias."

**Slide 8 — Calidad de datos (1 min).**
"Antes de transformar, perfilamos la calidad: nulos, duplicados, llaves rotas. Cada
problema lo corrige una regla. Esto da trazabilidad y confianza en los números."

**Slide 9 — Tablero (1 min).**
"El tablero tiene 6 vistas con segmentadores por año, canal y categoría. Aquí lo
mostraremos en vivo." (Si haces demo en vivo, ver Parte 4.)

**Slides 10–14 — Respuestas PN1 a PN5 (4–5 min, ~1 min c/u).**
Para cada una, di el hallazgo y la recomendación:
- **PN1**: "3 productos = 85 % del ingreso; las especialidades casi no rotan, ~390
  días de inventario. Recomendación: racionalizar el catálogo."
- **PN2**: "El mayoreo es el 91 %. Margen parejo entre canales. Riesgo: dependemos de
  un solo canal."
- **PN3**: "Demanda estacional, picos en nov–dic. Recomendación: producir las
  estrella antes de noviembre."
- **PN4**: "La promo 'Liquidación lenta' baja el margen a 45,6 % y casi no vende.
  Recomendación: eliminarla."
- **PN5**: "No dependemos de pocos clientes (top-5 = 6,8 %). El riesgo es de canal y
  de surtido. Geográficamente, 65 % en la GAM."

**Slide 15 — Hallazgos y recomendaciones (1 min).**
Resume los 5 hallazgos y las 5 recomendaciones.

**Slide 16 — Cierre (40 s).**
"Limitaciones: datos sintéticos, margen bruto. A futuro: pronóstico de demanda y
datos en tiempo real. Todo el código y la colaboración están en nuestro GitHub.
¡Gracias!"

---

## PARTE 4 · Demo en vivo del tablero (opcional, suma puntos)

En tu máquina, dentro de la carpeta del proyecto:

```bash
pip install -r requirements.txt
export BI_BACKEND=sqlite          # en Windows PowerShell:  $env:BI_BACKEND="sqlite"
cd etl
python run_pipeline.py            # genera datos y construye el almacén
cd ..
streamlit run dashboard/app.py    # abre el tablero en el navegador
```

Navega las 6 vistas y muestra los segmentadores. Con eso demuestras que la solución
**funciona de verdad**.

---

## PARTE 5 · Preguntas probables del profesor (y cómo responder)

- *"¿Por qué un esquema estrella y no copo de nieve?"* → Porque prioriza simplicidad
  y rapidez de consulta; las jerarquías caben en las dimensiones sin normalizar.
- *"¿Por qué dos tablas de hechos?"* → Ventas e inventario tienen distinta
  granularidad (línea de factura vs. snapshot mensual), pero comparten tiempo y
  producto; es una constelación de hechos.
- *"¿Cómo garantizan reproducibilidad?"* → Semilla fija + un único comando
  (`run_pipeline.py`) + pipeline agnóstico del motor (SQLite/PostgreSQL).
- *"¿Qué harían con más tiempo?"* → Integrar costos indirectos, pronóstico de demanda
  y conectar el sistema real de facturación.

---

## PARTE 6 · ⚠️ Lo que TÚ debes completar (yo no puedo hacerlo)

1. ~~Nombres~~ ✅ **Hecho:** tu nombre (Gerom Watson Araya — carné 2017168284) ya
   está en la portada del informe, el PPTX y el README.
2. **Firma de la carta de aceptación** — la carta ya está redactada y lista en
   `evidencia/requerimientos/Carta_Aceptacion_Las_Salsas_de_Lucho.pdf`. Solo falta
   que **Lucho la firme** (y complete fecha, cédula y contacto), la escaneás y la
   envías al profesor junto con el correo de aprobación (`02_correo_aprobacion.md`).
   **Esto es lo más urgente: sin la firma + el correo, el enunciado da nota CERO.**
3. **Subir a GitHub** — corre `inicializar_git.sh` (ver instrucciones dentro del
   archivo). Si tu carpeta tiene una subcarpeta `.git` rota, el script la borra solo.
4. **Tus commits** — el script ya crea el historial por fases; al final del archivo
   hay un ejemplo por si querés agregar commits propios adicionales.
5. **Grabar la exposición** (máx. 20 min) y pegar el enlace en el informe
   (sección 15) donde dice "[enlace por completar]".
6. **Recompilar si cambias texto**: el PDF se regenera con
   `pandoc docs/informe.md -o docs/Informe_Proyecto_BI_Las_Salsas_de_Lucho.pdf --pdf-engine=xelatex`
   y la presentación con `python presentacion/generar_presentacion.py`.

> Nota: la fecha de entrega del enunciado era 02/06/2026 y hoy ya pasó. Confirma con
> el profesor si tienes prórroga.
