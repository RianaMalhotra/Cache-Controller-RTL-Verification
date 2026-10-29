"""Deterministic randomized cache verification with a software scoreboard.

The scoreboard tracks the architectural memory image independently of the
cache's backing memory, which is only updated when dirty lines are evicted.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def tick(dut):
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def transfer(dut, address, write, value, backing, stats):
    for _ in range(10):
        if int(dut.req_ready.value):
            break
        await tick(dut)
    else:
        raise AssertionError("controller never became ready")

    dut.req_addr.value = address
    dut.req_write.value = int(write)
    dut.req_wdata.value = value
    dut.req_valid.value = 1
    await tick(dut)
    dut.req_valid.value = 0

    for _ in range(50):
        if int(dut.resp_valid.value):
            return int(dut.resp_rdata.value)

        if int(dut.mem_req_valid.value) and int(dut.mem_req_ready.value):
            mem_address = int(dut.mem_req_addr.value)
            assert mem_address % 4 == 0, "unaligned memory request"
            if int(dut.mem_req_write.value):
                backing[mem_address] = int(dut.mem_req_wdata.value)
                stats["writebacks"] += 1
                await tick(dut)
            else:
                stats["refills"] += 1
                # Request accepted at the next edge, then supply the read
                # response while the controller is in REFILL_WAIT.
                await tick(dut)
                dut.mem_resp_data.value = backing.get(mem_address, 0)
                dut.mem_resp_valid.value = 1
                await tick(dut)
                dut.mem_resp_valid.value = 0
        else:
            await tick(dut)
    raise AssertionError(f"timeout for address 0x{address:04x}")


@cocotb.test()
async def randomized_scoreboard(dut):
    rng = random.Random(0xCAFE2026)
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.req_valid.value = 0
    dut.req_write.value = 0
    dut.req_addr.value = 0
    dut.req_wdata.value = 0
    dut.mem_req_ready.value = 1
    dut.mem_resp_valid.value = 0
    dut.mem_resp_data.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await tick(dut)
    dut.rst_n.value = 1
    await tick(dut)

    # Mix conflicting addresses and different sets to stress LRU and writeback.
    addresses = [((tag << 5) | (set_idx << 2))
                 for set_idx in range(8) for tag in range(6)]
    initial = {addr: rng.getrandbits(32) for addr in addresses}
    backing = dict(initial)
    expected = dict(initial)
    stats = {"refills": 0, "writebacks": 0}
    writes = 0
    reads = 0

    for op in range(400):
        address = rng.choice(addresses)
        write = rng.random() < 0.45
        value = rng.getrandbits(32) if write else 0
        actual = await transfer(dut, address, write, value, backing, stats)
        if write:
            expected[address] = value
            writes += 1
            assert actual == value, f"write acknowledgement mismatch at op {op}"
        else:
            reads += 1
            assert actual == expected[address], (
                f"scoreboard mismatch op={op}, addr=0x{address:04x}, "
                f"got=0x{actual:08x}, expected=0x{expected[address]:08x}"
            )

    # Read every address: ensures all recent writes are still observable,
    # whether they remain cached or have been written back.
    for address in addresses:
        actual = await transfer(dut, address, False, 0, backing, stats)
        assert actual == expected[address], f"final sweep mismatch at 0x{address:04x}"

    assert stats["refills"] > 0, "no refills observed"
    assert stats["writebacks"] > 0, "no dirty evictions observed"
    dut._log.info(
        "Randomized scoreboard PASS: %d reads, %d writes, %d refills, %d writebacks",
        reads, writes, stats["refills"], stats["writebacks"]
    )
