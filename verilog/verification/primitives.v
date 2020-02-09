// This is a modified version of the primitive.v of the verilog to routing project:
https://github.com/verilog-to-routing/vtr-verilog-to-routing.
Therefore this file is under MIT License.

//Overivew
//========
//This file contains the verilog primitives produced by VPR's
//post-synthesis netlist writer.
//

//K-input Look-Up Table
module LUT_K #(
    //The Look-up Table size (number of inputs)
    parameter K = 6,

    //The lut mask.
    //Left-most (MSB) bit corresponds to all inputs logic one.
    //Defaults to always false.
    parameter LUT_MASK={2**K{1'b0}}
) (
    input [K-1:0] in,
    output out
);

    assign out = LUT_MASK[in];

endmodule

//D-FlipFlop module
module DFF #(
    parameter INITIAL_VALUE=1'b0
) (
    input clock,
    input D,
    output reg Q
);

    initial begin
        Q <= INITIAL_VALUE;
    end

    always@(posedge clock) begin
        Q <= D;
    end
endmodule

//D-FlipFlop module
module DFF_RESET #(
    parameter INITIAL_VALUE=1'b0
) (
    input clock,
    input D,
    input reset,
    output reg Q
);

    initial begin
        Q <= INITIAL_VALUE;
    end

    always@(posedge clock or posedge reset) begin
        if (reset == 1'b1) begin
            Q <= INITIAL_VALUE;
        end else begin
            Q <= D;
        end

    end
endmodule

//Routing fpga_interconnect module
module fpga_interconnect(
    input datain,
    output dataout
);

    assign dataout = datain;

endmodule


//2-to-1 mux module
module mux(
    input select,
    input x,
    input y,
    output z
);

    assign z = (x & ~select) | (y & select);

endmodule
