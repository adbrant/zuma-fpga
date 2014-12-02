/*
#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	Configuration controller (low area, serial write only)
*/
`include "mathmacros.v"

module config_controller
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
	
	wire initiate;
	assign initiate =  (addr_in[0] == 1'b1);
	assign clk_gate = (wren_in == 1'b1) && (count == 0);
	assign progress = config_progress;
	//need to load actual bitstream from off-chip

	// generates the write anable for each tile (or other stage of configuration)
	shiftreg
	#(
	.LENGTH(STAGES)
	) 
	lutmuxconfig_shift
	 (
	.shift_in(initiate) ,
	.clk(clk),
	.wren(clk_gate),
	.data(wren_out),
	.shift_out(done)
	);
		
	always @ (posedge clk)
	  begin : COUNTER
	   if (reset == 1'b1) begin
		 count <=  0;
		 end
	   else if (wren_in == 1'b1) begin
		
		 count <=  count + 1;
	   end
		else begin
		
		 count <=  count;
	   end
		
	end
	
	always @ (posedge clk)
	  begin : COUNTER2
	   if (reset == 1'b1 || (addr_in == 32'b1 && wren_in) || done)  begin
		 config_progress <= 0;
		 end
	   else if (wren_in == 1'b1) begin
		 config_progress <= config_progress + 1;
		
	   end
		else begin
		config_progress <= config_progress;
		
	   end
		
	end
	assign addr_out = count;


endmodule