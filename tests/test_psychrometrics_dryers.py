import itertools
import math

import psychrolib
import pytest

from secado_app_1er_parcial.psychrometrics import air_state, saturation_ratio
from secado_app_1er_parcial.dryers.continuous import profile
from secado_app_1er_parcial.dryers import rotary


def test_psychrometric_ip_invariants():
    psychrolib.SetUnitSystem(psychrolib.SI)
    state = air_state('dry_bulb', 86, 'relative_humidity', 50)
    assert psychrolib.GetUnitSystem() == psychrolib.IP
    assert state.dry_bulb_f == 86
    assert state.relative_humidity_percent == pytest.approx(50)
    assert state.dew_point_f < state.wet_bulb_f < state.dry_bulb_f
    assert 0.013 < state.humidity_ratio < 0.014
    assert state.density_lb_ft3 == pytest.approx((1+state.humidity_ratio)/state.volume_ft3_lb_dry)


PAIRS = [p for p in itertools.combinations(
    ['dry_bulb', 'wet_bulb', 'dew_point', 'relative_humidity', 'humidity_ratio'], 2)
    if set(p) != {'dew_point', 'humidity_ratio'}]


@pytest.mark.parametrize('pair', PAIRS)
def test_independent_pairs_recover_the_same_state(pair):
    original = air_state('dry_bulb', 86, 'relative_humidity', 50)
    values = dict(dry_bulb=86, wet_bulb=original.wet_bulb_f,
                  dew_point=original.dew_point_f, relative_humidity=50,
                  humidity_ratio=original.humidity_ratio)
    result = air_state(pair[0], values[pair[0]], pair[1], values[pair[1]])
    assert result.dry_bulb_f == pytest.approx(86, abs=0.005)
    assert result.humidity_ratio == pytest.approx(original.humidity_ratio, abs=2e-6)


@pytest.mark.parametrize('temperature', [-4, 32, 68, 170])
@pytest.mark.parametrize('pair', PAIRS)
def test_saturated_independent_pairs_remain_valid(temperature, pair):
    values = dict(dry_bulb=temperature, wet_bulb=temperature, dew_point=temperature,
                  relative_humidity=100, humidity_ratio=saturation_ratio(temperature))
    result = air_state(pair[0], values[pair[0]], pair[1], values[pair[1]])
    assert result.dry_bulb_f == pytest.approx(temperature, abs=0.004)
    assert result.relative_humidity_percent == pytest.approx(100, abs=0.001)


def test_small_real_supersaturation_is_still_rejected():
    with pytest.raises(ValueError, match='sobresaturado'):
        air_state('dry_bulb', 68, 'humidity_ratio', saturation_ratio(68)*1.00001)


@pytest.mark.parametrize('args', [
    ('humidity_ratio', 0.01, 'dew_point', 50),
    ('dry_bulb', 80, 'dry_bulb', 70),
    ('dry_bulb', 80, 'wet_bulb', 90),
    ('dry_bulb', 80, 'dew_point', 90),
    ('dry_bulb', 80, 'humidity_ratio', 0.1),
    ('dry_bulb', 80, 'relative_humidity', 101),
    ('dry_bulb', 80, 'relative_humidity', 0),
    ('dry_bulb', math.nan, 'relative_humidity', 50),
    ('dry_bulb', 390, 'wet_bulb', 10),
    ('dry_bulb', 392, 'relative_humidity', 100),
])
def test_invalid_or_underdetermined_air(args):
    with pytest.raises(ValueError):
        air_state(*args)


def test_saturation_and_celsius_input():
    state = air_state('dry_bulb', 20, 'relative_humidity', 100, temperature_unit='C')
    assert state.dry_bulb_f == pytest.approx(68)
    assert state.wet_bulb_f == pytest.approx(68, abs=0.002)
    assert state.humidity_ratio == pytest.approx(saturation_ratio(68))


def test_fractional_continuous_endpoint_and_fixed_wet_bulb():
    initial = air_state('dry_bulb', 140, 'relative_humidity', 10)
    outlet = initial.wet_bulb_f+(140-initial.wet_bulb_f)*math.exp(-0.1377*2.5)
    result = profile(initial, outlet)
    assert [row.z_ft for row in result.rows] == pytest.approx([0, 1, 2, 2.5])
    assert result.rows[0].air is initial
    assert result.rows[-1].air.dry_bulb_f == outlet
    assert result.length_ft == pytest.approx(2.5)
    assert all(row.wet_bulb_f == initial.wet_bulb_f for row in result.rows)
    assert len({row.saturated_humidity_ratio for row in result.rows}) == 1
    assert 'no se verifica' in result.procedure.lower()
    assert result.procedure.count('Extremo inferior') == 1
    assert result.procedure.count('Extremo superior') == 1
    assert 'Fila intermedia' not in result.procedure
    assert '**Ecuación**' in result.procedure
    assert '**Sustitución de valores**' in result.procedure
    assert '**Resultado**' in result.procedure


def test_integer_endpoint_not_duplicated():
    initial = air_state('dry_bulb', 140, 'relative_humidity', 10)
    outlet = initial.wet_bulb_f+(140-initial.wet_bulb_f)*math.exp(-0.1377*3)
    result = profile(initial, outlet)
    assert len(result.rows) == 4
    assert result.rows[-1].z_ft == result.length_ft


def test_zero_length_and_impossible_outlet():
    initial = air_state('dry_bulb', 140, 'relative_humidity', 10)
    zero = profile(initial, 140)
    assert zero.length_ft == 0
    assert len(zero.rows) == 1
    assert 'indefinida' in zero.procedure
    for outlet in (initial.wet_bulb_f, initial.wet_bulb_f-1, 150, math.inf):
        with pytest.raises(ValueError):
            profile(initial, outlet)


def test_rotary_defined_primitives():
    assert rotary.outlet_temperature(200, 100, math.log(2)) == pytest.approx(150)
    assert rotary.log_mean_difference(200, 150, 100) == pytest.approx(50/math.log(2))
    assert rotary.latent_heat(20, 1000) == 20000
    assert rotary.dry_gas_flow(250940, 0.02, 200, 100) == pytest.approx(10000)
    assert rotary.gas_mass_balance(100, 0.02, 10) == (102, 112)


def test_rotary_sizing_with_explicit_heat_input():
    result = rotary.size_from_heat(10000, 100, 10, 0.02, 200, 150, 100, 1000)
    assert result.outlet_mass_lb_h == 112
    assert result.diameter_ft > 0
    assert result.length_ft > 0
    assert math.pi*result.diameter_ft**2/4*result.mass_flux_lb_ft2_h == pytest.approx(112)
    assert result.volumetric_coefficient*result.log_mean_difference_f*math.pi*result.diameter_ft**2/4*result.length_ft == pytest.approx(10000)


@pytest.mark.parametrize('args', [(100, 110, 1.5), (200, 100, -1), (math.inf, 100, 1)])
def test_invalid_rotary_outlet(args):
    with pytest.raises(ValueError):
        rotary.outlet_temperature(*args)


def test_rotary_heat_balance_uses_mass_ratios_not_percentages():
    result = rotary.heat_balance(100, 0.25, 0.05, 60, 120, 100, 150, 0.2, 1000)
    assert result == pytest.approx(22747)


@pytest.mark.parametrize('xi,xo', [(0.05, 0.25), (-0.1, 0), (math.nan, 0)])
def test_rotary_heat_balance_rejects_invalid_moisture(xi, xo):
    with pytest.raises(ValueError):
        rotary.heat_balance(100, xi, xo, 60, 120, 100, 150, 0.2, 1000)
