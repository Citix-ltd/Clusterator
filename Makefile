.PHONY: *
run:
	python3 server/server.py

flake8:
	python3 -m flake8 server/
mypy:
	python3 -m mypy server/
lint: flake8 mypy

unittest:
	python3 -m pytest -q server/test
test: unittest