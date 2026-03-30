/*
This module is the last layer to check if the signature is valid or not.

Coded By:
Kamal Raj (kamal.raj@ntu.edu.sg)
*/
module comparator (
    input [255:0] data_c,
    input [255:0] data_c2,
    output signature_valid
);

assign signature_valid = (data_c == data_c2)? 1 : 0;

endmodule