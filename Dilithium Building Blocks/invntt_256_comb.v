module invntt_256_comb(
    input  wire [6143:0] poly_in,
    output wire [6143:0] poly_out
);

    function signed [23:0] get_zeta;
        input [7:0] index;
        case(index)
            8'd0:   get_zeta = 24'd0;
            8'd1:   get_zeta = 24'd25847;
            8'd2:   get_zeta = -24'd2608894;
            8'd3:   get_zeta = -24'd518909;
            8'd4:   get_zeta = 24'd237124;
            8'd5:   get_zeta = -24'd777960;
            8'd6:   get_zeta = -24'd876248;
            8'd7:   get_zeta = 24'd466468;
            8'd8:   get_zeta = 24'd1826347;
            8'd9:   get_zeta = 24'd2353451;
            8'd10:  get_zeta = -24'd359251;
            8'd11:  get_zeta = -24'd2091905;
            8'd12:  get_zeta = 24'd3119733;
            8'd13:  get_zeta = -24'd2884855;
            8'd14:  get_zeta = 24'd3111497;
            8'd15:  get_zeta = 24'd2680103;
            8'd16:  get_zeta = 24'd2725464;
            8'd17:  get_zeta = 24'd1024112;
            8'd18:  get_zeta = -24'd1079900;
            8'd19:  get_zeta = 24'd3585928;
            8'd20:  get_zeta = -24'd549488;
            8'd21:  get_zeta = -24'd1119584;
            8'd22:  get_zeta = 24'd2619752;
            8'd23:  get_zeta = -24'd2108549;
            8'd24:  get_zeta = -24'd2118186;
            8'd25:  get_zeta = -24'd3859737;
            8'd26:  get_zeta = -24'd1399561;
            8'd27:  get_zeta = -24'd3277672;
            8'd28:  get_zeta = 24'd1757237;
            8'd29:  get_zeta = -24'd19422;
            8'd30:  get_zeta = 24'd4010497;
            8'd31:  get_zeta = 24'd280005;
            8'd32:  get_zeta = 24'd2706023;
            8'd33:  get_zeta = 24'd95776;
            8'd34:  get_zeta = 24'd3077325;
            8'd35:  get_zeta = 24'd3530437;
            8'd36:  get_zeta = -24'd1661693;
            8'd37:  get_zeta = -24'd3592148;
            8'd38:  get_zeta = -24'd2537516;
            8'd39:  get_zeta = 24'd3915439;
            8'd40:  get_zeta = -24'd3861115;
            8'd41:  get_zeta = -24'd3043716;
            8'd42:  get_zeta = 24'd3574422;
            8'd43:  get_zeta = -24'd2867647;
            8'd44:  get_zeta = 24'd3539968;
            8'd45:  get_zeta = -24'd300467;
            8'd46:  get_zeta = 24'd2348700;
            8'd47:  get_zeta = -24'd539299;
            8'd48:  get_zeta = -24'd1699267;
            8'd49:  get_zeta = -24'd1643818;
            8'd50:  get_zeta = 24'd3505694;
            8'd51:  get_zeta = -24'd3821735;
            8'd52:  get_zeta = 24'd3507263;
            8'd53:  get_zeta = -24'd2140649;
            8'd54:  get_zeta = -24'd1600420;
            8'd55:  get_zeta = 24'd3699596;
            8'd56:  get_zeta = 24'd811944;
            8'd57:  get_zeta = 24'd531354;
            8'd58:  get_zeta = 24'd954230;
            8'd59:  get_zeta = 24'd3881043;
            8'd60:  get_zeta = 24'd3900724;
            8'd61:  get_zeta = -24'd2556880;
            8'd62:  get_zeta = 24'd2071892;
            8'd63:  get_zeta = -24'd2797779;
            8'd64:  get_zeta = -24'd3930395;
            8'd65:  get_zeta = -24'd1528703;
            8'd66:  get_zeta = -24'd3677745;
            8'd67:  get_zeta = -24'd3041255;
            8'd68:  get_zeta = -24'd1452451;
            8'd69:  get_zeta = 24'd3475950;
            8'd70:  get_zeta = 24'd2176455;
            8'd71:  get_zeta = -24'd1585221;
            8'd72:  get_zeta = -24'd1257611;
            8'd73:  get_zeta = 24'd1939314;
            8'd74:  get_zeta = -24'd4083598;
            8'd75:  get_zeta = -24'd1000202;
            8'd76:  get_zeta = -24'd3190144;
            8'd77:  get_zeta = -24'd3157330;
            8'd78:  get_zeta = -24'd3632928;
            8'd79:  get_zeta = 24'd126922;
            8'd80:  get_zeta = 24'd3412210;
            8'd81:  get_zeta = -24'd983419;
            8'd82:  get_zeta = 24'd2147896;
            8'd83:  get_zeta = 24'd2715295;
            8'd84:  get_zeta = -24'd2967645;
            8'd85:  get_zeta = -24'd3693493;
            8'd86:  get_zeta = -24'd411027;
            8'd87:  get_zeta = -24'd2477047;
            8'd88:  get_zeta = -24'd671102;
            8'd89:  get_zeta = -24'd1228525;
            8'd90:  get_zeta = -24'd22981;
            8'd91:  get_zeta = -24'd1308169;
            8'd92:  get_zeta = -24'd381987;
            8'd93:  get_zeta = 24'd1349076;
            8'd94:  get_zeta = 24'd1852771;
            8'd95:  get_zeta = -24'd1430430;
            8'd96:  get_zeta = -24'd3343383;
            8'd97:  get_zeta = 24'd264944;
            8'd98:  get_zeta = 24'd508951;
            8'd99:  get_zeta = 24'd3097992;
            8'd100: get_zeta = 24'd44288;
            8'd101: get_zeta = -24'd1100098;
            8'd102: get_zeta = 24'd904516;
            8'd103: get_zeta = 24'd3958618;
            8'd104: get_zeta = -24'd3724342;
            8'd105: get_zeta = -24'd8578;
            8'd106: get_zeta = 24'd1653064;
            8'd107: get_zeta = -24'd3249728;
            8'd108: get_zeta = 24'd2389356;
            8'd109: get_zeta = -24'd210977;
            8'd110: get_zeta = 24'd759969;
            8'd111: get_zeta = -24'd1316856;
            8'd112: get_zeta = 24'd189548;
            8'd113: get_zeta = -24'd3553272;
            8'd114: get_zeta = 24'd3159746;
            8'd115: get_zeta = -24'd1851402;
            8'd116: get_zeta = -24'd2409325;
            8'd117: get_zeta = -24'd177440;
            8'd118: get_zeta = 24'd1315589;
            8'd119: get_zeta = 24'd1341330;
            8'd120: get_zeta = 24'd1285669;
            8'd121: get_zeta = -24'd1584928;
            8'd122: get_zeta = -24'd812732;
            8'd123: get_zeta = -24'd1439742;
            8'd124: get_zeta = -24'd3019102;
            8'd125: get_zeta = -24'd3881060;
            8'd126: get_zeta = -24'd3628969;
            8'd127: get_zeta = 24'd3839961;
            8'd128: get_zeta = 24'd2091667;
            8'd129: get_zeta = 24'd3407706;
            8'd130: get_zeta = 24'd2316500;
            8'd131: get_zeta = 24'd3817976;
            8'd132: get_zeta = -24'd3342478;
            8'd133: get_zeta = 24'd2244091;
            8'd134: get_zeta = -24'd2446433;
            8'd135: get_zeta = -24'd3562462;
            8'd136: get_zeta = 24'd266997;
            8'd137: get_zeta = 24'd2434439;
            8'd138: get_zeta = -24'd1235728;
            8'd139: get_zeta = 24'd3513181;
            8'd140: get_zeta = -24'd3520352;
            8'd141: get_zeta = -24'd3759364;
            8'd142: get_zeta = -24'd1197226;
            8'd143: get_zeta = -24'd3193378;
            8'd144: get_zeta = 24'd900702;
            8'd145: get_zeta = 24'd1859098;
            8'd146: get_zeta = 24'd909542;
            8'd147: get_zeta = 24'd819034;
            8'd148: get_zeta = 24'd495491;
            8'd149: get_zeta = -24'd1613174;
            8'd150: get_zeta = -24'd43260;
            8'd151: get_zeta = -24'd522500;
            8'd152: get_zeta = -24'd655327;
            8'd153: get_zeta = -24'd3122442;
            8'd154: get_zeta = 24'd2031748;
            8'd155: get_zeta = 24'd3207046;
            8'd156: get_zeta = -24'd3556995;
            8'd157: get_zeta = -24'd525098;
            8'd158: get_zeta = -24'd768622;
            8'd159: get_zeta = -24'd3595838;
            8'd160: get_zeta = 24'd342297;
            8'd161: get_zeta = 24'd286988;
            8'd162: get_zeta = -24'd2437823;
            8'd163: get_zeta = 24'd4108315;
            8'd164: get_zeta = 24'd3437287;
            8'd165: get_zeta = -24'd3342277;
            8'd166: get_zeta = 24'd1735879;
            8'd167: get_zeta = 24'd203044;
            8'd168: get_zeta = 24'd2842341;
            8'd169: get_zeta = 24'd2691481;
            8'd170: get_zeta = -24'd2590150;
            8'd171: get_zeta = 24'd1265009;
            8'd172: get_zeta = 24'd4055324;
            8'd173: get_zeta = 24'd1247620;
            8'd174: get_zeta = 24'd2486353;
            8'd175: get_zeta = 24'd1595974;
            8'd176: get_zeta = -24'd3767016;
            8'd177: get_zeta = 24'd1250494;
            8'd178: get_zeta = 24'd2635921;
            8'd179: get_zeta = -24'd3548272;
            8'd180: get_zeta = -24'd2994039;
            8'd181: get_zeta = 24'd1869119;
            8'd182: get_zeta = 24'd1903435;
            8'd183: get_zeta = -24'd1050970;
            8'd184: get_zeta = -24'd1333058;
            8'd185: get_zeta = 24'd1237275;
            8'd186: get_zeta = -24'd3318210;
            8'd187: get_zeta = -24'd1430225;
            8'd188: get_zeta = -24'd451100;
            8'd189: get_zeta = 24'd1312455;
            8'd190: get_zeta = 24'd3306115;
            8'd191: get_zeta = -24'd1962642;
            8'd192: get_zeta = -24'd1279661;
            8'd193: get_zeta = 24'd1917081;
            8'd194: get_zeta = -24'd2546312;
            8'd195: get_zeta = -24'd1374803;
            8'd196: get_zeta = 24'd1500165;
            8'd197: get_zeta = 24'd777191;
            8'd198: get_zeta = 24'd2235880;
            8'd199: get_zeta = 24'd3406031;
            8'd200: get_zeta = -24'd542412;
            8'd201: get_zeta = -24'd2831860;
            8'd202: get_zeta = -24'd1671176;
            8'd203: get_zeta = -24'd1846953;
            8'd204: get_zeta = -24'd2584293;
            8'd205: get_zeta = -24'd3724270;
            8'd206: get_zeta = 24'd594136;
            8'd207: get_zeta = -24'd3776993;
            8'd208: get_zeta = -24'd2013608;
            8'd209: get_zeta = 24'd2432395;
            8'd210: get_zeta = 24'd2454455;
            8'd211: get_zeta = -24'd164721;
            8'd212: get_zeta = 24'd1957272;
            8'd213: get_zeta = 24'd3369112;
            8'd214: get_zeta = 24'd185531;
            8'd215: get_zeta = -24'd1207385;
            8'd216: get_zeta = -24'd3183426;
            8'd217: get_zeta = 24'd162844;
            8'd218: get_zeta = 24'd1616392;
            8'd219: get_zeta = 24'd3014001;
            8'd220: get_zeta = 24'd810149;
            8'd221: get_zeta = 24'd1652634;
            8'd222: get_zeta = -24'd3694233;
            8'd223: get_zeta = -24'd1799107;
            8'd224: get_zeta = -24'd3038916;
            8'd225: get_zeta = 24'd3523897;
            8'd226: get_zeta = 24'd3866901;
            8'd227: get_zeta = 24'd269760;
            8'd228: get_zeta = 24'd2213111;
            8'd229: get_zeta = -24'd975884;
            8'd230: get_zeta = 24'd1717735;
            8'd231: get_zeta = 24'd472078;
            8'd232: get_zeta = -24'd426683;
            8'd233: get_zeta = 24'd1723600;
            8'd234: get_zeta = -24'd1803090;
            8'd235: get_zeta = 24'd1910376;
            8'd236: get_zeta = -24'd1667432;
            8'd237: get_zeta = -24'd1104333;
            8'd238: get_zeta = -24'd260646;
            8'd239: get_zeta = -24'd3833893;
            8'd240: get_zeta = -24'd2939036;
            8'd241: get_zeta = -24'd2235985;
            8'd242: get_zeta = -24'd420899;
            8'd243: get_zeta = -24'd2286327;
            8'd244: get_zeta = 24'd183443;
            8'd245: get_zeta = -24'd976891;
            8'd246: get_zeta = 24'd1612842;
            8'd247: get_zeta = -24'd3545687;
            8'd248: get_zeta = -24'd554416;
            8'd249: get_zeta = 24'd3919660;
            8'd250: get_zeta = -24'd48306;
            8'd251: get_zeta = -24'd1362209;
            8'd252: get_zeta = 24'd3937738;
            8'd253: get_zeta = 24'd1400424;
            8'd254: get_zeta = -24'd846154;
            8'd255: get_zeta = 24'd1776782;
            default: get_zeta = 24'd0;
        endcase
    endfunction

    wire signed [23:0] F_INV_MONT;
    assign F_INV_MONT = 24'd41978; 

    wire [6143:0] s0, s1, s2, s3, s4, s5, s6, s7, s8;
    assign s0 = poly_in;

    genvar start, j, k;

    generate
        for (start = 0; start < 256; start = start + 2) begin : s1_loop
            butterfly_inv b1 (
                .a_j(s0[24*start +: 24]), .a_j_len(s0[24*(start+1) +: 24]),
                .zeta(-get_zeta(255 - (1 + start/2))),
                .out_j(s1[24*start +: 24]), .out_j_len(s1[24*(start+1) +: 24])
            );
        end

        for (start = 0; start < 256; start = start + 4) begin : s2_group
            for (j = 0; j < 2; j = j + 1) begin : s2_bfly
                butterfly_inv b2 (
                    .a_j(s1[24*(start+j) +: 24]), .a_j_len(s1[24*(start+j+2) +: 24]),
                    .zeta(-get_zeta(255 - (2 + start/4))),
                    .out_j(s2[24*(start+j) +: 24]), .out_j_len(s2[24*(start+j+2) +: 24])
                );
            end
        end

        for (start = 0; start < 256; start = start + 8) begin : s3_group
            for (j = 0; j < 4; j = j + 1) begin : s3_bfly
                butterfly_inv b3 (
                    .a_j(s2[24*(start+j) +: 24]), .a_j_len(s2[24*(start+j+4) +: 24]),
                    .zeta(-get_zeta(255 - (4 + start/8))),
                    .out_j(s3[24*(start+j) +: 24]), .out_j_len(s3[24*(start+j+4) +: 24])
                );
            end
        end

        for (start = 0; start < 256; start = start + 16) begin : s4_group
            for (j = 0; j < 8; j = j + 1) begin : s4_bfly
                butterfly_inv b4 (
                    .a_j(s3[24*(start+j) +: 24]), .a_j_len(s3[24*(start+j+8) +: 24]),
                    .zeta(-get_zeta(255 - (8 + start/16))),
                    .out_j(s4[24*(start+j) +: 24]), .out_j_len(s4[24*(start+j+8) +: 24])
                );
            end
        end

        for (start = 0; start < 256; start = start + 32) begin : s5_group
            for (j = 0; j < 16; j = j + 1) begin : s5_bfly
                butterfly_inv b5 (
                    .a_j(s4[24*(start+j) +: 24]), .a_j_len(s4[24*(start+j+16) +: 24]),
                    .zeta(-get_zeta(255 - (16 + start/32))),
                    .out_j(s5[24*(start+j) +: 24]), .out_j_len(s5[24*(start+j+16) +: 24])
                );
            end
        end

        for (start = 0; start < 256; start = start + 64) begin : s6_group
            for (j = 0; j < 32; j = j + 1) begin : s6_bfly
                butterfly_inv b6 (
                    .a_j(s5[24*(start+j) +: 24]), .a_j_len(s5[24*(start+j+32) +: 24]),
                    .zeta(-get_zeta(255 - (32 + start/64))),
                    .out_j(s6[24*(start+j) +: 24]), .out_j_len(s6[24*(start+j+32) +: 24])
                );
            end
        end

        for (start = 0; start < 256; start = start + 128) begin : s7_group
            for (j = 0; j < 64; j = j + 1) begin : s7_bfly
                butterfly_inv b7 (
                    .a_j(s6[24*(start+j) +: 24]), .a_j_len(s6[24*(start+j+64) +: 24]),
                    .zeta(-get_zeta(255 - (64 + start/128))),
                    .out_j(s7[24*(start+j) +: 24]), .out_j_len(s7[24*(start+j+64) +: 24])
                );
            end
        end

        for (j = 0; j < 128; j = j + 1) begin : s8_bfly
            butterfly_inv b8 (
                .a_j(s7[24*j +: 24]), .a_j_len(s7[24*(j+128) +: 24]),
                .zeta(-get_zeta(255 - 128)),
                .out_j(s8[24*j +: 24]), .out_j_len(s8[24*(j+128) +: 24])
            );
        end

        for (k = 0; k < 256; k = k + 1) begin : scale_loop
            wire signed [47:0] unscaled;
            assign unscaled = $signed(s8[24*k +: 24]) * F_INV_MONT;
            montgomery_reduce red_scale (
                .unreduced(unscaled),
                .reduced(poly_out[24*k +: 24])
            );
        end
    endgenerate

endmodule

module butterfly_inv(
    input  wire signed [23:0] a_j,
    input  wire signed [23:0] a_j_len,
    input  wire signed [23:0] zeta,
    output wire signed [23:0] out_j,
    output wire signed [23:0] out_j_len
);
    wire signed [47:0] mult;
    assign out_j = a_j + a_j_len;
    assign mult  = $signed(a_j - a_j_len) * zeta;
    montgomery_reduce mr (.unreduced(mult), .reduced(out_j_len));
endmodule

module montgomery_reduce(
    input  wire signed [47:0] unreduced,
    output wire signed [23:0] reduced
);
    localparam signed [31:0] QINV = 32'd58728449;
    localparam signed [23:0] Q    = 24'd8380417;

    wire signed [31:0] t_low;
    wire signed [63:0] prod_q;
    wire signed [63:0] sub;

    assign t_low  = $signed(unreduced[31:0]) * QINV;
    assign prod_q = $signed(t_low) * Q;
    assign sub    = unreduced - prod_q;
    assign reduced = sub[55:32];
endmodule