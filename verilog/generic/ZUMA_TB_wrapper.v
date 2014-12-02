/*
#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	Test bench wrapper
*/
module ZUMA_TB_wrapper 
(	
	reset,
	write,
	inputs,
	outputs,
	cfg,
	clk);
	
	input  write;
	input reset;
	output [15:0] outputs;
	input [15:0] inputs;
	input  clk;

	reg [31:0] address;
	
	reg [31:0] address_in;
	
	output [31:0] cfg; 
	
	wire [31:0] cfg_in;
	always @ (posedge clk)
	  begin : COUNTER
	  
	  address_in <= address;
	   if (reset) begin
		 address <=  32'b0;
	   end else if (write) begin
		 address <=  address + 1;
		 end else begin
		 address <= address;
	   end		
	end
	
	
	
	generate
	genvar i;
	for(i=0;i<32;i=i+1)
	begin: reverse
	assign cfg_in[31-i] = cfg[i];
	end
	endgenerate
	
	init_config config_data (
	.address(address),
	.clock(clk),
	.q(cfg) );

	ZUMA_custom_generated XUM
	(
	.clk(clk),
	.fpga_inputs(inputs),
	.fpga_outputs(outputs),
	.config_data(cfg_in),
	.config_en(write),
	.progress(),
	.config_addr(address_in));

endmodule