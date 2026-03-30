module tb_invntt_256_comb;

reg [6143:0] poly_in;
wire [6143:0] poly_out;

invntt_256_comb uut(poly_in, poly_out);

integer seed;
integer i,j;

integer total_test = 20;
integer test_idx;

integer fd;

initial begin
    fd = $fopen("dilithium_tests/invntt_256_comb.txt", "w");

    poly_in = 0;

    seed = 32'hDEADBEEF;   // fixed seed -> deterministic

    for (test_idx = 0; test_idx < total_test; test_idx = test_idx + 1) begin
        for (i = 0; i < 6144; i = i + 32) begin
          poly_in[i +: 32] = $urandom(seed);
        end

        #100
        $fdisplay(fd, "%6144b  %6144b", poly_in, poly_out);
    end
    #10
    $finish();
end

endmodule
