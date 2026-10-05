# Procedimiento de Cálculos

## Cálculo de Tiempo Crítico

### Datos requeridos dentro de textfields modificables

1. Área de la Charola: Puede darse en unidades de in2, cm2, m2, ft2. Sin embargo, el sistema debe calcular el valór a m2.
2. Masa del solido humedo en kg
3. Contenido de Humedad del sólido: Puede darse en base seca o base humeda en %.
4. Presión de aire: Siempre 1 atm
5. 2 Datos para poder usar la carta psicrométirica en el aire. Pueden ser : Humedad relativa, Humedad absoluta, Temperatura de rocío, Temperatura de bulbo humedo o Temperatura de bulbo seco. debe devolver los datos en sistema ingles
De ser el caso que los datos sean Temperaturas pueden estar en Rankie, Farenheit, Celcius o Kelvin. El sistema deberá convertirlas a Farenheit por sistema inglés.
6. Velocidad del aire : en metros/hora.
7. Calor latente de ebullición a temperatura de bulbo humedo en Btu/lb.
8. Humedad crítica (salida del sólido): Puede darse en base seca o base humeda en %.

### Fórmula necesaria

Tiempo Crítico = mv*(delta_H)/(h*(Td-Tw)*A) [=] Horas

#### Significado de las Variables

1. mv: Masa Vaporizada
2. delta_H: Calor latente de ebullición a temperatura de bulbo humedo.
3. h: Coeficiente convectivo.
4. Td: Temperatura de Bulbo seco.
5. Tw: Temperatura de Bulbo Húmedo.
6. A: Área de la charola.

### Procedimiento de Cálculo

#### Cálculo de la masa vaporizada

    Para ello se tiene la masa del solido Húmedo, y el contenido de humedad del sólido. 
    Si el contenido de humedad de solido a la entrada obtiene datos en base seca se calcula:

    Xi=contenido de humedad de solido humedo a la entrada en porcentaje
    Wi = 100*Xi/(100+Xi)  ---> Wi = Contenido de Humedad en base humeda
    mi_H2O = m_ws*(wi/100) ---> mi_H2O = Masa de agua al inicio
    mss= m_ws-mi_H2O ---> Masa de sólido séco.

    Si el contenido de humedad de solido a la salida obtiene datos en base seca se calcula:
    Xo=Humedad crítica (salida del sólido) base seca
    mo_H2O = mss*(Xo/100)

    Si el contenido de humedad de solido a la salida obtiene datos en base humeda se calcula:
    Wo=Humedad crítica (salida del sólido) base húmeda
    Xo = 100*Wo/(100-Wo)
    mo_H2O = mss*(Xo/100)
    
    mv= mi_H2O-mo_H2O

#### Cálculo de Coeficiente convectivo

    h=0.0204*G**0.8
    G=densidad_aire*velocidad_aire [=] kg/(m2*h)
    VH=(R*T/P)(1/PM_Aire+H_abs/PM_H2O)
Donde:
R = Constante de Gases ideales = 0.730 [=] Atm*ft3/(lb_mol*Rankie)
Td = Temperatura de gas a la entrada en Rankie = Temperatura de bulbo seco= Temperatura en Farenheit + 460
P = Presión del Gas = 1atm
PM_Agua = 18.02 [=] lb/lbmol
PM_Aire = 28.97 [=] lb/lbmol
H_abs : Humedad Absoluta del Gas a la salida. Se calcula con los 2 Datos para poder usar la carta psicrométirica en el aire.

VH_Humedo = VH/(1+H_abs) [=] ft3/lb_aire
densidad_aire=1/VH_Humedo
densidad_aire=densidad_aire*(0.454)/(0.3048**3)  ---->Conversión a Kg/m3

#### Cálculo de Diferencia de Temperaturas

Las unidades deben coincidir con grados Kelvin:
Delta_T= (Td-Tw)*5/9 [=] Kelvin
Td y Tw deben haber sido convertidas previamente en °F.

## Cálculo de Tiempo Crítico para sólidos extruidos

### Datos requeridos dentro de textfields modificables

1. Forma Física extruida: Las figuras requeridas se encuentran en @./FIGURAS_FORMULAS/FORMULAS_FIGURAS.md. 
Deberá haber una opción: "Otra" en caso de que el usuario tenga una figura diferente.
Una ves que el usuario seleccione una figura debe llenarse un cuadro de imágen con la figura seleccionada. Las imagenes se encuentran en @./Figuras/*.
Tambien deberá aparecer uno o varios textfields dependiendo de la figura seleccionada con los campos necesarios para calcular Volumen como area.
Por ejemplo:

- Figura : Cilíndro
- Textfield 1: Radio
- Textfield 2: Altura
En el caso de que el usuario haya seleccionado "Otra", el usuario tendrá un textfield de "Área" y uno de "Volúmen" donde el usuario deberá escribir el valor del Área y el volúmen de forma manual.

2. Contenido de Humedad del sólido: Puede darse en base seca o base humeda en %.

3. Humedad crítica (salida del sólido): Puede darse en base seca o base humeda en %.

4. Calor latente de ebullición a temperatura de bulbo humedo.

5. 2 Datos para poder usar la carta psicrométirica en el aire. Pueden ser : Humedad relativa, Humedad absoluta, Temperatura de rocío, Temperatura de bulbo humedo o Temperatura de bulbo seco.
De ser el caso que los datos sean Temperaturas pueden estar en Rankie, Farenheit, Celcius o Kelvin. El sistema deberá convertirlas a Farenheit por sistema inglés.

6. Área de la Charola: Puede darse en unidades de in2, cm2, m2, ft2. Sin embargo, el sistema debe calcular el valór a m2.

7. Altúra de la Charola: Puede darse en unidades de in, cm, m, ft. Sin embargo, el sistema debe calcular el valór a m.

8. Porosidad: en % 

9. Viscosidad del aire: Valor por defecto 0.02 cp
Donde 1cp= 1*10**-3 kg/(s*m)
y donde 3600 segundos = 1 horas
el sistema debe calcular viscosidad en términos de kg/(h*m)

8. Calor latente de ebullición a temperatura de bulbo humedo.

9. Masa del solido humedo

10. Velocidad del aire : en metros/hora.

### Fórmula necesaria

Tiempo Crítico = mv*(delta_H)/(h*(Td-Tw)*A) [=] segundos

### Cálculo de la masa vaporizada

    Para ello se tiene la masa del solido Húmedo, y el contenido de humedad del sólido. 
    Si el contenido de humedad de solido a la entrada obtiene datos en base seca se calcula:

    Xi=contenido de humedad de solido humedo a la entrada en porcentaje
    Wi = 100*Xi/(100+Xi)  ---> Wi = Contenido de Humedad en base humeda
    mi_H2O = m_ws*(wi/100) ---> mi_H2O = Masa de agua al inicio
    mss= m_ws-mi_H2O ---> Masa de sólido séco.

    Si el contenido de humedad de solido a la salida obtiene datos en base seca se calcula:
    Xo=Humedad crítica (salida del sólido) base seca
    mo_H2O = mss*(Xo/100)

    Si el contenido de humedad de solido a la salida obtiene datos en base humeda se calcula:
    Wo=Humedad crítica (salida del sólido) base húmeda
    Xo = 100*Wo/(100-Wo)
    mo_H2O = mss*(Xo/100)
    Xo y Wo están en porcentajes.
    
    mv= mi_H2O-mo_H2O

### Cálculo de Diferencia de Temperaturas

Las unidades deben coincidir con grados Kelvin:
Delta_T= (Td-Tw)*5/9 [=] Kelvin
Td y Tw deben haber sido convertidas previamente en °F.

### Cálculo del volúmen total en la charola

    V_T_sin_porosidad= area_base_charola*altura_charola
    V_T_poroso =  V_T_sin_porosidad*(1-porosidad/100)

### Cálculo del número de figuras geométricas extruidas

    Num_figuras= V_T_poroso / V_figura

### Cálculo del Área Total

    A_TOTAL = A_figura*Num_figuras

### Cálculo de Coeficiente convectivo

    Ecuación 
    
    Para Re > 350
    h = 0.151 * G^0.59 / d_p^0.41

    Para Re <= 350:
    h = 0.214 * G^0.49 / d_p^0.51

    Donde: Re= G*dp/viscosidad_aire
    dp = sqrt(A_figura/pi())


    G=densidad_aire*velocidad_aire [=] kg/(m2*h)
    VH=(R*T/P)(1/PM_Aire + H_abs/PM_H2O)
Donde:
R = Constante de Gases ideales = 0.730 [=] Atm*ft3/(lb_mol*Rankie)
Td = Temperatura de gas a la entrada en Rankie = Temperatura de bulbo seco= Temperatura en Farenheit + 460
P = Presión del Gas = 1atm
PM_Agua = 18.02 [=] lb/lbmol
PM_Aire = 28.97 [=] lb/lbmol
H_abs : Humedad Absoluta del Gas a la salida. Se calcula con los 2 Datos para poder usar la carta psicrométirica en el aire.

VH_Humedo = VH/(1+H_abs) [=] ft3/lb_aire
densidad_aire=1/VH_Humedo
densidad_aire=densidad_aire*(0.454)/(0.3048**3)  ---->Conversión a Kg/m3

## Límites

si la humedad crítica supera a la humedad inicial, la temperatura de bulbo húmedo es mayor que la de bulbo seco o las condiciones psicrométricas son imposibles, debe aparecer un error explicativo.
