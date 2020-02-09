#!/usr/bin/python2.7


import sys
from plumbum import local


##compile a ZUMA overlay and a bitstream for the given circuit.
#@param circuitFileName Path to the user circuit file
def compileZUMA(circuitFileName):

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

    #import the cwd zuma config
    import zuma_config

    #start Synthesizing
    print 'Synthesizing ' + str(circuitPath) + ' to ZUMA'

    import CompileUtils

    #create the build forlder,copy necessary scripts, then
    #run odin, abc and vpr
    CompileUtils.createBuildDirAndRunVpr(vtrDir,libDir,circuitPath,zuma_config.params.vprVersion)

    #run zuma
    CompileUtils.runZUMA(zuma_config.params.vprVersion)
    CompileUtils.createMif(zumaExampleDir)
    CompileUtils.checkEquivalence(vtrDir,zuma_config.params.vprVersion)
    CompileUtils.displayRessourceUsage()

    #verify the generated verilog description
    if zuma_config.params.verifyOverlay:
        #load the yosys path
        yosysDir = local.path(toolpaths.yosysDir)
        CompileUtils.checkOverlayEquivalence(zumaDir,yosysDir,vtrDir)

def main():

    #check which user circuit file to compile
    if len(sys.argv) > 1:
        fileName =  sys.argv[1]
    else:
        fileName = "test.v"

    #start the compilation
    compileZUMA(fileName)

if __name__ == '__main__':
    main()
