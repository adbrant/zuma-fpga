import sys
from plumbum import local
import os
import inspect

# use this if you want to include modules from a subforder
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"VprParsers")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

#to exract the model name
import BlifParser


def checkOverlayEquivalence(zumaDir,yosysDir,vtrDir,vprVersion):

    if vprVersion == 8:
        abcPath =  vtrDir / "abc/abc"
        yosysPath = yosysDir / "yosys"
    elif vprVersion == 7:
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        yosysPath = yosysDir / "yosys"
    else:
        print "ERROR: Unsupported vpr version for verilog verification: " + str(vprVersion)
        sys.exit(1)

    from plumbum.cmd import cp

    #copy the verification files
    cp("abc_out_v.blif", str(zumaDir / "verilog/verification/VerificationTestsuite"))
    cp("verificationOverlay.v", str(zumaDir / "verilog/verification/VerificationTestsuite"))
    cp("top_module.v", str(zumaDir / "verilog/verification/VerificationTestsuite"))

    #back up the curent cwd
    oldcwd = str(local.cwd)

    #change dir in the testsuite
    local.cwd.chdir(zumaDir / "verilog/verification/VerificationTestsuite")

    #run yosys
    yosys = local[yosysPath]
    print yosys("-s","specification.ys")
    print yosys("-s","removeports.ys")
    print yosys("-s","removeports_abc.ys")

    #run the equivalence check
    result = runAbcEquivalenceCheck(abcPath,"abc_out_v_opt.blif","test_opt.blif")

    #return to the old dir
    local.cwd.chdir(oldcwd)

    return result

def runAbcEquivalenceCheck(abcPath,circuit1Path,circuit2Path):

    #load the abc tool
    abc = local[abcPath]

    #count latches
    from plumbum.cmd import grep
    #grep returns exit code 2 if an error occured. ignore other codes
    (returnCode,output,stderr)=grep["-c","-m","1","^.latch",str(circuit1Path)].run(retcode=(0,1))
    count = int(output.rstrip())


    #no latches were found --> combinatorial circuit
    if count == 0:
        print "Found no latches in input circuit: Circuit is combinational\n"
        print "Checking for combinational equivalence with ODINs result:"

        (returnCode,output,stderr) = abc["-c","cec " + str(circuit1Path) +" "+ str(circuit2Path)].run()
        print output

    #has latches -> sequential circuit
    else:
        print "Found latches in input circuit: Circuit is sequential\n"
        print "Checking for sequential equivalence with ODINs result:"

        (returnCode,output,stderr) = abc["-c","dsec " + str(circuit1Path) +" "+str(circuit2Path)].run()
        print output

    #because abc don't want to comunicate a failing miter check over return codes
    #we have to search the fail string in its output...

    if (output.find("failed") > -1) or (output.find("Error") > -1):
        return False
    else:
        return True


#return True or False depending if the circuits are equvalent or not
def checkEquivalence(vtrDir,vprVersion):

    #choose the right tool path, depending on the vpr version
    if vprVersion == 8:
        abcPath =  vtrDir / "abc/abc"
        blif_file = "clock_fixed.blif"
    elif vprVersion == 7:
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        blif_file = "clock_fixed.blif"
    elif vprVersion == 6:
        abcPath =  vtrDir / "abc_with_bb_support/abc"
        blif_file = "clock_fixed.blif"
    else:
        print "ERROR: Unsupported vpr version: " + str(vprVersion)
        sys.exit(1)

    return runAbcEquivalenceCheck(abcPath,blif_file,"zuma_out.blif")

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


def createBuildDirAndRunVpr(vtrDir,libDir,fileName,vprVersion,clockName):

    #first create a build dir an copy the necessary build files(scripts + config)
    createBuildFolderAndChDir(libDir,clockName)

    #now run odin abc and vpr scripts in the build file
    #fix the clock in the abc output if necessary.
    runOdinAndAbc(vtrDir,fileName,vprVersion)
    fixClock(clockName,vtrDir,vprVersion)
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
def createBuildFolderAndChDir(libDir,clockName):

    cwd = local.cwd

    from plumbum.cmd import mkdir, rm

    #create a build dir and use it as cwd
    mkdir("-p","build")
    buildPath = cwd / "build"
    cwd.chdir(buildPath)

    #configure via templates
    import generate_buildfiles

    templateDir = libDir / "templates"
    generate_buildfiles.make_files(str(buildPath), str(templateDir),clockName)


def createMif(zumaExampleDir):
    #copy the hex file
    hexToMifPath = zumaExampleDir / "hex2mif.sh"
    hexToMif = local[hexToMifPath]
    out = (hexToMif["../output.hex"] > "../output.hex.mif").run()
    #sh $ZUMA_DIR/example/hex2mif.sh output.hex > output.hex.mif

def fixClock(clockName,vtrDir,vprVersion):

    #for earlier versions a generic clockfix was done in the vpr scripts.
    if vprVersion != 8 :
        return

    #get the cwd. Note that we should be in the build dir
    cwd = local.cwd

    #the blif file we want to fix the latches
    blif_file = cwd / 'abc_out.blif'
    #fixed clock file
    fixed_blif = cwd / 'clock_fixed.blif'
    fixed_blif_temp = cwd / 'clock_fixed_temp.blif'

    #if we don't have a clock to fix just copy the abc file
    if clockName is None:

        from plumbum.cmd import cp
        cp(str(blif_file), str(fixed_blif))
        return

    #get the modelname of the blif file. need for the fix
    modelName = BlifParser.extractModelName(str(blif_file))

    #run the fix. the first run add the re attribut. the second remove some empty added models
    fixCommand = "latch_^_re_^_"  + modelName + "^" + clockName + "_^_0"
    fixLatchesPath = vtrDir / "vtr_flow/scripts/blackbox_latches.pl"
    fixLatches = local[fixLatchesPath]

    print fixLatches("--input",str(blif_file),"--output", str(fixed_blif_temp),"--restore",fixCommand)
    print fixLatches("--input",str(fixed_blif_temp),"--output",str(fixed_blif), "--vanilla")


def runZUMA(vprVersion,timingRun):

    import zuma_build

    if vprVersion == 6:
        blif_file = 'clock_fixed.blif'
        graph_file = 'rr_graph.echo'
    elif vprVersion == 7:
        blif_file = 'clock_fixed.blif'
        graph_file = 'rr_graph.echo'
    else:
        #WORKAROUND: the blif parser seems to have problems with the fixed file clock_fixed
        #caused by the vpr8 fix script
        #so we use the original abc_out as a workaround for now.
        #the additional informations of the fixed file are not used by zuma so this is ok.
        blif_file = 'abc_out.blif'
        #blif_file = 'clock_fixed.blif'
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
