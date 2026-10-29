# CacheForge
### SystemVerilog Cache Controller · Cocotb Verification · Verilator

[![RTL Simulation and Verification](https://github.com/RianaMalhotra/CacheForge/actions/workflows/verification.yml/badge.svg)](https://github.com/RianaMalhotra/CacheForge/actions/workflows/verification.yml)

**CacheForge is a simulation-based, two-way set-associative cache controller implementing write-back, write-allocate, and per-set LRU replacement.** The project combines synthesizable SystemVerilog RTL with Python/cocotb directed tests, a deterministic randomized scoreboard, and automated regression testing.

> **In 30 seconds:** A CPU issues a read or write. CacheForge checks the tag and valid bits, serves hits locally, and handles misses by choosing a victim, writing it back if dirty, fetching a replacement word, and responding to the CPU. A Python reference model checks that reads return the latest architecturally written values—even when backing memory has not yet received a dirty line.

## At a glance

| Design | Verification |
| --- | --- |
| 2-way, 8-set cache; 64 bytes of data storage | Directed tests for lookup, arrays, LRU and integrated controller |
| 16-bit addresses; 32-bit words | 400 seeded randomized read/write operations |
| Per-line valid and dirty metadata | Independent architectural-memory scoreboard |
| Per-set true LRU; invalid-way priority | Final readback sweep across 48 test addresses |
| Blocking write-back / write-allocate FSM | GitHub Actions runs five cocotb suites |

**Scope:** A focused educational RTL design using a custom request/response memory interface. It is not an AXI cache, does not support subword accesses, and has not been validated on hardware.

## System overview

```text
  CPU request: valid, read/write, address, write data
                          |
                          v
                +------------------+
                | Cache controller |
                |  blocking FSM    |
                +----+--------+----+
                     |        |
           tag/data  |        | victim / access
                     v        v
             +-------------+  +-------------+
             | Cache arrays|  | Per-set LRU |
             | 8 sets x 2  |  | replacement |
             | tags/data   |  +-------------+
             | valid/dirty |
             +-------------+
                     |
                     v
         Backing-memory request/response
         (write-back or refill on miss)
```

For state transitions, interface timing, and design tradeoffs, see **[Architecture & design decisions](docs/architecture.md)**.

## Key design decisions

**Why two ways?** Two-way associativity exposes realistic conflict-miss and victim-selection behavior while keeping the RTL and reference model small enough to inspect carefully.

**Why write-back and write-allocate?** Stores can update cached data and mark a line dirty; backing memory is updated only when that line is evicted. This makes eviction ordering and data integrity meaningful verification targets.

**Why a blocking FSM?** One outstanding CPU transaction makes request/response ordering explicit and avoids conflating cache policy correctness with pipelined bus arbitration.

**Why an independent scoreboard?** A cache can return correct values even while its backing memory is intentionally stale. The scoreboard therefore tracks the latest logical value separately from the simulated backing-memory image.

## Verification approach

| Testbench | What it exercises |
| --- | --- |
| [`test_cache_lookup.py`](tests/test_cache_lookup.py) | Tag hit/miss and invalid-line behavior |
| [`test_cache_arrays.py`](tests/test_cache_arrays.py) | Tag/data storage and valid/dirty metadata |
| [`test_cache_lru.py`](tests/test_cache_lru.py) | Victim selection and per-set isolation |
| [`test_cache_controller.py`](tests/test_cache_controller.py) | Integrated read/write, refill, LRU and dirty eviction |
| [`test_cache_randomized.py`](tests/test_cache_randomized.py) | 400 seeded operations, reference-memory comparison and final sweep |

The randomized test uses seed `0xCAFE2026`, 48 word-aligned addresses spanning eight sets and six tags, and a mix of reads and writes. It asserts that refills and dirty write-backs occur. The seed is reproducible for debugging.

**Validation:** Directed controller and randomized scoreboard simulations passed locally; the GitHub Actions workflow was also confirmed passing. These tests are meaningful regression evidence, **not** exhaustive coverage, a formal proof, or a performance benchmark.

Read the [verification walkthrough](docs/verification.md) for the reference-model approach, test stimulus, and what remains untested.

## Run it yourself

Ubuntu or Windows Subsystem for Linux (WSL) recommended. Requires Git, Python 3 with `venv`, make, a C++ compiler and Verilator.

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip make g++ verilator
git clone https://github.com/RianaMalhotra/CacheForge.git
cd CacheForge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the complete regression locally:

```bash
make clean && make TOPLEVEL=cache_lookup
make clean && make TOPLEVEL=cache_arrays
make clean && make TOPLEVEL=cache_lru
make clean && make TOPLEVEL=cache_controller
make clean && make MODULE=test_cache_randomized
```

Each suite uses a different RTL top level or test module; `make clean` prevents reuse of an incompatible Verilator build. The project pins cocotb 1.9.2, which has been used successfully with Verilator 5.032. CI installs dependencies in an isolated virtual environment and runs the same five suites.

## Repository map

```text
rtl/
  cache_lookup.sv        Standalone tag-lookup building block
  cache_arrays.sv        Data/tag arrays and valid/dirty metadata
  cache_lru.sv           Two-way replacement policy
  cache_controller.sv    Blocking miss/eviction/refill FSM
tests/
  test_cache_*.py        Cocotb directed and randomized testbenches
docs/
  architecture.md        RTL structure, interfaces, FSM, tradeoffs
  verification.md        Scoreboard, scenarios, limitations
.github/workflows/
  verification.yml       Automated five-suite regression
Makefile                 Simulation target selection
requirements.txt         Python test dependencies
```

## What I would improve next

The highest-value extensions are **memory backpressure and variable response latency**, explicit functional coverage and assertions, multiple randomized seeds, and waveform capture for failing regressions. The current controller deliberately omits byte enables, cache coherence, flush/invalidate, multiple outstanding requests, and standard bus protocols.

---

**Interview discussion starters:** How does dirty eviction preserve the latest data? Why does the reference model differ from backing memory? When does LRU update? What happens if a refill response arrives too early? How would the FSM change to support backpressure or multiple outstanding misses?
