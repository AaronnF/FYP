module tb_comparator;

reg [255:0] data_c;
reg [255:0] data_c2;
wire signature_valid;

comparator uut(data_c,data_c2,signature_valid);

integer seed;
integer i,j;

integer total_test = 100;
integer test_idx;

integer fd;

initial begin
    fd = $fopen("dilithium_tests/comparator.txt", "w");

    data_c = 0;
    data_c2 = 0;

    seed = 32'hDEADBEEF;   // fixed seed → deterministic

    for (test_idx = 0; test_idx < total_test; test_idx = test_idx + 1) begin
        for (i = 0; i < 256; i = i + 32) begin
          data_c[i +: 32] = $urandom(seed);
          data_c2[i +: 32] = $urandom(seed);
        end

        #100
        $fdisplay(fd, "%256b  %256b  %b", data_c, data_c2, signature_valid);
    end
    #10
    $finish();
end

endmodule
