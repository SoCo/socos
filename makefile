
lint:
	flake8 runner.py socos/*.py
	pylint runner.py socos/*.py


.PHONY: lint
