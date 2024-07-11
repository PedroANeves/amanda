VENV = venv
BIN=$(VENV)/bin

.PHONY: help
help: # Show this help.
	@egrep -h '\s#\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?# "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: all
all: test # Runs full tests

$(VENV): requirements-dev.txt # Creates/updates a venv.
	python -m venv $(VENV)
	$(BIN)/pip install --upgrade -r requirements-dev.txt
	touch $(VENV)

###############################################################################
# test
###############################################################################
.PHONY: test
test: format sort lint typing unittest # Runs full tests suites.
	$(BIN)/pytest --reverse tests/

.PHONY: lint
lint: $(VENV) # using flake8.
	$(BIN)/flake8 src/ tests/

.PHONY: format
format: $(VENV) # using black.
	$(BIN)/black src/ tests/

.PHONY: sort
sort: $(VENV) # using isort.
	$(BIN)/isort src/ tests/

.PHONY: typing
typing: $(VENV) # using mypy.
	$(BIN)/mypy src/

.PHONY: unittest
unittest: $(VENV) # pytest.
	$(BIN)/pytest tests/

###############################################################################
# build
###############################################################################
.PHONY: clean
clean: # remove caches and other generated temp files.
	rm -rf $(VENV)
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
	find . -type f -name db.sqlite3 -delete
	find . -type d -name .mypy_cache -exec rm -r {} +
	find . -type d -name .pytest_cache -exec rm -r {} +
	find . -type d -name htmlcov -exec rm -r {} +
	find . -type d -name dist -exec rm -r {} +

