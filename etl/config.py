# -*- coding: utf-8 -*-
"""
Configuracion central del proyecto.

El pipeline es AGNOSTICO DEL MOTOR gracias a SQLAlchemy. Se definen dos
conexiones logicas:
  - OPERACIONAL : base transaccional de origen (replica de la fuente real).
  - DWH         : almacen dimensional (esquema estrella) para analitica.

Por defecto apunta a PostgreSQL (entorno objetivo del proyecto). Para una
ejecucion rapida y reproducible SIN servidor (verificacion/CI) se puede
exportar BI_BACKEND=sqlite y se usaran archivos .db locales.

Variables de entorno soportadas:
  BI_BACKEND = postgres | sqlite        (default: postgres)
  PG_HOST, PG_PORT, PG_USER, PG_PASSWORD
  PG_DB_OP   (default salsas_op)        base operacional
  PG_DB_DW   (default salsas_dw)        base dimensional
"""
import os, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
RAW_DIR  = os.path.join(ROOT, "data", "raw")
PROC_DIR = os.path.join(ROOT, "data", "processed")
LOG_DIR  = os.path.join(ROOT, "evidencia", "etl_logs")

BACKEND = os.getenv("BI_BACKEND", "postgres").lower()

def _pg_url(db):
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    user = os.getenv("PG_USER", "postgres")
    pwd  = os.getenv("PG_PASSWORD", "postgres")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"

if BACKEND == "sqlite":
    # Las bases SQLite se ubican por defecto en data/processed/ (junto al proyecto),
    # de modo que el tablero abra directamente. Se puede sobrescribir con BI_SQLITE_DIR.
    _SQLITE_DIR = os.getenv("BI_SQLITE_DIR", PROC_DIR)
    os.makedirs(_SQLITE_DIR, exist_ok=True)
    URL_OPERACIONAL = f"sqlite:///{os.path.join(_SQLITE_DIR, 'salsas_op.db')}"
    URL_DWH         = f"sqlite:///{os.path.join(_SQLITE_DIR, 'salsas_dw.db')}"
else:
    URL_OPERACIONAL = _pg_url(os.getenv("PG_DB_OP", "salsas_op"))
    URL_DWH         = _pg_url(os.getenv("PG_DB_DW", "salsas_dw"))

# Parametros de negocio usados por el ETL
FECHA_INICIO_DIM_TIEMPO = "2024-01-01"
FECHA_FIN_DIM_TIEMPO    = "2025-12-31"
UMBRAL_OUTLIER_IQR      = 1.5     # factor IQR para deteccion de atipicos
MIEMBRO_NO_IDENTIFICADO = "No identificado"
