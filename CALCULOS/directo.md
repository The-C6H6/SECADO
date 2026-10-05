# Procedimiento de Cálculos

## Cálculo para Balance de energía

### Datos requeridos dentro de textfields modificables

1. 2 Datos para poder usar la carta psicrométirica en el aire. Pueden ser : Temperatura de bulbo seco (Forzoso), Humedad relativa o Humedad absoluta (Dependiendo de que se seleccione con un dropdown).
De ser el caso que los datos sean Temperaturas pueden estar en Rankie, Farenheit, Celcius o Kelvin. El sistema deberá convertirlas a Farenheit por sistema inglés.
2. Presión de aire: Siempre 1 atm.(P = 14.69595   psi)
3. Temperatura de Salida del aire.

### Secuencia para resolución

Al precionar boton de "calcular", debe desplegarse una tabla con las siguientes columnas :
Z | Tg | Tbh | H_rel | H_abs | Hv
Donde se hara lo siguiente:
Tg es la temperatura de bulbo seco para el extremo superior y T_salida_gas es la temperatura inferior de dicha columna.
Con psychrolib debera calcularse la temperatura de bulblo seco, bulbo humedo (Tbh), Humedad relativa (H_rel), Humedad absoluta (H_abs), Humedad absoluta a la temperatura de bulbo humedo (Hv) con los dos datos que se proporcionan en los textfields correspondientes.
Valores que NO deben de cambiar a lo largo de la tabla: Tbh y Hv.
Hv es la humedad absoluta de saturación del aire a Tbh.
Debe calcularse el valor de z con la Ecuación del Equipo donde :
Ecuación del Equipo:
Tgas - Tsat = (T0-Tsat)*exp(-0.1377 * z)
Tgas= T_salida_gas
Tsat = Tbh
T0 = Temperatura de bulbo seco.
\[
\boxed{
z=\frac{1}{0.1377}
\ln\left(
\frac{T_0-T_{bh}}{T_g-T_{bh}}
\right)
}
\]
z [=] ft
La última fila debe corresponder siempre a z_max, aunque no sea un número entero. No debes redondear la longitud antes de generar la tabla.

Una vez hecho eso se completan los demás valores incrementando de 1 en 1 los valores de z de la tabla. Desde z=0 hasta z= z_calculada para lo que en z=0 Tg = temperatura de bulbo seco
Y para z = z_calculada  
Tg = T_salida_gas

Para el resto de los valores:
 Debe calcularse el valor de z con la Ecuación del Equipo donde :

Ecuación del Equipo:
 Tgas - Tsat = (T0-Tsat)*exp(-0.1377 * z)
Tsat = Tbh --> Se debe mantener igual a lo largo de toda la columna.
T0 = Temperatura de bulbo seco.
z = valor de z dentro de la iteración
\[
\boxed{T_g(z)=T_{bh}+(T_0-T_{bh})e^{-0.1377z}}
\]

Una vez que se encuentra el valor de Tg:
Se obtiene por psicrometría a partir de los datos de Tbh (temperatura de bulbo humedo que se mantiene estático) y Tg (se entra como temperatura de bulbo seco) obteniendo la Humedad relativa (H_rel), Humedad absoluta (H_abs) y se llenan los campos de Hv y Tbh los cuales no deberan cambiar a lo largo de la columna.
utilizar directamente la temperatura de salida proporcionada por el usuario en la última fila para evitar pequeñas diferencias causadas por la precisión numérica.

Una ves hecho eso escribir la siguiente ecuación:
(Tv-Tg)/(T0-Tg) = (H_abs - Hv)/(Hg- H0)
Y posteriormente reescribirla sustituyendo valores de:
Tv con Tbh.
T0 con Temperatura de bulbo seco del textfield.
Hv con Hv.
y Tg con la temperatura del gas a la salida.
es decir:

\[
\boxed{
\frac{T_{bh}-T_{g,salida}}
{T_0-T_{g,salida}}
=
\frac{H_g-H_v}{H_g-H_0}
}
\]

Donde:
- \(H_g\): humedad absoluta del gas a la salida.
- \(H_v\): humedad de saturación a la temperatura de bulbo húmedo.
- \(H_0\): humedad absoluta del gas a la entrada.

Finalmente mostrar la igualdad:
El sistema NO DEBE validar que la igualdad sea cierta, solo debe mostrar la igualdad.
El sistema NO DEBE modificar los resultados para forzar la igualdad ni comprobar automáticamente si ambos miembros coinciden.

### Aclaraciones

1. La primera fila debe conservar los datos iniciales. Cuando z = 0, utiliza directamente T0, H0 y la humedad relativa inicial. Para las filas posteriores, calcula las nuevas propiedades con PsychroLib a partir de Tg y Tbh.
2. La última fila debe utilizar los datos de salida. Conserva el valor exacto de z_max y utiliza la temperatura de salida introducida por el usuario. No generes una fila duplicada si z_max es un número entero.
3. Condiciones límite. Exige que \(T_0>T_{bh}\). Para obtener una longitud positiva y finita, también debe cumplirse:
\[
T_{bh}<T_{g,salida}<T_0
\]

   Si la temperatura de salida es igual a la inicial, la longitud es cero. Si es igual a la de bulbo húmedo, la longitud teórica es infinita.
4. Precisa cómo presentar la igualdad final. No validar la igualdad es una decisión aceptable para reproducir el procedimiento académico. Sin embargo, los resultados de PsychroLib no necesariamente satisfarán exactamente esa relación, porque se basa en una aproximación de la trayectoria psicrométrica.
