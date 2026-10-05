"""Closed total surface areas in m² and volumes in m³; dimensions in metres."""

import math
from dataclasses import dataclass

from .validation import nonnegative, positive

DIMENSIONS = {
    'cylinder': ('r', 'h'), 'sphere': ('r',), 'cube': ('a',),
    'box': ('a', 'b', 'h'), 'cone': ('r', 'h'),
    'square_pyramid': ('a', 'h'),
    'triangular_prism': ('a', 'length'),
    'quadrangular_prism': ('a', 'b', 'h'), 'frustum': ('r', 'R', 'h'),
    'hemisphere': ('r',), 'hexagonal_prism': ('a', 'h'),
    'other': ('area', 'volume'),
}


@dataclass(frozen=True)
class Geometry:
    area_m2: float
    volume_m3: float

    def __post_init__(self):
        positive(self.area_m2, 'Área (m²)')
        positive(self.volume_m3, 'Volumen (m³)')


def calculate(shape: str, **dimensions: float) -> Geometry:
    if shape not in DIMENSIONS or set(dimensions) != set(DIMENSIONS[shape]):
        raise ValueError('Figura o dimensiones incorrectas.')
    for name, value in dimensions.items():
        positive(value, name)
    d = dimensions
    pi = math.pi
    if shape == 'other':
        return Geometry(d['area'], d['volume'])
    if shape in ('cylinder', 'cone', 'sphere', 'hemisphere', 'frustum'):
        r = d['r']
        if shape == 'sphere':
            return Geometry(4*pi*r*r, 4*pi*r**3/3)
        if shape == 'hemisphere':
            return Geometry(3*pi*r*r, 2*pi*r**3/3)
        h = d['h']
        if shape == 'cylinder':
            return Geometry(2*pi*r*(h+r), pi*r*r*h)
        if shape == 'cone':
            return Geometry(pi*r*(r+math.hypot(r, h)), pi*r*r*h/3)
        large = d['R']
        return Geometry(pi*(large+r)*math.hypot(h, large-r)+pi*(large**2+r*r),
                        pi*h*(large**2+large*r+r*r)/3)
    a = d['a']
    if shape == 'cube':
        return Geometry(6*a*a, a**3)
    if shape == 'triangular_prism':
        length = d['length']
        triangle_height = math.sqrt(a**2-(a/2)**2)
        base = a*triangle_height/2
        return Geometry(2*base+3*a*length, base*length)
    h = d['h']
    if shape == 'square_pyramid':
        return Geometry(a*a+2*a*math.hypot(h, a/2), a*a*h/3)
    if shape == 'hexagonal_prism':
        return Geometry(3*math.sqrt(3)*a*a+6*a*h, 3*math.sqrt(3)*a*a*h/2)
    b = d['b']
    return Geometry(2*(a*b+a*h+b*h), a*b*h)


@dataclass(frozen=True)
class BedGeometry:
    particles: float
    area_m2: float
    diameter_m: float
    occupied_volume_m3: float


def bed(tray_area_m2: float, height_m: float, porosity_percent: float,
        particle: Geometry) -> BedGeometry:
    """Continuum particle count (not rounded); dp = sqrt(total particle area / pi)."""
    positive(tray_area_m2, 'Área de charola')
    positive(height_m, 'Altura de lecho')
    nonnegative(porosity_percent, 'Porosidad')
    if porosity_percent >= 100:
        raise ValueError('La porosidad debe ser menor que 100%.')
    occupied = positive(tray_area_m2*height_m*(1-porosity_percent/100), 'Volumen ocupado')
    count = occupied/particle.volume_m3
    positive(count, 'Número de partículas')
    area = positive(count*particle.area_m2, 'Área total')
    return BedGeometry(count, area, math.sqrt(particle.area_m2/math.pi), occupied)
