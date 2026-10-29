import cocotb
from cocotb.triggers import Timer


async def settle():
    await Timer(1, unit="ns")


@cocotb.test()
async def lookup_hit_miss(dut):
    dut.tag_way0.value = 0x12
    dut.tag_way1.value = 0x23
    dut.valid_way0.value = 1
    dut.valid_way1.value = 1
    dut.address.value = (0x12 << 5) | (3 << 2)
    await settle()
    assert int(dut.hit.value) == 1
    assert int(dut.hit_way.value) == 0
    assert int(dut.set_index.value) == 3

    dut.address.value = (0x23 << 5) | (6 << 2)
    await settle()
    assert int(dut.hit.value) == 1
    assert int(dut.hit_way.value) == 1

    dut.address.value = (0x24 << 5)
    await settle()
    assert int(dut.hit.value) == 0


@cocotb.test()
async def invalid_tags_never_hit(dut):
    dut.address.value = 0
    dut.tag_way0.value = 0
    dut.tag_way1.value = 0
    dut.valid_way0.value = 0
    dut.valid_way1.value = 0
    await settle()
    assert int(dut.hit.value) == 0
