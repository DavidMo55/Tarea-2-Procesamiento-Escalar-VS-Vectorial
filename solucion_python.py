"""Solución: ciclos y vectores, validación, medición y exportación para MATLAB."""
import time
import statistics
import numpy as np


def generar_datos(n=1_000_000, semilla=42):
    """Equivalente al esquema rand(1, N) * 100 de la diapositiva."""
    rng = np.random.default_rng(semilla)
    x = rng.random(n) * 100
    y = rng.random(n) * 100
    return x, y


def distancias_for(x, y):
    """Código base: conserva esta función para comparar el antes y después."""
    N = len(x)
    distancias = np.zeros(N, dtype=np.float64)
    for i in range(N):
        distancias[i] = np.sqrt(x[i]**2 + y[i]**2)
    return distancias


def distancias_vectorizadas(x, y):
    """Aplica Pitágoras elemento a elemento, sin ciclos de Python."""
    return np.sqrt(x**2 + y**2)

def comparar_tiempos(x, y, repeticiones=5):
    if not isinstance(repeticiones, int) or repeticiones < 5:
        raise ValueError("Se requieren al menos cinco repeticiones.")
    original_x, original_y = x.copy(), y.copy()
    funciones = (distancias_for, distancias_vectorizadas)
    tiempos = [[], []]

    def validar(resultado):
        assert isinstance(resultado, np.ndarray)
        assert resultado.shape == x.shape
        assert resultado.dtype == np.float64
        np.testing.assert_array_equal(x, original_x)
        np.testing.assert_array_equal(y, original_y)

    # Calentamiento y referencia fuera del cronómetro.
    referencia = distancias_for(x, y)
    validar(referencia)
    calentamiento = distancias_vectorizadas(x, y)
    validar(calentamiento)
    np.testing.assert_allclose(calentamiento, referencia, rtol=1e-12, atol=1e-12)
    del calentamiento

    for repeticion in range(repeticiones):
        orden = (0, 1) if repeticion % 2 == 0 else (1, 0)
        for indice in orden:
            inicio = time.perf_counter()
            resultado = funciones[indice](x, y)
            duracion = time.perf_counter() - inicio
            tiempos[indice].append(duracion)
            # Validaciones fuera del intervalo medido; se revisa todo el arreglo.
            validar(resultado)
            np.testing.assert_allclose(resultado, referencia, rtol=1e-12, atol=1e-12)
            if indice == 1:
                distancias = resultado
            del resultado

    tiempo_for = statistics.median(tiempos[0])
    tiempo_vectorizado = statistics.median(tiempos[1])
    return distancias, {
        "tiempo_for_s": tiempo_for,
        "tiempo_vectorizado_s": tiempo_vectorizado,
        "aceleracion": tiempo_for / tiempo_vectorizado,
    }

def graficar_resultados(x, y, distancias):
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(2026)
    indices = rng.choice(len(x), size=min(10_000, len(x)), replace=False)
    figura, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    puntos = ax1.scatter(x[indices], y[indices], c=distancias[indices],
                         s=5, cmap="viridis", alpha=0.75)
    ax1.set(xlabel="Coordenada x", ylabel="Coordenada y",
            title="A · Distancia al origen (muestra de hasta 10 000)")
    ax1.set_aspect("equal", adjustable="box")
    figura.colorbar(puntos, ax=ax1, label="Distancia al origen")
    ax2.hist(distancias, bins=60, color="#337eaa", edgecolor="white", linewidth=0.3)
    ax2.set(xlabel="Distancia al origen", ylabel="Frecuencia (número de puntos)",
            title="B · Distancias de todos los puntos")
    return figura

def comprobar_casos(funcion):
    """Casos pequeños conocidos; no sustituyen la validación del millón."""
    casos = [
        ([0, 3, 6, 0, 0.3], [0, 4, 8, 5, 0.4], [0, 5, 10, 5, 0.5]),
        ([5], [12], [13]),
        ([], [], []),
    ]
    for valores_x, valores_y, esperado in casos:
        x = np.array(valores_x, dtype=np.float64)
        y = np.array(valores_y, dtype=np.float64)
        original_x, original_y = x.copy(), y.copy()
        resultado = funcion(x, y)
        if not isinstance(resultado, np.ndarray):
            raise AssertionError("Devuelve un arreglo NumPy.")
        if resultado.shape != x.shape or resultado.dtype != np.float64:
            raise AssertionError("Revisa la forma (N,) y el tipo float64.")
        np.testing.assert_allclose(resultado, esperado, rtol=1e-12, atol=1e-12)
        np.testing.assert_array_equal(x, original_x)
        np.testing.assert_array_equal(y, original_y)
    print(f"{funcion.__name__}: casos pequeños correctos.")


if __name__ == "__main__":
    from pathlib import Path
    import json
    import platform
    import matplotlib
    destino = Path(__file__).resolve().parent
    comprobar_casos(distancias_for)
    comprobar_casos(distancias_vectorizadas)
    x, y = generar_datos()
    distancias, resumen = comparar_tiempos(x, y)
    print(f"{'Método':<20} {'Mediana (s)':>14}")
    print(f"{'Ciclo for':<20} {resumen['tiempo_for_s']:>14.6f}")
    print(f"{'Vectorizado':<20} {resumen['tiempo_vectorizado_s']:>14.6f}")
    print(f"Aceleración: {resumen['aceleracion']:.2f} veces")
    print("Validación completa correcta: 1 000 000 de puntos.")
    figura = graficar_resultados(x, y, distancias)
    figura.savefig(destino / "distancias.png", dpi=160)
    # 17 cifras significativas conservan los float64 al leerlos en MATLAB.
    np.savetxt(destino / "coordenadas.csv", np.column_stack((x, y)),
               delimiter=",", header="x,y", comments="", fmt="%.17g")
    datos = dict(resumen, python=platform.python_version(), numpy=np.__version__,
                 matplotlib=matplotlib.__version__, equipo=platform.platform(),
                 arquitectura=platform.machine())
    (destino / "resultados_python.json").write_text(json.dumps(datos, indent=2))
