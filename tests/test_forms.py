import pytest
import flet as ft

from secado_app_1er_parcial.ui.app import (
    ACCENT,
    FIELD_BACKGROUND,
    CalculatorForm,
    Workbench,
)
from secado_app_1er_parcial.ui.fields import MODE_DETAILS, MODES


def semantic_groups(form):
    controls_to_keys = {id(control): key for key, control in form.fields.items()}
    return [
        tuple(controls_to_keys[id(control)] for control in group.controls)
        for group in form.input_controls
        if isinstance(group, ft.ResponsiveRow)
        and group.controls
        and all(id(control) in controls_to_keys for control in group.controls)
    ]


def test_every_mode_has_specific_interface_copy():
    assert MODE_DETAILS.keys() == MODES.keys()
    for mode, details in MODE_DETAILS.items():
        assert details['eyebrow']
        assert details['title'] == MODES[mode]
        assert details['description']


@pytest.mark.parametrize('mode,expected_groups', [
    ('air', [
        ('temperature_unit',), ('air1_key', 'air1'), ('air2_key', 'air2'),
    ]),
    ('conversion', [('value', 'source', 'target')]),
    ('tray', [
        ('temperature_unit',), ('air1_key', 'air1'), ('air2_key', 'air2'),
        ('mass',), ('initial', 'initial_basis'), ('final', 'final_basis'),
        ('velocity', 'velocity_unit'), ('area', 'area_unit'), ('latent', 'latent_unit'),
    ]),
    ('continuous', [
        ('temperature_unit',), ('air1_key', 'air1'), ('air2_key', 'air2'), ('outlet',),
    ]),
    ('rotary', [
        ('temperature_unit',), ('air1_key', 'air1'), ('air2_key', 'air2'),
        ('mass',), ('initial', 'initial_basis'), ('final', 'final_basis'), ('velocity',),
        ('solid_inlet', 'solid_outlet'), ('cp_solid', 'latent'), ('nt',),
        ('cp_air', 'cp_vapor'), ('cp_liquid',),
    ]),
])
def test_forms_declare_semantic_groups_in_reading_order(mode, expected_groups):
    form = CalculatorForm(mode, lambda: None)
    assert semantic_groups(form) == expected_groups


def test_group_columns_stack_in_narrow_views_and_share_rows_when_space_allows():
    form = CalculatorForm('conversion', lambda: None)
    group = form.input_controls[0]
    assert isinstance(group, ft.ResponsiveRow)
    assert [control.col for control in group.controls] == [
        {'xs': 12, 'md': 4}, {'xs': 12, 'md': 4}, {'xs': 12, 'md': 4},
    ]
    assert all(control.expand is True for control in group.controls)


def test_extruded_geometry_and_bed_controls_remain_in_semantic_groups():
    form = CalculatorForm('extruded', lambda: None)
    controls_to_keys = {id(control): key for key, control in form.fields.items()}
    assert tuple(controls_to_keys[id(control)] for control in form.geometry_header.controls) == (
        'shape', 'length_unit',
    )
    assert [
        tuple(controls_to_keys[id(control)] for control in group.controls)
        for group in form.geometry_controls.controls
    ] == [('r', 'h')]
    groups = semantic_groups(form)
    assert ('height', 'height_unit') in groups
    assert ('porosity', 'viscosity') in groups
    height_group = next(
        group for group in form.input_controls
        if isinstance(group, ft.ResponsiveRow)
        and form.fields['height'] in group.controls
    )
    assert form.input_controls.index(height_group) > form.input_controls.index(
        form.geometry_section)


def test_reorganization_preserves_field_keys_and_data_mapping():
    form = CalculatorForm('tray', lambda: None)
    expected_keys = {
        'temperature_unit', 'air1_key', 'air1', 'air2_key', 'air2', 'mass',
        'initial', 'initial_basis', 'final', 'final_basis', 'velocity',
        'velocity_unit', 'area', 'area_unit', 'latent', 'latent_unit',
    }
    assert set(form.fields) == expected_keys
    for index, control in enumerate(form.fields.values()):
        control.value = f'value-{index}'
    assert form._data() == {
        key: control.value for key, control in form.fields.items()
    }


def test_continuous_form_calculates_and_clears_stale_results_on_error():
    updates = []
    form = CalculatorForm('continuous', lambda: updates.append(True))
    for key, value in {'air1': '140', 'air2': '10', 'outlet': '120'}.items():
        form.fields[key].value = value
    form.submit(None)
    assert form.report is not None
    assert form.report.tables
    assert form.error.value == ''
    assert form.empty_state.visible is False
    form.fields['air1'].value = 'no es un número'
    form.submit(None)
    assert form.report is None
    assert form.result.controls == []
    assert 'número' in form.error.value
    assert form.empty_state.visible is True
    assert len(updates) == 2


def test_tray_form_displays_seconds_and_hours_with_confirmed_units():
    form = CalculatorForm('tray', lambda: None)
    for key, value in {'air1': '140', 'air2': '10', 'mass': '100',
                       'initial': '20', 'final': '10', 'velocity': '3600',
                       'area': '1', 'latent': '1000'}.items():
        form.fields[key].value = value
    form.submit(None)
    assert form.error.value == ''
    assert form.report is not None
    assert ('Tiempo crítico', 's') in {(label, unit) for label, value, unit in form.report.values}
    assert ('Tiempo crítico', 'h') in {(label, unit) for label, value, unit in form.report.values}
    markdown = form.result.controls[-1]
    assert markdown.extension_set == pytest.importorskip('flet').MarkdownExtensionSet.GITHUB_WEB
    assert '$$' in markdown.value


def test_result_table_limits_display_to_five_decimals_without_changing_report_value():
    form = CalculatorForm('air', lambda: None)
    form.fields['air1'].value = '170'
    form.fields['air2'].value = '10'
    form.submit(None)
    wet_bulb = next(value for label, value, unit in form.report.values
                    if label == 'Bulbo húmedo')
    table = form.result.controls[0].controls[0]
    displayed = next(row.cells[1].content.value for row in table.rows
                     if row.cells[0].content.value == 'Bulbo húmedo')
    assert wet_bulb == pytest.approx(100.28284807093631)
    assert displayed == '100.28285'


def test_geometry_selector_rebuilds_dimensions_and_image():
    form = CalculatorForm('geometry', lambda: None)
    form.fields['shape'].value = 'cylinder'
    form.change_shape(None)
    assert 'r' in form.fields and 'h' in form.fields
    assert form.image.src.endswith('CILINDRO.png')
    form.fields['shape'].value = 'other'
    form.change_shape(None)
    assert 'r' not in form.fields
    assert 'area' in form.fields and 'volume' in form.fields
    assert form.image.visible is False


def test_triangular_prism_form_only_requests_side_and_length():
    form = CalculatorForm('geometry', lambda: None)
    form.fields['shape'].value = 'triangular_prism'
    form.change_shape(None)
    assert {'a', 'length'} <= form.fields.keys()
    assert {'b', 'c', 'ht'}.isdisjoint(form.fields)


@pytest.mark.parametrize('mode', ['air', 'conversion', 'geometry', 'tray',
                                  'extruded', 'continuous', 'rotary'])
def test_forms_handle_empty_input_without_crashing(mode):
    form = CalculatorForm(mode, lambda: None)
    form.submit(None)
    assert form.error.value
    assert form.report is None


def test_navigation_switches_forms():
    workbench = Workbench(lambda: None)
    workbench.navigation.value = 'geometry'
    workbench.change_mode(None)
    assert workbench.form.mode == 'geometry'
    assert workbench.mode_title.value == 'Geometría'


def test_interface_has_instrument_layout_and_filled_fields():
    workbench = Workbench(lambda: None)
    assert workbench.header.bgcolor
    assert workbench.sidebar.bgcolor
    assert len(workbench.process_line.controls) == 3
    assert workbench.form.input_panel.col == {'xs': 12, 'lg': 5}
    assert workbench.form.result_panel.col == {'xs': 12, 'lg': 7}
    first_field = workbench.form.fields['temperature_unit']
    assert first_field.filled is True
    assert first_field.fill_color == FIELD_BACKGROUND
    assert workbench.form.calculate_button.bgcolor == ACCENT
