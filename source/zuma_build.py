#!/usr/bin/env python
#	ZUMA Open FPGA Overlay
#	Alex Brant
#	Email: alex.d.brant@gmail.com
#	2012
#	Command line interface


import globs
globs.init()

import ReadNetlist
import BuildVerilog
import ReadBlif
import ReadPlacement
import ReadRouting
import BuildBitstream
import InitFpga
import OutputBlif
import Dump
import UCFConstraints
import BuildConectionMatrix
import TimingAnalysisSDF
import TimingAnalysis
import ReadSDF


import os

import sys


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

globs.load_params()

#Import graph from VTR
InitFpga.load_graph(graph_file)

#Build ZUMA verilog global routing
BuildVerilog.build_global_routing_verilog(verilog_file)
if build_bit:
    #Read all VPR output files
    ReadBlif.read_BLIF(blif_file)
    ReadPlacement.read_placement(place_file)
    
    ReadRouting.read_routing(route_file)
    
    ReadNetlist.read_netlist(net_file)

    #Build the bitstream
    BuildBitstream.build_bitstream(bit_file)

    #dump the node graph. textual and graphical
    if globs.params.dumpNodeGraph:
        Dump.dumpGraph('originGraph')

    if globs.params.dumpNodeGraph:
        Dump.dumpTechnologyGraph('mappedGraph')
    
    #output a BLIF of the design
    OutputBlif.output_blif('zuma_out.blif')

    if globs.params.TimingConstraints:
        #output the ucf timing stuff
        UCFConstraints.CreateUCFConstraints()
        
        #dump the node graph. textual and graphical
        if globs.params.dumpNodeGraph:
            Dump.dumpGraph('constrainGraph')

        #if we want to build the connection matrix
        if globs.params.buildConnectionMatrix:
            BuildConectionMatrix.BuildConnectionMatrix(globs.params.TimingFilename)
            TimingAnalysis.performTimingAnalysis()

    #if we want to parse the sdf file
    if globs.params.sdf:
        ReadSDF.ReadSDF()
        TimingAnalysisSDF.performTimingAnalysis()
        if globs.params.dumpNodeGraph:
            Dump.dumpTechnologyGraph('mappedTimedGraph')

