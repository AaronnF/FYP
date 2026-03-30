/*
This module is for unpacking one coefficient of ML-DSA signature.
+---------------------------------+
|Designed By:                     | 
|Kamal Raj (kamal.raj@ntu.edu.sg) |
|Research Associate               |
|Temasek Laboratories @ NTU       |
+---------------------------------+
*/

module unpack_z_one_coeff(
    input [17:0] packed_z,
    output [23:0] unpacked_z
);

wire [23:0] Q;
wire [23:0] GAMMA_LIMIT;

assign Q = 8380417;
assign GAMMA_LIMIT = 24'h3ffff - 1;

assign unpacked_z = (packed_z > GAMMA_LIMIT) ? GAMMA_LIMIT + Q - packed_z : GAMMA_LIMIT - packed_z;


endmodule