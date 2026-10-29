import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def cycle(dut):
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def request(dut, addr, write=0, data=0):
    while not int(dut.req_ready.value):
        await cycle(dut)
    dut.req_addr.value = addr
    dut.req_write.value = write
    dut.req_wdata.value = data
    dut.req_valid.value = 1
    await cycle(dut)
    dut.req_valid.value = 0


async def transact(dut, addr, write=0, data=0, memory=None):
    await request(dut, addr, write, data)
    for _ in range(40):
        # Memory model: accept request, respond to reads one cycle later.
        if int(dut.mem_req_valid.value):
            mem_addr = int(dut.mem_req_addr.value)
            if int(dut.mem_req_write.value):
                memory[mem_addr] = int(dut.mem_req_wdata.value)
            else:
                # First clock accepts the refill request and enters REFILL_WAIT.
                await cycle(dut)
                # Present the response for the following clock edge.
                dut.mem_resp_data.value = memory.get(mem_addr, 0)
                dut.mem_resp_valid.value = 1
                await cycle(dut)
                dut.mem_resp_valid.value = 0
                continue
        if int(dut.resp_valid.value):
            return int(dut.resp_rdata.value)
        await cycle(dut)
    raise AssertionError("cache request timed out")


@cocotb.test()
async def hits_misses_and_dirty_eviction(dut):
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
    await cycle(dut)
    dut.rst_n.value = 1
    await cycle(dut)
    memory = {0x0000: 0x11, 0x0020: 0x22, 0x0040: 0x33}
    assert await transact(dut, 0x0000, memory=memory) == 0x11
    assert await transact(dut, 0x0020, memory=memory) == 0x22
    assert await transact(dut, 0x0000, write=1, data=0xABCD, memory=memory) == 0xABCD
    # Accessing third conflicting line evicts way holding 0x0020.
    assert await transact(dut, 0x0040, memory=memory) == 0x33
    assert await transact(dut, 0x0000, memory=memory) == 0xABCD
    # Make 0x0000 least recently used then force dirty writeback.
    assert await transact(dut, 0x0040, memory=memory) == 0x33
    assert await transact(dut, 0x0020, memory=memory) == 0x22
    assert memory[0x0000] == 0xABCD
