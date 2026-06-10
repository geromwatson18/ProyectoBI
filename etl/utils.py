# -*- coding: utf-8 -*-
"""Utilidades compartidas: motores SQLAlchemy y bitacora del ETL."""
import os, sys, logging, datetime as dt
from sqlalchemy import create_engine
import config

def get_engine(rol):
    """rol = 'op' (operacional) | 'dw' (dimensional)."""
    url = config.URL_OPERACIONAL if rol == "op" else config.URL_DWH
    return create_engine(url, future=True)

def get_logger(nombre):
    os.makedirs(config.LOG_DIR, exist_ok=True)
    log = logging.getLogger(nombre)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s",
                            "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(os.path.join(config.LOG_DIR, f"{nombre}.log"),
                             mode="w", encoding="utf-8")
    fh.setFormatter(fmt); log.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout); sh.setFormatter(fmt); log.addHandler(sh)
    return log
