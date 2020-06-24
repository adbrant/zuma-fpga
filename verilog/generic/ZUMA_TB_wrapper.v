/*
#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	Test bench wrapper
#
# 	Changes by Tobias Wiersema:
#	- Pulled configuration (counting) logic into the TB to make it self-contained
#   - Adapted for sequential circuits
*/
`include "define.v"
`include "def_generated.v"
module ZUMA_TB_wrapper 
(	
    reset,
    clk,
    inputs,
    outputs
);
    parameter LUT_SIZE   = ZUMA_LUT_SIZE;
    parameter NUM_STAGES = NUM_CONFIG_STAGES;
    
    input clk;
    input reset;    
    input  [NUM_INPUTS-1:0] inputs;
    output [NUM_OUTPUTS-1:0] outputs;

    reg  [31:0] next_address; 
    reg  [31:0] address;
    
    wire [CONFIG_WIDTH-1:0] cfg;    
    wire [CONFIG_WIDTH-1:0] cfg_in;
    
    reg write;
    reg reset_done;
    reg virtual_reset;
    
    // Reprogram the virtual device after a reset
    // Generate all required configuration addresses
    // Reset the virtual device after configuration
    always @ (posedge clk)
    begin : COUNTER
    	// Data fetching required one cycle after address generation
    	// thus we lag the actual configuration address once cycle
        address <= next_address;
        if (reset) begin
        	// Start a new config process
            next_address  <= 32'b0;
            write         <=  1'b1;
            reset_done    <=  1'b0;
            virtual_reset <=  1'b0;
        end else if (write) begin
        	// Generate all addresses until we are done
            next_address <=  next_address + 1;
            if (next_address > (2**LUT_SIZE)*NUM_STAGES) begin
               write <= 1'b0;
            end
        end else if (~reset_done) begin
        	// If write is finished, reset the virtual device once
            virtual_reset <= 1'b1;
            reset_done    <= 1'b1;
        end else if (virtual_reset) begin
        	// Pull back the virtual reset, device should be running now
            virtual_reset <= 1'b0;
        end else begin
        	// No-op, we are done.
            next_address <= next_address;
        end     
    end 
    
    // Reverse the retrieved config data, as the
    // overlay requires it in reverse direction as stored
    generate
        genvar i;
        for (i = 0; i < CONFIG_WIDTH; i = i + 1)
        begin: reverse
           assign cfg_in[CONFIG_WIDTH-1-i] = cfg[i];
        end
    endgenerate
    
    // Fetch config data for next address
    fixed_config #(.LUT_SIZE(LUT_SIZE), .NUM_STAGES(NUM_STAGES)) config_data (
        .address_in(next_address),
        .clock(clk),
        .q(cfg) 
    );

    // Include the actual overlay
    ZUMA_custom_generated XUM (
        .clk(clk),
        .fpga_inputs(inputs),
        .fpga_outputs(outputs),
        .config_data(cfg_in),
        .config_en(write),
        .progress(),
        .config_addr(address),
        .clk2(clk),
        .ffrst(virtual_reset)
    );

endmodule
