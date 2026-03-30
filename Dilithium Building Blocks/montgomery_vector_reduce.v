/*
Montgomery Reduction for one coefficient
*/

module montgomery_vector_reduce #(
    parameter VECTOR_SIZE = 256
)(
    input  wire [(VECTOR_SIZE*48)-1:0] unreduced_vec,
    output wire [(VECTOR_SIZE*24)-1:0] reduced_vec
);

    genvar i;
    generate
        for (i = 0; i < VECTOR_SIZE; i = i + 1) begin
            montgomery_reduce inst (
                .unreduced(unreduced_vec[48*i +: 48]),
                .reduced(reduced_vec[24*i +: 24])
            );
        end
    endgenerate

endmodule


module montgomery_reduce(
    input  wire [47:0] unreduced,
    output wire [23:0] reduced
);

    // Parameters for KDilithium style reduction
    localparam signed [31:0] QINV = 32'd58728449;
    localparam signed [23:0] Q    = 24'd8380417; 

    wire signed [31:0] t_low;
    wire signed [55:0] product_q;
    wire signed [55:0] a_extended;
    wire signed [55:0] sub_result;

    assign t_low = $signed(unreduced[31:0]) * QINV;
    assign product_q = $signed(t_low) * Q;

    assign a_extended = $signed(unreduced);
    assign sub_result = a_extended - product_q;

    assign reduced = sub_result[55:32];

endmodule