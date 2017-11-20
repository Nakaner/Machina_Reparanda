all: lint tests

lint: machina_reparanda/*.py implementations/*.py tests/*.py
	flake8 . | grep -v "line too long"

tests: machina_reparanda/*.py implementations/*.py tests/*.py
	python3 -m unittest
