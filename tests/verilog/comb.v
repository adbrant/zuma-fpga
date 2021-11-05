
module popcount 
	(
	in,
	out
	);
	input [16-1:0] in;
	output	 [16-1:0] out;

	assign out[0] = in[0] & in[1] & in[2] & in[3] & in[4] & in[5] & in[6] & in[7];
	assign out[1] = in[0] | in[1] | in[2] | in[3] | in[4] | in[5] | in[6] | in[7];
endmodule
