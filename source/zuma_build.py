#!/usr/bin/env python
#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	Command line interface

from parse_vpr import *
import os

import sys

#infolder = sys.argv[1]
#outfolder =  sys.argv[2]
options = sys.argv[1:]


graph_file = 'rr_graph.echo'
verilog_file = 'ZUMA_custom_generated.v'
blif_file = 'abc_out.blif'
place_file = 'place.p'
route_file = 'route.r'
net_file = 'netlist.net'
bit_file = 'output.hex'
blif_out_file = 'zuma_out.blif'


build_bit = False
for i in range(len(options)/2):
	id = options[i*2]
	val = options[i*2+1]
	if id == '-graph_file':
		graph_file = val
	if id == '-verilog_file':
		verilog_file = val
	if id == '-blif_file':
		blif_file = val
	if id == '-place_file':
		place_file = val
	if id == '-net_file':
		net_file = val
	if id == '-route_file':
		route_file = val
	if id == '-bit_file':
		build_bit = True
		bit_file = val
	if id == '-blif_out_file':
		blif_out_file = val
		
load_params()
		
#Import graph from VTR
load_graph(graph_file)

#Build ZUMA verilog global routing
build_global_routing_verilog(verilog_file)
if build_bit:
	#Read all VPR output files
	read_BLIF(blif_file)
	read_placement(place_file)
	read_routing(route_file)
	read_netlist(net_file)

	#Build the bitstream 
	build_bitstream(bit_file)


	#output a BLIF of the design
	output_blif('zuma_out.blif')


