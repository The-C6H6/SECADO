"""Presentation-neutral calculation reports; all input conversions are explicit."""

from dataclasses import dataclass, field

from . import correlations, geometry, moisture, units
from .dryers import rotary
from .dryers.continuous import profile
from .dryers.tray import critical_time, mass_flux
from .psychrometrics import AirState, air_state
from .procedure import conversion_step, geometry_procedure, psychrometric_procedure, step, value
from .validation import finite, positive


@dataclass
class Report:
    values: list[tuple[str, float, str]] = field(default_factory=list)
    tables: list[tuple[list[str], list[list[float]]]] = field(default_factory=list)
    procedure: str = ''


def number(data: dict[str, str], key: str) -> float:
    try:
        value = float(data.get(key, '').strip().replace(',', '.'))
    except ValueError:
        raise ValueError(f'{key}: introduce un número (sin separadores de miles).') from None
    return finite(value, key)


def input_air(data: dict[str, str]) -> AirState:
    return air_state(data['air1_key'], number(data, 'air1'),
                     data['air2_key'], number(data, 'air2'),
                     temperature_unit=data['temperature_unit'])


def air_values(state: AirState) -> list[tuple[str, float, str]]:
    return [('Bulbo seco', state.dry_bulb_f, '°F'),
            ('Bulbo húmedo', state.wet_bulb_f, '°F'),
            ('Rocío', state.dew_point_f, '°F'),
            ('Humedad relativa', state.relative_humidity_percent, '%'),
            ('Humedad absoluta', state.humidity_ratio, 'lb agua/lb aire seco'),
            ('Volumen específico', state.volume_ft3_lb_dry, 'ft³/lb aire seco'),
            ('Densidad húmeda', state.density_lb_ft3, 'lb/ft³'),
            ('Entalpía', state.enthalpy_btu_lb_dry, 'Btu/lb aire seco')]


def input_geometry(data: dict[str, str]) -> geometry.Geometry:
    shape = data['shape']
    if shape == 'other':
        area_key = 'particle_area' if 'particle_area' in data else 'area'
        area_unit_key = 'particle_area_unit' if 'particle_area_unit' in data else 'area_unit'
        return geometry.calculate(shape,
            area=units.convert(number(data, area_key), data[area_unit_key], 'm2'),
            volume=units.convert(number(data, 'volume'), data['volume_unit'], 'm3'))
    dimensions = {key: units.convert(number(data, key), data['length_unit'], 'm')
                  for key in geometry.DIMENSIONS[shape]}
    return geometry.calculate(shape, **dimensions)


def _geometry_dimensions(data: dict[str, str]) -> dict[str, float]:
    return {key: units.convert(number(data, key), data['length_unit'], 'm')
            for key in geometry.DIMENSIONS[data['shape']]}


def _moisture_procedure(data: dict[str, str], balance: moisture.MassBalance) -> str:
    mass = number(data, 'mass')
    initial = number(data, 'initial')
    final = number(data, 'final')
    xi = moisture.dry_ratio(initial, data['initial_basis'])
    xo = moisture.dry_ratio(final, data['final_basis'])

    def ratio_step(label: str, percent: float, basis: str, ratio: float) -> str:
        if basis == 'dry':
            equation = r'X=\frac{w_{bs}}{100}'
            substitution = rf'X=\frac{{{value(percent)}\ \%}}{{100}}'
        else:
            equation = r'X=\frac{w_{bh}}{100-w_{bh}}'
            substitution = rf'X=\frac{{{value(percent)}\ \%}}{{100-{value(percent)}}}'
        return step(label, equation, substitution,
                    rf'X={value(ratio)}\ kg\ agua/kg\ sólido\ seco')

    return '\n\n'.join([
        '## Balance de humedad del sólido',
        ratio_step('Humedad inicial en base seca', initial, data['initial_basis'], xi),
        ratio_step('Humedad final en base seca', final, data['final_basis'], xo),
        step('Masa de sólido seco', r'm_{ss}=\frac{m_h}{1+X_i}',
             rf'm_{{ss}}=\frac{{{value(mass)}\ kg}}{{1+{value(xi)}\ kg\ agua/kg\ sólido\ seco}}',
             rf'm_{{ss}}={value(balance.dry_solid)}\ kg'),
        step('Agua inicial', r'm_{a,i}=m_h-m_{ss}',
             rf'm_{{a,i}}={value(mass)}\ kg-{value(balance.dry_solid)}\ kg',
             rf'm_{{a,i}}={value(balance.initial_water)}\ kg'),
        step('Agua final', r'm_{a,f}=m_{ss}X_f',
             rf'm_{{a,f}}=({value(balance.dry_solid)}\ kg)'
             rf'({value(xo)}\ kg\ agua/kg\ sólido\ seco)',
             rf'm_{{a,f}}={value(balance.final_water)}\ kg'),
        step('Masa de agua evaporada', r'm_v=m_{a,i}-m_{a,f}',
             rf'm_v={value(balance.initial_water)}\ kg-{value(balance.final_water)}\ kg',
             rf'm_v={value(balance.evaporated)}\ kg'),
    ])


def _transfer_procedure(data: dict[str, str], state: AirState, balance: moisture.MassBalance,
                        area: float, velocity: float, density: float, flux: float,
                        delta: float, latent: float, correlation,
                        transfer_area: float, seconds: float,
                        bed_data=None, particle=None) -> str:
    raw_area = number(data, 'area')
    raw_velocity = number(data, 'velocity')
    raw_latent = number(data, 'latent')
    dry_rankine = units.convert(state.dry_bulb_f, 'F', 'R')
    specific_volume = 0.730*dry_rankine*(1/28.97+state.humidity_ratio/18.02)
    density_ip = (1+state.humidity_ratio)/specific_volume
    pieces = [
        '## Flujo másico del aire',
        conversion_step('Temperatura de bulbo seco absoluta', state.dry_bulb_f, 'F', 'R', dry_rankine),
        step('Volumen específico del aire húmedo',
             r'V_H=0.730T_{bs,R}\left(\frac{1}{28.97}+\frac{H}{18.02}\right)',
             rf'V_H=0.730\ \frac{{atm\,ft^3}}{{lbmol\,^\circ R}}'
             rf'({value(dry_rankine)}\ ^\circ R)\left(\frac{{1}}{{28.97\ lb/lbmol}}+'
             rf'\frac{{{value(state.humidity_ratio)}\ lb\ agua/lb\ aire\ seco}}{{18.02\ lb/lbmol}}\right)',
             rf'V_H={value(specific_volume)}\ ft^3/lb\ aire\ seco'),
        step('Densidad del aire húmedo en sistema inglés', r'\rho_h=\frac{1+H}{V_H}',
             rf'\rho_h=\frac{{1+{value(state.humidity_ratio)}\ lb\ agua/lb\ aire\ seco}}'
             rf'{{{value(specific_volume)}\ ft^3/lb\ aire\ seco}}',
             rf'\rho_h={value(density_ip)}\ lb/ft^3'),
        conversion_step('Densidad del aire húmedo', density_ip, 'lb/ft3', 'kg/m3', density),
        conversion_step('Velocidad del aire', raw_velocity, data['velocity_unit'], 'm/h', velocity),
        step('Flujo másico superficial', r'G=\rho_h v',
             rf'G=({value(density)}\ kg/m^3)({value(velocity)}\ m/h)',
             rf'G={value(flux)}\ kg/(m^2\,h)'),
        conversion_step('Área de charola', raw_area, data['area_unit'], 'm2', area),
        step('Diferencia de temperatura en °F', r'\Delta T_F=T_{bs}-T_{bh}',
             rf'\Delta T_F={value(state.dry_bulb_f)}\ ^\circ F-{value(state.wet_bulb_f)}\ ^\circ F',
             rf'\Delta T_F={value(state.dry_bulb_f-state.wet_bulb_f)}\ ^\circ F\ de\ diferencia'),
        step('Conversión de diferencia de temperatura', r'\Delta T_K=\Delta T_F\frac{5}{9}',
             rf'\Delta T_K=({value(state.dry_bulb_f-state.wet_bulb_f)}\ ^\circ F)\frac{{5\ K}}{{9\ ^\circ F}}',
             rf'\Delta T={value(delta)}\ K'),
        conversion_step('Calor latente', raw_latent, data['latent_unit'], 'J/kg', latent),
    ]
    if bed_data is not None and particle is not None:
        if data['shape'] == 'other':
            particle_area = units.convert(number(data, 'particle_area'), data['particle_area_unit'], 'm2')
            particle_volume = units.convert(number(data, 'volume'), data['volume_unit'], 'm3')
            pieces.extend([
                conversion_step('Área de una partícula', number(data, 'particle_area'),
                                data['particle_area_unit'], 'm2', particle_area),
                conversion_step('Volumen de una partícula', number(data, 'volume'),
                                data['volume_unit'], 'm3', particle_volume),
            ])
        else:
            pieces.append(geometry_procedure(data['shape'], data, _geometry_dimensions(data), particle))
        bed_height = units.convert(number(data, 'height'), data['height_unit'], 'm')
        porosity_fraction = number(data, 'porosity')/100
        viscosity = units.convert(number(data, 'viscosity'), 'cP', 'kg/(m*h)')
        pieces.extend([
            conversion_step('Altura del lecho', number(data, 'height'), data['height_unit'], 'm', bed_height),
            step('Porosidad como fracción', r'\varepsilon=\frac{\varepsilon_{\%}}{100}',
                 rf'\varepsilon=\frac{{{value(number(data, "porosity"))}\ \%}}{{100}}',
                 rf'\varepsilon={value(porosity_fraction)}'),
            step('Volumen ocupado por sólidos', r'V_{ocupado}=A_cL_c(1-\varepsilon)',
                 rf'V_{{ocupado}}=({value(area)}\ m^2)({value(bed_height)}\ m)'
                 rf'(1-{value(porosity_fraction)})',
                 rf'V_{{ocupado}}={value(bed_data.occupied_volume_m3)}\ m^3'),
            step('Número equivalente de partículas', r'N=\frac{V_{ocupado}}{V_p}',
                 rf'N=\frac{{{value(bed_data.occupied_volume_m3)}\ m^3}}'
                 rf'{{{value(particle.volume_m3)}\ m^3/partícula}}',
                 rf'N={value(bed_data.particles)}\ partículas\ (sin\ redondear)'),
            step('Área total de partículas', r'A_T=NA_p',
                 rf'A_T=({value(bed_data.particles)}\ partículas)'
                 rf'({value(particle.area_m2)}\ m^2/partícula)',
                 rf'A_T={value(bed_data.area_m2)}\ m^2'),
            step('Diámetro equivalente', r'd_p=\sqrt{\frac{A_p}{\pi}}',
                 rf'd_p=\sqrt{{\frac{{{value(particle.area_m2)}\ m^2}}{{\pi}}}}',
                 rf'd_p={value(bed_data.diameter_m)}\ m'),
            conversion_step('Viscosidad del aire', number(data, 'viscosity'), 'cP', 'kg/(m*h)', viscosity),
            step('Número de Reynolds', r'Re=\frac{Gd_p}{\mu}',
                 rf'Re=\frac{{({value(flux)}\ kg/(m^2h))({value(bed_data.diameter_m)}\ m)}}'
                 rf'{{{value(viscosity)}\ kg/(m\,h)}}',
                 rf'Re={value(correlation.reynolds)}\quad\Rightarrow\quad {correlation.branch}'),
        ])
        if correlation.reynolds > 350:
            h_equation = r'h=\frac{0.151G^{0.59}}{d_p^{0.41}}'
            h_substitution = (rf'h=\frac{{0.151({value(flux)}\ kg/(m^2h))^{{0.59}}}}'
                              rf'{{({value(bed_data.diameter_m)}\ m)^{{0.41}}}}')
        else:
            h_equation = r'h=\frac{0.214G^{0.49}}{d_p^{0.51}}'
            h_substitution = (rf'h=\frac{{0.214({value(flux)}\ kg/(m^2h))^{{0.49}}}}'
                              rf'{{({value(bed_data.diameter_m)}\ m)^{{0.51}}}}')
        pieces.append(f'Correlación seleccionada: **{correlation.branch}**.')
    else:
        h_equation = r'h=0.0204G^{0.8}'
        h_substitution = rf'h=0.0204({value(flux)}\ kg/(m^2h))^{{0.8}}'
    pieces.extend([
        step('Coeficiente convectivo', h_equation, h_substitution,
             rf'h={value(correlation.value)}\ W/(m^2K)'),
        'Las unidades de las constantes empíricas fueron confirmadas por los apuntes del usuario: '
        '**h en W/(m²·K), G en kg/(m²·h) y dp en m**. Las constantes no se ajustaron.',
        step('Tiempo crítico de secado', r't=\frac{m_v\Delta H_v}{h\Delta T A}',
             rf't=\frac{{({value(balance.evaporated)}\ kg)({value(latent)}\ J/kg)}}'
             rf'{{({value(correlation.value)}\ W/(m^2K))({value(delta)}\ K)'
             rf'({value(transfer_area)}\ m^2)}}',
             rf't={value(seconds)}\ s\qquad (J/W=s)'),
    ])
    if bed_data is None:
        hours = units.convert(seconds, 's', 'h')
        pieces.append(conversion_step('Tiempo crítico', seconds, 's', 'h', hours))
    pieces.append(
        'La precisión interna se conserva. Los ejercicios académicos se comparan con las '
        'tolerancias autorizadas de 1 % para tiempos y ±0.5 °F para bulbo húmedo.'
    )
    return '\n\n'.join(pieces)


def _rotary_procedure(data: dict[str, str], state: AirState,
                      output: rotary.RotaryResult) -> str:
    unit = data['temperature_unit']
    mass = number(data, 'mass')
    initial = number(data, 'initial')
    final = number(data, 'final')
    xi = moisture.dry_ratio(initial, data['initial_basis'])
    xo = moisture.dry_ratio(final, data['final_basis'])
    solid_inlet = units.convert(number(data, 'solid_inlet'), unit, 'F')
    solid_outlet = units.convert(number(data, 'solid_outlet'), unit, 'F')
    cp_solid = number(data, 'cp_solid')
    latent = number(data, 'latent')
    nt = number(data, 'nt')
    cp_air = number(data, 'cp_air')
    cp_vapor = number(data, 'cp_vapor')
    cp_liquid = number(data, 'cp_liquid')
    velocity = number(data, 'velocity')
    inlet_wet_mass = output.dry_gas_lb_h*(1+state.humidity_ratio)
    outlet_ratio = state.humidity_ratio+output.evaporated_lb_h/output.dry_gas_lb_h
    molecular_weight = output.size.outlet_mass_lb_h/(
        output.dry_gas_lb_h/28.97+
        (output.size.outlet_mass_lb_h-output.dry_gas_lb_h)/18.02)
    outlet_rankine = units.convert(output.outlet_f, 'F', 'R')
    area = 3.141592653589793*output.size.diameter_ft**2/4

    def rotary_ratio(label: str, percent: float, basis: str, ratio: float) -> str:
        equation = r'X=\frac{w_{bs}}{100}' if basis == 'dry' else r'X=\frac{w_{bh}}{100-w_{bh}}'
        substitution = (rf'X=\frac{{{value(percent)}\ \%}}{{100}}' if basis == 'dry' else
                        rf'X=\frac{{{value(percent)}\ \%}}{{100-{value(percent)}}}')
        return step(label, equation, substitution,
                    rf'X={value(ratio)}\ lb\ agua/lb\ sólido\ seco')

    pieces = ['## Balance y dimensionamiento del secador rotatorio']
    for label, raw_key, converted in (
        ('Temperatura del sólido húmedo', 'solid_inlet', solid_inlet),
        ('Temperatura del sólido seco', 'solid_outlet', solid_outlet),
    ):
        pieces.append(conversion_step(label, number(data, raw_key), unit, 'F', converted))
    pieces.extend([
        rotary_ratio('Humedad inicial en base seca', initial, data['initial_basis'], xi),
        rotary_ratio('Humedad final en base seca', final, data['final_basis'], xo),
        step('Flujo de agua evaporada', r'm_v=m_{ss}(X_i-X_o)',
             rf'm_v=({value(mass)}\ lb\ sólido\ seco/h)'
             rf'({value(xi)}-{value(xo)}\ lb\ agua/lb\ sólido\ seco)',
             rf'm_v={value(output.evaporated_lb_h)}\ lb/h'),
        step('Temperatura del gas de salida',
             r'T_{go}=T_v+(T_{gi}-T_v)e^{-NT}',
             rf'T_{{go}}={value(state.wet_bulb_f)}\ ^\circ F+'
             rf'({value(state.dry_bulb_f)}-{value(state.wet_bulb_f)}\ ^\circ F)'
             rf'e^{{-{value(nt)}}}',
             rf'T_{{go}}={value(output.outlet_f)}\ ^\circ F'),
        step('Carga térmica total',
             r'Q=m_{ss}[C_{ps}(T_{ds}-T_{ws})+X_iC_{pl}(T_v-T_{ws})+'
             r'X_oC_{pl}(T_{ds}-T_v)+(X_i-X_o)(\Delta H_v+C_{pv}(T_{go}-T_v))]',
             rf'Q=({value(mass)}\ lb/h)[({value(cp_solid)}\ Btu/(lb\,^\circ F))'
             rf'({value(solid_outlet)}-{value(solid_inlet)}\ ^\circ F)+'
             rf'({value(xi)})({value(cp_liquid)}\ Btu/(lb\,^\circ F))'
             rf'({value(state.wet_bulb_f)}-{value(solid_inlet)}\ ^\circ F)+'
             rf'({value(xo)})({value(cp_liquid)}\ Btu/(lb\,^\circ F))'
             rf'({value(solid_outlet)}-{value(state.wet_bulb_f)}\ ^\circ F)+'
             rf'({value(xi)}-{value(xo)})({value(latent)}\ Btu/lb+'
             rf'({value(cp_vapor)}\ Btu/(lb\,^\circ F))'
             rf'({value(output.outlet_f)}-{value(state.wet_bulb_f)}\ ^\circ F))]',
             rf'Q={value(output.heat_btu_h)}\ Btu/h'),
        step('Carga térmica latente', r'Q_{latente}=m_v\Delta H_v',
             rf'Q_{{latente}}=({value(output.evaporated_lb_h)}\ lb/h)'
             rf'({value(latent)}\ Btu/lb)',
             rf'Q_{{latente}}={value(output.latent_btu_h)}\ Btu/h'),
        step('Flujo de gas seco',
             r'm_g=\frac{Q}{(C_{pa}+H_{gi}C_{pv})(T_{gi}-T_{go})}',
             rf'm_g=\frac{{{value(output.heat_btu_h)}\ Btu/h}}'
             rf'{{({value(cp_air)}+{value(state.humidity_ratio)}({value(cp_vapor)}))\ Btu/(lb\,^\circ F)'
             rf'({value(state.dry_bulb_f)}-{value(output.outlet_f)}\ ^\circ F)}}',
             rf'm_g={value(output.dry_gas_lb_h)}\ lb\ aire\ seco/h'),
        step('Gas húmedo de entrada', r'm_{g,h,i}=m_g(1+H_{gi})',
             rf'm_{{g,h,i}}=({value(output.dry_gas_lb_h)}\ lb/h)'
             rf'(1+{value(state.humidity_ratio)}\ lb\ agua/lb\ aire\ seco)',
             rf'm_{{g,h,i}}={value(inlet_wet_mass)}\ lb/h'),
        step('Gas húmedo de salida', r'm_{g,h,o}=m_{g,h,i}+m_v',
             rf'm_{{g,h,o}}={value(inlet_wet_mass)}\ lb/h+'
             rf'{value(output.evaporated_lb_h)}\ lb/h',
             rf'm_{{g,h,o}}={value(output.size.outlet_mass_lb_h)}\ lb/h'),
        step('Humedad absoluta del gas de salida', r'H_{go}=H_{gi}+\frac{m_v}{m_g}',
             rf'H_{{go}}={value(state.humidity_ratio)}+'
             rf'\frac{{{value(output.evaporated_lb_h)}\ lb/h}}'
             rf'{{{value(output.dry_gas_lb_h)}\ lb\ aire\ seco/h}}',
             rf'H_{{go}}={value(outlet_ratio)}\ lb\ agua/lb\ aire\ seco'),
        'Con $T_{go}$ y $H_{go}$ se consultó PsychroLib en sistema inglés a 1 atm. '
        'La consulta fue válida y confirmó que el gas de salida no está sobresaturado.',
        step('Diferencia media logarítmica de temperatura',
             r'\Delta T_{ml}=\frac{T_{gi}-T_{go}}{\ln[(T_{gi}-T_v)/(T_{go}-T_v)]}',
             rf'\Delta T_{{ml}}=\frac{{{value(state.dry_bulb_f)}-{value(output.outlet_f)}\ ^\circ F}}'
             rf'{{\ln[({value(state.dry_bulb_f)}-{value(state.wet_bulb_f)})/'
             rf'({value(output.outlet_f)}-{value(state.wet_bulb_f)})]}}',
             rf'\Delta T_{{ml}}={value(output.size.log_mean_difference_f)}\ ^\circ F\ de\ diferencia'),
        step('Peso molecular medio del gas de salida',
             r'PM=\frac{m_{g,h,o}}{m_g/28.97+(m_{g,h,o}-m_g)/18.02}',
             rf'PM=\frac{{{value(output.size.outlet_mass_lb_h)}\ lb/h}}'
             rf'{{{value(output.dry_gas_lb_h)}/28.97+'
             rf'({value(output.size.outlet_mass_lb_h)}-{value(output.dry_gas_lb_h)})/18.02\ lbmol/h}}',
             rf'PM={value(molecular_weight)}\ lb/lbmol'),
        conversion_step('Temperatura absoluta del gas de salida', output.outlet_f, 'F', 'R', outlet_rankine),
        step('Densidad del gas de salida', r'\rho=\frac{PM}{0.730T_{go,R}}',
             rf'\rho=\frac{{{value(molecular_weight)}\ lb/lbmol}}'
             rf'{{0.730\ atm\,ft^3/(lbmol\,^\circ R)({value(outlet_rankine)}\ ^\circ R)}}',
             rf'\rho={value(output.size.density_lb_ft3)}\ lb/ft^3'),
        step('Flujo másico superficial de salida', r'G=\rho v',
             rf'G=({value(output.size.density_lb_ft3)}\ lb/ft^3)({value(velocity)}\ ft/h)',
             rf'G={value(output.size.mass_flux_lb_ft2_h)}\ lb/(ft^2h)'),
        step('Diámetro del secador', r'D=\sqrt{\frac{4m_{g,h,o}}{\pi G}}',
             rf'D=\sqrt{{\frac{{4({value(output.size.outlet_mass_lb_h)}\ lb/h)}}'
             rf'{{\pi({value(output.size.mass_flux_lb_ft2_h)}\ lb/(ft^2h))}}}}',
             rf'D={value(output.size.diameter_ft)}\ ft'),
        step('Coeficiente volumétrico', r'ha=\frac{G^{0.67}}{2D}',
             rf'ha=\frac{{({value(output.size.mass_flux_lb_ft2_h)}\ lb/(ft^2h))^{{0.67}}}}'
             rf'{{2({value(output.size.diameter_ft)}\ ft)}}',
             rf'ha={value(output.size.volumetric_coefficient)}\ Btu/(h\,ft^3\,^\circ F)'),
        step('Área transversal', r'A=\frac{\pi D^2}{4}',
             rf'A=\frac{{\pi({value(output.size.diameter_ft)}\ ft)^2}}{{4}}',
             rf'A={value(area)}\ ft^2'),
        step('Longitud del secador', r'L=\frac{Q}{ha\Delta T_{ml}A}',
             rf'L=\frac{{{value(output.heat_btu_h)}\ Btu/h}}'
             rf'{{({value(output.size.volumetric_coefficient)}\ Btu/(h\,ft^3\,^\circ F))'
             rf'({value(output.size.log_mean_difference_f)}\ ^\circ F)({value(area)}\ ft^2)}}',
             rf'L={value(output.size.length_ft)}\ ft'),
        'Se verificó el límite confirmado por el usuario: '
        rf'${value(state.wet_bulb_f)}\ ^\circ F \leq {value(solid_outlet)}\ ^\circ F '
        rf'\leq {value(output.outlet_f)}\ ^\circ F$.',
    ])
    return '\n\n'.join(pieces)


def calculate(mode: str, data: dict[str, str]) -> Report:
    if mode == 'conversion':
        input_value = number(data, 'value')
        output_value = units.convert(input_value, data['source'], data['target'])
        return Report([('Resultado', output_value, data['target'])], procedure=conversion_step(
            'Resultado', input_value, data['source'], data['target'], output_value))
    if mode == 'geometry':
        shape = input_geometry(data)
        dimensions = {} if data['shape'] == 'other' else _geometry_dimensions(data)
        procedure = geometry_procedure(data['shape'], data, dimensions, shape)
        return Report([('Área total', shape.area_m2, 'm²'), ('Volumen', shape.volume_m3, 'm³')],
            procedure=procedure)
    state = input_air(data)
    result = Report(air_values(state), procedure=psychrometric_procedure(data, state)+'\n\n')
    if mode == 'air':
        return result
    if mode == 'continuous':
        if data['air1_key'] != 'dry_bulb' or data['air2_key'] not in {'relative_humidity', 'humidity_ratio'}:
            raise ValueError('Continuo requiere bulbo seco y humedad relativa o absoluta.')
        raw_outlet = number(data, 'outlet')
        outlet = units.convert(raw_outlet, data['temperature_unit'], 'F')
        calculation = profile(state, outlet)
        result.values.append(('Longitud', calculation.length_ft, 'ft'))
        result.tables.append((['Z (ft)', 'Tg (°F)', 'Tbh (°F)', 'HR (%)', 'H (lb/lb)', 'Hv (lb/lb)'],
            [[row.z_ft, row.air.dry_bulb_f, row.wet_bulb_f, row.air.relative_humidity_percent,
              row.air.humidity_ratio, row.saturated_humidity_ratio] for row in calculation.rows]))
        result.procedure += conversion_step('Temperatura del aire de salida', raw_outlet,
            data['temperature_unit'], 'F', outlet)+'\n\n'+calculation.procedure
        return result
    if mode == 'rotary':
        unit = data['temperature_unit']
        output = rotary.calculate(number(data, 'mass'), number(data, 'initial'), data['initial_basis'],
            number(data, 'final'), data['final_basis'], state,
            units.convert(number(data, 'solid_inlet'), unit, 'F'),
            units.convert(number(data, 'solid_outlet'), unit, 'F'), number(data, 'cp_solid'),
            number(data, 'latent'), number(data, 'velocity'), number(data, 'nt'),
            number(data, 'cp_air'), number(data, 'cp_vapor'), number(data, 'cp_liquid'))
        result.values += [('Agua evaporada', output.evaporated_lb_h, 'lb/h'),
            ('Gas de salida', output.outlet_f, '°F'), ('Q total', output.heat_btu_h, 'Btu/h'),
            ('Q latente', output.latent_btu_h, 'Btu/h'), ('Gas seco', output.dry_gas_lb_h, 'lb/h'),
            ('Gas húmedo de salida', output.size.outlet_mass_lb_h, 'lb/h'),
            ('Densidad de salida', output.size.density_lb_ft3, 'lb/ft³'),
            ('G de salida', output.size.mass_flux_lb_ft2_h, 'lb/(ft²·h)'),
            ('ΔT media logarítmica', output.size.log_mean_difference_f, '°F de diferencia'),
            ('ha', output.size.volumetric_coefficient, 'Btu/(h·ft³·°F)'),
            ('Diámetro', output.size.diameter_ft, 'ft'), ('Longitud', output.size.length_ft, 'ft')]
        result.procedure += _rotary_procedure(data, state, output)
        return result
    if mode not in {'tray', 'extruded'}:
        raise ValueError('Cálculo desconocido.')
    balance = moisture.batch_balance(number(data, 'mass'), number(data, 'initial'), data['initial_basis'],
                                     number(data, 'final'), data['final_basis'])
    area = positive(units.convert(number(data, 'area'), data['area_unit'], 'm2'), 'Área de charola')
    velocity = positive(units.convert(number(data, 'velocity'), data['velocity_unit'], 'm/h'), 'Velocidad (m/h)')
    density, flux = mass_flux(state, velocity)
    delta = units.temperature_difference(state.dry_bulb_f-state.wet_bulb_f, 'F', 'K')
    latent = units.convert(number(data, 'latent'), data['latent_unit'], 'J/kg')
    transfer_area = area
    bed = None
    particle = None
    result.values += [('Sólido seco', balance.dry_solid, 'kg'),
        ('Agua inicial', balance.initial_water, 'kg'), ('Agua final', balance.final_water, 'kg'),
        ('Agua evaporada', balance.evaporated, 'kg'), ('Área de charola', area, 'm²'),
        ('Densidad para correlación', density, 'kg/m³'), ('G', flux, 'kg/(m²·h)'),
        ('ΔT', delta, 'K'), ('Calor latente', latent, 'J/kg')]
    if mode == 'tray':
        correlation = correlations.tray(flux)
    else:
        particle = input_geometry(data)
        bed = geometry.bed(area, units.convert(number(data, 'height'), data['height_unit'], 'm'),
                           number(data, 'porosity'), particle)
        viscosity = units.convert(number(data, 'viscosity'), 'cP', 'kg/(m*h)')
        correlation = correlations.extruded(flux, bed.diameter_m, viscosity)
        transfer_area = bed.area_m2
        result.values += [('Volumen ocupado del lecho', bed.occupied_volume_m3, 'm³'),
            ('Número equivalente de partículas', bed.particles, 'sin redondear'),
            ('Área total de partículas', bed.area_m2, 'm²'), ('dp', bed.diameter_m, 'm'),
            ('Viscosidad', viscosity, 'kg/(m·h)'), ('Re', correlation.reynolds, 'adimensional')]
    seconds = critical_time(balance.evaporated, latent, correlation.value, delta, transfer_area)
    result.values += [('h', correlation.value, correlation.unit), ('Tiempo crítico', seconds, 's')]
    if mode == 'tray':
        result.values.append(('Tiempo crítico', units.convert(seconds, 's', 'h'), 'h'))
    result.procedure += _moisture_procedure(data, balance)+'\n\n'
    result.procedure += _transfer_procedure(
        data, state, balance, area, velocity, density, flux, delta, latent,
        correlation, transfer_area, seconds, bed, particle)
    return result
