"""Markdown builders for auditable calculation procedures."""

from . import geometry, units
from .psychrometrics import AirState, PRESSURE_PSI


PROPERTY_LABELS = {
    'dry_bulb': ('T_{bs}', 'Bulbo seco'),
    'wet_bulb': ('T_{bh}', 'Bulbo húmedo'),
    'dew_point': ('T_{rocío}', 'Punto de rocío'),
    'relative_humidity': ('HR', 'Humedad relativa'),
    'humidity_ratio': ('H', 'Humedad absoluta'),
}


def value(number: float) -> str:
    """Format a displayed value without changing the underlying calculation."""
    if number == 0:
        return '0'
    if abs(number) < 0.00001:
        mantissa, exponent = f'{number:.5e}'.split('e')
        return f'{mantissa.rstrip("0").rstrip(".")}e{exponent}'
    return f'{number:.5f}'.rstrip('0').rstrip('.')


def step(title: str, equation: str, substitution: str, result: str) -> str:
    return (
        f'### {title}\n\n'
        f'**Ecuación**\n\n$$ {equation} $$\n\n'
        f'**Sustitución de valores**\n\n$$ {substitution} $$\n\n'
        f'**Resultado**\n\n$$ {result} $$'
    )


def conversion_step(quantity: str, input_value: float, source: str,
                    target: str, output_value: float) -> str:
    if source in units.TEMPERATURES and target in units.TEMPERATURES:
        source_scale, source_offset = units.TEMPERATURES[source]
        target_scale, target_offset = units.TEMPERATURES[target]
        kelvin = (input_value+source_offset)*source_scale
        equation = (
            f'T_K=(T_{{{source}}}+{value(source_offset)})'
            rf'({value(source_scale)}),\quad '
            f'T_{{{target}}}=\\frac{{T_K}}{{{value(target_scale)}}}'
            f'-{value(target_offset)}'
        )
        substitution = (
            rf'T_K=({value(input_value)}\ ^\circ {source}+{value(source_offset)})'
            rf'({value(source_scale)})={value(kelvin)}\ K,\quad '
            rf'T_{{{target}}}=\frac{{{value(kelvin)}\ K}}{{{value(target_scale)}}}'
            f'-{value(target_offset)}'
        )
    else:
        _, source_factor = units.SCALES[source]
        _, target_factor = units.SCALES[target]
        equation = f'x_{{{target}}}=x_{{{source}}}\\frac{{f_{{{source}}}}}{{f_{{{target}}}}}'
        substitution = (
            rf'x_{{{target}}}={value(input_value)}\ {source}'
            rf'\left(\frac{{{value(source_factor)}}}{{{value(target_factor)}}}\right)'
        )
    rendered = step(
        f'Conversión: {quantity}', equation, substitution,
        rf'{quantity}={value(output_value)}\ {target}',
    )
    return (rendered+f'\n\nConversión comprobada: **{value(input_value)} {source} = '
            f'{value(output_value)} {target}**.')


def psychrometric_procedure(data: dict[str, str], state: AirState) -> str:
    unit = data['temperature_unit']
    pieces = ['## Consulta psicrométrica']
    for key in ('air1_key', 'air2_key'):
        property_key = data[key]
        if property_key in {'dry_bulb', 'wet_bulb', 'dew_point'} and unit != 'F':
            raw = float(data['air1' if key == 'air1_key' else 'air2'].replace(',', '.'))
            converted = units.convert(raw, unit, 'F')
            pieces.append(conversion_step(PROPERTY_LABELS[property_key][1], raw, unit, 'F', converted))
    for property_key, raw_key in ((data['air1_key'], 'air1'), (data['air2_key'], 'air2')):
        if property_key == 'relative_humidity':
            percent = float(data[raw_key].replace(',', '.'))
            pieces.append(step(
                'Conversión de humedad relativa', r'\phi=\frac{HR}{100}',
                rf'\phi=\frac{{{value(percent)}\ \%}}{{100}}',
                rf'\phi={value(percent/100)}',
            ))
    first_key, second_key = data['air1_key'], data['air2_key']
    first_raw = float(data['air1'].replace(',', '.'))
    second_raw = float(data['air2'].replace(',', '.'))
    first_unit = f'°{unit}' if first_key in {'dry_bulb', 'wet_bulb', 'dew_point'} else (
        '%' if first_key == 'relative_humidity' else 'lb agua/lb aire seco')
    second_unit = f'°{unit}' if second_key in {'dry_bulb', 'wet_bulb', 'dew_point'} else (
        '%' if second_key == 'relative_humidity' else 'lb agua/lb aire seco')
    first_ip = units.convert(first_raw, unit, 'F') if first_key in {'dry_bulb', 'wet_bulb', 'dew_point'} else (
        first_raw/100 if first_key == 'relative_humidity' else first_raw)
    second_ip = units.convert(second_raw, unit, 'F') if second_key in {'dry_bulb', 'wet_bulb', 'dew_point'} else (
        second_raw/100 if second_key == 'relative_humidity' else second_raw)
    first_ip_unit = '°F' if first_key in {'dry_bulb', 'wet_bulb', 'dew_point'} else (
        'fracción' if first_key == 'relative_humidity' else 'lb agua/lb aire seco')
    second_ip_unit = '°F' if second_key in {'dry_bulb', 'wet_bulb', 'dew_point'} else (
        'fracción' if second_key == 'relative_humidity' else 'lb agua/lb aire seco')
    pieces.append(
        f'Se tomaron los datos **{PROPERTY_LABELS[first_key][1]} = {value(first_raw)} {first_unit}** '
        f'y **{PROPERTY_LABELS[second_key][1]} = {value(second_raw)} {second_unit}** para entrar '
        'con psicrometría. Se empleó PsychroLib en sistema inglés a '
        f'**1 atm = {PRESSURE_PSI} psi** y, a partir de ellos se obtuvo el estado completo.'
    )
    obtained = (
        rf'T_{{bs}}={value(state.dry_bulb_f)}\ ^\circ F;\quad '
        rf'T_{{bh}}={value(state.wet_bulb_f)}\ ^\circ F;\quad '
        rf'T_{{rocío}}={value(state.dew_point_f)}\ ^\circ F;\\ '
        rf'HR={value(state.relative_humidity_percent)}\ \%;\quad '
        rf'H={value(state.humidity_ratio)}\ \frac{{lb\ agua}}{{lb\ aire\ seco}};\\ '
        rf'V_H={value(state.volume_ft3_lb_dry)}\ \frac{{ft^3}}{{lb\ aire\ seco}};\quad '
        rf'\rho_h={value(state.density_lb_ft3)}\ \frac{{lb}}{{ft^3}};\quad '
        rf'h_a={value(state.enthalpy_btu_lb_dry)}\ \frac{{Btu}}{{lb\ aire\ seco}}'
    )
    pieces.append(step(
        'Obtención del estado psicrométrico',
        r'Estado=PsychroLib_{IP}(Dato_1,Dato_2,P)',
        rf'PsychroLib_{{IP}}({PROPERTY_LABELS[first_key][0]}={value(first_ip)}\ {first_ip_unit},'
        rf'{PROPERTY_LABELS[second_key][0]}={value(second_ip)}\ {second_ip_unit},'
        rf'P={PRESSURE_PSI}\ psi)',
        obtained,
    ))
    pieces.append(
        'Datos obtenidos:\n\n'
        f'- Bulbo seco: **{value(state.dry_bulb_f)} °F**.\n'
        f'- Bulbo húmedo: **{value(state.wet_bulb_f)} °F**.\n'
        f'- Punto de rocío: **{value(state.dew_point_f)} °F**.\n'
        f'- Humedad relativa: **{value(state.relative_humidity_percent)} %**.\n'
        f'- Humedad absoluta: **{value(state.humidity_ratio)} lb agua/lb aire seco**.\n'
        f'- Volumen específico: **{value(state.volume_ft3_lb_dry)} ft³/lb aire seco**.\n'
        f'- Densidad húmeda: **{value(state.density_lb_ft3)} lb/ft³**.\n'
        f'- Entalpía: **{value(state.enthalpy_btu_lb_dry)} Btu/lb aire seco**.'
    )
    return '\n\n'.join(pieces)


def geometry_procedure(shape: str, data: dict[str, str], converted: dict[str, float],
                       result: geometry.Geometry) -> str:
    pieces = ['## Geometría']
    if shape == 'other':
        area_key = 'particle_area' if 'particle_area' in data else 'area'
        area_unit_key = 'particle_area_unit' if 'particle_area_unit' in data else 'area_unit'
        pieces.extend([
            conversion_step('Área total', float(data[area_key].replace(',', '.')),
                            data[area_unit_key], 'm2', result.area_m2),
            conversion_step('Volumen', float(data['volume'].replace(',', '.')),
                            data['volume_unit'], 'm3', result.volume_m3),
            'Para la figura “Otra” se utilizan directamente el área total y el volumen '
            'proporcionados; no se infiere ninguna forma geométrica.',
        ])
        return '\n\n'.join(pieces)
    source = data['length_unit']
    dimension_names = {
        'r': 'Radio r', 'R': 'Radio R', 'h': 'Altura h', 'a': 'Lado a',
        'b': 'Lado b', 'length': 'Longitud del prisma',
    }
    for key in geometry.DIMENSIONS[shape]:
        raw = float(data[key].replace(',', '.'))
        pieces.append(conversion_step(dimension_names[key], raw, source, 'm', converted[key]))
    d = converted
    a = d.get('a')
    if shape == 'triangular_prism':
        triangle_height = (a**2-(a/2)**2)**0.5
        base = a*triangle_height/2
        pieces.extend([
            step('Altura del triángulo equilátero', r'h = \sqrt{a^2-(a/2)^2}',
                 rf'h=\sqrt{{({value(a)}\ m)^2-({value(a)}\ m/2)^2}}',
                 rf'h={value(triangle_height)}\ m'),
            step('Área de la base triangular', r'A_b = \frac{a h}{2}',
                 rf'A_b=\frac{{({value(a)}\ m)({value(triangle_height)}\ m)}}{{2}}',
                 rf'A_b={value(base)}\ m^2'),
            step('Volumen del prisma', r'V = A_b L',
                 rf'V=({value(base)}\ m^2)({value(d["length"])}\ m)',
                 rf'V={value(result.volume_m3)}\ m^3'),
            step('Área total del prisma', r'A_T = 2A_b + 3aL',
                 rf'A_T=2({value(base)}\ m^2)+3({value(a)}\ m)({value(d["length"])}\ m)',
                 rf'A_T={value(result.area_m2)}\ m^2'),
        ])
        return '\n\n'.join(pieces)
    formulas = {
        'cylinder': (r'A_T=2\pi r(h+r)', r'V=\pi r^2h'),
        'sphere': (r'A_T=4\pi r^2', r'V=\frac{4}{3}\pi r^3'),
        'cube': (r'A_T=6a^2', r'V=a^3'),
        'box': (r'A_T=2(ab+ah+bh)', r'V=abh'),
        'quadrangular_prism': (r'A_T=2(ab+ah+bh)', r'V=abh'),
        'cone': (r'A_T=\pi r(r+\sqrt{r^2+h^2})', r'V=\frac{\pi r^2h}{3}'),
        'square_pyramid': (r'A_T=a^2+2a\sqrt{h^2+(a/2)^2}', r'V=\frac{a^2h}{3}'),
        'frustum': (r'A_T=\pi(R+r)\sqrt{h^2+(R-r)^2}+\pi(R^2+r^2)',
                    r'V=\frac{\pi h(R^2+Rr+r^2)}{3}'),
        'hemisphere': (r'A_T=3\pi r^2', r'V=\frac{2}{3}\pi r^3'),
        'hexagonal_prism': (r'A_T=3\sqrt{3}a^2+6ah',
                            r'V=\frac{3\sqrt{3}}{2}a^2h'),
    }
    area_equation, volume_equation = formulas[shape]
    substitutions = {
        'cylinder': lambda: (
            rf'A_T=2\pi({value(d["r"])}\ m)({value(d["h"])}\ m+{value(d["r"])}\ m)',
            rf'V=\pi({value(d["r"])}\ m)^2({value(d["h"])}\ m)'),
        'sphere': lambda: (
            rf'A_T=4\pi({value(d["r"])}\ m)^2',
            rf'V=\frac{{4}}{{3}}\pi({value(d["r"])}\ m)^3'),
        'cube': lambda: (
            rf'A_T=6({value(a)}\ m)^2',
            rf'V=({value(a)}\ m)^3'),
        'box': lambda: (
            rf'A_T=2[({value(a)}\ m)({value(d["b"])}\ m)+'
            rf'({value(a)}\ m)({value(d["h"])}\ m)+'
            rf'({value(d["b"])}\ m)({value(d["h"])}\ m)]',
            rf'V=({value(a)}\ m)({value(d["b"])}\ m)({value(d["h"])}\ m)'),
        'quadrangular_prism': lambda: (
            rf'A_T=2[({value(a)}\ m)({value(d["b"])}\ m)+'
            rf'({value(a)}\ m)({value(d["h"])}\ m)+'
            rf'({value(d["b"])}\ m)({value(d["h"])}\ m)]',
            rf'V=({value(a)}\ m)({value(d["b"])}\ m)({value(d["h"])}\ m)'),
        'cone': lambda: (
            rf'A_T=\pi({value(d["r"])}\ m)'
            rf'[({value(d["r"])}\ m)+\sqrt{{({value(d["r"])}\ m)^2+'
            rf'({value(d["h"])}\ m)^2}}]',
            rf'V=\frac{{\pi({value(d["r"])}\ m)^2({value(d["h"])}\ m)}}{{3}}'),
        'square_pyramid': lambda: (
            rf'A_T=({value(a)}\ m)^2+2({value(a)}\ m)'
            rf'\sqrt{{({value(d["h"])}\ m)^2+({value(a)}\ m/2)^2}}',
            rf'V=\frac{{({value(a)}\ m)^2({value(d["h"])}\ m)}}{{3}}'),
        'frustum': lambda: (
            rf'A_T=\pi({value(d["R"])}\ m+{value(d["r"])}\ m)'
            rf'\sqrt{{({value(d["h"])}\ m)^2+({value(d["R"])}\ m-'
            rf'{value(d["r"])}\ m)^2}}+\pi[({value(d["R"])}\ m)^2+'
            rf'({value(d["r"])}\ m)^2]',
            rf'V=\frac{{\pi({value(d["h"])}\ m)[({value(d["R"])}\ m)^2+'
            rf'({value(d["R"])}\ m)({value(d["r"])}\ m)+'
            rf'({value(d["r"])}\ m)^2]}}{{3}}'),
        'hemisphere': lambda: (
            rf'A_T=3\pi({value(d["r"])}\ m)^2',
            rf'V=\frac{{2}}{{3}}\pi({value(d["r"])}\ m)^3'),
        'hexagonal_prism': lambda: (
            rf'A_T=3\sqrt{{3}}({value(a)}\ m)^2+'
            rf'6({value(a)}\ m)({value(d["h"])}\ m)',
            rf'V=\frac{{3\sqrt{{3}}}}{{2}}({value(a)}\ m)^2'
            rf'({value(d["h"])}\ m)'),
    }
    area_substitution, volume_substitution = substitutions[shape]()
    pieces.extend([
        step('Área total cerrada', area_equation, area_substitution,
             rf'A_T={value(result.area_m2)}\ m^2'),
        step('Volumen', volume_equation, volume_substitution,
             rf'V={value(result.volume_m3)}\ m^3'),
    ])
    return '\n\n'.join(pieces)
