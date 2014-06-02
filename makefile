all: lint test

lint:
	flake8 test.py socos/*.py
	pylint test.py socos/*.py
	rstcheck README.rst

test:
	python test.py

.PHONY: all lint test
