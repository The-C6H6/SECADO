"""PsychroLib IP adapter: temperatures °F, pressure psi, W lb water/lb dry air.

RH input/output is percent. Reject W below PsychroLib's 1e-7 floor instead of
silently replacing dry air. Inverse pairs use bounded bisection on library calls.
"""

import math
from dataclasses import dataclass
from threading import RLock

import psychrolib as psy

from .units import convert
from .validation import finite, positive

PRESSURE_PSI = 14.69595
TEMPERATURE_KEYS = {'dry_bulb', 'wet_bulb', 'dew_point'}
KEYS = TEMPERATURE_KEYS | {'humidity_ratio', 'relative_humidity'}
_LOCK = RLock()


@dataclass(frozen=True)
class AirState:
    dry_bulb_f: float
    wet_bulb_f: float
    dew_point_f: float
    relative_humidity_percent: float
    humidity_ratio: float
    volume_ft3_lb_dry: float
    density_lb_ft3: float
    enthalpy_btu_lb_dry: float


def _temperature(value: float) -> float:
    finite(value, 'Temperatura')
    if not -148 <= value <= 392:
        raise ValueError('PsychroLib requiere temperaturas entre -148 y 392 °F.')
    return value


def _bisect(function, low: float, high: float) -> float:
    """Invert a monotone increasing function, returning the upper root bracket.

    Convergence is in °F, not an absolute vapor-pressure residual that becomes
    inaccurate at low pressures. The upper bracket prevents numerical saturation
    roots from falling just below the dew point.
    """
    left, right = function(low), function(high)
    if left == 0:
        return low
    if right == 0:
        return high
    if left > 0 or right < 0:
        raise ValueError('El par no define un estado en el intervalo de PsychroLib.')
    for _ in range(70):
        middle = (low+high)/2
        value = function(middle)
        if value == 0:
            return middle
        if high-low < 1e-10:
            return high
        if value > 0:
            high = middle
        else:
            low, left = middle, value
    raise ValueError('No convergió la inversión psicrométrica.')


def _ratio_from_vapor(vapor: float) -> float:
    if not 0 < vapor < PRESSURE_PSI:
        raise ValueError('La presión de vapor debe estar entre cero y la presión total.')
    ratio = psy.GetHumRatioFromVapPres(vapor, PRESSURE_PSI)
    if ratio <= psy.MIN_HUM_RATIO:
        raise ValueError('Humedad fuera del rango representable: W debe superar 1e-7.')
    return ratio


def saturation_ratio(temperature_f: float) -> float:
    with _LOCK:
        psy.SetUnitSystem(psy.IP)
        return _ratio_from_vapor(psy.GetSatVapPres(_temperature(temperature_f)))


def _from_dry(dry: float, key: str, value: float) -> AirState:
    _temperature(dry)
    if key == 'relative_humidity':
        ratio = _ratio_from_vapor(psy.GetSatVapPres(dry)*value/100)
    elif key == 'dew_point':
        if value > dry:
            raise ValueError('La temperatura de rocío no puede superar el bulbo seco.')
        ratio = _ratio_from_vapor(psy.GetSatVapPres(value))
    elif key == 'wet_bulb':
        if value > dry:
            raise ValueError('El bulbo húmedo no puede superar el bulbo seco.')
        saturated = saturation_ratio(value)
        # Equal dry/wet bulbs define saturation exactly, including below freezing.
        ratio = saturated if value == dry else psy.GetHumRatioFromTWetBulb(dry, value, PRESSURE_PSI)
    else:
        ratio = value
    if ratio <= psy.MIN_HUM_RATIO:
        raise ValueError('Humedad fuera del rango representable: W debe superar 1e-7.')
    rh = psy.GetRelHumFromHumRatio(dry, ratio, PRESSURE_PSI)
    if rh > 1+1e-10 or rh <= 0:
        raise ValueError('El estado está sobresaturado o tiene humedad inválida.')
    wet = psy.GetTWetBulbFromHumRatio(dry, ratio, PRESSURE_PSI)
    if key == 'wet_bulb' and abs(wet-value) > 0.004:
        raise ValueError('El par de bulbos implicaría una humedad no física.')
    dew = psy.GetTDewPointFromHumRatio(dry, ratio, PRESSURE_PSI)
    return AirState(dry, value if key == 'wet_bulb' else wet, dew,
                    value if key == 'relative_humidity' else min(100, rh*100), ratio,
                    psy.GetMoistAirVolume(dry, ratio, PRESSURE_PSI),
                    psy.GetMoistAirDensity(dry, ratio, PRESSURE_PSI),
                    psy.GetMoistAirEnthalpy(dry, ratio))


def air_state(first: str, first_value: float, second: str, second_value: float,
              *, temperature_unit: str = 'F') -> AirState:
    """Resolve nine independent pairs; W + dew point is underdetermined at fixed P.

    Both temperature inputs use temperature_unit. No numeric default air conditions
    are supplied. The lock protects calls made through this adapter from each other.
    """
    if first not in KEYS or second not in KEYS or first == second:
        raise ValueError('Selecciona dos propiedades diferentes y válidas.')
    values = {first: first_value, second: second_value}
    for key, value in values.items():
        finite(value, key)
        if key in TEMPERATURE_KEYS:
            values[key] = _temperature(convert(value, temperature_unit, 'F'))
        elif key == 'relative_humidity' and not 0 < value <= 100:
            raise ValueError('Humedad relativa: mayor que 0 y hasta 100%; aire seco exacto no representable.')
        elif key == 'humidity_ratio':
            positive(value, 'Humedad absoluta')
    if set(values) == {'humidity_ratio', 'dew_point'}:
        raise ValueError('Humedad absoluta y rocío son dependientes a presión fija; falta otra propiedad.')
    with _LOCK:
        psy.SetUnitSystem(psy.IP)
        if 'dry_bulb' in values:
            key = next(key for key in values if key != 'dry_bulb')
            return _from_dry(values['dry_bulb'], key, values[key])
        if 'dew_point' in values:
            values['humidity_ratio'] = _ratio_from_vapor(psy.GetSatVapPres(values.pop('dew_point')))
        if 'humidity_ratio' in values:
            ratio = values['humidity_ratio']
            if ratio <= psy.MIN_HUM_RATIO:
                raise ValueError('W debe superar 1e-7 lb/lb para evitar el recorte de PsychroLib.')
            vapor = psy.GetVapPresFromHumRatio(ratio, PRESSURE_PSI)
            dew = _bisect(lambda t: psy.GetSatVapPres(t)-vapor, -148, 392)
            if 'relative_humidity' in values:
                rh = values['relative_humidity']/100
                dry = dew if rh == 1 else _bisect(lambda t: psy.GetSatVapPres(t)*rh-vapor, dew, 392)
            else:
                wet = values['wet_bulb']
                at_saturation = math.isclose(wet, dew, rel_tol=0, abs_tol=1e-9)
                if wet < dew and not at_saturation:
                    raise ValueError('El bulbo húmedo no puede ser menor que el rocío.')
                saturation_ratio(wet)
                dry = max(wet, dew) if at_saturation else _bisect(
                    lambda t: psy.GetTWetBulbFromHumRatio(t, ratio, PRESSURE_PSI)-wet, dew, 392)
            return _from_dry(dry, 'humidity_ratio', ratio)
        wet, rh = values['wet_bulb'], values['relative_humidity']
        saturation_ratio(wet)
        if rh == 100:
            return _from_dry(wet, 'relative_humidity', 100)
        vapor_limit = PRESSURE_PSI*(1-1e-10)/(rh/100)
        high = 392.0
        if psy.GetSatVapPres(high) >= vapor_limit:
            high = _bisect(lambda t: psy.GetSatVapPres(t)-vapor_limit, wet, high)
        dry = _bisect(lambda t: psy.GetTWetBulbFromRelHum(t, rh/100, PRESSURE_PSI)-wet,
                      wet, high)
        return _from_dry(dry, 'relative_humidity', rh)
