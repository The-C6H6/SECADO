import runpy
from pathlib import Path

import pytest

import secado_app_1er_parcial


@pytest.mark.parametrize('relative_path', ['main.py', 'src/secado_app_1er_parcial/__main__.py'])
def test_flet_can_execute_entrypoint_as_script(monkeypatch, relative_path):
    calls = []
    monkeypatch.setattr(secado_app_1er_parcial, 'main', lambda: calls.append(True))
    root = Path(__file__).resolve().parents[1]
    runpy.run_path(str(root / relative_path), run_name='__main__')
    assert calls == [True]
