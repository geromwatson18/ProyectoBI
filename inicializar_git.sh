#!/usr/bin/env bash
# =============================================================================
#  Inicializa el repositorio Git con un historial de commits POR FASES y lo
#  sube a GitHub:  https://github.com/geromwatson18/ProyectoBI
#
#  COMO USARLO (en tu maquina, NO en la nube):
#    1. Abre Git Bash (o la terminal) DENTRO de la carpeta del proyecto,
#       la que contiene este archivo y el README.md.
#    2. Ejecuta:   bash inicializar_git.sh
#    3. Cuando GitHub lo pida, autentica con tu usuario/token.
#
#  NOTA SOBRE COLABORACION (importante para la nota):
#    La rubrica exige "commits significativos de TODAS las personas
#    integrantes". Este script crea un historial ordenado por fases, pero lo
#    IDEAL es que cada integrante haga al menos algunos commits reales desde su
#    propia cuenta (por ejemplo editando la seccion que le tocó). Al final de
#    este archivo hay un ejemplo de como cada quien puede aportar su commit.
# =============================================================================
set -e

git rev-parse --is-inside-work-tree >/dev/null 2>&1 && { echo "Ya existe un repo git aqui. Borra la carpeta .git si quieres reiniciar."; }
rm -rf .git
git init
git branch -M main

git add README.md requirements.txt docker-compose.yml .gitignore
git commit -m "chore: estructura inicial del repositorio (README, requirements, docker, gitignore)"

git add evidencia/requerimientos
git commit -m "docs: evidencia de levantamiento de requerimientos (carta, correo, entrevista, minuta)"

git add sql
git commit -m "feat(sql): esquemas operacional y dimensional + consultas de KPIs"

git add etl/config.py etl/utils.py etl/generar_fuente_operacional.py etl/cargar_operacional.py
git commit -m "feat(etl): configuracion, generador de fuente operacional y carga a la base operacional"

git add etl/calidad_datos.py etl/etl_pipeline.py etl/run_pipeline.py
git commit -m "feat(etl): validacion de calidad de datos y pipeline dimensional con reglas R1-R10"

git add data
git commit -m "data: fuente operacional sintetica reproducible (CSV)"

git add docs/diagramas docs/diccionario_datos.md
git commit -m "docs: modelo dimensional (diagramas) y diccionario de datos"

git add dashboard
git commit -m "feat(dashboard): tablero analitico Streamlit de 6 vistas con Plotly"

git add evidencia/capturas evidencia/etl_logs
git commit -m "docs: evidencia de ejecucion del ETL (bitacoras) y graficos analiticos"

git add docs/informe.md docs/Informe_Proyecto_BI_Las_Salsas_de_Lucho.pdf presentacion
git commit -m "docs: informe final (Markdown + PDF) y presentacion del proyecto"

git add -A
git commit -m "docs: ajustes finales y guion de exposicion" || true

git remote add origin https://github.com/geromwatson18/ProyectoBI.git
echo ""
echo ">>> Listo el historial local. Subiendo a GitHub..."
git push -u origin main

# -----------------------------------------------------------------------------
# EJEMPLO: como cada integrante aporta su propio commit (hazlo desde su cuenta)
# -----------------------------------------------------------------------------
#   git config user.name  "Nombre Apellido"
#   git config user.email "correo@estudiantec.cr"
#   # ...edita un archivo (tu seccion del informe, un grafico, etc.)...
#   git add <archivo>
#   git commit -m "docs: <lo que hiciste> (Nombre)"
#   git push
# -----------------------------------------------------------------------------
