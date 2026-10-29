# Waveform Walkthrough: Dirty Eviction and Refill

[← README](../README.md) · [Architecture](architecture.md) · [Verification](verification.md)

This guide explains how to generate and interpret a **real VCD waveform** from the existing directed controller test. No waveform screenshot is included until it has been captured from a simulation run.

## 1. Generate a trace

From Ubuntu/WSL, in the repository root:

```bash
git pull origin main
source .venv/bin/activate
make wave-controller
```

The target cleans the old build, then runs the existing `test_cache_controller.py` suite with `WAVES=1` for Verilator VCD tracing. Look for a generated `dump.vcd` (commonly under the project root; locate it with `find . -name '*.vcd'`). The exact output location can depend on the installed cocotb/Verilator makefiles.

Alternatively:

```bash
make clean
make TOPLEVEL=cache_controller WAVES=1
```

**Important:** VCD tracing is opt-in because traces can be large. The normal CI regression remains unchanged. `*.vcd` is ignored by Git; commit a curated screenshot, not a full raw trace.

## 2. Open the waveform

Install GTKWave in Ubuntu if needed:

```bash
sudo apt install -y gtkwave
```

Then open the actual VCD path returned by `find`, for example:

```bash
gtkwave dump.vcd
```

If you are using WSL without GUI support, you can open the VCD in a Windows waveform viewer instead. From Windows Explorer, navigate to `\\wsl$\Ubuntu\home\riana\CacheForge` (your distro name may differ).

## 3. Add these signals

Expand the `cache_controller` scope in GTKWave and add the following to the trace. Set address and data buses to **hexadecimal**.

| Signal | Why to inspect it |
| --- | --- |
| `clk` / `rst_n` | Clock edges and reset release |
| `req_valid` / `req_ready` | CPU request acceptance |
| `req_addr` / `req_write` / `req_wdata` | Operation and address being tested |
| `state` | FSM progression (may display numeric state encoding) |
| `hit` / `hit_way` | Hit detection and matching way |
| `victim_way` / `victim_q` | Replacement decision and latched victim |
| `selected_valid` / `selected_dirty` | Whether write-back is necessary |
| `mem_req_valid` / `mem_req_ready` | Memory request handshake |
| `mem_req_write` / `mem_req_addr` / `mem_req_wdata` | Write-back versus refill transaction |
| `mem_resp_valid` / `mem_resp_data` | Refill data return |
| `resp_valid` / `resp_rdata` | CPU completion and returned data |

Internal signals may be grouped differently by Verilator. If an internal signal is unavailable, focus on the external interface signals, which still show the memory transaction sequence.

## 4. Find the interesting transaction

The directed test uses three conflicting addresses (`0x0000`, `0x0020`, `0x0040`), all mapping to set 0. It writes `0x0000 = 0x0000ABCD`, accesses other lines, then eventually forces the dirty line to be evicted.

Locate the region where:

1. `mem_req_valid=1` and `mem_req_write=1`: dirty victim **write-back**. Expect `mem_req_addr=0x0000` and `mem_req_wdata=0x0000ABCD`.
2. A subsequent `mem_req_valid=1` and `mem_req_write=0`: **refill read** for the conflicting address.
3. `mem_resp_valid=1`: the memory model returns the requested word after read acceptance.
4. `resp_valid=1`: the CPU request completes.

The write-back must occur **before** the refill that replaces the dirty line. Zoom to include a few clock cycles before and after these events.

## 5. Suggested interviewer screenshot

Capture one readable GTKWave screenshot with:

- Clock and controller `state` near the top.
- CPU request and completion signals.
- `mem_req_valid`, `mem_req_write`, `mem_req_addr`, `mem_req_wdata`.
- `mem_resp_valid`, `mem_resp_data`.
- The time axis visible and bus values displayed in hex.

Add a short caption such as:

> **Dirty eviction trace:** CacheForge writes back a modified cache line before issuing a refill request, then completes the pending CPU transaction.

Save the image as `docs/images/dirty-eviction.png` and link it from the README **only after capturing and verifying it**. Do not substitute a mock waveform for a real simulation trace.

## 6. What this demonstrates (and what it does not)

A waveform is direct evidence of the observed transaction sequence for this test. It is useful for explaining handshake timing, the blocking FSM, and write-back ordering. It is not proof of correctness for all input combinations or arbitrary memory latencies.

If `WAVES=1` does not generate a VCD on your local toolchain, capture the command output and check the installed cocotb/Verilator tracing options before changing RTL.
