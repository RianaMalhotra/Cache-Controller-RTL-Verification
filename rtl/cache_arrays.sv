module cache_arrays #(
    parameter int ADDR_WIDTH = 16,
    parameter int SET_BITS = 3,
    parameter int OFFSET_BITS = 2,
    parameter int DATA_WIDTH = 32,
    parameter int TAG_BITS = ADDR_WIDTH - SET_BITS - OFFSET_BITS
)(
    input  logic clk,
    input  logic rst_n,
    input  logic [SET_BITS-1:0] set_index,
    input  logic [TAG_BITS-1:0] lookup_tag,
    output logic hit,
    output logic hit_way,
    output logic [DATA_WIDTH-1:0] hit_data,
    input  logic write_en,
    input  logic write_way,
    input  logic [TAG_BITS-1:0] write_tag,
    input  logic [DATA_WIDTH-1:0] write_data,
    input  logic write_valid,
    input  logic write_dirty,
    output logic [TAG_BITS-1:0] selected_tag,
    output logic [DATA_WIDTH-1:0] selected_data,
    output logic selected_valid,
    output logic selected_dirty,
    output logic way0_valid,
    output logic way1_valid
);
    localparam int NUM_SETS = 1 << SET_BITS;
    logic [TAG_BITS-1:0] tags [0:NUM_SETS-1][0:1];
    logic [DATA_WIDTH-1:0] data [0:NUM_SETS-1][0:1];
    logic valid [0:NUM_SETS-1][0:1];
    logic dirty [0:NUM_SETS-1][0:1];

    always_comb begin
        hit = 1'b0;
        hit_way = 1'b0;
        hit_data = '0;
        if (valid[set_index][0] && tags[set_index][0] == lookup_tag) begin
            hit = 1'b1;
            hit_data = data[set_index][0];
        end else if (valid[set_index][1] && tags[set_index][1] == lookup_tag) begin
            hit = 1'b1;
            hit_way = 1'b1;
            hit_data = data[set_index][1];
        end
    end

    assign way0_valid = valid[set_index][0];
    assign way1_valid = valid[set_index][1];
    assign selected_tag = tags[set_index][write_way];
    assign selected_data = data[set_index][write_way];
    assign selected_valid = valid[set_index][write_way];
    assign selected_dirty = dirty[set_index][write_way];

    // Metadata reset invalidates all lines; data and tags are don't-care until valid.
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            for (int s = 0; s < NUM_SETS; s++) begin
                for (int w = 0; w < 2; w++) begin
                    valid[s][w] <= 1'b0;
                    dirty[s][w] <= 1'b0;
                end
            end
        end else if (write_en) begin
            tags[set_index][write_way] <= write_tag;
            data[set_index][write_way] <= write_data;
            valid[set_index][write_way] <= write_valid;
            dirty[set_index][write_way] <= write_dirty;
        end
    end
endmodule
