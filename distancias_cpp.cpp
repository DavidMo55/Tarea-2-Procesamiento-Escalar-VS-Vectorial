// C++17 + Eigen: fórmula algebraica elemento a elemento, sin bucle explícito.
#include <Eigen/Dense>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
using Eigen::ArrayXd;
using Reloj = std::chrono::steady_clock;

ArrayXd distancias_for(const ArrayXd& x, const ArrayXd& y,
                       const ArrayXd& z, int dimension) {
    ArrayXd salida(x.size());
    if (dimension == 2) {
        for (Eigen::Index i = 0; i < x.size(); ++i)
            salida(i) = std::sqrt(x(i)*x(i) + y(i)*y(i));
    } else {
        for (Eigen::Index i = 0; i < x.size(); ++i)
            salida(i) = std::sqrt(x(i)*x(i) + y(i)*y(i) + z(i)*z(i));
    }
    return salida;
}

ArrayXd distancias_vectoriales(const ArrayXd& x, const ArrayXd& y,
                               const ArrayXd& z, int dimension) {
    if (dimension == 2) return (x.square() + y.square()).sqrt().eval();
    return (x.square() + y.square() + z.square()).sqrt().eval();
}

void validar(const ArrayXd& resultado, const ArrayXd& referencia) {
    if (resultado.size() != referencia.size() ||
        !(resultado.isFinite().all()) ||
        !((resultado-referencia).abs() <= 1e-12 + 1e-12*referencia.abs()).all())
        throw std::runtime_error("Resultados incorrectos");
}

double mediana(std::vector<double> valores) {
    std::sort(valores.begin(), valores.end());
    return valores[valores.size()/2];
}

int main(int argc, char** argv) {
    try {
        const std::filesystem::path carpeta = argc > 1 ? argv[1] : ".";
        constexpr int maximo = 1000000, repeticiones = 5;
        // El formato compartido es IEEE-754 float64 little-endian.
        const unsigned short endian = 1;
        if (*reinterpret_cast<const unsigned char*>(&endian) != 1 || sizeof(double) != 8)
            throw std::runtime_error("Se necesita double de 8 bytes y equipo little-endian");
        ArrayXd todos_x(maximo), todos_y(maximo), todos_z(maximo);
        std::ifstream datos(carpeta / "coordenadas.bin", std::ios::binary);
        for (auto* arreglo : {&todos_x, &todos_y, &todos_z})
            datos.read(reinterpret_cast<char*>(arreglo->data()), maximo*sizeof(double));
        if (!datos) throw std::runtime_error("Ejecuta primero distancias_python.py");
        ArrayXd cx(4), cy(4), cz(4), esperado2(4), esperado3(4);
        cx << 0, 3, -3, 1; cy << 0, 4, 4, 2; cz << 0, 12, -12, 2;
        esperado2 << 0, 5, 5, std::sqrt(5.); esperado3 << 0, 13, 13, 3;
        for (auto funcion : {distancias_for, distancias_vectoriales}) {
            validar(funcion(cx,cy,cz,2), esperado2);
            validar(funcion(cx,cy,cz,3), esperado3);
            validar(funcion(ArrayXd(0),ArrayXd(0),ArrayXd(0),2), ArrayXd(0));
            validar(funcion(ArrayXd(0),ArrayXd(0),ArrayXd(0),3), ArrayXd(0));
        }
        std::ofstream resumen(carpeta / "tiempos_cpp.csv"), ensayos(carpeta / "ensayos_cpp.csv");
        resumen << std::setprecision(17) << "lenguaje,dimension,N,for_s,vectorial_s,aceleracion\n";
        ensayos << std::setprecision(17) << "lenguaje,dimension,N,repeticion,metodo,segundos\n";
        for (int dimension : {2,3}) {
            for (int n : {10,100,1000,10000,100000,1000000}) {
                const ArrayXd x = todos_x.head(n), y = todos_y.head(n), z = todos_z.head(n);
                const ArrayXd original_x=x, original_y=y, original_z=z;
                auto funciones = std::vector{distancias_for, distancias_vectoriales};
                ArrayXd referencia = funciones[0](x,y,z,dimension);
                validar(funciones[1](x,y,z,dimension), referencia);
                std::vector<double> tiempos[2];
                for (int repeticion=0; repeticion<repeticiones; ++repeticion) {
                    for (int turno=0; turno<2; ++turno) {
                        const int indice = (repeticion % 2 == 0) ? turno : 1-turno;
                        const auto inicio = Reloj::now();
                        ArrayXd resultado = funciones[indice](x,y,z,dimension);
                        const double segundos = std::chrono::duration<double>(Reloj::now()-inicio).count();
                        tiempos[indice].push_back(segundos);
                        // La validación consume el resultado y queda fuera del cronómetro.
                        validar(resultado, referencia);
                        if (!(x==original_x).all() || !(y==original_y).all() || !(z==original_z).all())
                            throw std::runtime_error("Se modificaron las entradas");
                        ensayos << "C++," << dimension << ',' << n << ',' << repeticion+1 << ','
                                << (indice == 0 ? "for" : "vectorial") << ',' << segundos << '\n';
                    }
                }
                const double a=mediana(tiempos[0]), b=mediana(tiempos[1]);
                resumen << "C++," << dimension << ',' << n << ',' << a << ',' << b << ',' << a/b << '\n';
                std::cout << "C++ " << dimension << "D N=" << n << ": for=" << a
                          << " s; vector=" << b << " s; " << a/b << "x\n";
            }
        }
        std::ofstream entorno(carpeta / "entorno_cpp.txt");
        entorno << "Compilador: " << __VERSION__ << "\nEigen: " << EIGEN_WORLD_VERSION << '.'
                << EIGEN_MAJOR_VERSION << '.' << EIGEN_MINOR_VERSION
                << "\nConfiguración utilizada: -std=c++17 -O3 -DNDEBUG; sin -ffast-math\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
