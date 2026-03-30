module tb_montgomery_vector_reduce;

reg [12287:0] unreduced_vec;
wire [6143:0] reduced_vec;

montgomery_vector_reduce uut(unreduced_vec, reduced_vec);

integer seed;
integer i,j;

integer total_test = 50;
integer test_idx;

integer fd;

initial begin
    fd = $fopen("dilithium_tests/montgomery_vector_reduce.txt", "w");

    unreduced_vec = 0;

    seed = 32'hDEADBEEF;   // fixed seed -> deterministic

    for (test_idx = 0; test_idx < total_test; test_idx = test_idx + 1) begin
        for (i = 0; i < 12288; i = i + 32) begin
          unreduced_vec[i +: 32] = $urandom(seed);
        end

        #100
        $fdisplay(fd, "%12288b  %6144b", unreduced_vec, reduced_vec);
    end
    #10
    $finish();
end

endmodule
