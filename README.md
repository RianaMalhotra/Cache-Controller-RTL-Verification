# CacheForge

**A 2-way set-associative cache controller design and verification project.**

CacheForge is built incrementally in synthesizable SystemVerilog with Python/cocotb verification and Verilator simulation. No physical hardware is required.

## Target architecture

- 16-bit byte addresses, 8 sets, 2 ways, 4-byte cache lines (64-byte data capacity)
- Write-back, write-allocate cache
- Per-set true LRU replacement
- Blocking cache controller with refill/write-back sequencing

## Current status

**Milestone 1 — tag lookup RTL and basic cocotb tests.** The current module checks whether a supplied pair of tags/valid bits contains a matching address tag. Full cache behavior is planned, **not yet implemented**.

## Run locally

Install Python, make and Verilator, then:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make
```

See [architecture and roadmap](docs/architecture.md).

## Planned verification

Directed and randomized cocotb tests, a Python reference model, scoreboards, corner cases and GitHub Actions CI.
