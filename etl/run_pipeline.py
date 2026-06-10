# -*- coding: utf-8 -*-
"""Orquestador: ejecuta el pipeline completo de punta a punta."""
import generar_fuente_operacional   # (regenera CSV si se desea; idempotente)
import cargar_operacional, calidad_datos, etl_pipeline
from utils import get_logger
log = get_logger("00_orquestador")

if __name__ == "__main__":
    log.info("################ PIPELINE BI LAS SALSAS DE LUCHO ################")
    cargar_operacional.main()
    calidad_datos.main()
    etl_pipeline.main()
    log.info("################ PIPELINE COMPLETADO ################")
