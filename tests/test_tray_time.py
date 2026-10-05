"""Analytic checks and partial academic regression; no reverse-engineered inputs."""

import math

import pytest

from secado_app_1er_parcial import correlations
from secado_app_1er_parcial.dryers.tray import critical_time, mass_flux
from secado_app_1er_parcial.psychrometrics import air_state
from secado_app_1er_parcial.reports import calculate


def test_academic_tray_mass_flux_to_coefficient():
    # User-provided rounded academic values, 2026-10-04.
    assert correlations.tray(14314).value == pytest.approx(43.07, abs=0.01)


def test_analytic_time_is_energy_divided_by_power_in_seconds():
    # Synthetic dimensional example, NOT an academic reference exercise.
    assert critical_time(2, 2000, 10, 5, 4) == 20
    assert critical_time(0, 2000, 10, 5, 4) == 0


@pytest.mark.parametrize('args', [
    (-1, 2000, 10, 5, 4), (1, 0, 10, 5, 4), (1, 2000, 0, 5, 4),
    (1, 2000, 10, 0, 4), (1, 2000, 10, -5, 4), (1, 2000, 10, 5, 0),
    (math.nan, 2000, 10, 5, 4), (1, math.inf, 10, 5, 4),
])
def test_time_rejects_invalid_inputs(args):
    with pytest.raises(ValueError):
        critical_time(*args)


def test_mass_flux_uses_explicit_source_constants():
    state = air_state('dry_bulb', 86, 'relative_humidity', 50)
    density, flux = mass_flux(state, 3600)
    assert 1 < density < 1.3
    assert flux == density*3600


def test_latent_heat_unit_invariance_and_hours():
    inputs = dict(air1_key='dry_bulb', air2_key='relative_humidity', air1='140', air2='10',
        temperature_unit='F', mass='100', initial='20', initial_basis='wet',
        final='10', final_basis='dry', velocity='3600', velocity_unit='m/h', area='1', area_unit='m2',
        latent='1000', latent_unit='Btu/lb')
    btu = calculate('tray', inputs)
    si = calculate('tray', {**inputs, 'latent': '2326000', 'latent_unit': 'J/kg'})
    btu_times = {unit: value for name, value, unit in btu.values if name == 'Tiempo crítico'}
    si_times = {unit: value for name, value, unit in si.values if name == 'Tiempo crítico'}
    assert btu_times == si_times
    assert btu_times['h'] == btu_times['s']/3600


def academic_inputs():
    return dict(air1_key='dry_bulb', air2_key='relative_humidity', air1='170', air2='10',
        temperature_unit='F', mass='73', initial='30', initial_basis='dry', final='10',
        final_basis='dry', velocity='4', velocity_unit='m/s', area='1.5', area_unit='m2',
        latent='1037.2', latent_unit='Btu/lb')


def academic_extruded_inputs():
    # The source gives diameter 0.25 in; the geometry API requires radius.
    return {**academic_inputs(), 'velocity': '2', 'shape': 'cylinder',
        'r': str(0.25/2), 'h': '0.5', 'length_unit': 'in', 'height': '2.5',
        'height_unit': 'cm', 'porosity': '50', 'viscosity': '0.02'}


def test_academic_tray_checkpoints_from_complete_inputs():
    report = calculate('tray', academic_inputs())
    values = {name: value for name, value, unit in report.values}
    assert values['Agua evaporada'] == pytest.approx(11.23, abs=0.005)
    assert values['G'] == pytest.approx(14314, abs=1)
    assert values['h'] == pytest.approx(43.07, abs=0.01)
    assert values['Humedad absoluta'] == pytest.approx(0.0265, abs=0.00005)
    assert report.procedure.count('**Ecuación**') >= 8
    assert '1037.2 Btu/lb' in report.procedure
    assert 'J/kg' in report.procedure
    assert 'kg/(m²·h)' in report.procedure
    assert 'W/(m²·K)' in report.procedure


def test_academic_extruded_geometric_and_transfer_checkpoints():
    report = calculate('extruded', academic_extruded_inputs())
    values = {name: value for name, value, unit in report.values}
    assert values['Volumen ocupado del lecho'] == pytest.approx(0.01875)
    assert values['Número equivalente de partículas'] == pytest.approx(46618, abs=1)
    assert values['Área total de partículas'] == pytest.approx(14.76, abs=0.005)
    assert values['dp'] == pytest.approx(0.01004, abs=0.000005)
    assert values['G'] == pytest.approx(7157, abs=1)
    assert values['Re'] == pytest.approx(998, abs=1)
    assert values['h'] == pytest.approx(187.3, abs=0.05)
    assert '**Re > 350**' in report.procedure


@pytest.mark.parametrize('mode,inputs,target,unit', [
    ('tray', academic_inputs(), 3, 'h'),
    ('extruded', academic_extruded_inputs(), 252, 's'),
])
def test_academic_time_with_chart_tolerance(mode, inputs, target, unit):
    report = calculate(mode, inputs)
    values = {name: value for name, value, result_unit in report.values if result_unit == unit}
    assert values['Tiempo crítico'] == pytest.approx(target, rel=0.01)
    all_values = {name: value for name, value, result_unit in report.values}
    assert all_values['Bulbo húmedo'] == pytest.approx(100, abs=0.5)
    assert all_values['ΔT'] == pytest.approx(38.89, abs=0.5*5/9+0.005)
