module dilithium_ntt_unrolled (
    input  wire [6143:0] in_vec_flat,
    output wire [6143:0] out_vec_flat
);

    // Internal wires for 9 levels (Stage 0 to 8)
    // 256 elements per level, 24 bits per element
    wire [23:0] w [0:8][0:255];

    // --- Input Mapping ---
    genvar i;
    generate
        for (i = 0; i < 256; i = i + 1) begin : input_bind
            assign w[0][i] = in_vec_flat[i*24 +: 24];
        end
    endgenerate

    // --- Butterfly Stages ---
    genvar stage, j, k;
    generate
        for (stage = 0; stage < 8; stage = stage + 1) begin : stage_gen
            for (j = 0; j < (1 << stage); j = j + 1) begin : group_gen
                
                // Fetch the Zeta constant for this group
                wire [23:0] curr_zeta;
                assign curr_zeta = zeta_lut((1 << stage) + j);

                for (k = 0; k < (1 << (7 - stage)); k = k + 1) begin : bf_gen
                    localparam step = 1 << (7 - stage);
                    localparam idx_u = 2 * j * step + k;
                    localparam idx_v = idx_u + step;

                    ntt_butterfly_unit u_bf (
                        .u_in(w[stage][idx_u]),
                        .v_in(w[stage][idx_v]),
                        .zeta(curr_zeta),
                        .u_out(w[stage+1][idx_u]),
                        .v_out(w[stage+1][idx_v])
                    );
                end
            end
        end
    endgenerate

    // --- Output Mapping ---
    generate
        for (i = 0; i < 256; i = i + 1) begin : output_bind
            assign out_vec_flat[i*24 +: 24] = w[8][i];
        end
    endgenerate

    // --- The Complete Zeta Look-Up Table ---
    function [23:0] zeta_lut;
        input [7:0] index;
        case (index)
            8'd1:   zeta_lut = 24'd25847;   8'd2:   zeta_lut = 24'd577156;  8'd3:   zeta_lut = 24'd3222400; 8'd4:   zeta_lut = 24'd86828;
            8'd5:   zeta_lut = 24'd28258;   8'd6:   zeta_lut = 24'd105347;  8'd7:   zeta_lut = 24'd11363;   8'd8:   zeta_lut = 24'd4261248;
            8'd9:   zeta_lut = 24'd37418;   8'd10:  zeta_lut = 24'd436573;  8'd11:  zeta_lut = 24'd48074;   8'd12:  zeta_lut = 24'd309062;
            8'd13:  zeta_lut = 24'd1027731; 8'd14:  zeta_lut = 24'd233137;  8'd15:  zeta_lut = 24'd500134;  8'd16:  zeta_lut = 24'd493439;
            8'd17:  zeta_lut = 24'd399353;  8'd18:  zeta_lut = 24'd138612;  8'd19:  zeta_lut = 24'd1217551; 8'd20:  zeta_lut = 24'd1011030;
            8'd21:  zeta_lut = 24'd240081;  8'd22:  zeta_lut = 24'd143520;  8'd23:  zeta_lut = 24'd157309;  8'd24:  zeta_lut = 24'd195977;
            8'd25:  zeta_lut = 24'd725454;  8'd26:  zeta_lut = 24'd101654;  8'd27:  zeta_lut = 24'd370188;  8'd28:  zeta_lut = 24'd104531;
            8'd29:  zeta_lut = 24'd266657;  8'd30:  zeta_lut = 24'd564177;  8'd31:  zeta_lut = 24'd557007;  8'd32:  zeta_lut = 24'd192135;
            8'd33:  zeta_lut = 24'd246690;  8'd34:  zeta_lut = 24'd151239;  8'd35:  zeta_lut = 24'd289047;  8'd36:  zeta_lut = 24'd114486;
            8'd37:  zeta_lut = 24'd332617;  8'd38:  zeta_lut = 24'd254399;  8'd39:  zeta_lut = 24'd270387;  8'd40:  zeta_lut = 24'd325776;
            8'd41:  zeta_lut = 24'd445585;  8'd42:  zeta_lut = 24'd201201;  8'd43:  zeta_lut = 24'd317076;  8'd44:  zeta_lut = 24'd457493;
            8'd45:  zeta_lut = 24'd485121;  8'd46:  zeta_lut = 24'd494191;  8'd47:  zeta_lut = 24'd271501;  8'd48:  zeta_lut = 24'd181467;
            8'd49:  zeta_lut = 24'd304953;  8'd50:  zeta_lut = 24'd563533;  8'd51:  zeta_lut = 24'd271295;  8'd52:  zeta_lut = 24'd402123;
            8'd53:  zeta_lut = 24'd326938;  8'd54:  zeta_lut = 24'd403756;  8'd55:  zeta_lut = 24'd143048;  8'd56:  zeta_lut = 24'd345579;
            8'd57:  zeta_lut = 24'd354605;  8'd58:  zeta_lut = 24'd525732;  8'd59:  zeta_lut = 24'd378077;  8'd60:  zeta_lut = 24'd255146;
            8'd61:  zeta_lut = 24'd332912;  8'd62:  zeta_lut = 24'd209121;  8'd63:  zeta_lut = 24'd213988;  8'd64:  zeta_lut = 24'd424367;
            8'd65:  zeta_lut = 24'd212217;  8'd66:  zeta_lut = 24'd360980;  8'd67:  zeta_lut = 24'd343160;  8'd68:  zeta_lut = 24'd406214;
            8'd69:  zeta_lut = 24'd552885;  8'd70:  zeta_lut = 24'd205096;  8'd71:  zeta_lut = 24'd105267;  8'd72:  zeta_lut = 24'd395893;
            8'd73:  zeta_lut = 24'd333010;  8'd74:  zeta_lut = 24'd336886;  8'd75:  zeta_lut = 24'd185854;  8'd76:  zeta_lut = 24'd564415;
            8'd77:  zeta_lut = 24'd531742;  8'd78:  zeta_lut = 24'd224302;  8'd79:  zeta_lut = 24'd378943;  8'd80:  zeta_lut = 24'd262102;
            8'd81:  zeta_lut = 24'd229617;  8'd82:  zeta_lut = 24'd321151;  8'd83:  zeta_lut = 24'd349479;  8'd84:  zeta_lut = 24'd421258;
            8'd85:  zeta_lut = 24'd241774;  8'd86:  zeta_lut = 24'd297298;  8'd87:  zeta_lut = 24'd274577;  8'd88:  zeta_lut = 24'd302325;
            8'd89:  zeta_lut = 24'd254247;  8'd90:  zeta_lut = 24'd231998;  8'd91:  zeta_lut = 24'd314845;  8'd92:  zeta_lut = 24'd376114;
            8'd93:  zeta_lut = 24'd422933;  8'd94:  zeta_lut = 24'd236378;  8'd95:  zeta_lut = 24'd342045;  8'd96:  zeta_lut = 24'd264319;
            8'd97:  zeta_lut = 24'd501509;  8'd98:  zeta_lut = 24'd406085;  8'd99:  zeta_lut = 24'd410712;  8'd100: zeta_lut = 24'd327855;
            8'd101: zeta_lut = 24'd295096;  8'd102: zeta_lut = 24'd220967;  8'd103: zeta_lut = 24'd336465;  8'd104: zeta_lut = 24'd408331;
            8'd105: zeta_lut = 24'd240213;  8'd106: zeta_lut = 24'd532059;  8'd107: zeta_lut = 24'd341901;  8'd108: zeta_lut = 24'd183842;
            8'd109: zeta_lut = 24'd319724;  8'd110: zeta_lut = 24'd480608;  8'd111: zeta_lut = 24'd270381;  8'd112: zeta_lut = 24'd206263;
            8'd113: zeta_lut = 24'd242699;  8'd114: zeta_lut = 24'd219754;  8'd115: zeta_lut = 24'd354512;  8'd116: zeta_lut = 24'd353634;
            8'd117: zeta_lut = 24'd525741;  8'd118: zeta_lut = 24'd333947;  8'd119: zeta_lut = 24'd260589;  8'd120: zeta_lut = 24'd234812;
            8'd121: zeta_lut = 24'd341386;  8'd122: zeta_lut = 24'd552432;  8'd123: zeta_lut = 24'd248434;  8'd124: zeta_lut = 24'd412039;
            8'd125: zeta_lut = 24'd218844;  8'd126: zeta_lut = 24'd244923;  8'd127: zeta_lut = 24'd241940;  default: zeta_lut = 24'd1;
        endcase
    endfunction

endmodule

// --- Butterfly Module ---
module ntt_butterfly_unit (
    input  wire [23:0] u_in,
    input  wire [23:0] v_in,
    input  wire [23:0] zeta,
    output wire [23:0] u_out,
    output wire [23:0] v_out
);
    localparam [23:0] Q = 24'd8380417;

    wire [47:0] mul_raw;
    wire [24:0] red_tmp; // Extra bit for sign/overflow during subtraction
    reg  [23:0] v_zeta;
    wire [24:0] add_res, sub_res;

    assign mul_raw = v_in * zeta;

    // Optimized Solinas Reduction for Dilithium Prime Q = 2^23 - 2^13 + 1
    // High = mul_raw[45:23], Low = mul_raw[22:0]
    // red_tmp = Low - (High << 13) + High
    assign red_tmp = {2'b0, mul_raw[22:0]} - {mul_raw[45:23], 13'b0} + {2'b0, mul_raw[45:23]};

    always @(*) begin
        // Verilog uses 2's complement. If the MSB of our 25-bit wire is 1, it's negative.
        if (red_tmp[24]) 
            v_zeta = red_tmp + Q + Q + Q; // Add Q enough times to make it positive
        else if (red_tmp >= Q)
            v_zeta = red_tmp % Q; // Simple modulo for synthesis
        else
            v_zeta = red_tmp[23:0];
    end

    // Butterfly: u = u + v*zeta, v = u - v*zeta
    assign add_res = u_in + v_zeta;
    assign u_out   = (add_res >= Q) ? (add_res - Q) : add_res[23:0];

    assign sub_res = {1'b0, u_in} + Q - v_zeta;
    assign v_out   = (sub_res >= Q) ? (sub_res - Q) : sub_res[23:0];

endmodule