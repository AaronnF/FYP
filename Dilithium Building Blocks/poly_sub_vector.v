module poly_sub_vector #(
    parameter N = 256,
    parameter WIDTH = 24
)(
    input  wire [(N*WIDTH)-1:0] poly_a,
    input  wire [(N*WIDTH)-1:0] poly_b,
    output wire [(N*WIDTH)-1:0] poly_c
);

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin
            assign poly_c[WIDTH*i +: WIDTH] = $signed(poly_a[WIDTH*i +: WIDTH]) - $signed(poly_b[WIDTH*i +: WIDTH]);  
        end
    endgenerate

endmodule