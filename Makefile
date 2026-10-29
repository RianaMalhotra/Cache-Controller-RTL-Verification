SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/rtl/cache_lookup.sv
TOPLEVEL = cache_lookup
MODULE = test_cache_lookup
include $(shell cocotb-config --makefiles)/Makefile.sim
