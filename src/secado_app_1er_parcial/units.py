"""Explicit conversions using international foot, pound and IT Btu definitions.

Pressure uses the course's fixed 1 atm = 14.69595 psi. Temperature differences
have a separate API so offsets cannot accidentally enter a heat balance.
"""

from .validation import finite, nonnegative

TEMPERATURES = {'C': (1, 273.15), 'F': (5 / 9, 459.67),
                'K': (1, 0), 'R': (5 / 9, 0)}
SCALES = {
    'm': ('length', 1), 'cm': ('length', 0.01),
    'ft': ('length', 0.3048), 'in': ('length', 0.0254),
    'm2': ('area', 1), 'cm2': ('area', 0.0001),
    'ft2': ('area', 0.3048**2), 'in2': ('area', 0.0254**2),
    'm3': ('volume', 1), 'cm3': ('volume', 1e-6),
    'ft3': ('volume', 0.3048**3), 'in3': ('volume', 0.0254**3),
    'kg': ('mass', 1), 'lb': ('mass', 0.45359237),
    'J/kg': ('specific_energy', 1), 'Btu/lb': ('specific_energy', 2326),
    'cP': ('viscosity', 0.001), 'kg/(m*s)': ('viscosity', 1),
    'kg/(m*h)': ('viscosity', 1 / 3600),
    'atm': ('pressure', 14.69595), 'psi': ('pressure', 1),
    'm/h': ('velocity', 1), 'ft/h': ('velocity', 0.3048),
    'm/s': ('velocity', 3600),
    'kg/m3': ('density', 1), 'lb/ft3': ('density', 0.45359237 / 0.3048**3),
    's': ('time', 1), 'h': ('time', 3600),
}


def convert(value: float, source: str, target: str) -> float:
    finite(value, 'Valor')
    if source in TEMPERATURES and target in TEMPERATURES:
        scale, offset = TEMPERATURES[source]
        kelvin = (value + offset) * scale
        nonnegative(kelvin, 'Temperatura absoluta')
        if source == target:
            return value
        target_scale, target_offset = TEMPERATURES[target]
        return finite(kelvin / target_scale - target_offset, 'Resultado')
    if source not in SCALES or target not in SCALES:
        raise ValueError('Unidades desconocidas o incompatibles.')
    dimension, factor = SCALES[source]
    target_dimension, target_factor = SCALES[target]
    if dimension != target_dimension:
        raise ValueError('No se pueden convertir magnitudes diferentes.')
    return finite(value * factor / target_factor, 'Resultado')


def temperature_difference(value: float, source: str, target: str) -> float:
    finite(value, 'Diferencia de temperatura')
    if source not in TEMPERATURES or target not in TEMPERATURES:
        raise ValueError('Unidad de temperatura desconocida.')
    return finite(value * TEMPERATURES[source][0] / TEMPERATURES[target][0], 'Resultado')
