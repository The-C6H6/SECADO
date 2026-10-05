"""Course equipment equation, coefficient 0.1377 ft⁻¹, constant wet bulb."""

import math
from dataclasses import dataclass

from ..psychrometrics import AirState, air_state, saturation_ratio
from ..procedure import step, value
from ..validation import finite


@dataclass(frozen=True)
class ProfileRow:
    z_ft: float
    air: AirState
    wet_bulb_f: float
    saturated_humidity_ratio: float


@dataclass(frozen=True)
class ContinuousProfile:
    length_ft: float
    rows: tuple[ProfileRow, ...]
    procedure: str


def profile(initial: AirState, outlet_f: float) -> ContinuousProfile:
    finite(outlet_f, 'Temperatura de salida')
    dry, wet = initial.dry_bulb_f, initial.wet_bulb_f
    if dry <= wet:
        raise ValueError('Se requiere T0 > Tbh.')
    if outlet_f == wet:
        raise ValueError('Salida igual a Tbh: longitud teórica infinita.')
    if not wet < outlet_f <= dry:
        raise ValueError('La salida debe cumplir Tbh < Tsalida <= T0.')
    length = math.log((dry-wet)/(outlet_f-wet))/0.1377
    hv = saturation_ratio(wet)
    positions = [0.0]
    if length > 0:
        positions.extend(float(i) for i in range(1, math.ceil(length))
                         if not math.isclose(i, length, rel_tol=0, abs_tol=1e-10))
        positions.append(length)
    rows = []
    for index, z in enumerate(positions):
        if index == 0:
            state = initial
        else:
            temperature = outlet_f if index == len(positions)-1 else wet+(dry-wet)*math.exp(-0.1377*z)
            state = air_state('dry_bulb', temperature, 'wet_bulb', wet)
        rows.append(ProfileRow(z, state, wet, hv))
    outlet = rows[-1].air
    procedure = '\n\n'.join([
        '## Perfil axial del secador continuo',
        step('Longitud del secador',
             r'L=\frac{\ln[(T_0-T_{bh})/(T_{salida}-T_{bh})]}{0.1377}',
             rf'L=\frac{{\ln[({value(dry)}\ ^\circ F-{value(wet)}\ ^\circ F)'
             rf'/({value(outlet_f)}\ ^\circ F-{value(wet)}\ ^\circ F)]}}{{0.1377\ ft^{{-1}}}}',
             rf'L={value(length)}\ ft'),
        'La tabla se evalúa con paso de 1 ft y conserva el extremo fraccionario final. '
        'El desarrollo se muestra solamente para sus extremos inferior y superior; '
        'las filas intermedias permanecen visibles en la tabla.',
        step('Extremo inferior de la tabla (z = 0)',
             r'T_g(z)=T_{bh}+(T_0-T_{bh})e^{-0.1377z}',
             rf'T_g(0\ ft)={value(wet)}\ ^\circ F+'
             rf'({value(dry)}\ ^\circ F-{value(wet)}\ ^\circ F)e^{{-0.1377(0\ ft)}}',
             rf'T_g(0)={value(initial.dry_bulb_f)}\ ^\circ F,\quad '
             rf'H={value(initial.humidity_ratio)}\ lb/lb,\quad '
             rf'HR={value(initial.relative_humidity_percent)}\ \%'),
        step('Extremo superior de la tabla (z = L)',
             r'T_g(z)=T_{bh}+(T_0-T_{bh})e^{-0.1377z}',
             rf'T_g({value(length)}\ ft)={value(wet)}\ ^\circ F+'
             rf'({value(dry)}\ ^\circ F-{value(wet)}\ ^\circ F)'
             rf'e^{{-0.1377({value(length)}\ ft)}}',
             rf'T_g(L)={value(outlet.dry_bulb_f)}\ ^\circ F,\quad '
             rf'H={value(outlet.humidity_ratio)}\ lb/lb,\quad '
             rf'HR={value(outlet.relative_humidity_percent)}\ \%'),
        step('Humedad de saturación constante', r'H_v=H_{sat}(T_{bh},P)',
             rf'H_v=PsychroLib_{{IP}}({value(wet)}\ ^\circ F,{14.69595}\ psi)',
             rf'H_v={value(hv)}\ lb\ agua/lb\ aire\ seco'),
        step('Relación académica mostrada',
             r'\frac{T_{bh}-T_{salida}}{T_0-T_{salida}}='
             r'\frac{H_g-H_v}{H_g-H_0}',
             rf'\frac{{{value(wet)}-{value(outlet_f)}}}{{{value(dry)}-{value(outlet_f)}}}='
             rf'\frac{{{value(outlet.humidity_ratio)}-{value(hv)}}}'
             rf'{{{value(outlet.humidity_ratio)}-{value(initial.humidity_ratio)}}}',
             r'La\ igualdad\ se\ muestra;\ no\ se\ verifica\ ni\ se\ fuerzan\ sus\ miembros.'),
        'Esta igualdad se muestra; no se verifica ni se fuerzan sus miembros.',
    ])
    if length == 0:
        procedure += '\n\nLa relación es indefinida para longitud cero (denominadores nulos).'
    return ContinuousProfile(length, tuple(rows), procedure)
