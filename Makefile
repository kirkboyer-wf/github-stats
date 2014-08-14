SHELL := /bin/bash
PYTHON := python
PIP := pip
LINK_LIBS := link_libs

LINK_LIBS_DIR := lib
BUILD_DIR := .build

all: deps link_libs

clean:
	find . -name "*.py[co]" -delete

distclean: clean
	rm -rf $(BUILD_DIR)
	rm -rf $(LIBS_DIR)

run: deps link_libs
	dev_appserver.py .

test: clean integrations

deps: py_dev_deps py_deploy_deps 

bootstrap-gae:
	./bootstrap-gae.sh

link_libs: bootstrap-gae $(BUILD_DIR)/link_libs.out

py_deploy_deps: $(BUILD_DIR)/pip-deploy.out

py_dev_deps: $(BUILD_DIR)/pip-dev.out

$(BUILD_DIR)/pip-deploy.out: requirements.txt
	@mkdir -p $(BUILD_DIR)
	$(PIP) install -Ur $< && touch $@

$(BUILD_DIR)/pip-dev.out: requirements_dev.txt
	@mkdir -p $(BUILD_DIR)
	$(PIP) install -Ur $< && touch $@

$(BUILD_DIR)/link_libs.out: requirements.txt $(BUILD_DIR)/pip-dev.out
	@mkdir -p $(BUILD_DIR)
	$(LINK_LIBS) -d lib -r $< && touch $@

unit:
	nosetests
