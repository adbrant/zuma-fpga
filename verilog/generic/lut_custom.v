/*
#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	LUTRAM wrapper
*/
`include "define.v"
`include "def_generated.v"
module lut_custom(
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

`ifdef PLATFORM_XILINX      
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
