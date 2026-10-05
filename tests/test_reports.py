import pytest

from secado_app_1er_parcial.reports import calculate
from secado_app_1er_parcial.psychrometrics import air_state
from secado_app_1er_parcial.dryers import rotary
from secado_app_1er_parcial.procedure import value


@pytest.mark.parametrize('number,expected', [
    (1.23456789, '1.23457'),
    (1.2, '1.2'),
    (100.0, '100'),
    (-2.345678, '-2.34568'),
    (0.000001234567, '1.23457e-06'),
])
def test_visual_values_have_at_most_five_decimal_places(number, expected):
    assert value(number) == expected


def test_conversion_report():
    report = calculate('conversion', {'value': '1', 'source': 'ft', 'target': 'm'})
    assert report.values == [('Resultado', 0.3048, 'm')]
    assert '**Ecuación**' in report.procedure
    assert '**Sustitución de valores**' in report.procedure
    assert '**Resultado**' in report.procedure
    assert '1 ft' in report.procedure
    assert '0.3048 m' in report.procedure


def test_geometry_report_explicit_unit_conversion():
    report = calculate('geometry', {'shape': 'cube', 'a': '10', 'length_unit': 'cm'})
    values = {name: value for name, value, unit in report.values}
    assert values['Área total'] == pytest.approx(0.06)
    assert values['Volumen'] == pytest.approx(0.001)
    assert '10 cm' in report.procedure
    assert '0.1 m' in report.procedure
    assert report.procedure.count('**Ecuación**') >= 3
    assert r'A_T=6(0.1\ m)^2' in report.procedure
    assert r'V=(0.1\ m)^3' in report.procedure


def test_equilateral_triangular_prism_report_develops_every_geometry_step():
    report = calculate('geometry', {
        'shape': 'triangular_prism', 'a': '2', 'length': '3', 'length_unit': 'm',
    })
    assert 'h = \\sqrt{a^2-(a/2)^2}' in report.procedure
    assert 'A_b = \\frac{a h}{2}' in report.procedure
    assert 'V = A_b L' in report.procedure
    assert 'A_T = 2A_b + 3aL' in report.procedure


@pytest.mark.parametrize('shape,dimensions', [
    ('cylinder', {'r': '2', 'h': '3'}),
    ('sphere', {'r': '2'}),
    ('cube', {'a': '2'}),
    ('box', {'a': '2', 'b': '3', 'h': '4'}),
    ('cone', {'r': '2', 'h': '3'}),
    ('square_pyramid', {'a': '2', 'h': '3'}),
    ('quadrangular_prism', {'a': '2', 'b': '3', 'h': '4'}),
    ('frustum', {'r': '2', 'R': '4', 'h': '3'}),
    ('hemisphere', {'r': '2'}),
    ('hexagonal_prism', {'a': '2', 'h': '3'}),
])
def test_every_standard_geometry_report_substitutes_values(shape, dimensions):
    report = calculate('geometry', {'shape': shape, 'length_unit': 'm', **dimensions})
    assert report.procedure.count('**Sustitución de valores**') == len(dimensions)+2
    assert report.procedure.count('**Resultado**') == len(dimensions)+2


def test_psychrometric_report_states_inputs_and_all_obtained_properties():
    report = calculate('air', {
        'air1_key': 'dry_bulb', 'air2_key': 'relative_humidity',
        'air1': '170', 'air2': '10', 'temperature_unit': 'F',
    })
    assert 'Se tomaron los datos' in report.procedure
    assert '170 °F' in report.procedure
    assert '10 %' in report.procedure
    assert 'a partir de ellos se obtuvo' in report.procedure
    for label in ('Bulbo húmedo', 'Punto de rocío', 'Humedad absoluta',
                  'Volumen específico', 'Densidad húmeda', 'Entalpía'):
        assert label in report.procedure


def test_rotary_integrated_calculation_conserves_water_and_energy():
    inlet = air_state('dry_bulb', 200, 'relative_humidity', 5)
    outlet = rotary.outlet_temperature(200, inlet.wet_bulb_f)
    result = rotary.calculate(100, 25, 'dry', 5, 'dry', inlet, 70,
                              (inlet.wet_bulb_f+outlet)/2, 0.2, 1000, 1000)
    assert result.evaporated_lb_h == pytest.approx(20)
    assert result.latent_btu_h == pytest.approx(20000)
    assert result.size.outlet_mass_lb_h-result.dry_gas_lb_h*(1+inlet.humidity_ratio) == pytest.approx(20)
    assert result.heat_btu_h > result.latent_btu_h
    assert result.size.length_ft > 0


def test_rotary_confirmed_solid_temperature_limit():
    inlet = air_state('dry_bulb', 200, 'relative_humidity', 5)
    with pytest.raises(ValueError, match='Tv <= Tds <= Tgo'):
        rotary.calculate(100, 25, 'dry', 5, 'dry', inlet, 70, 200, 0.2, 1000, 1000)


def test_extruded_report_has_reynolds_and_si_time():
    report = calculate('extruded', dict(
        air1_key='dry_bulb', air2_key='relative_humidity', air1='140', air2='10',
        temperature_unit='F', mass='100', initial='20', initial_basis='wet',
        final='10', final_basis='dry', velocity='3600', velocity_unit='m/h', area='1', area_unit='m2',
        shape='cube', a='1', length_unit='cm', height='10', height_unit='cm',
        porosity='40', viscosity='0.02', latent='1000', latent_unit='Btu/lb'))
    assert 'Re' in {name for name, value, unit in report.values}
    assert ('Tiempo crítico', 's') in {(name, unit) for name, value, unit in report.values}
