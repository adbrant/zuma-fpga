from parse_vpr import *
import os

#Import graph from VTR
load_graph('rr_graph.echo')

#Build ZUMA verilog global routing
build_global_routing_verilog('XUMA_custom_generated.v')

#Read all VPR output files
read_BLIF('abc_out.map6.abc.blif')
read_placement('place.p')
read_routing('route.r')
read_netlist('netlist.net')

#Build the bitstream 
build_bitstream('output.hex')


#output a BLIF of the design
#output_blif('out.blif')
