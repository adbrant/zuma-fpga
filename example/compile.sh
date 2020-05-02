#!/usr/bin/python2.7


import sys
from plumbum import local
import imp
import argparse

##compile a ZUMA overlay and a bitstream for the given circuit.
#@param circuitFileName Path to the user circuit file
def compileZUMA(circuitFileName,zumaConfigFileName,clockName):

    #load the user circuit path
    circuitPath = local.path(circuitFileName)
    if not circuitPath.exists():
        print 'Can\'t load file: ' + str(circuitPath)
        sys.exit(1)

    #get the path of this file to extract the zuma base dir.
    zumaExampleDir = local.path(__file__).parent
    zumaDir = zumaExampleDir.parent
    libDir = zumaDir / 'source'

    #add the zuma dir as well as the cwd to the python path variable
    #cwd is used for import the zuma config
    sys.path.insert(0, str(libDir))
    sys.path.insert(0, str(zumaDir))
    sys.path.insert(0, str(local.cwd))

    #load the vtr dir (and optinal yosys dir)
    import toolpaths
    vtrDir = local.path(toolpaths.vtrDir)

    #if the zuma config file is not given just import one from the first
    #match in the sys path. cwd is also in there
    if zumaConfigFileName is None:
        import zuma_config
    else:
        zuma_config = imp.load_source('zuma_config', zumaConfigFileName)

    #start Synthesizing
    print 'Synthesizing ' + str(circuitPath) + ' to ZUMA'

    import CompileUtils

    #create the build forlder,copy necessary scripts, then
    #run odin, abc and vpr
    CompileUtils.createBuildDirAndRunVpr(vtrDir,libDir,circuitPath,zuma_config.params.vprVersion,clockName)

    #run zuma
    CompileUtils.runZUMA(zuma_config.params.vprVersion,False)
    CompileUtils.createMif(zumaExampleDir)
    CompileUtils.checkEquivalence(vtrDir,zuma_config.params.vprVersion)
    CompileUtils.displayRessourceUsage()

    #verify the generated verilog description
    if zuma_config.params.verifyOverlay:
        #load the yosys path
        yosysDir = local.path(toolpaths.yosysDir)
        CompileUtils.checkOverlayEquivalence(zumaDir,yosysDir,vtrDir,zuma_config.params.packedOverlay)

    #if vpr8 timing back annotation is used, run a zuma second time
    if zuma_config.params.vprAnnotation:
        CompileUtils.runVpr(vtrDir,zuma_config.params.vprVersion,True)
        CompileUtils.runZUMA(zuma_config.params.vprVersion,True)


def main():


    #parse the arguments

    argumentParser = argparse.ArgumentParser(prog='compile',
                                             usage='%(prog)s [options] circuit.v',
                                             description='The ZUMA circuit compiler. Compiles a ZUMA overlay and a bitstream for the given circuit')

    argumentParser.add_argument('circuitFileName',
                                metavar='circuit.v',
                                type=str,
                                help='The path to verilog circuit file you want to compile a configuration for your virtual fpga')

    argumentParser.add_argument('-config',
                                '--config',
                                action='store',
                                type=str,
                                help='The path to a zuma config file. If not given ZUMA search in your current location')

    argumentParser.add_argument('-clock',
                                '--clock',
                                action='store',
                                type=str,
                                help='The name of the clock in the circuit file')

    arguments = argumentParser.parse_args()

    circuitFileName = arguments.circuitFileName
    clockName = arguments.clock
    configFileName = arguments.config

    #start the compilation
    compileZUMA(circuitFileName,configFileName,clockName)

if __name__ == '__main__':
    main()
