
    module top_module
    (
        fpga_inputs,
        fpga_outputs
    );
    input [8-1:0] fpga_inputs;
output [8-1:0] fpga_outputs;
    ZUMA_custom_generated #() zuma
    (
    .clk(1'b0),
    .fpga_inputs(fpga_inputs),
    .fpga_outputs(fpga_outputs),
    .config_data({32{1'b0}}),
    .config_en(1'b0),
    //.progress(),
    .config_addr({32{1'b0}}),
    .clk2(1'b0),
    .ffrst(1'b0)
    );

    endmodule
    