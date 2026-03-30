module tb_unpack_z_one_coeff;

reg [17:0] packed_z;
wire [23:0] unpacked_z;

unpack_z_one_coeff uut(packed_z, unpacked_z);

integer seed;
integer i,j;

integer total_test = 100;
integer test_idx;

integer fd;

initial begin
    fd = $fopen("dilithium_tests/unpack_z_one_coeff.txt", "w");

    packed_z = 0;

    seed = 32'hDEADBEEF;   // fixed seed -> deterministic

    for (test_idx = 0; test_idx < total_test; test_idx = test_idx + 1) begin
        packed_z = $urandom(seed);

        #100
        $fdisplay(fd, "%18b %24b", packed_z, unpacked_z);
    end
    #10
    $finish();
end

endmodule
