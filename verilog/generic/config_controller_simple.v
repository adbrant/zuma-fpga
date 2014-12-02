/*
#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	Configuration controller (addressable)
*/
`include "mathmacros.v"

module config_controller_simple
#(
	parameter WIDTH = 40,
	parameter STAGES = 16,
	parameter LUTSIZE = 6

 )
	
(
clk,
reset,
wren_in,
wren_out,
addr_in,
addr_out,
progress,
done

);

	input clk;
	input reset;
	input wren_in;
	output [ STAGES-1:0] wren_out;
	output [ LUTSIZE-1:0] addr_out;
	
	input [31:0] addr_in;
	
	output done;
	output [15:0] progress;
	wire clk_gate;
	reg [ LUTSIZE-1:0] count;
	reg [15:0] config_progress; 
	
	generate
	genvar stage;
	for(stage = 0; stage < STAGES; stage = stage+1) begin: stage_m
	assign wren_out[stage] = ((addr_in >> LUTSIZE) == stage) && wren_in;
	end
	endgenerate
	
	

	assign addr_out = addr_in[LUTSIZE-1:0];


endmodule