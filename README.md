# 🌶️ Solución de Inteligencia de Negocios — Las Salsas de Lucho

Proyecto 02 · Curso de Inteligencia de Negocios · Tecnológico de Costa Rica (ATI)

Solución integral de BI para una **PYME comercial** de salsas artesanales: desde la
fuente operacional hasta un tablero analítico, pasando por un **modelo dimensional
en estrella** y un **proceso ETL reproducible** en Python sobre **PostgreSQL**.

> Producto: botella de **200 ml a ₡3.000**. Distribución por **~80 puntos de venta**
> (mayoreo) en todo Costa Rica, más tienda física, ferias y en línea.
> Resultado del periodo 2024–2025: ingreso ≈₡2,03 M/mes y **utilidad ≈₡1,17 M/mes**.
>
> Repositorio: <https://github.com/geromwatson18/ProyectoBI>

## 1. Problema de negocio
Las Salsas de Lucho vende tres salsas insignia de alta rotación y varias variedades
nuevas que rotan poco. La dueña del negocio no tiene visibilidad de qué productos y
canales dejan margen, cuánto inventario lento acumula, ni cómo planificar la
producción según la estacionalidad. Esta solución responde **5 preguntas de negocio**
con datos.

## 2. Arquitectura de la solución
```
Fuente operacional (CSV/PostgreSQL "salsas_op")
        │   extracción
        ▼
   ETL en Python (pandas + SQLAlchemy)  ── reglas R1..R10, validación de calidad
        │   carga
        ▼
Modelo dimensional estrella (PostgreSQL "salsas_dw")
   2 hechos · 6 dimensiones · dim_tiempo · llaves subrogadas
        │
        ▼
   Dashboard analítico (Streamlit + Plotly) · 6 vistas
```

## 3. Herramientas
| Capa | Herramienta |
|---|---|
| Almacenamiento | PostgreSQL 16 (bases `salsas_op` y `salsas_dw`) |
| ETL | Python 3.10 · pandas · SQLAlchemy · psycopg2 |
| Modelo dimensional | SQL (esquema estrella) |
| Visualización | Streamlit + Plotly |
| Diagramas | Graphviz |

## 4. Estructura del repositorio
```
gerom/
├── README.md
├── requirements.txt
├── docker-compose.yml          # levanta PostgreSQL con las 2 bases
├── data/
│   ├── raw/                     # fuente operacional (CSV generados)
│   └── processed/               # bases SQLite de verificación
├── sql/
│   ├── 00_crear_bases.sql
│   ├── 01_esquema_operacional.sql
│   ├── 02_esquema_dimensional.sql
│   └── 03_consultas_kpis.sql    # consultas que responden las preguntas
├── etl/
│   ├── config.py                # conexiones (Postgres o SQLite)
│   ├── generar_fuente_operacional.py
│   ├── cargar_operacional.py     # paso 1
│   ├── calidad_datos.py          # paso 2 (perfilado de calidad)
│   ├── etl_pipeline.py           # paso 3 (reglas R1..R10)
│   ├── run_pipeline.py           # orquestador end-to-end
│   └── utils.py
├── dashboard/
│   └── app.py                   # tablero Streamlit (6 vistas)
├── docs/
│   ├── Informe_Proyecto_BI_Las_Salsas_de_Lucho.pdf
│   ├── diccionario_datos.md
│   └── diagramas/               # modelo operacional y dimensional (PNG)
├── presentacion/
│   └── Presentacion_Las_Salsas_de_Lucho.pptx
└── evidencia/
    ├── requerimientos/          # carta, entrevista, minutas
    ├── etl_logs/                # bitácoras y reporte de calidad
    └── capturas/                # gráficos analíticos
```

## 5. Cómo ejecutar

### Opción A — PostgreSQL (entorno objetivo)
```bash
pip install -r requirements.txt
docker compose up -d                      # levanta PostgreSQL con salsas_op y salsas_dw
psql -h localhost -U postgres -d salsas_op -f sql/01_esquema_operacional.sql
psql -h localhost -U postgres -d salsas_dw -f sql/02_esquema_dimensional.sql
cd etl && python run_pipeline.py          # genera datos, carga, calidad y ETL
streamlit run ../dashboard/app.py         # abre el tablero
```

### Opción B — Verificación rápida sin servidor (SQLite)
```bash
pip install -r requirements.txt
export BI_BACKEND=sqlite
cd etl && python generar_fuente_operacional.py && python run_pipeline.py
BI_BACKEND=sqlite streamlit run ../dashboard/app.py
```
> El pipeline es **agnóstico del motor** gracias a SQLAlchemy. La opción B existe
> solo para reproducir/verificar la solución sin instalar PostgreSQL; el entorno
> objetivo del proyecto es PostgreSQL (Opción A).

## 6. Proceso ETL — reglas de transformación (no triviales)
| Regla | Descripción |
|---|---|
| R1 | Construcción de `dim_tiempo` (derivación de calendario y temporada). |
| R2 | Generación de llaves subrogadas en todas las dimensiones. |
| R3 | Homologación/normalización de catálogos (provincia, canal, producto). |
| R4 | Cálculo de antigüedad del cliente con imputación de nulos por mediana. |
| R5 | Segmentación de clientes (RFM simplificado). |
| R6 | Detección de outliers por canal (regla IQR). |
| R7 | Deduplicación de líneas de venta por clave natural. |
| R8 | Derivación y validación de medidas (neto, costo, margen). |
| R9 | Integridad referencial con miembros "No identificado". |
| R10 | Tratamiento de nulos y estandarización de formatos. |

## 7. Estudiante
- Gerom Watson Araya — carné 2017168284

## 8. Datos
Los datos son **sintéticos y anonimizados**, generados de forma reproducible
(`etl/generar_fuente_operacional.py`, semilla fija) a partir del caso real de la
PYME. No contienen información personal real.
