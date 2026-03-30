module poly_use_hint #(
    parameter N = 256,
    parameter WIDTH = 24
)(
    input  wire [(N*WIDTH)-1:0] poly_a,   // Input coefficients
    input  wire [N-1:0]         poly_h,   // 1-bit hints for each N
    output wire [(N*WIDTH)-1:0] poly_b    // Output coefficients
);

    localparam signed [WIDTH-1:0] Q = 24'd8380417;
    localparam signed [WIDTH-1:0] GAMMA2 = 24'd95360; // Example for Dilithium3

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : gen_use_hint
            
            wire signed [WIDTH-1:0] a_i;
            wire hint_i;
            
            assign a_i = $signed(poly_a[WIDTH*i +: WIDTH]);
            assign hint_i = poly_h[i];
            
            wire [WIDTH-1:0] r1; // High bits
            wire signed [WIDTH-1:0] r0; // Low bits
            
            decompose_logic #(WIDTH) decomp_inst (
                .a(a_i),
                .gamma2(GAMMA2),
                .high_bits(r1),
                .low_bits(r0)
            );

            assign poly_b[WIDTH*i +: WIDTH] = (!hint_i) ? r1 :
                                              (r0 > 0)  ? (r1 + 1) : (r1 - 1);
        end
    endgenerate

endmodule

module decompose_logic #(parameter WIDTH = 24) (
    input  wire signed [WIDTH-1:0] a,
    input  wire signed [WIDTH-1:0] gamma2,
    output wire [WIDTH-1:0] high_bits,
    output wire signed [WIDTH-1:0] low_bits
);
    assign low_bits  = a % (2 * gamma2); 
    assign high_bits = (a - low_bits) / (2 * gamma2);
    
endmodule