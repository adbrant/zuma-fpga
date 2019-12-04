#!/usr/bin/python2.7
def checkEquivalence(local,vtrDir):

    abcPath =  vtrDir / "abc/abc"
    abc = local[abcPath]

    #count latches
    from plumbum.cmd import grep
    #grep returns 2 if an error occured
    (returnCode,output,stderr)=grep["-c","-m","1","\"^.names\"","abc_out.blif"].run(retcode=(0,1))
    count = int(output.rstrip())


    #no latches were found --> cobinatorial circuit
    if count == 0:
        print "Found no latches in input circuit: Circuit is combinational\n"
        print "Checking for combinational equivalence with ODINs result:"
        #     echo -e 'cec abc_out.blif zuma_out.blif\nquit' | $VTR_DIR/abc/abc
        print abc("-c","cec abc_out.blif zuma_out.blif")
    else:
        print "Found latches in input circuit: Circuit is sequential\n"
        print "Checking for sequential equivalence with ODINs result:"
        #     echo -e 'sec abc_out.blif zuma_out.blif\nquit' | $VTR_DIR/abc/abc
        print abc("-c","sec abc_out.blif zuma_out.blif")


def displayRessourceUsage():

    from plumbum.cmd import grep
    #grep return exit 2 when error occured. ignore the rest
    (returnCode,output,stderr)=grep["-c","lut_custom","../ZUMA_custom_generated.v"].run(retcode=(0,1))
    lutrams = int(output.rstrip())

    (returnCode,output,stderr)=grep["-c","elut_custom","../ZUMA_custom_generated.v"].run(retcode=(0,1))
    eluts = int(output.rstrip())

    muxluts = lutrams - eluts

    print "Overlay uses " + str(eluts) + " embedded LUTs and " +str(muxluts) + \
          " routing/MUX LUTs, so " +str(lutrams) + " LUTRAMs in total."

def runVpr(local,vtrDir,fileName):

    cwd = local.cwd

    local.env["VTR_DIR"] = vtrDir

    #load the odin, vpr and abc command
    odinPath = vtrDir / "ODIN_II/odin_II"
    abcPath =  vtrDir / "abc/abc"
    vprPath = cwd / "vpr8.sh"

    odin = local[odinPath]
    abc = local[abcPath]
    vpr = local[vprPath]

    #run odin vpr and abc
    print odin("-V",str(fileName))
    print abc("-F","abccommands.vpr8")
    print vpr()

#create the build forlder and copy necessary scripts
def createBuildFolderAndChDir(local,libDir):

    cwd = local.cwd

    from plumbum.cmd import mkdir, rm

    #create a build dir and use at as cwd
    mkdir("-p","build")
    cwd.chdir(cwd / "build")

    #rm("ARCH_vpr8.xml")

    #configure via templates
    import generate_buildfiles

    templateDir = libDir / "templates"
    generate_buildfiles.make_files(str(cwd), str(templateDir))


def createMif(local,zumaExampleDir):
    #copy the hex file
    hexToMifPath = zumaExampleDir / "hex2mif.sh"
    hexToMif = local[hexToMifPath]
    out = (hexToMif["../output.hex"] > "../output.hex.mif").run()
    #sh $ZUMA_DIR/example/hex2mif.sh output.hex > output.hex.mif

def runZUMA():

    import zuma_build

    graph_file = 'rr_graph.echo'
    verilog_file = '../ZUMA_custom_generated.v'
    blif_file = 'abc_out.blif'
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

def main():

    from plumbum import local
    import sys

    #check which file to compile
    if len(sys.argv) > 1:
        fileName =  local.path(sys.argv[1])
    else:
        fileName = local.path("test.v")

    if not fileName.exists():
        print 'Can\'t load file: ' + str(fileName)
        sys.exit(1)


    #get the path of this file to extract the zuma base dir.
    zumaExampleDir = local.path(__file__).parent
    zumaDir = zumaExampleDir.parent
    libDir = zumaDir / 'source'

    # add the lib dir to the path variable to import the modules
    sys.path.insert(0, str(libDir))
    sys.path.insert(0, str(zumaDir))
    #print( str(libDir))
    #print(str(zumaDir))

    #load the vtr dir
    import toolpaths
    vtrDir = local.path(toolpaths.vtrDir)

    #import the current locale zuma configuration
    import zuma_config

    #start Synthesizing
    print 'Synthesizing ' + str(fileName) + ' to ZUMA'

    local.env["USE_VPR_7"] = "1"

    #create the build forlder and copy necessary scripts
    createBuildFolderAndChDir(local,libDir)

    #run odin, abc and vpr
    runVpr(local,vtrDir,fileName)

    runZUMA()

    createMif(local,zumaExampleDir)

    checkEquivalence(local,vtrDir)

    displayRessourceUsage()


if __name__ == '__main__':
    main()
