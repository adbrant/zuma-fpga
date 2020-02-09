#!/usr/bin/env python

import globs
import BuildVerilog

import ParseBitstream

import InitFpga
import OutputBlif
import Dump

import os

import sys

def main():

    options = sys.argv[1:]

    graph_file = 'rr_graph.echo'
    verilog_file = 'ZUMA_custom_generated.v'
    blif_file = 'zuma_out_revrese.blif'
    place_file = 'place.p'
    route_file = 'route.r'
    net_file = 'netlist.net'
    mif_file = '../output.hex.mif'

    maxInputNum = -1
    useClock = False
    useReset = False

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
                useReset = True

        if id == '-use_clock':
            if val == 'True':
                useClock = True

        if id == '-used_inputs_number':
            maxInputNum = (int(val)-1)

    bitToBlif(graph_file,
              verilog_file,
              blif_file,
              place_file,
              route_file,
              net_file,
              mif_file,
              maxInputNum,
              useClock,
              useReset):

def bitToBlif(graph_file,
              verilog_file,
              blif_file,
              place_file,
              route_file,
              net_file,
              mif_file,
              maxInputNum,
              useClock,
              useReset):

    globs.init()
    globs.load_params()

    globs.clock = useClock
    globs.reset = useReset
    globs.maxInputNum = maxInputNum

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

if __name__ == '__main__':
    main()
