#!/usr/bin/python2.7


import sys

def checkOverlayEquivalence(local,zumaDir,yosysDir):

    from plumbum.cmd import cp

    #copy the verification files
    cp("abc_out_v.blif", str(zumaDir / "verilog/verification/VerificationTestsuite"))
    cp("verificationOverlay.v", str(zumaDir / "verilog/verification/VerificationTestsuite"))
    cp("top_module.v", str(zumaDir / "verilog/verification/VerificationTestsuite"))

    #run the equivalence check
    check = local[zumaDir / "verilog/verification/VerificationTestsuite/check_equivalence.sh"]
    print check(str(yosysDir))

def checkEquivalence(local,vtrDir,vprVersion):

    #choose the right tool path, depending on the vpr version
    if vprVersion == 8:
        abcPath =  vtrDir / "abc/abc"
        blif_file = "abc_out.blif"
    elif vprVersion == 7:
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        blif_file = "abc_out.blif"
    elif vprVersion == 6:
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        blif_file = "clock_fixed.blif"
    else:
        print "ERROR: Unsupported vpr version: " + str(vprVersion)
        sys.exit(1)

    #load the abc tool
    abc = local[abcPath]

    #count latches
    from plumbum.cmd import grep
    #grep returns exit code 2 if an error occured. ignore other codes
    (returnCode,output,stderr)=grep["-c","-m","1","\"^.names\"",str(blif_file)].run(retcode=(0,1))
    count = int(output.rstrip())


    #no latches were found --> combinatorial circuit
    if count == 0:
        print "Found no latches in input circuit: Circuit is combinational\n"
        print "Checking for combinational equivalence with ODINs result:"

        print abc("-c","cec " + str(blif_file) + " zuma_out.blif")
    #has latches -> sequential circuit
    else:
        print "Found latches in input circuit: Circuit is sequential\n"
        print "Checking for sequential equivalence with ODINs result:"

        print abc("-c","dsec " + str(blif_file) + " zuma_out.blif")


def displayRessourceUsage():

    from plumbum.cmd import grep
    #grep return exit code 2 when error occured. ignore the rest of codes
    (returnCode,output,stderr)=grep["-c","lut_custom","../ZUMA_custom_generated.v"].run(retcode=(0,1))
    lutrams = int(output.rstrip())

    (returnCode,output,stderr)=grep["-c","elut_custom","../ZUMA_custom_generated.v"].run(retcode=(0,1))
    eluts = int(output.rstrip())

    muxluts = lutrams - eluts

    print "Overlay uses " + str(eluts) + " embedded LUTs and " +str(muxluts) + \
          " routing/MUX LUTs, so " +str(lutrams) + " LUTRAMs in total."

def runVpr(local,vtrDir,fileName,vprVersion):

    cwd = local.cwd

    #the vpr bash script use this enviroment variable to locate the vpr dir
    local.env["VTR_DIR"] = str(vtrDir)

    #choose the right tool path, depending on the vpr version
    if vprVersion == 8:
        odinPath = vtrDir / "ODIN_II/odin_II"
        abcPath =  vtrDir / "abc/abc"
        vprPath = cwd / "vpr8.sh"
        abcCommands = "abccommands.vpr8"
    elif vprVersion == 7:
        odinPath = vtrDir / "ODIN_II/odin_II.exe"
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        vprPath = cwd / "vpr7.sh"
        abcCommands = "abccommands"
    elif vprVersion == 6:
        odinPath = vtrDir / "ODIN_II/odin_II.exe"
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        vprPath = cwd / "vpr6.sh"
        abcCommands = "abccommands"
    else:
        print "ERROR: Unsupported vpr version: " + str(vprVersion)
        sys.exit(1)

    #because the vpr script was copied, set the x flag
    from plumbum.cmd import chmod
    chmod("a+x",str(vprPath))

    #load the odin, vpr and abc command
    odin = local[odinPath]
    abc = local[abcPath]
    vpr = local[vprPath]

    #run odin vpr and abc
    print odin("-V",str(fileName))
    print abc("-F",str(abcCommands))
    print vpr()

#create the build folder and copy necessary scripts
def createBuildFolderAndChDir(local,libDir):

    cwd = local.cwd

    from plumbum.cmd import mkdir, rm

    #create a build dir and use it as cwd
    mkdir("-p","build")
    buildPath = cwd / "build"
    cwd.chdir(buildPath)

    #configure via templates
    import generate_buildfiles

    templateDir = libDir / "templates"
    generate_buildfiles.make_files(str(buildPath), str(templateDir))


def createMif(local,zumaExampleDir):
    #copy the hex file
    hexToMifPath = zumaExampleDir / "hex2mif.sh"
    hexToMif = local[hexToMifPath]
    out = (hexToMif["../output.hex"] > "../output.hex.mif").run()
    #sh $ZUMA_DIR/example/hex2mif.sh output.hex > output.hex.mif

def runZUMA(vprVersion):

    import zuma_build

    if vprVersion == 6:
        blif_file = 'clock_fixed.blif'
    else:
        blif_file = 'abc_out.blif'

    graph_file = 'rr_graph.echo'
    verilog_file = '../ZUMA_custom_generated.v'

    place_file = 'place.p'
    route_file = 'route.r'
    net_file = 'netlist.net'
    bit_file = '../output.hex'
    blif_out_file = 'zuma_out.blif'
    build_bit = True

    zuma_build.Zuma(verilog_file,
                    graph_file,
                    blif_file,
                    place_file,
                    net_file,
                    route_file,
                    bit_file,
                    blif_out_file,
                    build_bit)

    print "Success: All done."

##compile a ZUMA overlay and a bitstream for the given circuit.
#@param circuitFileName Path to the user circuit file
def compileZUMA(circuitFileName):

    from plumbum import local

    #load the user circuit path
    circuitPath = local.path(circuitFileName)
    if not circuitPath.exists():
        print 'Can\'t load file: ' + str(circuitPath)
        sys.exit(1)

    #get the path of this file to extract the zuma base dir.
    zumaExampleDir = local.path(__file__).parent
    zumaDir = zumaExampleDir.parent
    libDir = zumaDir / 'source'

    #add the lib dir to the path variable to import the zuma modules
    sys.path.insert(0, str(libDir))
    sys.path.insert(0, str(zumaDir))

    #load the vtr dir (and optinal yosys dir)
    import toolpaths
    vtrDir = local.path(toolpaths.vtrDir)

    #import the current locale zuma configuration
    #Therefore we need to add the path of the current folder
    #to the python libary to avoid problems if we change the cwd.
    #NOTE: the zuma configuration need the struct module and therefore
    #the libDir in the sys path
    sys.path.insert(0, str(local.cwd))
    import zuma_config

    #start Synthesizing
    print 'Synthesizing ' + str(circuitPath) + ' to ZUMA'

    #create the build forlder and copy necessary scripts
    createBuildFolderAndChDir(local,libDir)

    #run odin, abc and vpr
    runVpr(local,vtrDir,circuitPath,zuma_config.params.vprVersion)

    runZUMA(zuma_config.params.vprVersion)

    createMif(local,zumaExampleDir)

    checkEquivalence(local,vtrDir,zuma_config.params.vprVersion)

    displayRessourceUsage()

    #verify the generated verilog description
    if zuma_config.params.verifyOverlay:
        #load the yosys path
        yosysDir = local.path(toolpaths.yosysDir)
        checkOverlayEquivalence(local,zumaDir,yosysDir)

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
