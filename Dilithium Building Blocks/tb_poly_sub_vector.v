module tb_poly_sub_vector;

reg [6143:0] poly_a;
reg [6143:0] poly_b;
wire [6143:0] poly_c;

poly_sub_vector uut(poly_a, poly_b, poly_c);

integer seed;
integer i,j;

integer total_test = 50;
integer test_idx;

integer fd;

initial begin
    fd = $fopen("dilithium_tests/poly_sub_vector.txt", "w");

    poly_a = 0;
    poly_b = 0;

    seed = 32'hDEADBEEF;   // fixed seed -> deterministic

    for (test_idx = 0; test_idx < total_test; test_idx = test_idx + 1) begin
        for (i = 0; i < 6144; i = i + 32) begin
          poly_a[i +: 32] = $urandom(seed);
        end
        for (i = 0; i < 6144; i = i + 32) begin
          poly_b[i +: 32] = $urandom(seed);
        end

        #100
        $fdisplay(fd, "%6144b  %6144b  %6144b", poly_a, poly_b, poly_c);
    end
    #10
    $finish();
end

endmodule
