# CacheForge

**A 2-way set-associative cache controller design and verification project.**

CacheForge is built incrementally in synthesizable SystemVerilog with Python/cocotb verification and Verilator simulation. No physical hardware is required.

## Target architecture

- 16-bit byte addresses, 8 sets, 2 ways, 4-byte cache lines (64-byte data capacity)
- Write-back, write-allocate cache
- Per-set true LRU replacement
- Blocking cache controller with refill/write-back sequencing

## Current status

**Milestones 1–4 — tag lookup, cache arrays, LRU, and blocking write-back/refill controller.** The storage module provides per-set tags, data, valid and dirty bits, synchronous line writes, and combinational lookup. The standalone LRU module selects invalid ways first and otherwise evicts the least recently used way. A blocking cache controller now integrates the arrays and LRU, with a simple request/response backing-memory interface. This milestone is committed but its integration test is **not yet validated**.

## Run locally

Install Python, make and Verilator, then:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make
make TOPLEVEL=cache_arrays
make TOPLEVEL=cache_lru
make TOPLEVEL=cache_controller
```

See [architecture and roadmap](docs/architecture.md).

## Planned verification

Directed and randomized cocotb tests, a Python reference model, scoreboards, corner cases and GitHub Actions CI.
