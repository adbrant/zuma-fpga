/*
#	ZUMA Open FPGA Overlay
#	Alex Brant
#	Email: alex.d.brant@gmail.com
#	2012
#	LUTRAM wrapper
*/

/* These luts are used for building configurable muxes.*/

`include "def_generated.v"

module lut_custom #(

	parameter used = 0,
	parameter [0:2**6-1] LUT_MASK={2**6{1'b0}}

) (
	a,
	d,
	dpra,
	clk,
	we,
	dpo);


input [5 : 0] a;
input [0 : 0] d;
input [5 : 0] dpra;
input clk;
input we;
output  dpo;

wire lut_output;

//no plattform. just for a verificational build.

//	generate
//		if( used == 1)
			//we generate a lut
			LUT_K #(
				.K(6),
				.LUT_MASK(LUT_MASK)
				) verification_lut  (
				.in(dpra),
				.out(lut_output)
				);
//	endgenerate

assign dpo = lut_output;


endmodule
