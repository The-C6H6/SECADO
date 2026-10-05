import math

import pytest

from secado_app_1er_parcial import units, moisture, geometry, correlations


@pytest.mark.parametrize('value,source,target,expected', [
    (0, 'C', 'F', 32), (212, 'F', 'C', 100),
    (273.15, 'K', 'R', 491.67), (491.67, 'R', 'C', 0),
    (1, 'ft', 'm', 0.3048), (1, 'in2', 'm2', 0.00064516),
    (1, 'ft3', 'm3', 0.028316846592), (1, 'lb', 'kg', 0.45359237),
    (1, 'cP', 'kg/(m*h)', 3.6),
    (1, 'Btu/lb', 'J/kg', 2326), (1, 'atm', 'psi', 14.69595),
])
def test_explicit_conversions(value, source, target, expected):
    assert units.convert(value, source, target) == pytest.approx(expected)


def test_temperature_difference_has_no_offset():
    assert units.temperature_difference(18, 'F', 'K') == 10


@pytest.mark.parametrize('args', [(1, 'm', 'kg'), (-1, 'K', 'F'),
                                   (math.inf, 'm', 'ft'), (math.nan, 'C', 'F')])
def test_invalid_conversion(args):
    with pytest.raises(ValueError):
        units.convert(*args)


def test_supplied_moisture_example():
    assert moisture.dry_ratio(21, 'wet') == pytest.approx(21 / 79)
    assert moisture.wet_percent(21 / 79) == pytest.approx(21)


def test_batch_mass_conservation():
    result = moisture.batch_balance(100, 20, 'wet', 10, 'dry')
    assert result.dry_solid == 80
    assert result.initial_water == 20
    assert result.final_water == 8
    assert result.evaporated == 12
    assert result.dry_solid + result.initial_water == 100


def test_dry_solid_flow_balance():
    assert moisture.evaporated_from_dry(100, 25, 'dry', 5, 'dry') == 20


@pytest.mark.parametrize('args', [(100, 100, 'wet', 0, 'dry'),
    (100, 10, 'dry', 20, 'dry'), (0, 10, 'dry', 0, 'dry'),
    (100, math.nan, 'dry', 0, 'dry'), (100, 20, 'unknown', 0, 'dry')])
def test_invalid_balance(args):
    with pytest.raises(ValueError):
        moisture.batch_balance(*args)


@pytest.mark.parametrize('shape,dimensions,area,volume', [
    ('cylinder', {'r': 1, 'h': 2}, 6*math.pi, 2*math.pi),
    ('sphere', {'r': 1}, 4*math.pi, 4*math.pi/3),
    ('cube', {'a': 2}, 24, 8),
    ('box', {'a': 2, 'b': 3, 'h': 4}, 52, 24),
    ('quadrangular_prism', {'a': 2, 'b': 3, 'h': 4}, 52, 24),
    ('cone', {'r': 3, 'h': 4}, 24*math.pi, 12*math.pi),
    ('square_pyramid', {'a': 6, 'h': 4}, 96, 48),
    ('triangular_prism', {'a': 2, 'length': 3}, 18+2*math.sqrt(3), 3*math.sqrt(3)),
    ('frustum', {'r': 1, 'R': 4, 'h': 4}, 42*math.pi, 28*math.pi),
    ('hemisphere', {'r': 1}, 3*math.pi, 2*math.pi/3),
    ('hexagonal_prism', {'a': 1, 'h': 2}, 3*math.sqrt(3)+12, 3*math.sqrt(3)),
    ('other', {'area': 7, 'volume': 2}, 7, 2),
])
def test_closed_surface_geometry(shape, dimensions, area, volume):
    result = geometry.calculate(shape, **dimensions)
    assert result.area_m2 == pytest.approx(area)
    assert result.volume_m3 == pytest.approx(volume)


@pytest.mark.parametrize('shape,dimensions', [
    ('cube', {'a': -1}), ('sphere', {'r': math.nan}),
    ('triangular_prism', {'a': 1, 'length': 0}),
])
def test_invalid_geometry(shape, dimensions):
    with pytest.raises(ValueError):
        geometry.calculate(shape, **dimensions)


def test_triangular_prism_only_requires_equilateral_side_and_length():
    assert geometry.DIMENSIONS['triangular_prism'] == ('a', 'length')
    result = geometry.calculate('triangular_prism', a=2, length=3)
    triangle_height = math.sqrt(2**2-(2/2)**2)
    base_area = 2*triangle_height/2
    assert result.volume_m3 == pytest.approx(base_area*3)
    assert result.area_m2 == pytest.approx(2*base_area+3*2*3)


def test_bed_uses_fractional_particle_count():
    result = geometry.bed(2, 0.5, 40, geometry.calculate('cube', a=0.2))
    assert result.particles == pytest.approx(75)
    assert result.occupied_volume_m3 == pytest.approx(0.6)
    assert result.area_m2 == pytest.approx(18)
    assert result.diameter_m == pytest.approx(math.sqrt(0.24 / math.pi))


def test_tray_correlation_has_user_confirmed_si_units():
    result = correlations.tray(100)
    assert result.value == pytest.approx(0.812138627928)
    assert result.units_validated is True
    assert result.unit == 'W/(m²·K)'


@pytest.mark.parametrize('reynolds,branch,constant,power', [
    (349, 'Re <= 350', 0.214, 0.49),
    (350, 'Re <= 350', 0.214, 0.49),
    (351, 'Re > 350', 0.151, 0.59),
])
def test_reynolds_selects_correlation(reynolds, branch, constant, power):
    result = correlations.extruded(reynolds, 1, 1)
    assert result.branch == branch
    assert result.reynolds == reynolds
    assert result.value == pytest.approx(constant * reynolds**power)
    assert result.units_validated is True


@pytest.mark.parametrize('args', [(0, 1, 1), (1, 0, 1), (1, 1, 0), (math.inf, 1, 1)])
def test_correlation_rejects_nonphysical_inputs(args):
    with pytest.raises(ValueError):
        correlations.extruded(*args)
