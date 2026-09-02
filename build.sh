#!/usr/bin/env bash
# Script para empacotar o app em um executável único.
# Uso:  ./build.sh            (usa .venv)
#       PYTHON=python ./build.sh   (usa outro interpretador)
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-.venv/bin/python}

echo "==> Gerando executável com PyInstaller..."
"$PY" -m PyInstaller CalculadoraIMC.spec --noconfirm

echo
echo "==> Concluído! Executável em: dist/CalculadoraIMC"