# Verification Strategy

[← README](../README.md) · [Architecture](architecture.md)

## Verification objective

Check that cache operations preserve the **architecturally latest word value**, even when dirty data is held in the cache and the backing-memory model has not yet been updated.

The project uses Python/cocotb to drive the SystemVerilog RTL under Verilator. Five test suites separate module-level behavior from integrated end-to-end behavior.

## Test matrix

| Suite | DUT | Primary checks |
| --- | --- | --- |
| `test_cache_lookup` | `cache_lookup` | Valid tags hit; invalid tags cannot hit; mismatched tags miss |
| `test_cache_arrays` | `cache_arrays` | Data/tag writes, hits/misses, dirty metadata and invalidation |
| `test_cache_lru` | `cache_lru` | LRU updates, invalid-way priority and set independence |
| `test_cache_controller` | `cache_controller` | Refills, write hits, conflicting addresses and dirty eviction |
| `test_cache_randomized` | `cache_controller` | Seeded mixed traffic, reference-value comparisons, eviction/refill activity and final readback |

## Reference-model / scoreboard design

The randomized test maintains **two distinct Python dictionaries**:

1. `expected`: the latest logical value for each address, updated on every CPU write. This is the **scoreboard's architectural reference**.
2. `backing`: the simulated external memory. It is updated only when the controller issues a write-back transaction.

This separation is essential for a write-back cache: after a store hit, the latest value may be in a dirty cache line while external memory still contains an older value.

For every CPU read, the scoreboard checks:

```python
assert actual_read_data == expected[address]
```

For a CPU write, it updates `expected[address]` and checks the controller's completion value. A final read sweep visits all test addresses to expose lost or corrupted writes after further replacements.

## Random stimulus

- Fixed PRNG seed: `0xCAFE2026` for reproducibility.
- **400** randomly selected CPU operations, with a 45% write probability.
- **48** word-aligned addresses: 8 sets × 6 different tags.
- Random 32-bit initial contents and write data.
- Conflicting tags deliberately create replacement pressure.
- A final 48-address readback sweep checks all tracked values.
- The test requires at least one refill and at least one dirty write-back.

These are **stimulus and checker properties**, not claims of formal or measured functional coverage.

## Memory timing model

The testbench holds `mem_req_ready=1`, so backing-memory requests are accepted without backpressure. For a refill read, it waits for request acceptance, then drives `mem_resp_data` and pulses `mem_resp_valid` on a later clock. Write-backs update the `backing` dictionary when accepted.

This timing matters: asserting the response before the controller reaches `REFILL_WAIT` can cause a timeout. The integrated testbench was adjusted to model the request/response handshake correctly.

## Running the regression

From the repository root, with the Python virtual environment active:

```bash
make clean && make TOPLEVEL=cache_lookup
make clean && make TOPLEVEL=cache_arrays
make clean && make TOPLEVEL=cache_lru
make clean && make TOPLEVEL=cache_controller
make clean && make MODULE=test_cache_randomized
```

`make clean` is required between suites because the same `sim_build` directory is reused for different RTL top levels.

The [GitHub Actions workflow](../.github/workflows/verification.yml) runs the same five suites on pushes to `main`, pull requests and manual dispatch. A successful run is visible via the badge on the README.

## Interpreting results responsibly

- The directed controller and randomized scoreboard tests passed in local simulation, and CI was confirmed passing.
- A green CI check means the committed regression ran successfully for its configured simulator, versions and stimulus.
- The randomized scoreboard validates **returned data correctness** and the occurrence of memory traffic; it does not prove that the cache achieved optimal hit rate or correct performance under all timing conditions.
- No coverage closure, formal equivalence, timing closure, synthesis area or hardware measurements are claimed.

## Important untested cases

- `mem_req_ready` deasserted / backpressure.
- Arbitrary or long memory response latency.
- Simultaneous or same-cycle refill responses.
- Unaligned/subword accesses and byte enables.
- Cache flush, invalidate, reset during an in-flight miss.
- Multiple outstanding requests, coherency and standard bus integration.

**Interview angle:** The most important verification choice is separating the architectural scoreboard from the backing-memory model. That allows a write-back cache to be checked correctly even when the two intentionally disagree until eviction.
