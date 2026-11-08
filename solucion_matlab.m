% Ejecutar después de colocar coordenadas.csv en esta misma carpeta.
clear; clc;
carpeta = fileparts(mfilename('fullpath'));
datos = readmatrix(fullfile(carpeta, 'coordenadas.csv'), 'NumHeaderLines', 1);
x = datos(:, 1).';  % Vectores fila, con los mismos datos de Python.
y = datos(:, 2).';
clear datos;
comprobar_casos(@distancias_for);
comprobar_casos(@distancias_vectorizadas);
[distancias, resumen] = comparar_tiempos(x, y, 5);
fprintf('Ciclo for:   %.6f s (mediana)\n', resumen.tiempo_for_s);
fprintf('Vectorizado: %.6f s (mediana)\n', resumen.tiempo_vectorizado_s);
fprintf('Aceleración: %.2f veces\n', resumen.aceleracion);
fprintf('Validación completa correcta: %d puntos.\n', numel(x));
fprintf('MATLAB %s; equipo %s\n', version, computer);
figura = graficar_resultados(x, y, distancias);
saveas(figura, fullfile(carpeta, 'distancias_matlab.png'));
tabla = table(numel(x), resumen.tiempo_for_s, resumen.tiempo_vectorizado_s, ...
    resumen.aceleracion, 'VariableNames', ...
    {'N', 'Mediana_for_s', 'Mediana_vectorizada_s', 'Aceleracion'});
writetable(tabla, fullfile(carpeta, 'resultados_matlab.csv'));

function distancias = distancias_for(x, y)
    N = numel(x);
    distancias = zeros(1, N, 'double');
    for i = 1:N
        distancias(i) = sqrt(x(i)^2 + y(i)^2);
    end
end

function distancias = distancias_vectorizadas(x, y)
    % .^ eleva cada elemento: ^ sería una potencia matricial.
    distancias = sqrt(x.^2 + y.^2);
end

function [distancias, resumen] = comparar_tiempos(x, y, repeticiones)
    assert(isscalar(repeticiones) && repeticiones >= 5 && ...
        repeticiones == fix(repeticiones));
    original_x = x;
    original_y = y;
    funciones = {@distancias_for, @distancias_vectorizadas};
    tiempos = zeros(repeticiones, 2);
    % Calentamiento fuera de las mediciones.
    referencia = distancias_for(x, y);
    validar(referencia, referencia, x, y, original_x, original_y);
    calentamiento = distancias_vectorizadas(x, y);
    validar(calentamiento, referencia, x, y, original_x, original_y);
    clear calentamiento;
    for repeticion = 1:repeticiones
        if mod(repeticion, 2) == 1
            orden = [1 2];
        else
            orden = [2 1];
        end
        for indice = orden
            inicio = tic;
            resultado = funciones{indice}(x, y);
            duracion = toc(inicio);
            tiempos(repeticion, indice) = duracion;
            validar(resultado, referencia, x, y, original_x, original_y);
            if indice == 2
                distancias = resultado;
            end
            clear resultado;
        end
    end
    resumen.tiempo_for_s = median(tiempos(:, 1));
    resumen.tiempo_vectorizado_s = median(tiempos(:, 2));
    resumen.aceleracion = resumen.tiempo_for_s / resumen.tiempo_vectorizado_s;
end

function validar(resultado, referencia, x, y, original_x, original_y)
    assert(isequal(size(resultado), size(x)) && isa(resultado, 'double'));
    assert(isequal(x, original_x) && isequal(y, original_y));
    % Equivalente a la tolerancia de assert_allclose usada en Python.
    assert(all(abs(resultado - referencia) <= 1e-12 + 1e-12 * abs(referencia)));
end

function comprobar_casos(funcion)
    casos = {[0 3 6 0 0.3], [0 4 8 5 0.4], [0 5 10 5 0.5]; ...
             5, 12, 13; zeros(1, 0), zeros(1, 0), zeros(1, 0)};
    for k = 1:size(casos, 1)
        x = casos{k, 1}; y = casos{k, 2};
        original_x = x; original_y = y;
        resultado = funcion(x, y);
        validar(resultado, casos{k, 3}, x, y, original_x, original_y);
    end
end

function figura = graficar_resultados(x, y, distancias)
    rng(2026, 'twister');
    indices = randperm(numel(x), min(10000, numel(x)));
    figura = figure('Color', 'w', 'Position', [100 100 1200 500]);
    subplot(1, 2, 1);
    scatter(x(indices), y(indices), 7, distancias(indices), 'filled');
    axis equal;
    xlabel('Coordenada x'); ylabel('Coordenada y');
    title('A: Distancia al origen (muestra)');
    barra = colorbar; barra.Label.String = 'Distancia al origen';
    subplot(1, 2, 2);
    histogram(distancias, 60);
    xlabel('Distancia al origen'); ylabel('Frecuencia (número de puntos)');
    title('B: Distancias de todos los puntos');
end
