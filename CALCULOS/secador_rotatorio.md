# Procedimiento de Cálculos

## Cálculo para longitud y diamtero de un secador

### Datos requeridos dentro de textfields modificables

1. Temperatura del solido humedo. puede estar en Rankie , Kelvin, Farenheit o Celcius. Pero el sistema debe transformarlo a Farenheit.
2. Porcentaje de humedad del sólido húmedo. Puede estar en base humeda o base seca.
3. Masa de solido seco en lb/h.
4. 2 Datos para poder usar la carta psicrométirica en el aire. Pueden ser : Humedad relativa, Humedad absoluta, Temperatura de rocío, Temperatura de bulbo humedo o Temperatura de bulbo seco.
De ser el caso que los datos sean Temperaturas pueden estar en Rankie, Farenheit, Celcius o Kelvin. El sistema deberá convertirlas a Farenheit por sistema inglés.
5. La presión del aire es 1 atm.
6. Contenido de Humedad final del sólido. Puede darse en base humeda o base seca.
7. Velocidad del gas en ft/h
8. Cp del solido Btu/lb°F.
9. Número de unidades de transferencia. Debe tener un valor por defecto de 1.5 pero el usuario lo puede cambiar.
10. Cp del agua en fase gas. En inicio debe ser 0.447 Btu/lb°F
11. Cp del agua en fase líquida. En inicio debe ser 1 Btu/lb°F
12. Cp del aire. En inicio debe ser 0.242 Btu/lb°F

### Secuencia de calculos

1. Con los dos datos obtenidos del gas a la entrada se calculan el resto de variables psicrométricas: Humedad relativa, Humedad absoluta, Temperatura de bulbo humedo y Temperatura de bulbo seco y las despliega por la pantalla.
2. Debe aparecer un textfield que solicite el valor del calor latente de vaporización a la temperatura de bulbo humedo en Btu/lb.

3. Cálculo de la masa vaporizada.
    Si el contenido de humedad en el solido esta en base seca se calcula:
    mv=m_s*(X_ws-X_ds)/100
     m_s es la masa de sólido seco.
    X_ds es la humedad en base seca de solido seco.
    X_ws es la humedad en base seca de solido seco.
    Si el contenido de humedad en el solido esta en base humeda se debe calcular la humedad en base seca con:
    X=100*w/(100-w)
    siendo w la humedad del solido en base humeda representada como un porcentaje
    Ejemplo :
    X= 100*(21)/(100-21)

4. Cálculo de Temperatura del gas a la salida
\[
\boxed{T_o=T_v+(T_{gi}-T_v)e^{-N_T}}
\]
Donde :
T_gi= Temperatura del bulbo seco.
T_v= Temperatura de bulbo húmedo.
N_T= Número de unidades de transferencia.
T_o = Temperatura del gas a la salída.

5. Debe aparecer un textfield que solicite el valor de Tds con una especificación: Debe estar entre  Tgo y Tw.
6. Cálculo de calór total
Q = m_s { (Cp)_s (T_ds - T_ws)
    + X_ws (Cp)_H2O(l) (T_v - T_ws)
    + X_ds (Cp)_H2O(l) (T_ds - T_v)
    + (X_ws - X_ds) [ΔH_v^vap + (Cp)_H2O(g) (T_go - T_v)] }

    Donde:
    Cp_s es el Cp del sólido.
    T_ds es la temperatura de sólido seco.
    Tws es la temperatura de sólido húmedo.
    T_v es la temperatura de bulbo húmedo.
    (Cp)_H2O(l) es el Cp del agua liquida
    (Cp)_H2O(g) es el Cp del agua gaseosa.
    ΔH_v^vap es el calor latente de vaporización a la temperatura de bulbo humedo en Btu/lb.
    Tgo es la temperatura del gas a la salida.
    X_ds es la humedad en base seca de solido seco.
    X_ws es la humedad en base seca de solido seco.
    m_s es la masa de sólido seco.

7. Cálculo de calór latente
Q_latente = m_s*{(X_ws - X_ds) [ΔH_v^vap] }

    Donde:
    X_ds es la humedad en base seca de solido seco.
    X_ws es la humedad en base seca de solido seco.
    ΔH_v^vap es el calor latente de vaporización a la temperatura de bulbo humedo.
    m_s es la masa de sólido seco.

8. Cálculo de masa de gas seco
mg=Q/{ [(Cp)_air + H_gi (Cp)_H2O(g)] (T_gi - T_go) }
(Cp)_air es el cp del aire
H_gi es la humedad absoluta del gas a la entrada previamente calculada en el punto 1.
(Cp)_H2O(g) es el Cp del agua en fase gas.
T_gi es la temperatura del gas a la entrada, es decir es la temperatura de bulbo seco del gas.
T_go = Temperatura del gas a la salída.
mg= masa de gas en lb/h

9. Cálculo de masa de gas total a la entrada
mg_Total_entrada= mg_seco*(1+Humedad_absoluta)
mg_Total_entrada = masa de gas en lb/h

10. Cálculo de masa de gas total a la salida
mg_Total_salida= mg_Total_entrada + mv

11. Calculo de Delta T media logaritmica
ΔT_ml = (T_gi - T_go) / ln[(T_gi - Tv) / (T_go - Tv)]
T_gi= Temperatura del gas a la entrada o sea la de bulbo seco ya calculado en punto 1
T_go= Temperatura del gas a la salida.
Tv = Temperatura de bulbo humedo del gas a la entrada. Ya calculado en punto 1

12. Calculo de la densidad del gas total en la salida

ρ_salida = (P * PM_gas_total_salida) / (R * T_go)

R = 0.730 atm * ft3/(lbmol*rankie)
T = Temperatura a la salida del gas T_go convertida a rankie.
P = 1 atm
PM_gas_total_salida= (mg_Total_salida)/(mg/(28.97 lb/lbmol)+((mg_Total_salida-mg)/18.02 lb/lbmol))

13. Calculo de la masa velocidad G

G = ρ_salida * velocidad_gas
[=] lb/ft2*h

14. Calculo del diametro del secador

D = sqrt((4 * mg_Total_salida) / (π * G)) [=] ft

15. Cálculo del coeficiente convectivo volumétrico ha

ha = (G**0.67)/(2 * D)
ha[=] Btu/(h * ft3 * F)

17. Cálculo de longitud del secador L
L = (Q)/(ha * ΔT_ml * Area)
Area = (pi()*D**2)/4
