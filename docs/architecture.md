# Architecture & Design Decisions

[← README](../README.md) · [Verification strategy](verification.md)

## 1. Objective and scope

CacheForge implements a **blocking, two-way set-associative, write-back, write-allocate cache** as synthesizable SystemVerilog RTL. It connects a simplified CPU request port to a simplified backing-memory request/response port. The design is intended to make cache policy, metadata, replacement and miss sequencing observable in simulation.

It is a single-word-per-line cache; this intentionally avoids burst refill complexity. The current tests use word-aligned 32-bit accesses.

## 2. Cache geometry and address decomposition

| Field | Width | Source bits |
| --- | ---: | --- |
| Tag | 11 | `addr[15:5]` |
| Set index | 3 | `addr[4:2]` |
| Byte offset | 2 | `addr[1:0]` |

- **8 sets × 2 ways × 4 bytes/line = 64 bytes** of data capacity.
- Each line stores a 32-bit data word, 11-bit tag, valid bit and dirty bit.
- The controller uses the tag and set index; it does not implement byte lanes or byte enables.
- On reset, valid and dirty bits clear. Tag/data storage need not reset because invalid entries cannot hit.

Example: addresses `0x0000`, `0x0020` and `0x0040` all map to set 0 but have different tags, making them useful for replacement and eviction tests.

## 3. Module responsibilities

| RTL | Responsibility |
| --- | --- |
| [`cache_lookup.sv`](../rtl/cache_lookup.sv) | Standalone combinational hit/miss lookup milestone |
| [`cache_arrays.sv`](../rtl/cache_arrays.sv) | Two-way data/tag arrays, hit detection, valid/dirty storage and selected-way metadata |
| [`cache_lru.sv`](../rtl/cache_lru.sv) | Per-set LRU bit, invalid-way preference, access-driven replacement updates |
| [`cache_controller.sv`](../rtl/cache_controller.sv) | CPU request capture, hit response, write update, eviction, refill and completion |

The integrated controller instantiates `cache_arrays` and `cache_lru`; the standalone `cache_lookup` is an earlier educational module rather than an extra block in the integrated datapath.

## 4. Controller FSM

```text
                +------+
                | IDLE | <----------------------------+
                +--+---+                              |
                   | req_valid                        |
                   v                                  |
                +--------+                            |
                | LOOKUP |                            |
                +--+--+--+                            |
                   |  |                               |
          read hit |  | write hit                     |
          respond  |  v                               |
                   | UPDATE -- write/ack ------------>|
                   |                                  |
                   +-- miss --> EVICT_CHECK           |
                                    |                 |
                     dirty & valid  |                 |
                                    v                 |
                                WRITEBACK             |
                                    | accepted        |
                                    v                 |
                                REFILL_REQ <----------+
                                    | read accepted   ^ (clean/invalid
                                    v                 |  victim skips
                                REFILL_WAIT <---------+  WRITEBACK)
                                    | response valid
                                    v
                                   FILL -- respond --> IDLE
```

**Clarification:** The clean/invalid-victim path goes from `EVICT_CHECK` directly to `REFILL_REQ`. The diagram's shared arrows represent that branch, not a second independent request.

### Read hit
The tag matches a valid line; `resp_rdata` is captured from that way and `resp_valid` is pulsed. The accessed way becomes most recently used.

### Write hit
The controller enters `UPDATE`, overwrites the matching word and marks it dirty. The CPU receives a completion pulse; backing memory is not written immediately.

### Read miss
The controller chooses an invalid way if available, otherwise the least recently used way. If the selected line is dirty and valid, the controller first issues a write-back to the evicted line's reconstructed address. It then issues a refill request, waits for memory response, writes the fetched data into the selected way, and responds to the CPU.

### Write miss
The same miss/eviction/refill sequence occurs, but the allocated line is populated with the pending CPU write data and marked dirty. This is a **write-allocate** policy. The memory refill transaction still occurs in the current implementation.

## 5. External interfaces

### CPU side

| Signal | Direction | Meaning |
| --- | --- | --- |
| `req_valid` / `req_ready` | in / out | CPU request accepted when both are high on a rising clock edge |
| `req_write` | in | 1 = store, 0 = load |
| `req_addr[15:0]` | in | Byte address; tests use word alignment |
| `req_wdata[31:0]` | in | Store data |
| `resp_valid` | out | Completion pulse |
| `resp_rdata[31:0]` | out | Load data, or echoed store value in current RTL |

The controller is blocking: `req_ready` is asserted only in `IDLE`.

### Backing-memory side

| Signal | Direction | Meaning |
| --- | --- | --- |
| `mem_req_valid` / `mem_req_ready` | out / in | Request handshake |
| `mem_req_write` | out | 1 = dirty write-back; 0 = refill read |
| `mem_req_addr[15:0]` | out | Aligned word address |
| `mem_req_wdata[31:0]` | out | Evicted dirty word |
| `mem_resp_valid` | in | Read-response valid |
| `mem_resp_data[31:0]` | in | Returned refill word |

**Timing assumption:** A refill response must arrive after the memory request is accepted, when the controller is waiting in `REFILL_WAIT`. The interface has no response-ready signal or transaction IDs, and does not support same-cycle read responses. The cocotb memory model deliberately waits until the request is accepted before responding.

## 6. Replacement policy and metadata

Each set has one LRU bit indicating the next victim if both ways are valid. Accessing way 0 makes way 1 least recently used; accessing way 1 makes way 0 least recently used. When a way is invalid, the replacement logic prefers that way regardless of LRU state.

On a miss, the controller latches the victim way before checking whether that line is dirty. The selected line's tag, data, valid and dirty bits determine whether write-back is needed.

## 7. Tradeoffs and engineering limitations

- **Blocking vs nonblocking:** A blocking controller is simpler to reason about but cannot overlap independent CPU requests.
- **Write-back vs write-through:** Write-back reduces immediate backing-memory writes but requires correct dirty metadata and eviction ordering.
- **One-word lines:** Makes refill and eviction atomic in the current model, but does not model spatial locality or burst transfers.
- **Custom interface:** Useful for verification learning, but not a standard AXI/AHB/Wishbone implementation.
- **Verification boundary:** Passing directed and randomized tests establishes observed behavior for those stimuli, not exhaustive correctness.

**Potential next steps:** Introduce stalls on `mem_req_ready`, delayed read responses, coverage counters, assertions, additional random seeds, cache flush/invalidate and subword operations.

See [verification strategy](verification.md) for the executable checks.
