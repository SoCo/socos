all: lint test

lint:
	flake8 test.py socos/*.py
	pylint test.py socos/*.py

test:
	python test.py

.PHONY: all lint test
