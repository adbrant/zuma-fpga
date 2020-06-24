
module popcount
	(
	in,
	out
	);
	input [0:0] in;
	output	 [0:0] out;

	assign out[0] = ~in[0];
endmodule
