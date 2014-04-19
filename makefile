
lint: socos.py
	flake8 socos.py
	pylint socos.py

.PHONY: lint
