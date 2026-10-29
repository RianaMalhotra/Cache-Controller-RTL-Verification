# CacheForge Architecture and Verification

## Data path

```text
 CPU request (address, read/write, data)
                  |
                  v
       +---------------------+
       | Blocking controller |
       | lookup / eviction   |
       | refill / response   |
       +----+-----------+----+
            |           |
            v           v
   +----------------+  +----------------+
   | Cache arrays   |  | Per-set LRU    |
   | 8 sets x 2 ways|  | victim chooser |
   | tag/data/V/D   |  +----------------+
   +--------+-------+
            |
            v
   Backing memory request / response
```

## Cache geometry

- 16-bit byte address: `[tag (11)][set (3)][byte offset (2)]`.
- 8 sets × 2 ways × 4-byte lines = 64 bytes of data storage.
- Tag/valid/dirty bits are stored for each line.
- Invalid ways are selected before replacing valid lines; otherwise the LRU way is selected.

## Controller state machine

```text
 IDLE -> LOOKUP
           | hit read -> response -> IDLE
           | hit write -> UPDATE -> response -> IDLE
           | miss -> EVICT_CHECK
                        | dirty valid victim -> WRITEBACK
                        | otherwise -----------+
                                               v
                                          REFILL_REQ
                                               |
                                          REFILL_WAIT
                                               |
                                              FILL -> response -> IDLE
```

The controller supports one outstanding CPU request. The simulated backing memory accepts a write-back or read request through a valid/ready handshake and returns read data with a separate response-valid signal. A write miss allocates and updates the fetched line. A dirty victim is written back before refill.

## Verification strategy

| Test | Intent |
| --- | --- |
| `test_cache_lookup` | Tag comparison and valid-line hit gating |
| `test_cache_arrays` | Array reads/writes, valid/dirty metadata |
| `test_cache_lru` | Invalid-way priority, replacement and set isolation |
| `test_cache_controller` | Integrated hit/miss, refill and dirty eviction |
| `test_cache_randomized` | 400 deterministic random operations against an independent memory scoreboard and final read sweep |

Each cocotb suite is built independently with `make clean` between runs. GitHub Actions automates this sequence.

## Limitations and potential extensions

- Word-aligned, 32-bit accesses only; no byte enables or subword loads/stores.
- Simplified memory bus rather than AXI/AHB/Wishbone.
- No pipelining, multiple outstanding requests, flush, invalidate or coherence.
- Randomized verification is deterministic and finite, not formal proof.
- Future extensions: constrained-random seeds, functional coverage, assertions, waveform traces, backpressure and fault injection.
