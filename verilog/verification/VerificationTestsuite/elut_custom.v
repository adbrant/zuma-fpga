/*
#	ZUMA Open FPGA Overlay
#	Alex Brant
#	Email: alex.d.brant@gmail.com
#	2012
#	LUTRAM wrapper
*/

`include "def_generated.v"

module elut_custom #(

	parameter used = 0,
	parameter [0:2**6-1] LUT_MASK={2**6{1'b0}}

) (
	a,
	d,
	dpra,
	clk,
	we,
	dpo,
	qdpo_clk,
	qdpo_rst,
	qdpo);


input [5 : 0] a;
input [0 : 0] d;
input [5 : 0] dpra;
input clk;
input we;
input qdpo_clk;
input qdpo_rst;
output dpo;
output qdpo;

wire lut_output;
wire lut_registered_output;

//no plattform. just for a verificational build.

//	generate
//		if( used == 1)
			//we generate a lut and a latch
			LUT_K #(
				.K(6),
				.LUT_MASK(LUT_MASK)
				) verification_lut2  (
				.in(dpra),
				.out(lut_output)
				);

			DFF #(
	        .INITIAL_VALUE(1'b0)
	    ) verification_latch  (
	        .D(lut_output),
	        .Q(lut_registered_output),
	        .clock(qdpo_clk)
	    );


//	endgenerate


assign dpo  = lut_output;
assign qdpo = lut_registered_output;

endmodule
