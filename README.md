# SECADO

Calculadora de secado para ingeniería química en Python y Flet. Los motores
matemáticos no dependen de la interfaz. PsychroLib opera en sistema inglés a
1 atm (14.69595 psi); las conversiones están centralizadas.

## Ejecución

Desde este checkout, con Python 3.13 y uv:

```powershell
uv sync
uv run secado-app-1er-parcial
```

También se puede usar `uv run python -m secado_app_1er_parcial`.
Para vista web desde la raíz del checkout: `uv run flet run --web --port 8501`.
El CLI usa `main.py`; el lanzador oficial de Flet puede descargar su CLI auxiliar
en el primer uso.
Los extras oficiales `flet[desktop,web]` están declarados e instalados con autorización
del usuario. Las imágenes se leen de
`assets/` en este checkout; todavía no se ha preparado un instalador de Windows.

## Funcionalidad

- Psicrometría con nueve pares independientes de propiedades. Rocío y humedad
  absoluta son dependientes a presión fija y no determinan por sí solos el estado.
- Conversiones explícitas de temperatura, longitud, área, volumen, masa, velocidad,
  viscosidad, densidad, energía específica, presión y tiempo.
- Once geometrías, más entrada manual de área/volumen, y lechos porosos. El prisma
  triangular usa una base equilátera y solicita únicamente el lado y la longitud.
- Charolas y extruidos: balances, G, Reynolds, selección de correlación y tiempo SI.
  El calor latente se introduce en J/kg o Btu/lb; el tiempo se obtiene en segundos y,
  para charolas, también en horas. Las constantes no se ajustan.
- Secador continuo: tabla de propiedades con extremos exactos; desarrolla los cálculos
  de los extremos inferior y superior y conserva las filas intermedias en la tabla.
- Rotatorio: balances térmico y de masa, diámetro y longitud; validación de
  `Tv ≤ Tds ≤ Tgo` y de la humedad del gas a la salida.
- Formularios sin ejercicios precargados, resultados con unidades y procedimiento
  Markdown. Cada paso sigue Ecuación → Sustitución con unidades → Resultado. Las
  consultas psicrométricas declaran sus dos entradas y todas las propiedades obtenidas.
  Los valores se muestran con un máximo de cinco decimales sin redondear los datos
  internos. Al cambiar datos se eliminan los resultados anteriores.

## Pruebas

```powershell
uv run pytest -q -rs
uv run python -m compileall -q src tests
```

Las pruebas cubren ejemplos analíticos, conversiones, conservación de masa y energía,
límites físicos, inversas psicrométricas y callbacks Flet. No son todas comparaciones
con ejercicios académicos: esa distinción es explícita.

Las regresiones académicas usan los dos enunciados completos proporcionados:
**3.007433 h** para charolas y **252.972991 s** para extruidos. El usuario autorizó
1% de tolerancia para tiempos y ±0.5 °F para Tbh por la diferencia entre carta
psicrométrica y PsychroLib. No se modifican entradas ni constantes para ajustarlos.

Se verificaron 175 pruebas, compilación y recursos HTTP de Flet. La inspección visual
en navegador confirmó el formulario reducido del prisma y el renderizado LaTeX de las
ecuaciones dentro de `ft.Markdown`.

Ver [unidades y validación](docs/dimensional-validation.md) para hipótesis,
referencias parciales y decisiones confirmadas.
