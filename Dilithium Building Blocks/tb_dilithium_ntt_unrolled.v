module tb_dilithium_ntt_unrolled;

reg [6143:0] in_vec_flat;
wire [6143:0] out_vec_flat;

dilithium_ntt_unrolled uut(in_vec_flat, out_vec_flat);

integer seed;
integer i,j;

integer total_test = 10;
integer test_idx;

integer fd;

initial begin
    fd = $fopen("Dilithium Building Blocks/dilithium_ntt_unrolled_test.txt", "w");

    in_vec_flat = 0;

    seed = 32'hDEADBEEF;   // fixed seed -> deterministic

    for (test_idx = 0; test_idx < total_test; test_idx = test_idx + 1) begin
        for (i = 0; i < 6144; i = i + 32) begin
          in_vec_flat[i +: 32] = $urandom(seed);
        end

        #100
        $fdisplay(fd, "%6144b", in_vec_flat);
        $fdisplay(fd, "%6144b", out_vec_flat);
    end
    #10
    $finish();
end

endmodule
