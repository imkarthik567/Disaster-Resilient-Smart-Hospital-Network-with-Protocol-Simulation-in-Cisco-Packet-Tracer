# ==============================================================================
# Makefile: Disaster-Resilient Smart Hospital Network
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# VIT Vellore — SCOPE Computer Networks Project
# ==============================================================================

PYTHON ?= python

.PHONY: all addressing lint bench charts docs test help

all: addressing lint bench docs

help:
	@echo "Available make targets:"
	@echo "  make addressing   - Calculate VLSM and regenerate CSV/Markdown tables"
	@echo "  make lint         - Audit all device configurations using config_linter.py"
	@echo "  make bench        - Run GBN vs SR benchmark loss sweep harness"
	@echo "  make charts       - Generate protocol comparison charts"
	@echo "  make docs         - Regenerate addressing and topology documentation"
	@echo "  make test         - Run pytest unit tests on protocol algorithms"
	@echo "  make all          - Run addressing, lint, bench, and docs targets"

addressing:
	$(PYTHON) addressing/vlsm_calculator.py

lint:
	$(PYTHON) verification/config_linter.py

bench:
	$(PYTHON) sim/benchmark_harness.py

charts:
	$(PYTHON) sim/benchmark_harness.py

docs: addressing
	$(PYTHON) topology/pt_builder.py

test:
	$(PYTHON) -m pytest sim/test_protocols.py
