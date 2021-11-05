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


#to speed things up we compile the setupandholds pattern here instead
#in parseSetupHold

SetupHoldRegex = r'''\s* \( SETUPHOLD \s*
                         \(  (\s*posedge\s*|\s*negedge\s*) (?P<input>\S+) \s* \) \s*
                         \(  (\s*posedge\s*|\s*negedge\s*) (?P<clock>\S+) \s* \)
                         (?P<rest>.*)'''

SetupHoldPattern = re.compile(SetupHoldRegex,re.VERBOSE)

#to speed things up we compile the iopath pattern here instead
#in parseIoPath

#we assure in the output regex to not have a '(' included
IOPathRegex = r'''\s* \( IOPATH \s*
                       (?P<input>\S+) \s*
                       (?P<output>[^ \t\n\r\f\v\(]+) \s*
                       (?P<rest>.*)'''

IOPathPattern = re.compile(IOPathRegex,re.VERBOSE)


InterconnectRegex = r'''\s* \( INTERCONNECT \s*
                              (?P<source>\S+) \s*
                              (?P<sink>[^ \t\n\r\f\v\(]+) \s*
                              (?P<rest>.*)'''

InterconnectPattern = re.compile(InterconnectRegex,re.VERBOSE)

class Cell:

    def __init__(self, instanceName,ports,ioPaths,setupHolds):
        ##the name of the instance
        self.instanceName = instanceName

        ##dictonary of port objects
        self.ports = ports
        ##dictonary of IOPath objects
        self.ioPaths = ioPaths

        ##dictonary fot the setup and hold objects
        self.setupHolds = setupHolds

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

class SetupHold:

    def __init__(self, input, clock ,setupDelay,holdDelay):

        ##the input port name
        self.input = input
        self.clock = clock

        self.setupDelay = setupDelay
        self.holdDelay = holdDelay

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

        #read until a cell declaration. skip this line
        if not isCell(line,sdfFile):
            line = sdfFile.readline()
            continue

        #we have a cell check if it is a real cell or a interconnection cell
        if not isInterconnectCell(line,sdfFile):

            #get the next line after the celltype declaration
            line = sdfFile.readline()

            cell = parseCell(line,sdfFile)

            #append the cell to the dict
            if cell is not None:
                cells[cell.instanceName] = cell
            else:
                print "parse cell error in line: " + line + "\n"


        #if its a interconnect cell read out the delays and add them
        #as a port delay. The interconnect cell is at the end of the file
        #so we can provide the current parsed cells as an argument
        else:

            #get the next line after the celltype declaration
            line = sdfFile.readline()

            parseInterconnectCell(line,sdfFile,cells)

    return cells

##check if the current line has a cell declaration.
# return true or false.
def isCell(line,sdfFile):

    if line.find("CELLTYPE") > -1:

        #the interconnect cell is also a valid cell
        if line.find("CELLTYPE \"" + globs.params.sdfInterconnectCellType + "\"") > -1:
            return True

        #if the user has decide to only extract some cell types
        #check if it is one of the given celltypes
        if len(globs.params.knownCellTypes) > 0:

            for name in globs.params.knownCellTypes:
                if line.find(name) > -1:
                    return True

        #no constraint was given. extract all cells
        else:
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

        #skip the delay declaration
        line = sdfFile.readline()

        #read until the block ends
        while (line.strip() is not ')'):

            if line.find("ABSOLUTE") > -1:
                #skip to the next line
                line = sdfFile.readline()

                return True,line

            #go to the next line
            line = sdfFile.readline()


    #delay block has ended or the was no delay block at all
    return False,line

##get the instance name.
#return the instance name and the current line.
def getName(line,sdfFile):
    name = Util.find_substring( line, "INSTANCE ", ")" )

    line = sdfFile.readline()

    return name,line

##check if the cell has a timingcheck field.
#skip to the next line if it has a timingcheck field.
#return true or false and the current line.
def hasTimingcheckField(line,sdfFile):

    #because the delay field were read before there can be on or two closing
    #) before the timing check field

    #check line has only a single )
    if line.strip() == ')':
        line = sdfFile.readline()

    if line.strip() == ')':
        line = sdfFile.readline()

    if line.find("TIMINGCHECK") > -1:
        #skip to the next line
        line = sdfFile.readline()
        return True,line

    return False,line


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

    #now try to search for the timingcheck field
    setupHolds = None
    boolHasTimingcheckField,line = hasTimingcheckField(line,sdfFile)

    if boolHasTimingcheckField:
        setupHolds,line = getSetupHolds(line,sdfFile)

    cell = Cell(name,ports,ioPaths,setupHolds)

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

def hasSetupHold(line):
    if line.find("SETUPHOLD") > -1:
        return True
    return False

##parse a list of Setup and Hold declarations.
#return a dictonary of SetupHold objects and the current line.
def getSetupHolds(line,sdfFile):

    setupholds = {}

    #parse to the end of the block
    while (line.strip() is not ')'):

        if hasSetupHold(line):
            setuphold = parseSetupHold(line)
            setupholds[(setuphold.input,setuphold.clock)] = setuphold

        #go to the next line
        line = sdfFile.readline()

    return setupholds,line

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
#return a list of Interconnect objects and the current line.
def getInterconnects(line,sdfFile):

    interconnects = []

    while hasInterconnect(line):

        #get the port and append it to the list
        interconnect = parseInterconnect(line)
        interconnects.append(interconnect)

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

    #is now done in the module header, to speed things up
    # IOPathRegex = r'''\s* \( IOPATH \s*
    #                        (?P<input>\S+) \s*
    #                        (?P<output>\S+) \s*
    #                        (?P<rest>.*)'''
    #
    # IOPathPattern = re.compile(IOPathRegex,re.VERBOSE)

    res = IOPathPattern.search(line)

    if res is None:

        print "error cant find a iopath name in line: " + line + "\n"
        sys.exit(1)


    ioPathName = res.group('input')
    restString = res.group('rest')
    risingDelay,fallingDelay = parseDelays(0,restString)

    ioPath = IOPath(ioPathName.strip(),risingDelay,fallingDelay)

    return ioPath

##parse the setup and hold line and return a setupHold object
def parseSetupHold(line):

    #is now done in the module header, to speed things up
    # SetupHoldRegex = r'''\s* \( SETUPHOLD \s*
    #                          \(  (\s*posedge\s*|\s*negedge\s*) (?P<input>\S+) \s* \) \s*
    #                          \(  (\s*posedge\s*|\s*negedge\s*) (?P<clock>\S+) \s* \)
    #                          (?P<rest>.*)'''
    #
    # SetupHoldPattern = re.compile(SetupHoldRegex,re.VERBOSE)


    res = SetupHoldPattern.search(line)

    if res is None:

        print "error cant apply regex pattern for parsing setup an hold times: " + line + "\n"
        sys.exit(1)


    clock = res.group('clock')
    input = res.group('input')
    restString = res.group('rest')
    setupDelay, holdDelay = parseDelays(0,restString)

    setupHold = SetupHold(input, clock ,setupDelay,holdDelay)

    return setupHold


##parse the interconnect line and return a interconnect object
def parseInterconnect(line):


    #is now done in the module header, to speed things up
    # InterconnectRegex = r'''\s* \( INTERCONNECT \s*
    #                              (?P<source>\S+) \s*
    #                              (?P<sink>[^ \t\n\r\f\v\)]+ ) \s*
    #                              (?P<rest>.*)'''
    #
    # InterconnectPattern = re.compile(InterconnectRegex,re.VERBOSE)


    res = InterconnectPattern.search(line)

    if res is None:

        print "error cant find interconnect instance names in line: " + line + "\n"
        sys.exit(1)


    sourceString = res.group('source')
    sinkString = res.group('sink')
    restString = res.group('rest')

    #remove the port name at the end. also extract the port name of the sink
    indexDelimiter = sourceString.rfind('/')
    source = sourceString[:indexDelimiter]

    indexDelimiter = sinkString.rfind('/')
    sink = sinkString[:indexDelimiter]
    port = sinkString[indexDelimiter+1:]

    #now get the delays
    risingDelay, fallingDelay = parseDelays(0,restString)

    #finally create the interconnect object
    interconnect = Interconnect(source,sink,port,risingDelay,fallingDelay)

    return interconnect

def parseInterconnectCell(line,sdfFile,cells):

    #skip the next lines to get the interconnections
    line = sdfFile.readline()
    line = sdfFile.readline()
    line = sdfFile.readline()

    #print "start interconnection parsing at line", line

    #parse all interconnections
    interconnects,line = getInterconnects(line,sdfFile)

    #print "end interconnection parsing at line", line
    #print "has "  + str(len(interconnects))+" interconnect"

    #now go through the interconnections and add the port
    #delays to the sink cells
    for interconnect in interconnects:

        #get the right cell through the sink name
        #check if the key exist because we skipped some cells types like lut5
        if interconnect.sink not in cells:
            continue

        cell = cells[interconnect.sink]

        #add the port delay. therfore create a new port object
        portName = interconnect.port
        port = Port(portName,interconnect.risingDelay,interconnect.fallingDelay)
        cell.ports[portName] = port

    #debug
    #for interconnect in interconnects:
    #    print "new interconnect"
    #    print "source: ",interconnect.source
    #    print "sink: ",interconnect.sink
    #    print "port: ",interconnect.port


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

        for (input,clock),setupHold in cell.setupHolds.items():

            print "new setuphold: " + str(setupHold.input) + ',' + str(setupHold.clock)
            print "setupDelay: "  + str(setupHold.setupDelay)
            print "holdDelay: "  + str(setupHold.holdDelay)

        print "\n"


#a unit test
def main():
    TestParser()

if __name__ == '__main__':
    main()
