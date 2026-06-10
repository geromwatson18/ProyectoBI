# -*- coding: utf-8 -*-
"""
PASO 1 del pipeline: cargar los CSV de data/raw/ a la BASE OPERACIONAL.
Esto simula la extraccion desde el sistema transaccional real y deja la fuente
disponible para que el ETL la consuma con trazabilidad completa.
"""
import os
import pandas as pd
from sqlalchemy import text
import config
from utils import get_engine, get_logger

log = get_logger("01_carga_operacional")

ARCHIVOS = {
    "categorias":             "categorias.csv",
    "productos":              "productos.csv",
    "canales":                "canales.csv",
    "vendedores":             "vendedores.csv",
    "promociones":            "promociones.csv",
    "clientes":               "clientes.csv",
    "ventas":                 "ventas.csv",
    "detalle_ventas":         "detalle_ventas.csv",
    "movimientos_inventario": "movimientos_inventario.csv",
}

def main():
    eng = get_engine("op")
    log.info("=== CARGA DE FUENTE OPERACIONAL -> %s ===", eng.url)
    total = 0
    for tabla, archivo in ARCHIVOS.items():
        ruta = os.path.join(config.RAW_DIR, archivo)
        df = pd.read_csv(ruta, dtype=str)          # se carga TAL CUAL (crudo)
        df.to_sql(tabla, eng, if_exists="replace", index=False)
        log.info("Cargada op.%-24s %6d filas", tabla, len(df))
        total += len(df)
    log.info("Carga operacional finalizada. Total filas: %d", total)
    return total

if __name__ == "__main__":
    main()
