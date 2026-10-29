import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def settle():
    await Timer(1, units="ns")


async def store(dut, set_id, way, tag, value, valid=1, dirty=0):
    dut.set_index.value = set_id
    dut.write_way.value = way
    dut.write_tag.value = tag
    dut.write_data.value = value
    dut.write_valid.value = valid
    dut.write_dirty.value = dirty
    dut.write_en.value = 1
    await RisingEdge(dut.clk)
    dut.write_en.value = 0
    await Timer(1, units="ns")


@cocotb.test()
async def cache_arrays_basic(dut):
    dut.clk.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst_n.value = 0
    dut.write_en.value = 0
    dut.set_index.value = 0
    dut.lookup_tag.value = 7
    dut.write_way.value = 0
    dut.write_tag.value = 0
    dut.write_data.value = 0
    dut.write_valid.value = 0
    dut.write_dirty.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n.value = 1
    await settle()
    assert int(dut.hit.value) == 0

    await store(dut, 2, 0, 7, 0xDEADBEEF, dirty=1)
    dut.set_index.value = 2
    dut.lookup_tag.value = 7
    dut.write_way.value = 0
    await settle()
    assert int(dut.hit.value) == 1
    assert int(dut.hit_way.value) == 0
    assert int(dut.hit_data.value) == 0xDEADBEEF
    assert int(dut.selected_dirty.value) == 1

    await store(dut, 2, 1, 8, 0x12345678)
    dut.lookup_tag.value = 8
    await settle()
    assert int(dut.hit.value) == 1
    assert int(dut.hit_way.value) == 1
    assert int(dut.hit_data.value) == 0x12345678

    dut.set_index.value = 3
    await settle()
    assert int(dut.hit.value) == 0

    await store(dut, 2, 1, 8, 0x12345678, valid=0)
    dut.set_index.value = 2
    await settle()
    assert int(dut.hit.value) == 0
