#!/usr/bin/env python

import globs
globs.init()

import BuildVerilog

import ParseBitstream

import InitFpga
import OutputBlif
import Dump

import os

import sys


options = sys.argv[1:]

graph_file = 'rr_graph.echo'
verilog_file = 'ZUMA_custom_generated.v'
blif_file = 'zuma_out_revrese.blif'
place_file = 'place.p'
route_file = 'route.r'
net_file = 'netlist.net'
mif_file = '../output.hex.mif'

globs.clock = False
globs.reset = False
globs.maxInputNum = -1


for i in range(len(options)/2):
    id = options[i*2]
    val = options[i*2+1]
    if id == '-graph_file':
        graph_file = val
    if id == '-verilog_file':
        verilog_file = val
    if id == '-blif_file':
        blif_file = val

    if id == '-mif_file':
        mif_file = val
    if id == '-blif_out_file':
        blif_out_file = val

    if id == '-use_reset':
        if val == 'True':
            globs.reset = True

    if id == '-use_clock':
        if val == 'True':
            globs.clock = True

    if id == '-used_inputs_number':
        globs.maxInputNum = (int(val)-1)

globs.load_params()

#signal reverse build
globs.bit_to_blif = True

#Import graph from VTR
InitFpga.load_graph(graph_file)

#Build ZUMA verilog global routing
BuildVerilog.build_global_routing_verilog(verilog_file)

ParseBitstream.parseBitstream(mif_file)

Dump.dumpGraph('revereseGraph')
#output a BLIF of the design
OutputBlif.output_blif(blif_file)
