"""Comparación escalar/vectorial en 2D y 3D. Ejecutar antes de C++ y MATLAB."""
from pathlib import Path
import csv
import importlib
import json
import platform
import statistics
import time
try:
    np = importlib.import_module('numpy')
except ModuleNotFoundError as error:
    if error.name != 'numpy':
        raise
    raise SystemExit('Falta NumPy. Instálalo con: python -m pip install numpy') from error

CARPETA = Path(__file__).resolve().parent
TAMANOS = (10, 100, 1_000, 10_000, 100_000, 1_000_000)
REPETICIONES = 5


def distancias_for(x, y, z=None):
    salida = np.empty(x.size, dtype=np.float64)
    if z is None:
        for i in range(x.size):
            salida[i] = np.sqrt(x[i]**2 + y[i]**2)
    else:
        for i in range(x.size):
            salida[i] = np.sqrt(x[i]**2 + y[i]**2 + z[i]**2)
    return salida


def distancias_vectoriales(x, y, z=None):
    if z is None:
        return np.sqrt(x**2 + y**2)
    return np.sqrt(x**2 + y**2 + z**2)


def validar(salida, referencia):
    assert salida.shape == referencia.shape and salida.dtype == np.float64
    np.testing.assert_allclose(salida, referencia, rtol=1e-12, atol=1e-12)


def comprobar_casos():
    for funcion in (distancias_for, distancias_vectoriales):
        x = np.array([0., 3., -3., 1.])
        y = np.array([0., 4., 4., 2.])
        z = np.array([0., 12., -12., 2.])
        validar(funcion(x, y), np.array([0., 5., 5., np.sqrt(5.)]))
        validar(funcion(x, y, z), np.array([0., 13., 13., 3.]))
        validar(funcion(x[:0], y[:0]), np.empty(0))
        validar(funcion(x[:0], y[:0], z[:0]), np.empty(0))


def main():
    comprobar_casos()
    rng = np.random.default_rng(42)
    # Tres bloques consecutivos: todas las x, todas las y y todas las z.
    datos = rng.random((3, TAMANOS[-1])) * 100
    datos.astype('<f8').tofile(CARPETA / 'coordenadas.bin')
    original = datos.copy()
    filas, ensayos = [], []
    for dimension in (2, 3):
        for n in TAMANOS:
            argumentos = tuple(datos[k, :n] for k in range(dimension))
            funciones = (distancias_for, distancias_vectoriales)
            # Calentamiento; fuera de las mediciones.
            referencia = funciones[0](*argumentos)
            validar(funciones[1](*argumentos), referencia)
            tiempos = [[], []]
            for repeticion in range(REPETICIONES):
                orden = (0, 1) if repeticion % 2 == 0 else (1, 0)
                for indice in orden:
                    inicio = time.perf_counter()
                    salida = funciones[indice](*argumentos)
                    duracion = time.perf_counter() - inicio
                    tiempos[indice].append(duracion)
                    validar(salida, referencia)
                    np.testing.assert_array_equal(datos, original)
                    ensayos.append(['Python', dimension, n, repeticion + 1,
                                    'for' if indice == 0 else 'vectorial', duracion])
                    del salida
            a, b = map(statistics.median, tiempos)
            filas.append(['Python', dimension, n, a, b, a / b])
            print(f'Python {dimension}D N={n:7d}: for={a:.9f} s; vector={b:.9f} s; {a/b:.2f}x')
    guardar_csv(CARPETA / 'tiempos_python.csv',
                ['lenguaje', 'dimension', 'N', 'for_s', 'vectorial_s', 'aceleracion'], filas)
    guardar_csv(CARPETA / 'ensayos_python.csv',
                ['lenguaje', 'dimension', 'N', 'repeticion', 'metodo', 'segundos'], ensayos)
    (CARPETA / 'entorno_python.json').write_text(json.dumps({
        'python': platform.python_version(), 'numpy': np.__version__,
        'sistema': platform.platform(), 'maquina': platform.machine(),
        'repeticiones': REPETICIONES, 'semilla': 42}, indent=2))


def guardar_csv(ruta, columnas, filas):
    with ruta.open('w', newline='') as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(columnas)
        escritor.writerows(filas)


if __name__ == '__main__':
    main()
