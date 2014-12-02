/*
#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	Shift register
*/
`include "mathmacros.v"
// synopsys translate_off
`timescale 1 ps / 1 ps
// synopsys translate_on
module shiftreg 
#(
	parameter LENGTH = 16
 )
(	shift_in,
	clk,
	wren,
	data,
	shift_out);

	input 	  shift_in;
	input clk;
	input wren;

	output reg	[LENGTH-1:0]data;
	output shift_out;
	
	
	 assign shift_out = data[LENGTH-1];
	 
	 
	 always @(posedge clk) begin
	     data = wren ? {data[LENGTH-2:0], shift_in } :  data;
	 end
	 
	 
	
	 
endmodule