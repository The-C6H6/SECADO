"""IP rotary calculations with user-confirmed moisture ratios and solid limits.

Mass flows lb/h; heat rates Btu/h; temperatures °F; latent heat Btu/lb.
The source assigns ha Btu/(h ft³ °F); its empirical validity is not independently
verified. Sizing requires an explicitly supplied heat rate, never inferred Q.
"""

import math
from dataclasses import dataclass

from ..units import convert
from ..moisture import dry_ratio, evaporated_from_dry
from ..psychrometrics import AirState, air_state
from ..validation import finite, nonnegative, positive


def outlet_temperature(inlet_f: float, wet_bulb_f: float, transfer_units: float = 1.5) -> float:
    positive(convert(inlet_f, 'F', 'R'), 'Temperatura absoluta de entrada')
    positive(convert(wet_bulb_f, 'F', 'R'), 'Temperatura absoluta de bulbo húmedo')
    positive(inlet_f-wet_bulb_f, 'Tgi − Tv')
    nonnegative(transfer_units, 'Unidades de transferencia')
    return wet_bulb_f+(inlet_f-wet_bulb_f)*math.exp(-transfer_units)


def log_mean_difference(inlet_f: float, outlet_f: float, wet_bulb_f: float) -> float:
    for value in (inlet_f, outlet_f, wet_bulb_f):
        positive(convert(value, 'F', 'R'), 'Temperatura absoluta')
    high, low = inlet_f-wet_bulb_f, outlet_f-wet_bulb_f
    positive(low, 'Tgo − Tv')
    if high < low:
        raise ValueError('La salida no puede superar la temperatura de entrada.')
    if high == low:
        return low
    return (high-low)/math.log1p((high-low)/low)


def latent_heat(evaporated_lb_h: float, latent_btu_lb: float) -> float:
    """Use already-computed evaporated flow to avoid ambiguous percent notation."""
    nonnegative(evaporated_lb_h, 'Flujo evaporado')
    positive(latent_btu_lb, 'Calor latente específico')
    return finite(evaporated_lb_h*latent_btu_lb, 'Calor latente (Btu/h)')


def dry_gas_flow(heat_btu_h: float, humidity_ratio: float, inlet_f: float,
                 outlet_f: float, cp_air: float = 0.242, cp_vapor: float = 0.447) -> float:
    """Heat capacities are Btu/(lb °F); W is lb water/lb dry air."""
    positive(heat_btu_h, 'Q (Btu/h)')
    nonnegative(humidity_ratio, 'Humedad absoluta')
    positive(cp_air, 'Cp aire')
    positive(cp_vapor, 'Cp vapor')
    for value in (inlet_f, outlet_f):
        positive(convert(value, 'F', 'R'), 'Temperatura absoluta')
    positive(inlet_f-outlet_f, 'Tgi − Tgo')
    return positive(heat_btu_h/((cp_air+humidity_ratio*cp_vapor)*(inlet_f-outlet_f)), 'Flujo seco')


def gas_mass_balance(dry_lb_h: float, humidity_ratio: float,
                     evaporated_lb_h: float) -> tuple[float, float]:
    positive(dry_lb_h, 'Flujo de gas seco')
    nonnegative(humidity_ratio, 'Humedad absoluta')
    nonnegative(evaporated_lb_h, 'Flujo evaporado')
    inlet = positive(dry_lb_h*(1+humidity_ratio), 'Flujo húmedo inicial')
    return inlet, positive(inlet+evaporated_lb_h, 'Flujo húmedo final')


@dataclass(frozen=True)
class RotarySize:
    outlet_mass_lb_h: float
    density_lb_ft3: float
    mass_flux_lb_ft2_h: float
    diameter_ft: float
    volumetric_coefficient: float
    log_mean_difference_f: float
    length_ft: float


def size_from_heat(heat_btu_h: float, dry_gas_lb_h: float, evaporated_lb_h: float,
                   humidity_ratio: float, inlet_f: float, outlet_f: float,
                   wet_bulb_f: float, velocity_ft_h: float) -> RotarySize:
    """Evaluate source sizing with external Q; caller must establish the energy balance.

    R=0.730 atm ft³/(lbmol °R), molecular weights 28.97 and 18.02 lb/lbmol,
    pressure 1 atm. These source approximations are explicit, not conversions.
    """
    positive(heat_btu_h, 'Q (Btu/h)')
    positive(velocity_ft_h, 'Velocidad (ft/h)')
    _, total = gas_mass_balance(dry_gas_lb_h, humidity_ratio, evaporated_lb_h)
    delta = log_mean_difference(inlet_f, outlet_f, wet_bulb_f)
    molecular_weight = total/(dry_gas_lb_h/28.97+(total-dry_gas_lb_h)/18.02)
    density = molecular_weight/(0.730*convert(outlet_f, 'F', 'R'))
    flux = positive(density*velocity_ft_h, 'G')
    diameter = positive(math.sqrt(4*total/(math.pi*flux)), 'Diámetro')
    ha = positive(flux**0.67/(2*diameter), 'ha')
    length = positive(heat_btu_h/(ha*delta*math.pi*diameter**2/4), 'Longitud')
    return RotarySize(total, density, flux, diameter, ha, delta, length)


def heat_balance(dry_solid_lb_h: float, initial_ratio: float, final_ratio: float,
                  solid_inlet_f: float, solid_outlet_f: float, wet_bulb_f: float,
                  gas_outlet_f: float, cp_solid: float, latent_btu_lb: float,
                  cp_liquid: float = 1, cp_vapor: float = 0.447) -> float:
    """Return Q in Btu/h. Moistures are lb water/lb dry solid, never percent.

    Heat capacities are Btu/(lb °F). User confirmed Tv <= Tds <= Tgo.
    """
    positive(dry_solid_lb_h, 'Flujo de sólido seco')
    nonnegative(initial_ratio, 'Humedad inicial (lb/lb)')
    nonnegative(final_ratio, 'Humedad final (lb/lb)')
    nonnegative(initial_ratio-final_ratio, 'Diferencia de humedades')
    for value in (solid_inlet_f, solid_outlet_f, wet_bulb_f, gas_outlet_f):
        positive(convert(value, 'F', 'R'), 'Temperatura absoluta')
    if not wet_bulb_f <= solid_outlet_f <= gas_outlet_f:
        raise ValueError('Se requiere Tv <= Tds <= Tgo.')
    for name, value in [('Cp sólido', cp_solid), ('Cp líquido', cp_liquid),
                        ('Cp vapor', cp_vapor), ('Calor latente', latent_btu_lb)]:
        positive(value, name)
    heat = dry_solid_lb_h*(cp_solid*(solid_outlet_f-solid_inlet_f)
        + initial_ratio*cp_liquid*(wet_bulb_f-solid_inlet_f)
        + final_ratio*cp_liquid*(solid_outlet_f-wet_bulb_f)
        + (initial_ratio-final_ratio)*(latent_btu_lb+cp_vapor*(gas_outlet_f-wet_bulb_f)))
    return positive(heat, 'Carga térmica de secado Q')


@dataclass(frozen=True)
class RotaryResult:
    evaporated_lb_h: float
    outlet_f: float
    heat_btu_h: float
    latent_btu_h: float
    dry_gas_lb_h: float
    size: RotarySize


def calculate(dry_solid_lb_h: float, initial_percent: float, initial_basis: str,
               final_percent: float, final_basis: str, inlet: AirState,
               solid_inlet_f: float, solid_outlet_f: float, cp_solid: float,
               latent_btu_lb: float, velocity_ft_h: float, transfer_units: float = 1.5,
               cp_air: float = 0.242, cp_vapor: float = 0.447,
               cp_liquid: float = 1) -> RotaryResult:
    evaporation = evaporated_from_dry(dry_solid_lb_h, initial_percent, initial_basis,
                                     final_percent, final_basis)
    outlet = outlet_temperature(inlet.dry_bulb_f, inlet.wet_bulb_f, transfer_units)
    heat = heat_balance(dry_solid_lb_h, dry_ratio(initial_percent, initial_basis),
                        dry_ratio(final_percent, final_basis), solid_inlet_f,
                        solid_outlet_f, inlet.wet_bulb_f, outlet, cp_solid,
                        latent_btu_lb, cp_liquid, cp_vapor)
    dry_gas = dry_gas_flow(heat, inlet.humidity_ratio, inlet.dry_bulb_f, outlet, cp_air, cp_vapor)
    air_state('dry_bulb', outlet, 'humidity_ratio', inlet.humidity_ratio+evaporation/dry_gas)
    size = size_from_heat(heat, dry_gas, evaporation, inlet.humidity_ratio,
                          inlet.dry_bulb_f, outlet, inlet.wet_bulb_f, velocity_ft_h)
    return RotaryResult(evaporation, outlet, heat, latent_heat(evaporation, latent_btu_lb), dry_gas, size)
