function distancias_matlab()
% MATLAB / GNU Octave. Ejecutar desde esta carpeta: distancias_matlab
% Todos los cálculos usan float64 (double) y los mismos datos que Python/C++.
carpeta = fileparts(mfilename('fullpath'));
maximo = 1000000;
tamanos = [10 100 1000 10000 100000 1000000];
repeticiones = 5;
fid = fopen(fullfile(carpeta, 'coordenadas.bin'), 'rb', 'ieee-le');
assert(fid >= 0, 'Ejecuta primero distancias_python.py.');
datos = fread(fid, [maximo, 3], 'double=>double').';
fclose(fid);
assert(isequal(size(datos), [3, maximo]));
original = datos;
if exist('OCTAVE_VERSION', 'builtin')
    lenguaje = 'MATLAB (GNU Octave)';
else
    lenguaje = 'MATLAB';
end
funciones = {@distancias_for, @distancias_vectoriales};
for k = 1:2
    f = funciones{k};
    validar(f([0 3 -3 1], [0 4 4 2], [0 12 -12 2], 2), [0 5 5 sqrt(5)]);
    validar(f([0 3 -3 1], [0 4 4 2], [0 12 -12 2], 3), [0 13 13 3]);
    validar(f(zeros(1,0), zeros(1,0), zeros(1,0), 2), zeros(1,0));
    validar(f(zeros(1,0), zeros(1,0), zeros(1,0), 3), zeros(1,0));
end
resumen = fopen(fullfile(carpeta, 'tiempos_matlab.csv'), 'w');
ensayos = fopen(fullfile(carpeta, 'ensayos_matlab.csv'), 'w');
assert(resumen >= 0 && ensayos >= 0);
limpieza = onCleanup(@() cerrar(resumen, ensayos));
fprintf(resumen, 'lenguaje,dimension,N,for_s,vectorial_s,aceleracion\n');
fprintf(ensayos, 'lenguaje,dimension,N,repeticion,metodo,segundos\n');
for dimension = [2 3]
    for n = tamanos
        x = datos(1,1:n); y = datos(2,1:n); z = datos(3,1:n);
        original_x = x; original_y = y; original_z = z;
        % Calentamiento excluido del cronómetro.
        referencia = distancias_for(x,y,z,dimension);
        validar(distancias_vectoriales(x,y,z,dimension), referencia);
        tiempos = zeros(repeticiones, 2);
        for repeticion = 1:repeticiones
            if mod(repeticion,2) == 1
                orden = [1 2];
            else
                orden = [2 1];
            end
            for indice = orden
                inicio = tic;
                salida = funciones{indice}(x,y,z,dimension);
                duracion = toc(inicio);
                tiempos(repeticion,indice) = duracion;
                validar(salida, referencia);
                assert(isequal(x,original_x) && isequal(y,original_y) && isequal(z,original_z));
                if indice == 1, metodo = 'for'; else, metodo = 'vectorial'; end
                fprintf(ensayos,'%s,%d,%d,%d,%s,%.17g\n', ...
                        lenguaje,dimension,n,repeticion,metodo,duracion);
                clear salida;
            end
        end
        a = median(tiempos(:,1)); b = median(tiempos(:,2));
        assert(a > 0 && b > 0, 'Resolución temporal insuficiente: repetir el experimento.');
        fprintf(resumen,'%s,%d,%d,%.17g,%.17g,%.17g\n',lenguaje,dimension,n,a,b,a/b);
        fprintf('%s %dD N=%d: for=%.9f s; vector=%.9f s; %.2fx\n', ...
                lenguaje,dimension,n,a,b,a/b);
    end
end
assert(isequal(datos, original));
entorno = fopen(fullfile(carpeta, 'entorno_matlab.txt'), 'w');
fprintf(entorno, '%s\nVersión: %s\nEquipo: %s\n', lenguaje, version, computer);
fclose(entorno);
end

function salida = distancias_for(x,y,z,dimension)
salida = zeros(1,numel(x),'double');
if dimension == 2
    for i = 1:numel(x)
        salida(i) = sqrt(x(i)^2 + y(i)^2);
    end
else
    for i = 1:numel(x)
        salida(i) = sqrt(x(i)^2 + y(i)^2 + z(i)^2);
    end
end
end

function salida = distancias_vectoriales(x,y,z,dimension)
% .^ expresa potencia elemento a elemento; ^ sería potencia matricial.
if dimension == 2
    salida = sqrt(x.^2 + y.^2);
else
    salida = sqrt(x.^2 + y.^2 + z.^2);
end
end

function validar(salida,referencia)
assert(isa(salida,'double') && isequal(size(salida),size(referencia)));
assert(all(isfinite(salida)));
assert(all(abs(salida-referencia) <= 1e-12 + 1e-12*abs(referencia)));
end

function cerrar(a,b)
fclose(a); fclose(b);
end
