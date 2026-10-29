# CacheForge

**A two-way set-associative, write-back cache controller in SystemVerilog, verified with cocotb and Verilator.**

[![RTL Simulation and Verification](https://github.com/RianaMalhotra/CacheForge/actions/workflows/verification.yml/badge.svg)](https://github.com/RianaMalhotra/CacheForge/actions/workflows/verification.yml)

CacheForge is a simulation-only RTL and design verification project; no FPGA or physical hardware is required.

## Architecture

| Property | Configuration |
| --- | --- |
| Address width | 16 bits (byte-addressed) |
| Data / cache line | 32 bits / 4 bytes |
| Sets / ways | 8 sets / 2 ways |
| Data capacity | 64 bytes |
| Address decomposition | 11-bit tag, 3-bit set, 2-bit byte offset |
| Replacement | True per-set LRU, invalid-way priority |
| Write policy | Write-back, write-allocate |
| Controller | Blocking FSM, one outstanding CPU request |

The cache controller uses a simple request/response memory interface (not AXI). Requests are word-aligned in the current tests; byte-enable and subword operations are not implemented.

## RTL modules

- `rtl/cache_lookup.sv`: combinational tag lookup (standalone milestone).
- `rtl/cache_arrays.sv`: two-way tags, data, valid/dirty metadata.
- `rtl/cache_lru.sv`: per-set replacement state.
- `rtl/cache_controller.sv`: request handling, dirty eviction, refill and write-allocate FSM.

## Run locally (Ubuntu / WSL)

Prerequisites: Python 3.11 or 3.12, Verilator, make, C++ compiler and Git.

```bash
sudo apt update
sudo apt install -y verilator make g++ python3 python3-venv python3-pip
git clone https://github.com/RianaMalhotra/CacheForge.git
cd CacheForge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run each suite with a clean build directory:

```bash
make clean && make TOPLEVEL=cache_lookup
make clean && make TOPLEVEL=cache_arrays
make clean && make TOPLEVEL=cache_lru
make clean && make TOPLEVEL=cache_controller
make clean && make MODULE=test_cache_randomized
```

The test suite uses cocotb 1.9.2 for compatibility with the currently used Verilator 5.032. The last command selects `cache_controller` as the RTL top level and `test_cache_randomized` as the test module.

## Verification

- Directed tests for tag hits/misses, storage metadata, LRU behavior and controller read/write/eviction behavior.
- Deterministic randomized test with **400 operations**, an independent Python memory scoreboard, and a final address sweep.
- Read-refill and dirty write-back events are counted in the randomized test.
- GitHub Actions runs all five suites on pushes to `main` and pull requests.

The controller and randomized suites passed in local user-run simulations. GitHub Actions status should be checked separately; a passing test suite does not establish exhaustive correctness.

See [architecture details](docs/architecture.md).
