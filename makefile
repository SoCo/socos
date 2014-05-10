
lint:
	flake8 bin/socos socos/*.py
	pylint bin/socos socos/*.py


.PHONY: lint
