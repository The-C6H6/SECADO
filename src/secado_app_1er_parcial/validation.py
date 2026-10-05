import math


def finite(value: float, name: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f'{name}: debe ser un número finito.')
    return value


def positive(value: float, name: str) -> float:
    if finite(value, name) <= 0:
        raise ValueError(f'{name}: debe ser mayor que cero.')
    return value


def nonnegative(value: float, name: str) -> float:
    if finite(value, name) < 0:
        raise ValueError(f'{name}: no puede ser negativo.')
    return value
