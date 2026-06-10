# -*- coding: utf-8 -*-
"""
PASO 2 del pipeline: PERFILADO Y VALIDACION DE CALIDAD de la fuente operacional
ANTES del ETL. Genera un reporte (evidencia/etl_logs/reporte_calidad.md) con los
problemas detectados, que luego el ETL corrige.
"""
import os
import pandas as pd
import config
from utils import get_engine, get_logger

log = get_logger("02_calidad_datos")

def main():
    eng = get_engine("op")
    log.info("=== PERFILADO DE CALIDAD DE DATOS (pre-ETL) ===")
    clientes = pd.read_sql("SELECT * FROM clientes", eng)
    ventas   = pd.read_sql("SELECT * FROM ventas", eng)
    detalle  = pd.read_sql("SELECT * FROM detalle_ventas", eng)

    detalle["cantidad"] = pd.to_numeric(detalle["cantidad"], errors="coerce")
    ventas["id_cliente"] = pd.to_numeric(ventas["id_cliente"], errors="coerce")
    ids_cli = set(pd.to_numeric(clientes["id_cliente"]))

    hallazgos = []
    def add(dim, detalle_txt, n):
        hallazgos.append((dim, detalle_txt, int(n)))

    add("Completitud", "Clientes con fecha_registro nula/vacia",
        clientes["fecha_registro"].fillna("").str.strip().eq("").sum())
    add("Completitud", "Ventas con canal_texto nulo/vacio",
        ventas["canal_texto"].fillna("").str.strip().eq("").sum())
    add("Completitud", "Lineas con costo_unitario nulo",
        detalle["costo_unitario"].fillna("").astype(str).str.strip().eq("").sum())
    add("Validez", "Lineas con cantidad <= 0",
        (detalle["cantidad"] <= 0).sum())
    add("Validez", "Lineas con cantidad atipica (>500)",
        (detalle["cantidad"] > 500).sum())
    add("Unicidad", "Lineas duplicadas exactas (clave natural id_venta+producto+cant)",
        detalle.duplicated(subset=["id_venta","id_producto","cantidad","precio_unitario"]).sum())
    add("Integridad", "Ventas con id_cliente inexistente (FK rota)",
        (~ventas["id_cliente"].isin(ids_cli)).sum())
    add("Consistencia", "Variantes de texto distintas en provincia (cliente)",
        clientes["provincia"].nunique())
    add("Consistencia", "Variantes de texto distintas en canal_texto",
        ventas["canal_texto"].fillna("(nulo)").nunique())

    rep = pd.DataFrame(hallazgos, columns=["dimension_calidad","hallazgo","registros"])
    os.makedirs(config.LOG_DIR, exist_ok=True)
    csv_path = os.path.join(config.LOG_DIR, "reporte_calidad.csv")
    rep.to_csv(csv_path, index=False)

    md = ["# Reporte de calidad de datos (pre-ETL)\n",
          "Fuente: base operacional `op` de Las Salsas de Lucho.\n",
          "| Dimensión de calidad | Hallazgo | Registros |",
          "|---|---|---:|"]
    for _, r in rep.iterrows():
        md.append(f"| {r['dimension_calidad']} | {r['hallazgo']} | {r['registros']} |")
    md.append("\n> Estos hallazgos son tratados por las reglas R1–R10 del ETL "
              "(ver etl/etl_pipeline.py y la documentación).")
    md_path = os.path.join(config.LOG_DIR, "reporte_calidad.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    for _, r in rep.iterrows():
        log.info("%-13s | %-55s | %6d", r["dimension_calidad"], r["hallazgo"], r["registros"])
    log.info("Reporte de calidad escrito en %s", md_path)
    return rep

if __name__ == "__main__":
    main()
