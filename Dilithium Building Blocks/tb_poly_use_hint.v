module tb_poly_use_hint;

reg [6143:0] poly_a;
reg [255:0] poly_h;
wire [6143:0] poly_b;

poly_use_hint uut(poly_a, poly_h, poly_b);

integer seed;
integer i,j;

integer total_test = 20;
integer test_idx;

integer fd;

initial begin
    fd = $fopen("dilithium_tests/poly_use_hint.txt", "w");

    poly_a = 0;
    poly_h = 0;

    seed = 32'hDEADBEEF;   // fixed seed -> deterministic

    for (test_idx = 0; test_idx < total_test; test_idx = test_idx + 1) begin
        for (i = 0; i < 6144; i = i + 32) begin
          poly_a[i +: 32] = $urandom(seed);
        end
        for (i = 0; i < 256; i = i + 32) begin
          poly_h[i +: 32] = $urandom(seed);
        end

        #100
        $fdisplay(fd, "%6144b  %256b  %6144b", poly_a, poly_h, poly_b);
    end
    #10
    $finish();
end

endmodule
