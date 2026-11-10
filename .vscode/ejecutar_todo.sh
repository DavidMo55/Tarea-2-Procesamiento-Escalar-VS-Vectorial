#!/bin/zsh
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH='/Users/salieri/Documents/Codex/2026-11-08/sol/work/python_packages'
export MPLCONFIGDIR='/Users/salieri/Documents/Codex/2026-11-08/sol/work/mpl'
export OCTAVE_HOME='/Users/salieri/Documents/Codex/2026-11-08/sol/work/runtime/octave'
export OCTAVE_IMAGE_PATH="$PWD"
python_tarea='/Users/salieri/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
printf '\n[1/5] Compilando C++...\n'
clang++ -std=c++17 -O3 -DNDEBUG -I '/Users/salieri/Documents/Codex/2026-11-08/sol/work/runtime/eigen-3.4.0' distancias_cpp.cpp -o distancias_cpp
printf '\n[2/5] Ejecutando Python...\n'
"$python_tarea" -u distancias_python.py
printf '\n[3/5] Ejecutando C++...\n'
./distancias_cpp .
printf '\n[4/5] Ejecutando MATLAB con GNU Octave (puede tardar varios minutos)...\n'
"$OCTAVE_HOME/bin/octave-cli" --no-init-file --no-site-file --no-history --quiet --eval "distancias_matlab"
printf '\n[5/5] Generando gráficas e informe...\n'
"$python_tarea" graficar_tiempos.py
printf '\nTERMINADO. Abre INFORME.md, grafica_tiempos.png y grafica_aceleracion.png.\n'
