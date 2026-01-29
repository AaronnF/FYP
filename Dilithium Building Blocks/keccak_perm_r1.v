/*
+---------------------------------+
|Designed By:                     | 
|Kamal Raj (kamal.raj@ntu.edu.sg) |
|Research Associate               |
|Temasek Laboratories @ NTU       |
+---------------------------------+
*/
`timescale 1ns / 1ps

module keccak_perm_r1 (
    input  wire [1599:0] round_in_port,
    input  wire [63:0]   round_constant_signal,
    output wire [1599:0] round_out_port
);

    // Internal state arrays: [y][x][z]
    wire [63:0] round_in  [0:4][0:4];
    wire [63:0] theta_out [0:4][0:4];
    wire [63:0] rho_out   [0:4][0:4];
    wire [63:0] pi_out    [0:4][0:4];
    wire [63:0] chi_out   [0:4][0:4];
    wire [63:0] iota_out  [0:4][0:4];
    
    // Intermediate sum sheet for Theta
    wire [63:0] sum_sheet [0:4];

    // --------------------------------------------------------------------------
    // Input Mapping (Flattened vector to 3D array)
    // --------------------------------------------------------------------------
    genvar x, y, i;
    generate
        for (y = 0; y < 5; y = y + 1) begin : gen_input_y
            for (x = 0; x < 5; x = x + 1) begin : gen_input_x
                assign round_in[y][x] = round_in_port[((y*5 + x)*64) +: 64];
            end
        end
    endgenerate

    // --------------------------------------------------------------------------
    // THETA Step
    // --------------------------------------------------------------------------
    generate
        for (x = 0; x < 5; x = x + 1) begin : gen_theta_sum
            assign sum_sheet[x] = round_in[0][x] ^ round_in[1][x] ^ round_in[2][x] ^ 
                                 round_in[3][x] ^ round_in[4][x];
        end

        for (y = 0; y < 5; y = y + 1) begin : gen_theta_out
            for (x = 0; x < 5; x = x + 1) begin : gen_theta_out_x
                // Standard Theta: T = S ^ sum(col x-1) ^ sum(col x+1 <<< 1)
                assign theta_out[y][x] = round_in[y][x] ^ sum_sheet[(x+4)%5] ^ {sum_sheet[(x+1)%5][62:0], sum_sheet[(x+1)%5][63]};
            end
        end
    endgenerate

    // --------------------------------------------------------------------------
    // RHO Step (Circular Shifts)
    // --------------------------------------------------------------------------
    // Mapping the specific shift constants
    function [63:0] rotl64(input [63:0] in, input integer shift);
        rotl64 = (in << (shift % 64)) | (in >> (64 - (shift % 64)));
    endfunction

    assign rho_out[0][0] = theta_out[0][0];
    assign rho_out[0][1] = rotl64(theta_out[0][1], 1);
    assign rho_out[0][2] = rotl64(theta_out[0][2], 62);
    assign rho_out[0][3] = rotl64(theta_out[0][3], 28);
    assign rho_out[0][4] = rotl64(theta_out[0][4], 27);
    assign rho_out[1][0] = rotl64(theta_out[1][0], 36);
    assign rho_out[1][1] = rotl64(theta_out[1][1], 44);
    assign rho_out[1][2] = rotl64(theta_out[1][2], 6);
    assign rho_out[1][3] = rotl64(theta_out[1][3], 55);
    assign rho_out[1][4] = rotl64(theta_out[1][4], 20);
    assign rho_out[2][0] = rotl64(theta_out[2][0], 3);
    assign rho_out[2][1] = rotl64(theta_out[2][1], 10);
    assign rho_out[2][2] = rotl64(theta_out[2][2], 43);
    assign rho_out[2][3] = rotl64(theta_out[2][3], 25);
    assign rho_out[2][4] = rotl64(theta_out[2][4], 39);
    assign rho_out[3][0] = rotl64(theta_out[3][0], 41);
    assign rho_out[3][1] = rotl64(theta_out[3][1], 45);
    assign rho_out[3][2] = rotl64(theta_out[3][2], 15);
    assign rho_out[3][3] = rotl64(theta_out[3][3], 21);
    assign rho_out[3][4] = rotl64(theta_out[3][4], 8);
    assign rho_out[4][0] = rotl64(theta_out[4][0], 18);
    assign rho_out[4][1] = rotl64(theta_out[4][1], 2);
    assign rho_out[4][2] = rotl64(theta_out[4][2], 61);
    assign rho_out[4][3] = rotl64(theta_out[4][3], 56);
    assign rho_out[4][4] = rotl64(theta_out[4][4], 14);

    // --------------------------------------------------------------------------
    // PI Step (Permute positions)
    // --------------------------------------------------------------------------
    generate
        for (y = 0; y < 5; y = y + 1) begin : gen_pi_y
            for (x = 0; x < 5; x = x + 1) begin : gen_pi_x
                assign pi_out[(2*x+3*y)%5][y] = rho_out[y][x];
            end
        end
    endgenerate

    // --------------------------------------------------------------------------
    // CHI Step (Non-linear)
    // --------------------------------------------------------------------------
    generate
        for (y = 0; y < 5; y = y + 1) begin : gen_chi_y
            for (x = 0; x < 5; x = x + 1) begin : gen_chi_x
                assign chi_out[y][x] = pi_out[y][x] ^ ((~pi_out[y][(x+1)%5]) & pi_out[y][(x+2)%5]);
            end
        end
    endgenerate

    // --------------------------------------------------------------------------
    // IOTA Step (Round Constant)
    // --------------------------------------------------------------------------
    generate
        for (y = 0; y < 5; y = y + 1) begin : gen_iota_y
            for (x = 0; x < 5; x = x + 1) begin : gen_iota_x
                if (x == 0 && y == 0)
                    assign iota_out[y][x] = chi_out[y][x] ^ round_constant_signal;
                else
                    assign iota_out[y][x] = chi_out[y][x];
            end
        end
    endgenerate

    // --------------------------------------------------------------------------
    // Output Mapping (3D array back to flattened vector)
    // --------------------------------------------------------------------------
    generate
        for (y = 0; y < 5; y = y + 1) begin : gen_output_y
            for (x = 0; x < 5; x = x + 1) begin : gen_output_x
                assign round_out_port[((y*5 + x)*64) +: 64] = iota_out[y][x];
            end
        end
    endgenerate

endmodule