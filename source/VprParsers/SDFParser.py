import re
import sys


import os
import inspect
import sys

# use this if you want to include modules from a subforder.
# used for the unit tests to import the globs module
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"../")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import globs
import Util

class Cell:

    def __init__(self, instanceName,ports,ioPaths):
        ##the name of the instance
        self.instanceName = instanceName

        ##dictonary of port objects
        self.ports = ports
        ##dictonary of IOPath objects
        self.ioPaths = ioPaths

class Port:

    def __init__(self, name,risingDelay,fallingDelay):
        ##the name of port e.g waddr5
        self.name = name

        ##list of delays
        ##the first entry specifies the minimum delay,
        ##the second specifies the typical delay,
        ##and the third specifies the maximum delay

        self.risingDelay = risingDelay
        self.fallingDelay = fallingDelay

class IOPath:

    def __init__(self, name,risingDelay,fallingDelay):
        ##the src name of iopath to the ouput e.g waddr5
        self.name = name

        ##list of delays
        ##the first entry specifies the minimum delay,
        ##the second specifies the typical delay,
        ##and the third specifies the maximum delay

        self.risingDelay = risingDelay
        self.fallingDelay = fallingDelay

class Interconnect:

    def __init__(self,source,sink,port,risingDelay,fallingDelay):

        ##the source instance name
        self.source = source

        ##the sink instance name
        self.sink = sink

        ##the port name of the sink e.g waddr5
        self.port = port

        ##list of delays
        ##the first entry specifies the minimum delay,
        ##the second specifies the typical delay,
        ##and the third specifies the maximum delay
        self.risingDelay = risingDelay
        self.fallingDelay = fallingDelay

##Parse the sdf file and return a dictonary of cell objects, with
##the instance name as a key
def ParseSdf(fileName):

    sdfFile = open(fileName,"r")
    line = sdfFile.readline()

    cells = {}

    # Parse the file until the end
    while len(line) > 0:

        boolIsLutCell = isLutCell(line,sdfFile)
        boolIsFlipflopCell = isFlipflopCell(line,sdfFile)
        boolInterconnectCell = isInterconnectCell(line,sdfFile)

        #skip the celltype declaration, or the stuff around cells
        line = sdfFile.readline()

        if boolIsLutCell or boolIsFlipflopCell:
            cell = parseCell(line,sdfFile)

            #append the cell to the dict
            if cell is not None:
                cells[cell.instanceName] = cell
            else:
                print "parse cell error in line: " + line + "\n"

            #read the next line
            line = sdfFile.readline()

        #if its a interconnect cell read out the delays and add them
        #as a port delay. The interconnect cell is at the end of the file
        #so we can provide the current parsed cells as an argument
        if boolInterconnectCell:
            parseInterconnectCell(line,sdfFile,cells)

    return cells

## check if the current line has a cell declaration.
# return true or false.
def isLutCell(line,sdfFile):

    if globs.params.sdfUsedTool == "ise" and line.find("CELLTYPE \"X_RAMD64_ADV\"") > -1:
        return True
    elif globs.params.sdfUsedTool == "vivado" and line.find("CELLTYPE \"RAMD64E\"") > -1:
        return True

    return False


## check if the current line has a cell declaration.
# return true or false.
def isFlipflopCell(line,sdfFile):

    if  globs.params.sdfUsedTool == "ise" and line.find("CELLTYPE \"X_FF\"") > -1:
        return True
    elif globs.params.sdfUsedTool == "vivado" and line.find("CELLTYPE \"FDCE\"") > -1:
        return True

    return False

## check if the current line is a interconnection cell listing
## all the interconnection delays
# return true or false.
def isInterconnectCell(line,sdfFile):

    if line.find("CELLTYPE \"" + globs.params.sdfInterconnectCellType + "\"") > -1:
        return True

    return False

##check if the line has a instance declaration.
#return true or false.
def hasInstanceName(line):

    return line.find("INSTANCE") > -1


##check if the cell has a absolute delay field.
#skip to the next line if it has a delay field.
#return true or false and the current line.
def hasAbsolutDelayField(line,sdfFile):
    if line.find("DELAY") > -1:
        #skip the absolut declaration
        line = sdfFile.readline()

        if line.find("ABSOLUTE") > -1:
            #skip to the next line
            line = sdfFile.readline()

            return True,line

    return False,line

##get the instance name.
#return the instance name and the current line.
def getName(line,sdfFile):
    name = Util.find_substring( line, "INSTANCE ", ")" )

    line = sdfFile.readline()

    return name,line

##parse the cell declaration (lut or flipflop).
#return a cell object or None.
def parseCell(line,sdfFile):

    #skip the celltype declaration
    cell = None

    #check if there is a instance name
    if not hasInstanceName(line):
        #something gone wrong here.
        print "error cell has no instance name: " + line + "\n"
        return None

    name,line = getName(line,sdfFile)

    #check if the cell has delay porperties

    boolHasAbsoluteDelayField, line = hasAbsolutDelayField(line,sdfFile)

    if not boolHasAbsoluteDelayField:
        print "error: cell " + name + " has no delay field." + line + "\n"
        return None

    ports,line = getPorts(line,sdfFile)
    ioPaths,line = getIOPaths(line,sdfFile)

    cell = Cell(name,ports,ioPaths)

    return cell


def hasPort(line):
    if line.find("PORT") > -1:
        return True
    return False

def hasIOPath(line):
    if line.find("IOPATH") > -1:
        return True
    return False

def hasInterconnect(line):
    if line.find("INTERCONNECT") > -1:
        return True
    return False

##parse a list of ports declarations.
#return a dictonary of Port objects and the current line.
def getPorts(line,sdfFile):

    ports = {}

    while hasPort(line):

        #get the port and append it to the dictonary
        port = parsePort(line)
        ports[port.name] = port

        #go to the next line
        line = sdfFile.readline()

    return ports,line

##parse a list of ioPaths declarations.
#return a dictonary of ioPaths objects and the current line.
def getIOPaths(line,sdfFile):

    ioPaths = {}

    while hasIOPath(line):

        #get the port and append it to the dictonary
        ioPath = parseIOPath(line)
        ioPaths[ioPath.name] = ioPath

        #go to the next line
        line = sdfFile.readline()

    return ioPaths,line

##parse a list of interconnect declarations.
#return a dictonary of Interconnect objects, key is the source instance name of
#interconnction, and the current line.
def getInterconnects(line,sdfFile):

    interconnects = {}

    while hasInterconnect(line):

        #get the port and append it to the dictonary
        interconnect = parseInterconnect(line)
        interconnects[interconnect.source] = interconnect

        #go to the next line
        line = sdfFile.readline()

    return interconnects,line

##parse the delays.
#@param start the start index in the line where to look at the delays
#return rising and falling delay
def parseDelays(startPos,line):

    firstTupleStart = line.find('(',  startPos + 1)
    firstTupleEnd   = line.find(')',  firstTupleStart + 1)

    if firstTupleStart == -1 or firstTupleEnd == -1:
        print "ERROR: there are no delaya tuples in line", line
        sys.exit(1)

    risingTuple = line[(firstTupleStart+1):firstTupleEnd]

    risingDelay = risingTuple.strip().split(':')

    #convert the items to float
    for pos,delay in enumerate(risingDelay):
        risingDelay[pos] = float(delay)


    #if the delay has only one item, copy it two have always threee values
    if len(risingDelay) == 1:
        risingDelay.append(risingDelay[0])
        risingDelay.append(risingDelay[0])

    secondTupleStart = line.find('(',  firstTupleEnd + 1)
    secondTupleEnd   = line.find(')',  secondTupleStart + 1)

    #if there is no second tuple. just copy the frist one
    if secondTupleStart == -1 or secondTupleEnd == -1:
        fallingTuple = risingTuple
    else:
        fallingTuple = line[secondTupleStart+1:secondTupleEnd]

    fallingDelay = fallingTuple.strip().split(':')

    #convert the items to float
    for pos,delay in enumerate(fallingDelay):
        fallingDelay[pos] = float(delay)

    #if the delay has only one item, copy it two have always three values
    if len(fallingDelay) == 1:
        fallingDelay.append(fallingDelay[0])
        fallingDelay.append(fallingDelay[0])

    return risingDelay,fallingDelay

##parse the port line and return a port object
def parsePort(line):

    portName = Util.find_substring( line, "PORT ", " (" )

    if portName is None:
        print "error cant find a port name in line: " + line + "\n"
        sys.exit(1)

    #for the next search start after the port name
    portNamePos = line.find(portName)
    startSearchPos = portNamePos+len(portName) -1

    risingDelay,fallingDelay = parseDelays(startSearchPos,line)

    port = Port(portName.strip(),risingDelay,fallingDelay)

    return port

##parse the iopath line and return a iopath object
def parseIOPath(line):

    ioPathName = Util.find_substring( line, "IOPATH ", " O" )

    #if vivado is used the ff ports have the output Q and not O
    if ioPathName is None and globs.params.sdfUsedTool == "vivado":
        ioPathName = Util.find_substring( line, "IOPATH ", " Q" )

    # if its still empty print an error message
    if ioPathName is None:
        print "error cant find a iopath name in line: " + line + "\n"
        sys.exit(1)

    #for the next search start after the path name
    ioPathPos = line.find(ioPathName)
    startSearchPos = ioPathPos+len(ioPathName) -1

    risingDelay,fallingDelay = parseDelays(startSearchPos,line)

    ioPath = IOPath(ioPathName.strip(),risingDelay,fallingDelay)

    return ioPath

##parse the interconnect line and return a interconnect object
def parseInterconnect(line):

    #get the source and sink instance name string
    names = Util.find_substring( line, "INTERCONNECT ", " (" )

    if names is None:
        print "error cant find interconnect instance names in line: " + line + "\n"
        sys.exit(1)

    #seperate the source and sink instance name. they got still a port name at the end
    sourceAndSink = names.strip().split()

    if len(sourceAndSink) != 2:
        print "error not enough interconnect names in line" + line + "\n"
        sys.exit(1)

    #remove the port name at the end. also extract the port name of the sink
    sourceString = sourceAndSink[0]
    indexDelimiter = sourceString.rfind('/')
    source = sourceString[:indexDelimiter]

    sinkString = sourceAndSink[1]
    indexDelimiter = sinkString.rfind('/')
    sink = sinkString[:indexDelimiter]
    port = sinkString[indexDelimiter+1:]

    #now get the delays
    delayPos = line.find(names)
    startSearchPos = delayPos+len(names) -1
    risingDelay,fallingDelay = parseDelays(startSearchPos,line)

    #finally create the interconnect object
    interconnect = Interconnect(source,sink,port,risingDelay,fallingDelay)

    return interconnect

def parseInterconnectCell(line,sdfFile,cells):

    #skip the next four lines to get the interconnections
    line = sdfFile.readline()
    line = sdfFile.readline()
    line = sdfFile.readline()
    line = sdfFile.readline()

    #parse all interconnections
    interconnects,line = getInterconnects(line,sdfFile)

    #now go through the interconnections and add the port
    #delays to the sink cells
    for source,interconnect in interconnects.items():

        #get the right cell through the sink name
        #check if the key exist because we skipped some cells types like lut5
        if interconnect.sink not in cells:
            continue

        cell = cells[interconnect.sink]

        #add the port delay. therfore create a new port object
        portName = interconnect.port
        port = Port(portName,interconnect.risingDelay,interconnect.fallingDelay)
        cell.ports[portName] = port


#a unit test
def TestParser():

    globs.init()
    globs.load_params()
    globs.params.sdfUsedTool = "ise"
    globs.params.sdfInterconnectCellType = "zuma_wrapper"

    # cells = ParseSdf('Timing.sdf')
    #
    # for name,cell in cells.items():
    #
    #     print "new cell: " + str(cell.instanceName) + "\n"
    #
    #     for portName,port in cell.ports.items():
    #
    #         print "new port: " + str(port.name)
    #         print "risingDelay: " + str(port.risingDelay)
    #         print "fallingDelay: "  + str(port.fallingDelay)
    #
    #     for pathName,ioPath in cell.ioPaths.items():
    #
    #         print "new iopath: " + str(ioPath.name)
    #         print "risingDelay: "  + str(ioPath.risingDelay)
    #         print "fallingDelay: "  + str(ioPath.fallingDelay)
    #
    #     print "\n"

    globs.params.sdfUsedTool = "vivado"
    cells = ParseSdf('postRoute.sdf')

    for name,cell in cells.items():

        print "new cell: " + str(cell.instanceName) + "\n"

        for portName,port in cell.ports.items():

            print "new port: " + str(port.name)
            print "risingDelay: " + str(port.risingDelay)
            print "fallingDelay: "  + str(port.fallingDelay)

        for pathName,ioPath in cell.ioPaths.items():

            print "new iopath: " + str(ioPath.name)
            print "risingDelay: "  + str(ioPath.risingDelay)
            print "fallingDelay: "  + str(ioPath.fallingDelay)

        print "\n"


#a unit test
def main():
    TestParser()

if __name__ == '__main__':
    main()
