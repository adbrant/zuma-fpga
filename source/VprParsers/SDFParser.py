import re
import sys


import os
import inspect
import sys

cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"..")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import Util

class Cell:

    def __init__(self, instanceName,ports,ioPaths):
        ##the name of the instance
        self.instanceName = instanceName

        ##list of port objects
        self.ports = ports
        ##list of IOPath objects
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

##Parse the sdf file and return a list of cell objects.
def ParseSdf(fileName):

    sdfFile = open(fileName,"r")
    line = sdfFile.readline()

    cells = []

    # Parse the file until the end
    while len(line) > 0:

        boolIsLutCell = isLutCell(line,sdfFile)
        boolIsFlipflopCell = isFlipflopCell(line,sdfFile)

        #skip the celltype declaration
        line = sdfFile.readline()

        if boolIsLutCell or boolIsFlipflopCell:
            cell = parseCell(line,sdfFile)
            
            if cell is not None:
                cells.append(cell)
            else:
                print "parse cell error in line: " + line + "\n"

            #read the next line
            line = sdfFile.readline()

    return cells

## check if the current line has a cell declaration.
# return true or false.
def isLutCell(line,sdfFile):

    if line.find("CELLTYPE \"X_RAMD64_ADV\"") > -1:
        return True

    return False


## check if the current line has a cell declaration.
# return true or false.
def isFlipflopCell(line,sdfFile):

    if line.find("CELLTYPE \"X_FF\"") > -1:
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

##parse a list of ports declarations.
#return a list of Port objects and the current line.
def getPorts(line,sdfFile):

    ports = []

    while hasPort(line):
        
        #get the port and append it to the list
        port = parsePort(line)
        ports.append(port)

        #go to the next line
        line = sdfFile.readline()

    return ports,line

##parse a list of ioPaths declarations.
#return a list of ioPaths objects and the current line.
def getIOPaths(line,sdfFile):
    
    ioPaths = []

    while hasIOPath(line):
        
        #get the port and append it to the list
        ioPath = parseIOPath(line)
        ioPaths.append(ioPath)

        #go to the next line
        line = sdfFile.readline()

    return ioPaths,line

##parse the delays.
#@param start the start index in the line where to look at the delays
#return rising and falling delay
def parseDelays(startPos,line):

    firstTupleStart = line.find('(',  startPos + 1)
    firstTupleEnd   = line.find(')',  firstTupleStart + 1)

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

    fallingTuple = line[secondTupleStart+1:secondTupleEnd]

    fallingDelay = fallingTuple.strip().split(':')

    #convert the items to float
    for pos,delay in enumerate(fallingDelay):
        fallingDelay[pos] = float(delay)

    #if the delay has only one item, copy it two have always threee values
    if len(fallingDelay) == 1:
        fallingDelay.append(fallingDelay[0])
        fallingDelay.append(fallingDelay[0])

    return risingDelay,fallingDelay

##parse the port line and return a port object
def parsePort(line):

    portName = Util.find_substring( line, "PORT ", " (" )

    if portName is None:
        print "error cant find a port name in line: " + line + "\n"

    portNamePos = line.find(portName)

    risingDelay,fallingDelay = parseDelays(portNamePos,line)

    port = Port(portName,risingDelay,fallingDelay)

    return port

##parse the iopath line and return a iopath object
def parseIOPath(line):

    ioPathName = Util.find_substring( line, "IOPATH ", " O" )

    if ioPathName is None:
        print "error cant find a iopath name in line: " + line + "\n"

    ioPathPos = line.find(ioPathName)

    risingDelay,fallingDelay = parseDelays(ioPathPos,line)

    ioPath = IOPath(ioPathName,risingDelay,fallingDelay)

    return ioPath

#a unit test
def TestParser():
    cells = ParseSdf('Timing.sdf')

    for cell in cells:

        print "new cell: " + str(cell.instanceName) + "\n"

        for port in cell.ports:

            print "new port: " + str(port.name)
            print "risingDelay: " + str(port.risingDelay)
            print "fallingDelay: "  + str(port.fallingDelay)

        for ioPath in cell.ioPaths:

            print "new iopath: " + str(ioPath.name)
            print "risingDelay: "  + str(ioPath.risingDelay)
            print "fallingDelay: "  + str(ioPath.fallingDelay)

        print "\n"

#a unit test
def main():
    TestParser()

if __name__ == '__main__':
    main()

        