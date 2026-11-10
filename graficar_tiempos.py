"""Une las mediciones reales de los tres programas y genera gráficas/tablas."""
from pathlib import Path
import csv
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CARPETA = Path(__file__).resolve().parent


def main():
    filas = []
    for nombre in ('python', 'cpp', 'matlab'):
        with (CARPETA / f'tiempos_{nombre}.csv').open() as archivo:
            datos = list(csv.DictReader(archivo))
        assert len(datos) == 12, f'Faltan mediciones: {nombre}'
        for fila in datos:
            for campo in ('dimension', 'N'):
                fila[campo] = int(fila[campo])
            for campo in ('for_s', 'vectorial_s', 'aceleracion'):
                fila[campo] = float(fila[campo])
                assert fila[campo] > 0
        assert {(f['dimension'],f['N']) for f in datos} == {
            (d,n) for d in (2,3) for n in (10,100,1000,10000,100000,1000000)}
        filas.extend(datos)
    with (CARPETA / 'tiempos_completos.csv').open('w', newline='') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader(); escritor.writerows(filas)
    lenguajes = list(dict.fromkeys(f['lenguaje'] for f in filas))
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    figura, ejes = plt.subplots(3, 2, figsize=(13, 12), sharex=True, sharey=True,
                               constrained_layout=True)
    figura.suptitle('Distancias al origen: tiempo con ciclos y con vectores\n'
                    'Mediana de 5 mediciones · mismos datos · escalas logarítmicas', fontsize=16)
    for fila_ejes, lenguaje in zip(ejes, lenguajes):
        for eje, dimension in zip(fila_ejes, (2,3)):
            datos = [f for f in filas if f['lenguaje']==lenguaje and f['dimension']==dimension]
            n = [f['N'] for f in datos]
            eje.loglog(n, [f['for_s'] for f in datos], 'o-', color='#c34b36', label='Ciclo for')
            eje.loglog(n, [f['vectorial_s'] for f in datos], 's-', color='#177e89', label='Vectorial')
            eje.set_title(f'{lenguaje} · {dimension}D')
            eje.set_ylabel('Tiempo (segundos)')
            eje.set_xlabel('Número de puntos (N)')
            eje.grid(True, which='major', alpha=.25)
            eje.legend()
    figura.savefig(CARPETA / 'grafica_tiempos.png', dpi=170)
    plt.close(figura)
    figura, ejes = plt.subplots(1,2, figsize=(13,5), constrained_layout=True)
    for eje, dimension in zip(ejes, (2,3)):
        for lenguaje, color in zip(lenguajes, ('#177e89','#ad5e17','#6e59a5')):
            datos = [f for f in filas if f['lenguaje']==lenguaje and f['dimension']==dimension]
            eje.loglog([f['N'] for f in datos], [f['aceleracion'] for f in datos], 'o-',
                       label=lenguaje, color=color)
        eje.axhline(1, color='#555555', linestyle='--', linewidth=1, label='Igual tiempo (1×)')
        eje.set(title=f'Aceleración · {dimension}D', xlabel='Número de puntos (N)',
                ylabel='Tiempo for / tiempo vectorial')
        eje.grid(True, which='major', alpha=.25); eje.legend()
    figura.savefig(CARPETA / 'grafica_aceleracion.png', dpi=170)
    plt.close(figura)
    informe(filas, lenguajes)


def informe(filas, lenguajes):
    entorno = json.loads((CARPETA / 'entorno_python.json').read_text())
    texto = '''# Ejercicio 2 — Comparación escalar y vectorial en 2D y 3D

## Objetivo y entrega
Comparar dos formas de calcular las distancias al origen de 10, 100, 1 000, 10 000, 100 000 y 1 000 000 de puntos, en dos y tres dimensiones, en **Python, C++ y lenguaje MATLAB**. Hay 36 combinaciones de lenguaje, dimensión y tamaño; cada una incluye ambos métodos, con cinco repeticiones por método: **360 mediciones**, además de los calentamientos.

El programa `.m` se ejecutó con **GNU Octave**, un entorno compatible con gran parte del lenguaje MATLAB. Sus tiempos se identifican como “MATLAB (GNU Octave)”: no son mediciones del producto MATLAB. Para obtener tiempos de MATLAB, ejecutar el mismo archivo allí y regenerar las gráficas. El rendimiento de su compilador JIT puede ser muy distinto.

## 1. Fórmula matemática
La distancia se obtiene aplicando el teorema de Pitágoras:

- En 2D: `d = sqrt(x² + y²)`.
- En 3D: `d = sqrt(x² + y² + z²)`.

Por ejemplo, `(3,4)` está a distancia 5 y `(3,4,12)` está a distancia 13. No se calculan distancias entre pares de puntos.

## 2. Procedimiento
1. Python genera tres vectores de un millón de coordenadas uniformes en `[0,100)`, con `default_rng(42)`, y los exporta. Para cada N se toman las primeras N coordenadas; 2D utiliza x e y, y 3D agrega z.
2. C++ y MATLAB leen exactamente los mismos números. El archivo `coordenadas.bin` contiene tres bloques (x, y, z), cada uno con 1 000 000 de float64 little-endian. Pesa 24 000 000 bytes. Se evita generar datos distintos con semillas de otros lenguajes.
3. La versión escalar reserva un vector de resultados y aplica la fórmula a cada punto dentro de un `for`.
4. La versión vectorial aplica operaciones algebraicas a los arreglos completos. No contiene ciclos explícitos ni utiliza una función especializada que calcule la distancia.
5. Para cada combinación se calientan ambas funciones una vez. Después se miden cinco ejecuciones de cada método, alternando el orden de ejecución.
6. Se verifica cada resultado fuera del cronómetro. Se obtiene la mediana de las cinco duraciones y la aceleración `mediana_for / mediana_vectorial`.
7. Se reúnen los CSV y se grafican los tiempos y las aceleraciones.

Los bucles para recorrer tamaños, dimensiones y repeticiones son parte del experimento; los que se eliminan son los del cálculo vectorial de distancias.

## 3. De ciclos a sintaxis algebraica

| Lenguaje | Expresión vectorial 2D | Expresión vectorial 3D |
|---|---|---|
| Python / NumPy | `np.sqrt(x**2 + y**2)` | `np.sqrt(x**2 + y**2 + z**2)` |
| C++ / Eigen | `(x.square() + y.square()).sqrt().eval()` | `(x.square() + y.square() + z.square()).sqrt().eval()` |
| MATLAB / Octave | `sqrt(x.^2 + y.^2)` | `sqrt(x.^2 + y.^2 + z.^2)` |

En cada posición i, las expresiones vectoriales calculan exactamente la fórmula del ciclo. Python aplica `**2` elemento a elemento a arreglos NumPy. Eigen utiliza `ArrayXd` (arreglos de double) y `square()`. En MATLAB, `.^` es potencia elemento a elemento; `^` es potencia matricial. La suma y la raíz cuadrada se aplican a cada posición.

## 4. Cronometría y validación
- Python utiliza `time.perf_counter()`; C++ utiliza `std::chrono::steady_clock`; MATLAB/Octave utiliza `tic/toc`.
- Se incluyen la creación del resultado y los temporales del cálculo. Se excluyen generación, lectura/escritura de archivos, selección de datos, comprobaciones, impresiones y gráficas.
- Se verifica tamaño, precisión double/float64 y que las entradas se conserven. En C++, `ArrayXd` fija el tipo double; las funciones reciben las entradas como referencias constantes.
- Se prueban puntos conocidos, coordenadas negativas, el origen y arreglos vacíos. Todos los resultados de cada ejecución se comparan con la referencia escalar, no únicamente una muestra.
- La tolerancia es `abs(resultado - referencia) <= 1e-12 + 1e-12 * abs(referencia)`. En Python se aplica `np.testing.assert_allclose`.
- La validación consume el resultado de C++, evitando que todo el cálculo sea descartado por no utilizarse. Se compiló con optimización `-O3`, sin `-ffast-math`.

Los tiempos de N pequeño incluyen costos de llamada, reserva y cronómetro; pueden fluctuar o no crecer de forma monótona. Cinco repeticiones describen esta ejecución, no constituyen una garantía ni un estudio estadístico exhaustivo.

## 5. Resultados medidos
Todos los tiempos de las tablas están en **segundos**. Una aceleración mayor que 1 favorece al método vectorial; menor que 1 favorece al ciclo.

'''
    for lenguaje in lenguajes:
        texto += f'### {lenguaje}\n\n| Dimensión | N | Ciclo for (s) | Vectorial (s) | Aceleración |\n|---|---:|---:|---:|---:|\n'
        for f in filas:
            if f['lenguaje'] == lenguaje:
                texto += f"| {f['dimension']}D | {f['N']:,} | {f['for_s']:.9g} | {f['vectorial_s']:.9g} | {f['aceleracion']:.3f}× |\n"
        texto += '\n'
    texto += '''## 6. Gráficas e interpretación

![Tiempos de los tres lenguajes, en 2D y 3D](grafica_tiempos.png)

Cada panel corresponde a un lenguaje y una dimensión. La curva roja representa ciclos y la azul representa operaciones vectoriales. Las escalas son logarítmicas para que puedan verse seis tamaños de entrada y tiempos de órdenes de magnitud muy distintos. Los seis paneles comparten la escala de tiempo.

![Aceleración por tamaño de entrada](grafica_aceleracion.png)

La línea de 1× representa tiempos iguales. Por encima, la versión vectorial tarda menos; por debajo, el ciclo tarda menos.

'''
    for lenguaje in lenguajes:
        final = [f for f in filas if f['lenguaje']==lenguaje and f['N']==1000000]
        texto += f"- **{lenguaje}, un millón de puntos:** " + '; '.join(
            f"{f['dimension']}D: {f['for_s']:.6f} s con ciclo y {f['vectorial_s']:.6f} s vectorial ({f['aceleracion']:.2f}×)" for f in final) + '.\n'
    texto += '''
## 7. Qué explica las diferencias
Las dos versiones tienen complejidad temporal O(N). La vectorización mejora las constantes de ejecución, no cambia el orden de complejidad. El resultado requiere O(N) memoria: un millón de double ocupa 8 MB; las tres coordenadas ocupan 24 MB.

En Python, NumPy evita interpretar un millón de iteraciones y ejecuta operaciones compiladas; la expresión crea temporales para cuadrados y sumas. En C++, el ciclo ya está compilado y el compilador puede optimizarlo o vectorizarlo. Eigen puede fusionar expresiones y utilizar instrucciones SIMD cuando el equipo y la compilación lo permiten. Por eso no se espera la misma aceleración que en Python, ni que la versión vectorial gane siempre.

Vectorización a nivel del código fuente no significa necesariamente paralelismo en varios núcleos. No se atribuyen estas operaciones elementales a BLAS o LAPACK. Además, eliminar el `for` del código del usuario no elimina el recorrido de los elementos dentro de las bibliotecas.

En 3D hay una coordenada adicional que leer, elevar al cuadrado y sumar; esto agrega trabajo, pero no obliga a que cada medición sea mayor que su equivalente en 2D debido al ruido y al comportamiento de memoria. Los tiempos medidos en Octave no predicen los de MATLAB.

## 8. Entorno registrado

'''
    texto += f"Python {entorno['python']}; NumPy {entorno['numpy']}; sistema {entorno['sistema']}; arquitectura {entorno['maquina']}.\n\n"
    for nombre in ('cpp','matlab'):
        texto += '```text\n' + (CARPETA/f'entorno_{nombre}.txt').read_text() + '```\n\n'
    texto += 'Los CSV `ensayos_*.csv` conservan las 360 mediciones individuales; `tiempos_completos.csv` reúne las 36 filas de medianas. Las gráficas muestran resultados reales, sin sustituir tiempos pendientes por estimaciones.\n'
    (CARPETA / 'INFORME.md').write_text(texto)
    print('Generados: tiempos_completos.csv, dos gráficas e INFORME.md')


if __name__ == '__main__':
    main()
