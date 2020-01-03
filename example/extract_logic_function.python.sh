#!/usr/bin/python2.7
from plumbum import local

def extractLogicFuntion(bitstreamFile,outputBlifFile,hasClock,hasReset):

    #get the path of this file to extract the zuma base dir.
    zumaExampleDir = local.path(__file__).parent
    zumaDir = zumaExampleDir.parent
    libDir = zumaDir / 'source'

    #add the zuma dir as well as the cwd to the python path variable
    #cwd is used for import the zuma config
    sys.path.insert(0, str(libDir))
    sys.path.insert(0, str(zumaDir))
    sys.path.insert(0, str(local.cwd))

    #import the cwd zuma config
    import zuma_config

    #load the vtr dir (and optinal yosys dir)
    import toolpaths
    vtrDir = local.path(toolpaths.vtrDir)

    #create the build folder and copy necessary scripts
    import CompileUtils
    CompileUtils.createBuildFolderAndChDir(libDir)

    #apply a patch needed because of the reverse build
    #the first one is vor vpr > 6 and the second for vpr == 6
    from plumbum.cmd import cp
    cp(str(zumaExampleDir / "dummy_for_extraction.blif"), "./abc_out.blif")
    cp(str(zumaExampleDir / "dummy_for_extraction.blif"), "./clock_fixed.blif")

    #run vpr to create graph.echo
    CompileUtils.runVpr(vtrDir,vprVersion)


    #now run zuma in reverse mode

    graph_file = 'rr_graph.echo'
    verilog_file = 'ZUMA_custom_generated.v'
    blif_file = outputBlifFile
    place_file = 'place.p'
    route_file = 'route.r'
    net_file = 'netlist.net'
    mif_file = bitstreamFile

    maxInputNum = -1

    import ZumaBitToBlif
    ZumaBitToBlif.bitToBlif(graph_file,
              verilog_file,
              blif_file,
              place_file,
              route_file,
              net_file,
              mif_file,
              maxInputNum,
              hasClock,
              hasReset):


def main():

    if len(sys.argv) != 5:
        print "Usage: extract_logic_function bitstream.mif output.blif HasClock HasReset"

    bitstreamFile = sys.argv[1]
    outputBlifFile = sys.argv[2]
    hasClock = sys.argv[3] ==  "True"
    hasReset =  sys.argv[4] ==  "True"

    extractLogicFuntion(bitstreamFile,outputBlifFile,hasClock,hasReset)

if __name__ == '__main__':
    main()
