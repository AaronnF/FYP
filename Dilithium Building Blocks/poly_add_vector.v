module poly_caddq #(
    parameter N = 256,
    parameter WIDTH = 24
)(
    input  wire [(N*WIDTH)-1:0] poly_in,
    output wire [(N*WIDTH)-1:0] poly_out
);

    localparam signed [WIDTH-1:0] Q = 24'd8380417;

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin
            
            wire signed [WIDTH-1:0] coeff_in;
            wire signed [WIDTH-1:0] coeff_plus_q;
            
            assign coeff_in = $signed(poly_in[WIDTH*i +: WIDTH]);
            assign coeff_plus_q = coeff_in + Q;

            assign poly_out[WIDTH*i +: WIDTH] = (coeff_in[WIDTH-1]) ? coeff_plus_q : coeff_in;
            
        end
    endgenerate

endmodule