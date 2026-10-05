"""SI critical drying time for trays and extruded solids; no UI dependencies."""

from ..psychrometrics import AirState
from ..units import convert
from ..validation import finite, nonnegative, positive


def critical_time(evaporated_kg: float, latent_j_kg: float, h_w_m2_k: float,
                   delta_kelvin: float, area_m2: float) -> float:
    """Return seconds: (kg × J/kg) / (W/(m² K) × K × m²) = J/W = s.

    Zero evaporation returns zero with otherwise valid drying conditions.
    Saturated air (zero thermal driving force) is not a finite drying calculation.
    """
    nonnegative(evaporated_kg, 'Masa evaporada (kg)')
    positive(latent_j_kg, 'Calor latente (J/kg)')
    positive(h_w_m2_k, 'h (W/(m²·K))')
    positive(delta_kelvin, 'Diferencia de temperatura (K)')
    positive(area_m2, 'Área de transferencia (m²)')
    power = positive(h_w_m2_k*delta_kelvin*area_m2, 'Potencia térmica (W)')
    energy = nonnegative(evaporated_kg*latent_j_kg, 'Energía de vaporización (J)')
    return finite(energy/power, 'Tiempo crítico (s)')


def mass_flux(state: AirState, velocity_m_h: float) -> tuple[float, float]:
    """Return wet-gas density kg/m³ and G kg/(m² h) using the supplied air state.

    Course ideal-gas constants: R=0.730 atm ft³/(lbmol °R), P=1 atm,
    molecular weights 28.97 and 18.02 lb/lbmol. Exact unit conversions replace
    the source's rounded +460 and 0.454 approximations.
    """
    positive(velocity_m_h, 'Velocidad (m/h)')
    volume = positive(0.730*convert(state.dry_bulb_f, 'F', 'R')*
                      (1/28.97+state.humidity_ratio/18.02), 'Volumen específico')
    density = convert((1+state.humidity_ratio)/volume, 'lb/ft3', 'kg/m3')
    return density, positive(density*velocity_m_h, 'G (kg/(m²·h))')
