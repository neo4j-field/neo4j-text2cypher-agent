.PHONY: all format lint test help

# Default target executed when no arguments are given to make.
all: help

######################
# SET UP
######################

init:
	poetry install --with dev,ui

######################
# TESTING
######################

test:
	poetry run pytest tests

test_unit:
	poetry run pytest tests/unit -s

######################
# LINTING AND FORMATTING
######################

format:
	poetry run ruff format
	poetry run ruff check --select I . --fix
	poetry run ruff check .

clean:
	poetry run ruff check --select I . --fix
	poetry run ruff check . --fix

######################
# MYPY CHECK
######################

mypy:
	poetry run mypy .

######################
# STREAMLIT APP
######################

streamlit:
	poetry run streamlit run neo4j_text2cypher/ui/streamlit_app.py $(file_path)

######################
# LANGGRAPH STUDIO
######################

langgraph:
	langgraph dev

######################
# HELP
######################

help:
	@echo '----'
	@echo 'init........................ - initialize the repo for development'
	@echo 'format...................... - run code formatters'
	@echo 'test........................ - run all tests'
	@echo 'test_unit................... - run unit tests'
	@echo 'streamlit................... - run streamlit app: make streamlit file_path=example_apps/iqs_data_explorer/app-config.yml'
	@echo 'langgraph................... - start LangGraph Studio development server'
	@echo 'mypy........................ - run type checking'