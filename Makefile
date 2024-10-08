CONTRIB_TARGETS = $(subst contrib/,contrib-,$(wildcard contrib/*))
EXAMPLE_TARGETS = $(subst examples/,example-,$(wildcard examples/*))

default: build

docs:
	cd docs && make html

watch-docs:
	sphinx-autobuild docs/source docs/build/html

clean-docs:
	rm -rf ./docs/build

sync-jumpstarter:
	uv sync --all-extras --inexact

test-jumpstarter:
	uv run --isolated --package jumpstarter pytest jumpstarter tests

sync-contrib-%: contrib/%
	uv sync --all-extras --inexact --package jumpstarter_driver_$(<F)

test-contrib-%: contrib/%
	uv run --isolated --package jumpstarter_driver_$(<F) pytest $<

sync-contrib: $(addprefix sync-,$(CONTRIB_TARGETS))

test-contrib: $(addprefix test-,$(CONTRIB_TARGETS))

sync-example-%: examples/%
	uv sync --all-extras --inexact --package jumpstarter_example_$(<F)

sync-examples: $(addprefix sync-,$(EXAMPLE_TARGETS))

clean-venv:
	-rm -rf ./.venv
	-find . -type d -name __pycache__ -exec rm -r {} \+

clean-build:
	-rm -rf dist

clean-test:
	-rm .coverage
	-rm coverage.xml
	-rm -rf htmlcov

sync: sync-jumpstarter sync-contrib sync-examples

test: test-jumpstarter test-contrib

build:
	uv build --all --out-dir dist

clean: clean-docs clean-venv clean-build clean-test

.PHONY: sync docs test test-jumpstarter test-contrib build clean-test clean-docs clean-venv clean-build
