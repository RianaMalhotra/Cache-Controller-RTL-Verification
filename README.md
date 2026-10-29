# CacheForge

**A 2-way set-associative cache controller design and verification project.**

CacheForge is built incrementally in synthesizable SystemVerilog with Python/cocotb verification and Verilator simulation. No physical hardware is required.

## Target architecture

- 16-bit byte addresses, 8 sets, 2 ways, 4-byte cache lines (64-byte data capacity)
- Write-back, write-allocate cache
- Per-set true LRU replacement
- Blocking cache controller with refill/write-back sequencing

## Current status

**Milestones 1–3 — tag lookup, 2-way cache storage arrays, and standalone LRU replacement.** The storage module provides per-set tags, data, valid and dirty bits, synchronous line writes, and combinational lookup. The standalone LRU module selects invalid ways first and otherwise evicts the least recently used way. Integration into a full controller and memory refill/write-back are **not yet implemented**.

## Run locally

Install Python, make and Verilator, then:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make
make TOPLEVEL=cache_arrays
make TOPLEVEL=cache_lru
```

See [architecture and roadmap](docs/architecture.md).

## Planned verification

Directed and randomized cocotb tests, a Python reference model, scoreboards, corner cases and GitHub Actions CI.
