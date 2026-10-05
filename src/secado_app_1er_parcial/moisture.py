"""Moisture percentages at boundaries; water/dry-solid mass ratios internally."""

from dataclasses import dataclass

from .validation import finite, nonnegative, positive


def dry_ratio(percent: float, basis: str) -> float:
    nonnegative(percent, 'Humedad (%)')
    if basis == 'dry':
        return percent / 100
    if basis == 'wet':
        if percent >= 100:
            raise ValueError('La humedad en base húmeda debe ser menor que 100%.')
        return percent / (100 - percent)
    raise ValueError('Base de humedad desconocida.')


def wet_percent(ratio: float) -> float:
    nonnegative(ratio, 'Razón de humedad')
    return 100 * (ratio / (1 + ratio))


@dataclass(frozen=True)
class MassBalance:
    """All masses have the same unit as the supplied wet-solid mass."""

    dry_solid: float
    initial_water: float
    final_water: float
    evaporated: float


def batch_balance(wet_mass: float, initial: float, initial_basis: str,
                  final: float, final_basis: str) -> MassBalance:
    positive(wet_mass, 'Masa húmeda')
    xi, xo = dry_ratio(initial, initial_basis), dry_ratio(final, final_basis)
    if xo > xi:
        raise ValueError('La humedad final no puede superar la inicial.')
    dry = wet_mass / (1 + xi)
    initial_water = wet_mass - dry
    final_water = dry * xo
    return MassBalance(dry, initial_water, final_water, max(0, initial_water - final_water))


def evaporated_from_dry(dry_mass: float, initial: float, initial_basis: str,
                        final: float, final_basis: str) -> float:
    """Return evaporated mass (or flow) in the same unit as dry_mass."""
    positive(dry_mass, 'Masa o flujo de sólido seco')
    difference = dry_ratio(initial, initial_basis) - dry_ratio(final, final_basis)
    nonnegative(difference, 'Diferencia de humedad inicial menos final')
    return finite(dry_mass * difference, 'Masa vaporizada')
