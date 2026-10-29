# CacheForge Architecture

## Target cache (future milestones)

- 16-bit byte addresses
- 2-way set associative
- 8 sets, 4-byte cache lines
- 64 bytes total data capacity
- Write-back, write-allocate
- Per-set 1-bit true LRU
- Blocking (one outstanding request)

Address layout: `[tag:11][set:3][byte offset:2]`.

## Milestone 1: Tag lookup

The combinational `cache_lookup` module extracts set and tag bits and identifies a valid matching way. This is **not** the complete cache controller yet. It has no state arrays, refill, replacement policy, or memory transaction interface.

## Roadmap

1. Tag lookup and basic cocotb tests.
2. Set/way metadata arrays, data arrays, reset and hit handling.
3. LRU state updates and victim choice.
4. Write-back and refill finite state machine.
5. Python reference model, randomized scoreboard and coverage.
6. Continuous integration and waveform documentation.
