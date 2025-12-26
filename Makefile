#!make

include .env.local

VERSION = develop
SPARK_VERSION ?= 3.5
PYDANTIC_VERSION ?= 2
VIRTUAL_ENV ?= .venv
PYTHON = ${VIRTUAL_ENV}/bin/python
PIP = ${VIRTUAL_ENV}/bin/pip
UV ?= ${VIRTUAL_ENV}/bin/uv
PYTEST = ${VIRTUAL_ENV}/bin/pytest
COVERAGE = ${VIRTUAL_ENV}/bin/coverage

# Fix docker build and docker compose build using different backends
COMPOSE_DOCKER_CLI_BUILD = 1
DOCKER_BUILDKIT = 1
# Fix docker build on M1/M2
DOCKER_DEFAULT_PLATFORM = linux/amd64

HELP_FUN = \
	%help; while(<>){push@{$$help{$$2//'options'}},[$$1,$$3] \
	if/^([\w-_]+)\s*:.*\#\#(?:@(\w+))?\s(.*)$$/}; \
    print"$$_:\n", map"  $$_->[0]".(" "x(20-length($$_->[0])))."$$_->[1]\n",\
    @{$$help{$$_}},"\n" for keys %help; \

all: help

help: ##@Help Show this help
	@echo -e "Usage: make [target] ...\n"
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)



venv: venv-cleanup venv-install##@Env Init venv and install uv dependencies

venv-cleanup: ##@Env Cleanup venv
	@rm -rf ${VIRTUAL_ENV} || true
	python3 -m venv ${VIRTUAL_ENV}
	${PIP} install uv

venv-install: ##@Env Install requirements to venv
	${UV} sync \
		--inexact \
		--no-install-project \
		--all-extras \
		--group dev \
		--group docs \
		--group test \
		--group test-clickhouse \
		--group test-mongodb \
		--group test-mssql \
		--group test-mysql \
		--group test-oracle \
		--group test-postgres \
		--group test-pydantic-${PYDANTIC_VERSION} \
		--group test-spark-${SPARK_VERSION} \
		$(ARGS)

	${UV} pip install --no-deps sphinx-plantuml


.PHONY: docs

docs: docs-build docs-open ##@Docs Generate & open docs

docs-build: ##@Docs Generate docs
	$(MAKE) -C docs html

docs-open: ##@Docs Open docs
	xdg-open docs/_build/html/index.html

docs-cleanup: ##@Docs Cleanup docs
	$(MAKE) -C docs clean

docs-fresh: docs-cleanup docs-build ##@Docs Cleanup & build docs
