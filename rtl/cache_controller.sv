// Blocking 2-way write-back/write-allocate cache controller.
// One 32-bit word per line. Memory read responses must arrive after
// acceptance of the read request (not in the same cycle).
module cache_controller (
    input logic clk, rst_n,
    input logic req_valid, req_write,
    input logic [15:0] req_addr,
    input logic [31:0] req_wdata,
    output logic req_ready,
    output logic resp_valid,
    output logic [31:0] resp_rdata,
    output logic mem_req_valid,
    input logic mem_req_ready,
    output logic mem_req_write,
    output logic [15:0] mem_req_addr,
    output logic [31:0] mem_req_wdata,
    input logic mem_resp_valid,
    input logic [31:0] mem_resp_data
);
    typedef enum logic [2:0] {
        IDLE, LOOKUP, EVICT_CHECK, UPDATE, WRITEBACK, REFILL_REQ, REFILL_WAIT, FILL
    } state_t;
    state_t state;
    logic [15:0] addr_q;
    logic write_q;
    logic [31:0] wdata_q, refill_q;
    logic victim_q;
    wire [2:0] set_idx = addr_q[4:2];
    wire [10:0] tag = addr_q[15:5];
    logic hit, hit_way;
    logic [31:0] hit_data, selected_data;
    logic [10:0] selected_tag;
    logic selected_valid, selected_dirty, valid0, valid1;
    logic victim_way;
    wire array_write = (state == UPDATE || state == FILL);
    wire target_way = (state == LOOKUP && hit) || state == UPDATE ? hit_way : victim_q;
    wire [31:0] fill_data = write_q ? wdata_q : refill_q;

    cache_arrays arrays (
        .clk(clk), .rst_n(rst_n), .set_index(set_idx),
        .lookup_tag(tag), .hit(hit), .hit_way(hit_way), .hit_data(hit_data),
        .write_en(array_write), .write_way(target_way),
        .write_tag(tag), .write_data(state == UPDATE ? wdata_q : fill_data),
        .write_valid(1'b1), .write_dirty(write_q),
        .selected_tag(selected_tag), .selected_data(selected_data),
        .selected_valid(selected_valid), .selected_dirty(selected_dirty),
        .way0_valid(valid0), .way1_valid(valid1)
    );

    cache_lru lru (
        .clk(clk), .rst_n(rst_n),
        .access_en((state == LOOKUP && hit) || state == FILL),
        .access_set(set_idx),
        .access_way(state == FILL ? victim_q : hit_way),
        .victim_set(set_idx), .valid_way0(valid0), .valid_way1(valid1),
        .victim_way(victim_way)
    );

    assign req_ready = state == IDLE;
    assign mem_req_valid = state == WRITEBACK || state == REFILL_REQ;
    assign mem_req_write = state == WRITEBACK;
    assign mem_req_addr = state == WRITEBACK
        ? {selected_tag, set_idx, 2'b00}
        : {tag, set_idx, 2'b00};
    assign mem_req_wdata = selected_data;

    // On WRITEBACK, select the latched victim's metadata and data.
    // During LOOKUP, target_way is not yet latched, so victim selection
    // is performed using a separate lookup of each candidate below.
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE;
            addr_q <= '0;
            write_q <= 0;
            wdata_q <= '0;
            refill_q <= '0;
            victim_q <= 0;
            resp_valid <= 0;
            resp_rdata <= '0;
        end else begin
            resp_valid <= 0;
            case (state)
                IDLE: if (req_valid) begin
                    addr_q <= req_addr;
                    write_q <= req_write;
                    wdata_q <= req_wdata;
                    state <= LOOKUP;
                end
                LOOKUP: if (hit) begin
                    if (write_q)
                        state <= UPDATE;
                    else begin
                        resp_rdata <= hit_data;
                        resp_valid <= 1;
                        state <= IDLE;
                    end
                end else begin
                    victim_q <= victim_way;
                    // Dirty victim is evaluated in EVICT_CHECK below.
                    state <= EVICT_CHECK;
                end
                EVICT_CHECK: begin
                    if (selected_valid && selected_dirty)
                        state <= WRITEBACK;
                    else
                        state <= REFILL_REQ;
                end
                UPDATE: begin
                    resp_rdata <= wdata_q;
                    resp_valid <= 1;
                    state <= IDLE;
                end
                WRITEBACK: if (mem_req_ready)
                    state <= REFILL_REQ;
                REFILL_REQ: if (mem_req_ready)
                    state <= REFILL_WAIT;
                REFILL_WAIT: if (mem_resp_valid) begin
                    refill_q <= mem_resp_data;
                    state <= FILL;
                end
                FILL: begin
                    resp_rdata <= fill_data;
                    resp_valid <= 1;
                    state <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
