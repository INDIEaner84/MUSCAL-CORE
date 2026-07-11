import os
import sys


def test_flask_import():
    import flask
    _ = flask.__version__


def test_fastapi_import():
    import fastapi
    _ = fastapi.__version__


def test_create_app():
    sys.argv = ['test_api_boot.py', '--test']
    os.environ.setdefault("MUSCAL_ENV", "test")
    from runtime.api import create_app
    app = create_app()
    assert app is not None


def test_routes_registered():
    from runtime.api import create_app
    app = create_app()
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert len(rules) > 0
    assert any("/health" in r for r in rules)
