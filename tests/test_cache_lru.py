import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def tick(dut):
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


@cocotb.test()
async def lru_replacement_and_set_isolation(dut):
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.access_en.value = 0
    dut.access_set.value = 0
    dut.access_way.value = 0
    dut.victim_set.value = 2
    dut.valid_way0.value = 1
    dut.valid_way1.value = 1
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await tick(dut)
    dut.rst_n.value = 1
    assert int(dut.victim_way.value) == 0

    dut.access_set.value = 2
    dut.access_way.value = 0
    dut.access_en.value = 1
    await tick(dut)
    dut.access_en.value = 0
    assert int(dut.victim_way.value) == 1

    dut.access_way.value = 1
    dut.access_en.value = 1
    await tick(dut)
    dut.access_en.value = 0
    assert int(dut.victim_way.value) == 0

    dut.victim_set.value = 3
    await Timer(1, unit="ns")
    assert int(dut.victim_way.value) == 0

    dut.victim_set.value = 2
    dut.valid_way0.value = 0
    await Timer(1, unit="ns")
    assert int(dut.victim_way.value) == 0
    dut.valid_way0.value = 1
    dut.valid_way1.value = 0
    await Timer(1, unit="ns")
    assert int(dut.victim_way.value) == 1
