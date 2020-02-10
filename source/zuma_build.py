#!/usr/bin/env python

import globs

import ReadNetlist
import BuildVerilog
import ReadBlif
import ReadPlacement
import ReadRouting
import BuildBitstream
import InitFpga
import OutputBlif
import Dump
import TimingAnalysisSDF
import ReadSDF
import buildVerificationOverlay
import buildPackedOverlay

import os
import sys

def main ():

    options = sys.argv[1:]

    graph_file = 'rr_graph.xml'
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

    Zuma(verilog_file,
         graph_file,
         blif_file,
         place_file,
         net_file,
         route_file,
         bit_file,
         blif_out_file,
         build_bit)


def Zuma(verilog_file,
         graph_file,
         blif_file,
         place_file,
         net_file,
         route_file,
         bit_file,
         blif_out_file,
         build_bit ):

    globs.init()
    globs.load_params()

    #Import graph from VTR
    InitFpga.load_graph(graph_file)

    #Build ZUMA verilog global routing
    BuildVerilog.build_global_routing_verilog(verilog_file)

    #dump the node graph. textual and graphical
    if globs.params.dumpNodeGraph:
            Dump.dumpGraph('unconfiguredGraph')

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
            Dump.dumpGraph('configuredGraph')

        if globs.params.dumpNodeGraph:
            Dump.dumpTechnologyGraph('mappedGraph')

        #output a BLIF of the design
        OutputBlif.output_blif(blif_out_file)

        #output a verification verilog file
        if globs.params.packedOverlay:
            #build the first for verification and the second as an output overlay
            buildPackedOverlay.buildVerificationOverlay("verificationOverlay.v",True)
            buildPackedOverlay.buildVerificationOverlay("packedOverlay.v",False)
            buildVerificationOverlay.buildVerificationOverlay("verificationOverlayUnfolded.v")
        else:
            buildVerificationOverlay.buildVerificationOverlay("verificationOverlay.v")

        #if we want to parse the sdf file
        if globs.params.sdf:
            ReadSDF.ReadSDF()
            TimingAnalysisSDF.performTimingAnalysis()
            if globs.params.dumpNodeGraph:
                Dump.dumpTechnologyGraph('mappedTimedGraph')


if __name__ == '__main__':
    main()
