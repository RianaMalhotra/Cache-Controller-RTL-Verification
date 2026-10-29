module cache_lookup #(
    parameter int ADDR_WIDTH = 16,
    parameter int SET_BITS = 3,
    parameter int OFFSET_BITS = 2,
    parameter int TAG_BITS = ADDR_WIDTH - SET_BITS - OFFSET_BITS
)(
    input  logic [ADDR_WIDTH-1:0] address,
    input  logic [TAG_BITS-1:0] tag_way0, tag_way1,
    input  logic valid_way0, valid_way1,
    output logic [SET_BITS-1:0] set_index,
    output logic [TAG_BITS-1:0] requested_tag,
    output logic hit, 
    output logic hit_way
);
    assign set_index = address[OFFSET_BITS +: SET_BITS];
    assign requested_tag = address[ADDR_WIDTH-1 -: TAG_BITS];
    always_comb begin
        hit = 1'b0;
        hit_way = 1'b0;
        if (valid_way0 && tag_way0 == requested_tag) begin
            hit = 1'b1;
            hit_way = 1'b0;
        end else if (valid_way1 && tag_way1 == requested_tag) begin
            hit = 1'b1;
            hit_way = 1'b1;
        end
    end
endmodule
