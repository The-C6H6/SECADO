"""Empirical h in W/(m² K), confirmed by the user's academic notes, 2026-10-04.

G must be kg/(m² h), dp metres and viscosity kg/(m h). Constants are unchanged.
Confirmation of units is not independent experimental validation of applicability.
"""

from dataclasses import dataclass
from typing import ClassVar

from .validation import positive


@dataclass(frozen=True)
class CorrelationResult:
    value: float
    branch: str
    reynolds: float | None = None
    units_validated: ClassVar[bool] = True
    unit: ClassVar[str] = 'W/(m²·K)'


def tray(mass_flux_kg_m2_h: float) -> CorrelationResult:
    positive(mass_flux_kg_m2_h, 'G (kg/(m²·h))')
    return CorrelationResult(0.0204*mass_flux_kg_m2_h**0.8, 'h = 0.0204 G^0.8')


def extruded(mass_flux_kg_m2_h: float, diameter_m: float,
             viscosity_kg_m_h: float) -> CorrelationResult:
    positive(mass_flux_kg_m2_h, 'G (kg/(m²·h))')
    positive(diameter_m, 'dp (m)')
    positive(viscosity_kg_m_h, 'Viscosidad (kg/(m·h))')
    re = positive(mass_flux_kg_m2_h*diameter_m/viscosity_kg_m_h, 'Re')
    if re > 350:
        value = 0.151*mass_flux_kg_m2_h**0.59/diameter_m**0.41
        branch = 'Re > 350'
    else:
        value = 0.214*mass_flux_kg_m2_h**0.49/diameter_m**0.51
        branch = 'Re <= 350'
    return CorrelationResult(positive(value, 'Valor numérico'), branch, re)
