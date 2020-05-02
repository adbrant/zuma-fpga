
module popcount
	(
	clock,
	in,
	out
	);
	input [16-1:0] in;
	output	 [16-1:0] out;

	input clock;

	reg a;

	initial begin
   a = 1'b0;
 	end

	always @ (posedge clock)
	a <= a ^ 1'b1;

	assign out[0] = in[0] & in[1] & in[2] & in[3] & in[4] & in[5] & in[6] & in[7];
	assign out[1] = in[0] | in[1] | in[2] | in[3] | in[4] | in[5] | in[6] | a;

endmodule