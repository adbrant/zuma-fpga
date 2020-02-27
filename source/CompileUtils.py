import sys
from plumbum import local

def checkOverlayEquivalence(zumaDir,yosysDir,vtrDir):

    from plumbum.cmd import cp

    #copy the verification files
    cp("abc_out_v.blif", str(zumaDir / "verilog/verification/VerificationTestsuite"))
    cp("verificationOverlay.v", str(zumaDir / "verilog/verification/VerificationTestsuite"))
    cp("top_module.v", str(zumaDir / "verilog/verification/VerificationTestsuite"))

    #set the used env variables
    local.env["VTR_DIR"] = str(vtrDir)
    local.env["YOSYS_DIR"] = str(yosysDir)

    #run the equivalence check
    check = local[zumaDir / "verilog/verification/VerificationTestsuite/check_equivalence.sh"]
    print check()

def checkEquivalence(vtrDir,vprVersion):

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


def createBuildDirAndRunVpr(vtrDir,libDir,fileName,vprVersion):

    #first create a build dir an copy the necessary build files(scripts + config)
    createBuildFolderAndChDir(libDir)

    #now run odin abc and vpr scripts in the build file
    runOdinAndAbc(vtrDir,fileName,vprVersion)
    runVpr(vtrDir,vprVersion,False)


def runOdinAndAbc(vtrDir,fileName,vprVersion):

    #choose the right tool path, depending on the vpr version
    if vprVersion == 8:
        odinPath = vtrDir / "ODIN_II/odin_II"
        abcPath =  vtrDir / "abc/abc"
        abcCommands = "abccommands.vpr8"
    elif vprVersion == 7:
        odinPath = vtrDir / "ODIN_II/odin_II.exe"
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        abcCommands = "abccommands"
    elif vprVersion == 6:
        odinPath = vtrDir / "ODIN_II/odin_II.exe"
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        abcCommands = "abccommands"
    else:
        print "ERROR: Unsupported vpr version: " + str(vprVersion)
        sys.exit(1)

    #load the odin and abc command
    odin = local[odinPath]
    abc = local[abcPath]

    #run odin vpr and abc
    print odin("-V",str(fileName))
    print abc("-F",str(abcCommands))

#@ param timingRun indicate that vpr8 use built in timing analysis
#                  via the vpr8_timing script
def runVpr(vtrDir,vprVersion,timingRun):

    print 'vtrdDir: ' + str(vtrDir)

    #get the cwd. Note that we should be in the build dir
    cwd = local.cwd

    #the vpr bash script use this enviroment variable to locate the vpr dir
    local.env["VTR_DIR"] = str(vtrDir)

    #choose the right tool path, depending on the vpr version
    if vprVersion == 8:

        if timingRun:
            vprPath = cwd / "vpr8_timing.sh"
        else:
            vprPath = cwd / "vpr8.sh"

    elif vprVersion == 7:
        vprPath = cwd / "vpr7.sh"
    elif vprVersion == 6:
        vprPath = cwd / "vpr6.sh"
    else:
        print "ERROR: Unsupported vpr version: " + str(vprVersion)
        sys.exit(1)

    print 'vpr script path:' + str(vprPath)
    #because the vpr script was copied, set the x flag
    from plumbum.cmd import chmod
    chmod("a+x",str(vprPath))

    #load the vpr command and run it
    vpr = local[vprPath]
    print vpr()

#create the build folder and copy necessary scripts
def createBuildFolderAndChDir(libDir):

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


def createMif(zumaExampleDir):
    #copy the hex file
    hexToMifPath = zumaExampleDir / "hex2mif.sh"
    hexToMif = local[hexToMifPath]
    out = (hexToMif["../output.hex"] > "../output.hex.mif").run()
    #sh $ZUMA_DIR/example/hex2mif.sh output.hex > output.hex.mif

def runZUMA(vprVersion,timingRun):

    import zuma_build

    if vprVersion == 6:
        blif_file = 'clock_fixed.blif'
        graph_file = 'rr_graph.echo'
    elif vprVersion == 7:
        blif_file = 'abc_out.blif'
        graph_file = 'rr_graph.echo'
    else:
        blif_file = 'abc_out.blif'
        graph_file = 'rr_graph.xml'

    if timingRun:
        graph_file = 'rr_graph_timing.xml'

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
