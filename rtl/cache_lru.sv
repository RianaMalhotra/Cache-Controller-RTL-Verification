// True LRU for a two-way set-associative cache.
// lru_way[set] identifies the victim on the next replacement.
// On an access to way W, the other way becomes least recently used.
module cache_lru #(
    parameter int SET_BITS = 3
)(
    input  logic clk,
    input  logic rst_n,
    input  logic access_en,
    input  logic [SET_BITS-1:0] access_set,
    input  logic access_way,
    input  logic [SET_BITS-1:0] victim_set,
    input  logic valid_way0,
    input  logic valid_way1,
    output logic victim_way
);
    localparam int NUM_SETS = 1 << SET_BITS;
    logic lru_way [0:NUM_SETS-1];

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            for (int s = 0; s < NUM_SETS; s++)
                lru_way[s] <= 1'b0;
        end else if (access_en) begin
            lru_way[access_set] <= ~access_way;
        end
    end

    // Fill an invalid way before evicting a valid line.
    always_comb begin
        if (!valid_way0)
            victim_way = 1'b0;
        else if (!valid_way1)
            victim_way = 1'b1;
        else
            victim_way = lru_way[victim_set];
    end
endmodule
