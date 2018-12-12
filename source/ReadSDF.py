from structs import *
import globs
import SDFParser
import Util
import os
import inspect
import sys
import numpy

# use this if you want to include modules from a subforder
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"VprParsers")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

## Check if cell is a dual port or a single port cell.
# return True or False
def isDPCell(cell):

    #check if the last two characters are DP
    if cell.instanceName[-2:] == "DP":
        return True
    else:
        return False

## Check if cell is flipflop cell.
# return True or False
def isFlipFlopCell(cell):

    #check if the last two characters are DP
    if cell.instanceName[-11:] == "qsdpo_int_0":
        return True
    else:
        return False

## Extract the lut name out of the cell name
# return the lut name
def getLutName(cell):

    lutName = Util.find_substring(
                cell.instanceName, 
                globs.params.instancePrefix, 
                "_LUT" )

    #delete the prefix
    if lutName[0:4] == "mux_":
        lutName = lutName[4:]
    elif lutName[0:6] == "c_mux_":
        lutName = lutName[6:]

    return lutName


## Add the flipflop delay information of the cell to a mapped node.
# @param name name of the mapped node
def addFlipflopCellDelayToMappedNode(name,cell):

    mappedNode = globs.technologyMappedNodes.getNodeByName(name)

    ffIODelay = [0.0,0.0,0.0]
    ffReadPortDelay = [0.0,0.0,0.0]

    # Calc the ffIODelay and the ffReadPortDelay
    # The ffIODelay delay consist of the clk input delay 
    # and the Tshcko (Clk to Output) delay 
    # described as the io path delay from clk to output in the sdf
    # The ffReadPortDelay is the delay on the input port of the ff
    for port in cell.ports:

        if port.name == 'CLK':
            ffIODelay = numpy.add(port.fallingDelay,ffIODelay)

        if port.name == 'I':
            ffReadPortDelay = numpy.add(port.fallingDelay,ffReadPortDelay)

    for ioPath in cell.ioPaths:

        if ioPath.name == 'CLK':
            ffIODelay = numpy.add(port.fallingDelay,ffIODelay)

    #if ffReadPortDelay == [0.0,0.0,0.0]: 
    if all(delay == '0.0' for delay in ffReadPortDelay):
        print "ERROR no ffReadPort delay in node: " + name
        sys.exit(1)

    #if ffIODelay == [0.0,0.0,0.0]:
    if all(delay == '0.0' for delay in ffIODelay):
        print "ERROR no ffIO delay in node: " + name
        sys.exit(1)

    mappedNode.ffReadPortDelay = ffReadPortDelay
    mappedNode.ffIODelay = ffIODelay


## Add the lut delay information of the cell to a mapped node.
# @param name name of the mapped node
def addLutCellDelayToMappedNode(name,cell):

    mappedNode = globs.technologyMappedNodes.getNodeByName(name)

    #the delay list. index is the port number
    readPortDelay = []
    writePortDelay = []
    ioPathDelay = []

    for port in cell.ports:

        #in xilinx sdf, ports are in continuous order, 
        #so the ports are listed also in increasing port number.
        #Thus we only have to check if the name is in the list
        if port.name in ['RADR0','RADR1','RADR2','RADR3','RADR4','RADR5']:
            #for now we only use the falling delay, 
            #because in xilinx sdf rising and falling delays seems always the same
            readPortDelay.append(port.fallingDelay)

        if port.name in ['WADR0','WADR1','WADR2','WADR3','WADR4','WADR5']:
            writePortDelay.append(port.fallingDelay)

    for ioPath in cell.ioPaths:

        #in xilinx sdf, ports are in continuous order, 
        #so the ports are listed also in increasing port number.
        #Thus we only have to check if the name is in the list
        if ioPath.name in ['RADR0','RADR1','RADR2','RADR3','RADR4','RADR5']:
            #for now we only use the falling delay, 
            #because in xilinx sdf rising and falling delays seems always the same
            ioPathDelay.append(ioPath.fallingDelay)


    if len(readPortDelay) == 0:
        print "ERROR no read port delay in node: " + name
        sys.exit(1)

    if len(writePortDelay) == 0:
        print "ERROR no write port delay in node: " + name
        sys.exit(1)

    if len(ioPathDelay) == 0:
        print "ERROR no io port delay in node: " + name
        sys.exit(1)

    #append the delays to the node
    mappedNode.readPortDelay  = readPortDelay
    mappedNode.writePortDelay  = writePortDelay
    mappedNode.ioPathDelay  = ioPathDelay

## Add the flipflop delay information of the cell to a mapped node
## if it's a lut cell.
# Otherwise it does nothing
def addLutDelayToMappedNodes(cell):

    #check if the cell is a dual port not a SP instance
    if isDPCell(cell):
        #get the name of the lut
        lutName =  getLutName(cell)

        addLutCellDelayToMappedNode(lutName,cell)

## Add the flipflop delay information of the cell to a mapped node.
## if it's a lut cell.
# Otherwise it does nothing
def addFlipFlopDelayToMappedNodes(cell):

    if isFlipFlopCell(cell):
        #get the name of the lut
        lutName =  getLutName(cell)
        
        addFlipflopCellDelayToMappedNode(lutName,cell)

## Parse the globs.params.sdfFileName and globs.params.sdfFlipflopFileName
## and add the timing information to the technology mapped node graph. 
def ReadSDF():

    cells = SDFParser.ParseSdf(globs.params.sdfFileName)

    for cell in cells:
        addLutDelayToMappedNodes(cell)

    #now the workaround with the second file were we get the Tshcko 
    #(clock to output) time. The first file hasn't this information
    
    cells = SDFParser.ParseSdf(globs.params.sdfFlipflopFileName)
    for cell in cells:
         addFlipFlopDelayToMappedNodes(cell)
        