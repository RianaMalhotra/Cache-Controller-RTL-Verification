export PYTHONPATH := $(PWD)/tests:$(PYTHONPATH)
SIM ?= verilator
TOPLEVEL_LANG = verilog
MODULE ?= test_cache_lookup
TOPLEVEL ?= cache_lookup

ifeq ($(TOPLEVEL),cache_arrays)
VERILOG_SOURCES = $(PWD)/rtl/cache_arrays.sv
MODULE = test_cache_arrays
else ifeq ($(TOPLEVEL),cache_controller)
VERILOG_SOURCES = $(PWD)/rtl/cache_arrays.sv $(PWD)/rtl/cache_lru.sv $(PWD)/rtl/cache_controller.sv
MODULE = test_cache_controller
else ifeq ($(TOPLEVEL),cache_lru)
VERILOG_SOURCES = $(PWD)/rtl/cache_lru.sv
MODULE = test_cache_lru
else
VERILOG_SOURCES = $(PWD)/rtl/cache_lookup.sv
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
