.PHONY: test test-full test-fast lint lint-fix coverage clean install

test:
	python -m pytest -q --no-header -m "not slow" --ignore=tests/test_zzz_api_boot.py -x

test-full:
	python -m pytest -q --no-header -m "not slow" --ignore=tests/test_zzz_api_boot.py && \
	python -m pytest -q --no-header tests/test_zzz_api_boot.py tests/test_stress.py

test-fast:
	python -m pytest -q --no-header -m "not slow" -x --ignore=tests/test_zzz_api_boot.py --ignore=tests/test_stress.py -k "not stress"

lint:
	ruff check .

lint-fix:
	ruff check --fix .

coverage:
	python -m pytest -q --no-header -m "not slow" --ignore=tests/test_zzz_api_boot.py \
		--cov --cov-report=term-missing --cov-report=html

install:
	pip install -e ".[dev]"

clean:
	rm -rf .coverage htmlcov/ .pytest_cache/ __pycache__/
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
