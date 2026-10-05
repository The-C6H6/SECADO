# Unidades, hipótesis y validación

## Procedencia y confirmaciones

Los procedimientos son `CALCULOS/charolas.md`, `CALCULOS/directo.md`,
`CALCULOS/secador_rotatorio.md` y `FIGURAS_FORMULAS/FORMULAS_FIGURAS.md`.
No se modifican esos documentos originales.

Confirmaciones explícitas del usuario, 2026-10-04:

1. Las constantes 0.0204, 0.151 y 0.214 producen **h en W/(m²·K)** con
   **G en kg/(m²·h)** y **dp en metros**. No se sustituyen ni reajustan.
2. Tiempo interno en segundos, masa evaporada kg, calor latente J/kg,
   diferencia térmica K y área m². Charolas también presenta horas.
3. En rotatorio, Xi y Xo deben convertirse de porcentajes a razones
   **lb agua/lb sólido seco** antes de calcular Q y Qlatente.
4. Tds es la temperatura del sólido seco, Tv el bulbo húmedo;
   el intervalo correcto es **Tv ≤ Tds ≤ Tgo**.
5. Comparaciones académicas: tolerancia relativa de **1% en tiempos** y
   **±0.5 °F en Tbh**, manteniendo el resultado de PsychroLib sin ajustes.
6. El prisma triangular se considera equilátero. Solo recibe lado `a` y longitud `L`:
   `h = √(a² − (a/2)²)`, `Ab = ah/2`, `V = AbL` y `AT = 2Ab + 3aL`.
7. Los procedimientos visibles siguen **Ecuación → Sustitución con valores y unidades
   → Resultado con unidades**. En tablas iterativas se desarrollan únicamente sus
   extremos inferior y superior; las filas intermedias se presentan sin expansión.

Estas confirmaciones resuelven las ambigüedades que bloqueaban esas fórmulas.
No equivalen a validar experimentalmente el rango de aplicación de cada correlación.

## Contratos de los módulos

| Módulo | Entrada interna | Salida |
|---|---|---|
| `units` | valor y unidades explícitas | misma dimensión, unidad de destino |
| `moisture` | porcentajes con base explícita | razón agua/seco o masas en la unidad de entrada |
| `geometry` | longitudes m, porosidad % | área m², volumen m³, dp m |
| `psychrometrics` | temperatura con unidad, HR %, W lb/lb | °F, HR %, W lb/lb, ft³/lb seco, lb/ft³, Btu/lb seco |
| `correlations` | G kg/(m²·h), dp m, μ kg/(m·h) | h W/(m²·K), Re adimensional |
| `dryers/tray` | mv kg, ΔHv J/kg, h W/(m²·K), ΔT K, A m² | segundos |
| `dryers/continuous` | estado IP, salida °F | longitud ft y tabla IP |
| `dryers/rotary` | flujos lb/h, T °F, Cp Btu/(lb·°F), ΔHv Btu/lb | Q Btu/h, diámetro/longitud ft |

`reports` coordina conversiones y construye resultados sin importar Flet.
`ui` solo captura entradas, muestra tablas/Markdown y maneja errores.

## Procedimiento auditable

`procedure.py` genera Markdown con ecuaciones LaTeX para mantener un formato uniforme.
Las conversiones muestran el factor utilizado y las conversiones de temperatura pasan
por kelvin; las diferencias térmicas usan su escala sin aplicar desplazamientos.

Cada consulta psicrométrica identifica las dos propiedades independientes, sus unidades,
la conversión a las entradas IP de PsychroLib y la presión fija. Después enumera bulbo
seco, bulbo húmedo, rocío, humedad relativa, humedad absoluta, volumen específico,
densidad húmeda y entalpía. PsychroLib sigue siendo el motor del estado; el informe no
presenta sus iteraciones internas como si fueran operaciones hechas a mano.

Los balances de charolas, extruidos y rotatorio desarrollan sus conversiones y variables
intermedias antes del resultado final. Para el perfil continuo solo se desarrollan las
filas de `z = 0` y `z = L`, según la instrucción del usuario; todas las filas calculadas
permanecen disponibles en la tabla.

La presentación limita cada valor a cinco cifras decimales y elimina ceros finales.
Los valores no nulos menores que `0.00001` usan notación científica para evitar que se
vean como cero. Este formato solo se aplica al texto y a las tablas de Flet: los motores,
los objetos `Report` y las comparaciones de pruebas conservan los valores de punto
flotante completos.

## Conversiones

Todas se implementan en `units.py`, sin redondear valores intermedios.

- 1 ft = 0.3048 m; 1 in = 0.0254 m; 1 cm = 0.01 m. Áreas y volúmenes
  usan el cuadrado y cubo de esos factores.
- 1 lb = 0.45359237 kg. 1 Btu IT/lb = 2326 J/kg.
- °R = °F + **459.67**, no +460. K = °C +273.15.
- Diferencias: ΔK = Δ°F × 5/9; no se aplican offsets a diferencias.
- 1 cP = 0.001 kg/(m·s) = 3.6 kg/(m·h); 1 h = 3600 s.
- Velocidad de aire: 1 m/s = 3600 m/h, seleccionable en los formularios.
- 1 lb/ft³ = 0.45359237/0.3048³ kg/m³.
- La presión de curso es exactamente el valor especificado **14.69595 psi**.
- HR porcentual se divide entre 100 al llamar a PsychroLib. Las humedades de
  sólidos se convierten a razones: X = porcentaje/100 en base seca o w/(100−w)
  en base húmeda. Esas conversiones viven en el adaptador y `moisture`, respectivamente.

Se reemplazan las aproximaciones de conversión del documento (+460 y 0.454) por
definiciones consistentes, sin modificar constantes empíricas. Esto puede producir
diferencias pequeñas respecto a cálculos manuales redondeados.

## Charolas y extruidos

`t = mv ΔHv / (h ΔT A)` tiene dimensiones **J/W = segundos**.
En extruidos A es el área total de partículas; en charolas es el área de charola.

- Densidad de la correlación: se mantiene R = 0.730 atm·ft³/(lbmol·°R),
  PMaire = 28.97 y PMagua = 18.02 lb/lbmol del procedimiento.
  VH está por lb de aire seco; (1+H)/VH es densidad de aire húmedo.
  La densidad mostrada por PsychroLib puede diferir ligeramente debido a constantes.
- El estado de aire utilizado es el que introduce el usuario. La referencia a
  aire «de salida» en charolas no define un segundo estado; no se lo inventa.
- G usa densidad húmeda y velocidad en m/h. dp = sqrt(Apartícula/pi), según el
  procedimiento, no diámetro hidráulico 6V/A.
- Re = G dp/μ, con μ convertido a kg/(m·h). Re = 350 usa la rama inferior.
- Área de partículas: superficie cerrada completa, incluidas bases; no se
  descuentan contactos. Número de partículas equivalente continuo, sin redondear.
- El calor latente a Tbh se introduce por el usuario, no se estima.
- Humedad final mayor que inicial, masa/área no positivas, porosidad fuera de
  [0,100), ΔT no positivo y datos no finitos producen errores.

## Psicrometría y continuo

PsychroLib 2.5.0 usa IP. El adaptador admite nueve pares independientes, incluidos
pares sin bulbo seco mediante bisección de llamadas a PsychroLib. Humedad absoluta
y rocío son dependientes a presión fija; se informa que falta otra propiedad.

Temperaturas entre −148 y 392 °F, presión de vapor menor que la total y ausencia de
sobresaturación. Se rechaza W ≤ 1e-7 lb/lb para evitar el recorte silencioso de
PsychroLib. El aire exactamente seco es físicamente posible, pero queda fuera del
dominio numérico admitido por este adaptador. No se presenta como estado calculado.

El continuo mantiene Tbh y Hv constantes. La primera fila conserva el estado
original; la última conserva z_max sin redondear y la temperatura de salida exacta.
No duplica la fila final entera. Salida = entrada implica longitud cero; salida = Tbh
implica longitud infinita y un error explicativo. La igualdad académica final se
muestra con sustitución sin evaluar ni forzar sus miembros; en longitud cero es
indefinida. 0.1377 se interpreta en ft⁻¹ porque el documento define z en ft.

## Rotatorio

La confirmación del usuario resuelve porcentaje frente a razón e intervalo de Tds.
Qlatente se calcula directamente como mv ΔHv. Los balances trabajan con flujos,
aunque el documento use la palabra «masa». Se rechazan Q no positivo y salida
sobresaturada calculada mediante el balance de agua.

La correlación volumétrica ha = G^0.67/(2D) conserva la unidad expresamente
declarada en el procedimiento: Btu/(h·ft³·°F), con G lb/(ft²·h), D ft.
Sus unidades están especificadas; no se dispone de su rango de validez experimental.
No se aplica a charolas ni se confunde ha con h superficial.

## Ejercicios académicos completos

Ambos enunciados fueron proporcionados por el usuario. Entradas comunes:

- 73 kg de sólido húmedo; humedad inicial 30% seca; final 10% seca.
- Aire a 170 °F, 10% HR y 1 atm.
- Calor latente 1037.2 Btu/lb, convertido a **2412527.2 J/kg**.
- Área de charola 1.5 m².

Charolas: torta de carbonato de calcio, aire paralelo a **4 m/s**.

Extruidos: aire a **2 m/s**; cilindros de diámetro **0.25 in** y altura **0.5 in**.
La API geométrica recibe radio: 0.25/2 = **0.125 in**. Lecho de **2.5 cm**,
porosidad **50%**, viscosidad **0.02 cP**.

Datos proporcionados por el usuario (aproximados):

| Charolas | Valor |
|---|---:|
| Masa evaporada | 11.23 kg |
| G | 14314 kg/(m²·h) |
| h | 43.07 W/(m²·K) |
| ΔT | 38.88 K |
| Área | 1.5 m² |
| Tiempo | 3 h |

| Extruidos | Valor |
|---|---:|
| Re | 998 |
| Régimen | Re > 350 |
| Área total | 14.76 m² |
| h | 187.3 W/(m²·K) |
| Tiempo | 252 s |

### Resultados sin redondeo intermedio

| Magnitud | Charolas | Extruidos |
|---|---:|---:|
| Tbh (°F) | 100.282848071 | 100.282848071 |
| H (lb agua/lb aire seco) | 0.026470229606 | 0.026470229606 |
| Masa evaporada (kg) | 11.230769231 | 11.230769231 |
| G (kg/(m²·h)) | 14313.417087376 | 7156.708543688 |
| ΔT (K) | 38.731751072 | 38.731751072 |
| Volumen ocupado (m³) | — | 0.01875 |
| Número de cilindros | — | 46618.706489527 |
| Área de transferencia (m²) | 1.5 | 14.763779528 |
| dp (m) | — | 0.010040231571 |
| Re | — | 997.986264792 |
| h (W/(m²·K)) | 43.074954635 | 187.302202117 |
| Tiempo (s) | 10826.759811533 | 252.972990904 |
| Tiempo (h) | 3.007433281 | — |

Las diferencias de tiempo respecto a 3 h y 252 s son +0.2478% y +0.3861%.
La carta aproxima Tbh a 100 °F; PsychroLib calcula 100.282848071 °F. Esto cambia
ΔT de aproximadamente 38.89 K a 38.731751072 K. El usuario aceptó explícitamente
la diferencia y las tolerancias: no se sustituyó Tbh por 100 ni se ajustó h.

Las regresiones completas verifican tiempos al 1%, Tbh a ±0.5 °F y ΔT con
±(0.5×5/9 +0.005) K, propagando esa incertidumbre de lectura y el redondeo decimal.
Los demás checkpoints usan tolerancias absolutas documentadas en las pruebas
(por ejemplo, ±1 en G y Re, ±0.005 m² en área). No hay pruebas omitidas.

Los casos analíticos adicionales y comprobaciones físicas están separados de
estos ejercicios; no se presentan como referencias académicas independientes.

## Revisión y límites de entrega

Se corrigió un rechazo de estados saturados que aparecía al invertir pares sin
bulbo seco: la bisección ahora converge en temperatura y conserva el extremo
superior de la raíz. La igualdad de bulbos usa directamente la saturación, también
bajo congelación, evitando inconsistencias de coeficientes redondeados de PsychroLib.
Se mantiene el rechazo de estados realmente sobresaturados.

No quedan fórmulas bloqueadas por unidades sin confirmar en el alcance implementado.
Siguen sin estar especificados los rangos empíricos de validez de las correlaciones,
el descuento de superficies en contacto y un modelo de estados de entrada/salida
distintos para charolas; se implementa el procedimiento provisto, sin extensiones.
No se ha realizado validación experimental ni creado un instalador de Windows.
