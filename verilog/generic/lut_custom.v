/*
#	ZUMA Open FPGA Overlay
#	Alex Brant
#	Email: alex.d.brant@gmail.com
#	2012
#	LUTRAM wrapper
*/

/* These luts are used for building configurable muxes.*/

`include "define.v"
`include "def_generated.v"
`include "primitives.v"

module lut_custom #(

	parameter used = 0,
	parameter LUT_MASK={2**K{1'b0}}

) (
	a,
	d,
	dpra,
	clk,
	we,
	dpo);


input [ZUMA_LUT_SIZE-1 : 0] a;
input [0 : 0] d;
input [ZUMA_LUT_SIZE-1 : 0] dpra;
input clk;
input we;
output  dpo;

wire lut_output;

//no plattform. just for a verificational build.
`ifdef ZUMA_VERIFICATION

	generate
		if( used == 0)
			//nothing will be generated and connected
		else
			//we generate a lut
			LUT_K #(
				.K(ZUMA_LUT_SIZE),
				.LUT_MASK(LUT_MASK)
				) verification_lut  (
				.in(dpra),
				.out(lut_output)
				);
	endgenerate

`elsif  PLATFORM_XILINX

	lut_xilinx LUT (
	.a(a), // input [5 : 0] a
	.d(d), // input [0 : 0] d
	.dpra( dpra ), // input [5 : 0] dpra
	.clk(clk), // input clk
	.we(we), // input we
	.dpo( lut_output ));

`elsif PLATFORM_ALTERA

	 SDPR LUT(
	.clock(clk),
	.data(d),
	.rdaddress(dpra),
	.wraddress(a),
	.wren(we),
	.q(lut_output));

`endif



`ifdef SIMULATION //X'd inputs will break the simulation
assign dpo = (lut_output === 1'bx) ? 0 : lut_output ;
`else
assign dpo = lut_output;
`endif


endmodule
