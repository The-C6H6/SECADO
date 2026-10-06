from pathlib import Path

import flet as ft

from .. import geometry, units
from ..reports import Report, calculate, input_air, air_values, number
from ..procedure import value as format_value
from ..dryers.rotary import outlet_temperature
from .fields import DIMENSION_LABELS, MODE_DETAILS, MODES, PROPERTIES, SHAPES

INK = '#123044'
ACCENT = '#13A6B5'
HEAT = '#E56B35'
BACKGROUND = '#E8EFF1'
PAPER = '#FFFFFF'
FIELD_BACKGROUND = '#F4F7F8'
GRAPHITE = '#26343C'
MUTED = '#61747E'
DIVIDER = '#CCD9DE'
WARNING = '#9A4A20'
ASSETS_DIR = Path(__file__).resolve().parents[3] / 'assets'


def _eyebrow(text: str, color: str = ACCENT) -> ft.Text:
    return ft.Text(text, size=11, weight=ft.FontWeight.W_700, color=color,
                   font_family='Bahnschrift')


def _panel_border(color: str) -> ft.Border:
    return ft.Border(left=ft.BorderSide(width=4, color=color))


def _input_border(color: str, width: float = 1) -> ft.OutlineInputBorder:
    return ft.OutlineInputBorder(
        border_radius=8,
        side=ft.BorderSide(width=width, color=color),
    )


def _process_stage(icon, label: str, caption: str) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(icon, color=ACCENT, size=18),
                    ft.Text(label, color='white', size=13,
                            weight=ft.FontWeight.W_600)], spacing=7),
            ft.Text(caption, color='#B9CDD5', size=10),
        ], spacing=2),
        padding=8,
        col=4,
    )


class CalculatorForm:
    def __init__(self, mode: str, update):
        self.mode = mode
        self.update = update
        self.fields = {}
        self.report: Report | None = None
        self.error = ft.Text('', color='#AA2330', selectable=True)
        self.result = ft.Column(spacing=16)
        self.empty_state = ft.Container(
            content=ft.Column([
                ft.Container(content=ft.Icon(ft.Icons.DATA_OBJECT, color=ACCENT, size=28),
                             width=52, height=52, alignment=ft.Alignment.CENTER,
                             bgcolor='#E2F5F7', border_radius=26),
                ft.Text('Listo para calcular', size=18, color=INK,
                        weight=ft.FontWeight.W_600, font_family='Bahnschrift'),
                ft.Text('Completa los datos de entrada. Aquí aparecerán las magnitudes, '
                        'unidades y el procedimiento.', color=MUTED, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=32,
            alignment=ft.Alignment.CENTER,
        )
        self.input_controls = []
        self.geometry_keys = []
        self.geometry_header = ft.ResponsiveRow(spacing=12, run_spacing=12)
        self.geometry_controls = ft.Column(spacing=12)
        self.image = ft.Image(src='', height=150, visible=False)
        self.geometry_section = ft.Column([
            self.geometry_header,
            self.image,
            self.geometry_controls,
        ], spacing=12)
        self.air_preview = ft.Markdown('')
        self._build_inputs()
        left = ft.Column([
            _eyebrow('01 · CONDICIONES DE ENTRADA'),
            ft.Text('Datos de entrada', size=24, weight=ft.FontWeight.W_600,
                    color=INK, font_family='Bahnschrift'),
            ft.Text('Introduce los valores del ejercicio y selecciona la unidad de cada magnitud.',
                    color=MUTED),
            ft.Column(self.input_controls, spacing=14),
        ], spacing=16)
        if mode == 'rotary':
            left.controls += [ft.Button('Calcular aire y límites de Tds', icon=ft.Icons.AIR,
                                        on_click=self.preview_air, color=INK),
                              self.air_preview]
        self.calculate_button = ft.Button(
            'Calcular', icon=ft.Icons.CALCULATE, on_click=self.submit,
            bgcolor=ACCENT, color=INK, height=48, elevation=0,
        )
        left.controls += [self.calculate_button, self.error]
        right = ft.Column([
            _eyebrow('02 · RESULTADO DEL MODELO', HEAT),
            ft.Text('Resultados y procedimiento', size=24, weight=ft.FontWeight.W_600,
                    color=INK, font_family='Bahnschrift'),
            ft.Text('Cada valor conserva su unidad. El procedimiento documenta conversiones y supuestos.',
                    color=MUTED),
            self.empty_state,
            self.result,
        ], spacing=16)
        if mode in {'tray', 'extruded'}:
            right.controls.insert(3, ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO, color=WARNING, size=19),
                    ft.Text('h en W/(m²·K) · tiempo en s · calor latente en J/kg',
                            color=WARNING, size=12, expand=True),
                ]), padding=12, bgcolor='#FFF1E8', border_radius=8))
        self.input_panel = ft.Container(
            left, col={'xs': 12, 'lg': 5}, padding=24, bgcolor=PAPER,
            border=_panel_border(ACCENT), border_radius=12,
            shadow=ft.BoxShadow(blur_radius=18, color='#140B2533', offset=ft.Offset(0, 6)),
        )
        self.result_panel = ft.Container(
            right, col={'xs': 12, 'lg': 7}, padding=24, bgcolor=PAPER,
            border=_panel_border(HEAT), border_radius=12,
            shadow=ft.BoxShadow(blur_radius=18, color='#140B2533', offset=ft.Offset(0, 6)),
        )
        self.control = ft.ResponsiveRow([
            self.input_panel,
            self.result_panel,
        ], spacing=20, run_spacing=20)

    def _text(self, key, label, default=''):
        control = ft.TextField(
            label=label, value=default, col={'xs': 12, 'sm': 6},
            on_change=self.invalidate, filled=True, fill_color=FIELD_BACKGROUND,
            border={
                ft.ControlState.DEFAULT: _input_border(DIVIDER),
                ft.ControlState.FOCUSED: _input_border(ACCENT, 2),
            },
        )
        self.fields[key] = control
        return control

    def _select(self, key, label, options, default, *, handler=None):
        if not isinstance(options, dict):
            options = {value: value for value in options}
        control = ft.Dropdown(label=label, value=default,
            options=[ft.DropdownOption(key=value, text=text) for value, text in options.items()],
            col={'xs': 12, 'sm': 6}, on_select=handler or self.invalidate,
            filled=True, fill_color=FIELD_BACKGROUND,
            border={
                ft.ControlState.DEFAULT: _input_border(DIVIDER),
                ft.ControlState.FOCUSED: _input_border(ACCENT, 2),
            })
        self.fields[key] = control
        return control

    @staticmethod
    def _set_group_columns(controls):
        count = len(controls)
        for control in controls:
            control.expand = True
        if count == 1:
            controls[0].col = {'xs': 12}
            return
        breakpoint = 'md' if count == 3 else 'sm'
        width = 12 // count
        for control in controls:
            control.col = {'xs': 12, breakpoint: width}

    def _group(self, *controls, target=None):
        controls = list(controls)
        self._set_group_columns(controls)
        group = ft.ResponsiveRow(controls, spacing=12, run_spacing=12)
        (self.input_controls if target is None else target).append(group)
        return group

    def _build_inputs(self):
        mode = self.mode
        if mode == 'conversion':
            options = list(units.TEMPERATURES) + list(units.SCALES)
            self._group(
                self._text('value', 'Valor'),
                self._select('source', 'Unidad de origen', options, 'ft'),
                self._select('target', 'Unidad de destino', options, 'm'),
            )
            return

        if mode != 'geometry':
            self._group(self._select(
                'temperature_unit', 'Unidad de todas las temperaturas',
                ['F', 'C', 'K', 'R'], 'F'))
            first_properties = (
                {'dry_bulb': 'Bulbo seco'} if mode == 'continuous' else PROPERTIES
            )
            self._group(
                self._select('air1_key', 'Primera propiedad del aire',
                             first_properties, 'dry_bulb'),
                self._text('air1', 'Valor de primera propiedad'),
            )
            second_properties = (
                {key: PROPERTIES[key]
                 for key in ('relative_humidity', 'humidity_ratio')}
                if mode == 'continuous' else PROPERTIES
            )
            self._group(
                self._select('air2_key', 'Segunda propiedad del aire',
                             second_properties, 'relative_humidity'),
                self._text('air2', 'Valor de segunda propiedad'),
            )
            self.input_controls.append(ft.Text(
                'Presión fija: 1 atm = 14.69595 psi. HR en %; humedad absoluta '
                'en lb agua/lb aire seco. Las temperaturas usan la unidad seleccionada.'))

        if mode in {'tray', 'extruded', 'rotary'}:
            mass_label = (
                'Flujo de sólido seco (lb/h)' if mode == 'rotary'
                else 'Masa de sólido húmedo (kg)'
            )
            self._group(self._text('mass', mass_label))
            self._group(
                self._text('initial', 'Humedad inicial (%)'),
                self._select('initial_basis', 'Base inicial',
                             {'wet': 'Base húmeda', 'dry': 'Base seca'}, 'wet'),
            )
            self._group(
                self._text('final', 'Humedad final / crítica (%)'),
                self._select('final_basis', 'Base final',
                             {'wet': 'Base húmeda', 'dry': 'Base seca'}, 'dry'),
            )
            velocity = self._text(
                'velocity',
                'Velocidad del gas (ft/h)' if mode == 'rotary'
                else 'Velocidad del aire',
            )
            if mode == 'rotary':
                self._group(velocity)
            else:
                self._group(
                    velocity,
                    self._select('velocity_unit', 'Unidad de velocidad',
                                 ['m/h', 'm/s', 'ft/h'], 'm/h'),
                )

        if mode in {'tray', 'extruded'}:
            self._group(
                self._text('area', 'Área de charola'),
                self._select('area_unit', 'Unidad del área de charola',
                             ['m2', 'cm2', 'in2', 'ft2'], 'm2'),
            )
            self._group(
                self._text('latent', 'Calor latente de vaporización a Tbh'),
                self._select('latent_unit', 'Unidad del calor latente',
                             ['Btu/lb', 'J/kg'], 'Btu/lb'),
            )

        if mode in {'geometry', 'extruded'}:
            self._select(
                'shape', 'Figura', {key: value[0] for key, value in SHAPES.items()},
                'cylinder', handler=self.change_shape,
            )
            self.change_shape(None, refresh=False)
            self.input_controls.append(self.geometry_section)

        if mode == 'extruded':
            self._group(
                self._text('height', 'Altura del lecho'),
                self._select('height_unit', 'Unidad de altura del lecho',
                             ['m', 'cm', 'in', 'ft'], 'm'),
            )
            self._group(
                self._text('porosity', 'Porosidad (%)'),
                self._text('viscosity', 'Viscosidad del aire (cP)', '0.02'),
            )

        if mode == 'continuous':
            self._group(self._text('outlet', 'Temperatura del aire de salida'))

        if mode == 'rotary':
            self._group(
                self._text('solid_inlet', 'Temperatura del sólido húmedo'),
                self._text('solid_outlet', 'Temperatura del sólido seco Tds'),
            )
            self._group(
                self._text('cp_solid', 'Cp sólido (Btu/(lb·°F))'),
                self._text('latent', 'Calor latente a Tbh (Btu/lb)'),
            )
            self._group(self._text('nt', 'Unidades de transferencia NT', '1.5'))
            self._group(
                self._text('cp_air', 'Cp aire (Btu/(lb·°F))', '0.242'),
                self._text('cp_vapor', 'Cp vapor (Btu/(lb·°F))', '0.447'),
            )
            self._group(self._text(
                'cp_liquid', 'Cp agua líquida (Btu/(lb·°F))', '1'))

    def change_shape(self, event, refresh=True):
        for key in self.geometry_keys:
            self.fields.pop(key, None)
        before = set(self.fields)
        controls = []
        shape = self.fields['shape'].value
        if shape == 'other':
            area_key = 'area' if self.mode == 'geometry' else 'particle_area'
            area_unit_key = (
                'area_unit' if self.mode == 'geometry' else 'particle_area_unit'
            )
            header_controls = [self.fields['shape']]
            self._set_group_columns(header_controls)
            self.geometry_header.controls = header_controls
            self._group(
                self._text(area_key, 'Área total de una partícula'),
                self._select(area_unit_key, 'Unidad de área de partícula',
                             ['m2', 'cm2', 'in2', 'ft2'], 'm2'),
                target=controls,
            )
            self._group(
                self._text('volume', 'Volumen de una partícula'),
                self._select('volume_unit', 'Unidad de volumen',
                             ['m3', 'cm3', 'in3', 'ft3'], 'm3'),
                target=controls,
            )
        else:
            length_unit = self._select(
                'length_unit', 'Unidad de dimensiones de la figura',
                ['m', 'cm', 'in', 'ft'], 'm',
            )
            header_controls = [self.fields['shape'], length_unit]
            self._set_group_columns(header_controls)
            self.geometry_header.controls = header_controls
            dimensions = [
                self._text(key, DIMENSION_LABELS[key])
                for key in geometry.DIMENSIONS[shape]
            ]
            for index in range(0, len(dimensions), 2):
                self._group(*dimensions[index:index + 2], target=controls)
        self.geometry_keys = list(set(self.fields) - before)
        self.geometry_controls.controls = controls
        self.image.src = SHAPES[shape][1]
        self.image.visible = shape != 'other'
        if refresh:
            self.invalidate(None)

    def invalidate(self, event):
        self.report = None
        self.result.controls = []
        self.error.value = ''
        self.air_preview.value = ''
        self.empty_state.visible = True
        self.update()

    def _data(self):
        return {key: control.value or '' for key, control in self.fields.items()}

    def preview_air(self, event):
        self.report = None
        self.result.controls = []
        self.air_preview.value = ''
        self.error.value = ''
        self.empty_state.visible = True
        try:
            data = self._data()
            state = input_air(data)
            outlet = outlet_temperature(state.dry_bulb_f, state.wet_bulb_f, number(data, 'nt'))
            unit = data['temperature_unit']
            low = units.convert(state.wet_bulb_f, 'F', unit)
            high = units.convert(outlet, 'F', unit)
            self.air_preview.value = (
                f'**Intervalo de Tds:** {format_value(low)} ≤ Tds ≤ {format_value(high)} {unit}.\n\n'
                f'Consulta el calor latente a Tbh = {format_value(low)} {unit}; no se estima automáticamente.\n\n'
                + '\n\n'.join(f'{name}: {format_value(value)} {unit}'
                               for name, value, unit in air_values(state)))
        except (ValueError, ArithmeticError) as error:
            self.error.value = str(error)
        self.update()

    def submit(self, event):
        self.report = None
        self.result.controls = []
        self.error.value = ''
        try:
            report = calculate(self.mode, self._data())
            self.result.controls = [self._table(['Magnitud', 'Valor', 'Unidad'],
                [[name, format_value(value), unit] for name, value, unit in report.values])]
            for headings, rows in report.tables:
                self.result.controls.append(self._table(headings,
                    [[format_value(value) for value in row] for row in rows]))
            self.result.controls.append(ft.Markdown(
                report.procedure,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                latex_scale_factor=1.05,
            ))
            self.report = report
            self.empty_state.visible = False
        except ValueError as error:
            message = str(error)
            for key, control in self.fields.items():
                if message.startswith(f'{key}:'):
                    message = message.replace(f'{key}:', f'{control.label}:', 1)
                    break
            self.error.value = message
        except ArithmeticError:
            self.error.value = 'Los valores exceden el rango numérico. Revisa magnitudes y unidades.'
        if self.report is None:
            self.empty_state.visible = True
        self.update()

    @staticmethod
    def _table(headings, rows):
        table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(heading, weight=ft.FontWeight.W_600)) for heading in headings],
            rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(str(value), selectable=True,
                    font_family='Consolas')) for value in row]) for row in rows],
            heading_row_color='#E2F5F7', column_spacing=20,
            divider_thickness=0.6, data_row_color='#FBFDFD')
        return ft.Row([table], scroll=ft.ScrollMode.AUTO)


class Workbench:
    def __init__(self, update):
        self.update = update
        self.navigation = ft.Dropdown(label='Cálculo', value='air', width=340,
            options=[ft.DropdownOption(key=key, text=label) for key, label in MODES.items()],
            on_select=self.change_mode, filled=True, fill_color='#193E52',
            color='white', border={
                ft.ControlState.DEFAULT: _input_border('#547184'),
                ft.ControlState.FOCUSED: _input_border(ACCENT, 2),
            })
        details = MODE_DETAILS['air']
        self.mode_eyebrow = _eyebrow(details['eyebrow'])
        self.mode_title = ft.Text(details['title'], size=30, color=INK,
                                  weight=ft.FontWeight.W_600, font_family='Bahnschrift')
        self.mode_description = ft.Text(details['description'], color=MUTED, size=15)
        self.process_line = ft.ResponsiveRow([
            _process_stage(ft.Icons.AIR, 'Aire', 'Estado psicrométrico'),
            _process_stage(ft.Icons.SCIENCE, 'Sólido', 'Humedad y geometría'),
            _process_stage(ft.Icons.THERMOSTAT, 'Secado', 'Balance y dimensión'),
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        self.header = ft.Container(
            content=ft.ResponsiveRow([
                ft.Column([
                    _eyebrow('INGENIERÍA QUÍMICA · SISTEMA INGLÉS / SI', '#7EE2E8'),
                    ft.Text('SECADO', size=42, color='white',
                            weight=ft.FontWeight.W_700, font_family='Bahnschrift'),
                    ft.Text('Del estado del aire al dimensionamiento del equipo.',
                            color='#B9CDD5', size=15),
                ], col={'xs': 12, 'md': 5}, spacing=4),
                ft.Container(self.process_line, col={'xs': 12, 'md': 7},
                             padding=10, bgcolor='#0D2635', border_radius=10),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=INK, padding=24, border_radius=16,
        )
        self.sidebar = ft.Container(
            content=ft.Column([
                _eyebrow('MÓDULO DE CÁLCULO', '#7EE2E8'),
                ft.Text('Selecciona el problema', color='white', size=20,
                        weight=ft.FontWeight.W_600, font_family='Bahnschrift'),
                self.navigation,
                ft.Divider(color='#34566A', height=24),
                _eyebrow('CONDICIONES BASE', '#7EE2E8'),
                ft.Row([ft.Icon(ft.Icons.AIR, color=ACCENT, size=18),
                        ft.Text('Aire a 1 atm', color='white', size=13)]),
                ft.Row([ft.Icon(ft.Icons.THERMOSTAT, color=HEAT, size=18),
                        ft.Text('Psicrometría en IP', color='white', size=13)]),
                ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color='#7EE2E8', size=18),
                        ft.Text('Unidades explícitas', color='white', size=13)]),
            ], spacing=14),
            col={'xs': 12, 'lg': 3}, bgcolor=INK, padding=20, border_radius=12,
        )
        self.form = CalculatorForm('air', update)
        self.content = ft.Column([self.form.control])
        self.workspace = ft.Column([
            self.mode_eyebrow,
            self.mode_title,
            self.mode_description,
            ft.Container(height=4, width=72, bgcolor=HEAT, border_radius=2),
            self.content,
        ], col={'xs': 12, 'lg': 9}, spacing=8)
        self.control = ft.Column([
            self.header,
            ft.ResponsiveRow([self.sidebar, self.workspace], spacing=20, run_spacing=20),
        ], spacing=20)

    def change_mode(self, event):
        self.form = CalculatorForm(self.navigation.value, self.update)
        self.content.controls = [self.form.control]
        details = MODE_DETAILS[self.navigation.value]
        self.mode_eyebrow.value = details['eyebrow']
        self.mode_title.value = details['title']
        self.mode_description.value = details['description']
        self.update()


def main(page: ft.Page):
    page.title = 'SECADO · Ingeniería química'
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ACCENT, font_family='Segoe UI')
    page.bgcolor = BACKGROUND
    page.padding = 20
    page.window.width = 1000
    page.window.height = 800
    page.scroll = ft.ScrollMode.AUTO
    page.add(Workbench(page.update).control)


def run():
    ft.run(main, assets_dir=str(ASSETS_DIR))
