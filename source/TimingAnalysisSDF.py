import os, sys, inspect
from copy import deepcopy
import numpy
import Dump


# use this if you want to include modules from a subfolder
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"VprParsers")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import globs

class RoutingPath():
    def __init__(self):
        #the delay with min mavg and max delay
        self.delay = [0.0,0.0,0.0]
        #for debug purpose.
        #a list of the used delays
        self.path = [ ]
        self.pathlength = 0
        self.edgesWithoutDelay = 0
        #delay caused by the ordering layer
        self.orderedDelay = [0.0,0.0,0.0]

    def __init__(self, node):
        #the delay with min avg and max delay
        self.delay = [0.0,0.0,0.0]
        #for debug purpose.
        #a list of the used delays
        self.path = [ node ]
        self.pathlength = 0
        self.edgesWithoutDelay = 0
        #delay caused by the ordering layer
        self.orderedDelay = [0.0,0.0,0.0]


## returns all routing path sources and sinks of the current circuit,
## i.e. all primary IO and the latches.
# @return return a list of node references
def findSinksAndSources():

    sources = []
    sinks = []

    #search for driven IOPINs
    #build a list for all possible candidates

    opinIdList = []
    ipinIdList = []

    #TODO: merge the branches. the second branch can also applied for the first branch
    if globs.params.orderedIO:
        #IOMUXes are optimized away by Xilinx, thus one iomux is enough as global IO
        #source / sink, as it expands to all global inputs / outputs.
        #search driven IOPINs from this node.

        #get one iomux input node
        IOMuxInputNode = globs.nodes[globs.orderedInputs[0]]
        opinIdList += IOMuxInputNode.edges

        #little hack. when the ordered layer is not used we have ipins as sinks
        # and if it used we have the iomuxes as sinks
        ipinIdList += globs.orderedOutputs

    #if orderedIO is false we have to check all first lvl ipin/opins
    else:
        for sourceId in globs.orderedInputs:
            source = globs.nodes[sourceId]

            for opinId in source.edges:
                #if for some reasons, a opin is connected to two sources
                if opinId not in opinIdList:
                    opinIdList.append(opinId)

        for sinkId in globs.orderedOutputs:
            sink = globs.nodes[sinkId]

            for ipinId in sink.inputs:
                #if for some reasons, a ipin is connected to two sinks
                if ipinId not in ipinIdList:
                    ipinIdList.append(ipinId)

    for opinID in opinIdList:
        #is it driven?
        #check this in the normal node graph.
        #in the technology mapped graph, it could be that its optimized
        #and therefore the source attribute is set, whether or not its driven.

        #only take the nodes of the first lvl.
        #the further lvls make the critical path.

        #when orderedIO is not active check the primaryOpin flag
        opinNode = globs.nodes[opinID]
        if opinNode.source >= 0 or opinNode.primaryOpin:
            #now get the mapped opin of the first lvl
            #which connect to the outer world
            mappedOpin = globs.technologyMappedNodes.getFistInputNode(opinNode)
            sources += [ mappedOpin ]


    for ipinID in ipinIdList:
        #is it driven?
        #check this in the normal node graph.
        #In the technology mapped graph, it could be that its optimized
        #and therefore the source attribute is set, whether or not its driven.
        ipinNode = globs.nodes[ipinID]
        if ipinNode.source >= 0 and ipinNode.type > -1:
            #because its an output we only need the node of the last lvl
            mappedIpin = globs.technologyMappedNodes.getNodeByName(ipinNode.mappedNodes[-1])
            sinks += [ mappedIpin ]


    #now find LUTS before used latches
    #alternatively, we could inspect all elut nodes and check the lut reference
    for lut in globs.LUTs.values():

        if lut.useFF:
            #get the mapped node of the lut.
            lutNode = lut.node
            #get the last node of the lut.
            #this is for future extension,
            #where a lut can have several mapped nodes
            mappedNodeName = lutNode.mappedNodes[-1]
            mappedNode = globs.technologyMappedNodes.getNodeByName(mappedNodeName)

            #append it to source and sinks
            sources = sources + [ mappedNode ]
            sinks = sinks + [ mappedNode ]


    print "sink and sources:"
    #print sinks
    print "Printing sinks: ---------"

    for node in sinks:
        print "node in sinks: " + node.name

    print "Printing sources: ---------"

    for node in sources:
        print "node in sources: " + node.name

    return sources, sinks


##initialize trackable paths for backward tracking from the sinks
def initActivePaths(sinks):
    paths =  []
    for sink in sinks:
        path = RoutingPath(sink)
        paths.append(path)

    return paths


##update a path with a new node in front.
# @return return 1 if the new edge in the path has no delay. 0 otherwise.
def prependNodeToPath(path,newSrcNode):

    #get the port index were the new node is connected to.
    #has srcNode as input
    destNode = path.path[0]
    portIndex = destNode.inputs.index(newSrcNode.name)

    #add the new node to the path
    path.path = [ newSrcNode ] + path.path
    path.pathlength += 1

    return 0


##calculate the path delay for all paths, going backwards from sinks to sources.
def trackPathsBackwards(sources,sinks):
    activePaths = initActivePaths(sinks)

    #now find the critical path

    finishedPaths = []

    while len(activePaths) > 0:

        oldactivePaths = activePaths
        activePaths = []
        for path in oldactivePaths:

            activeNode = path.path[0]
            #follow path backwards
            #check if the node is driven
            if activeNode.source < 0:
                #its not driven
                if activeNode.type == 8: # this is a LUT, every pin may be driven - split paths
                    for mappedInputNodeName in activeNode.inputs:
                        mappedInputNode = globs.technologyMappedNodes.getNodeByName(mappedInputNodeName)

                        #we have to check if the input pin is driven.
                        #therefore we check the pin in the not mapped graph,
                        #the node graph.because the source attr can be set
                        #because of optimizations in the mapped graph.
                        inputNode = mappedInputNode.parentNode
                        if inputNode.source >= 0:
                            # driven pin of the LUT, use for new path
                            childpath = deepcopy(path)
                            newSrcNode = mappedInputNode
                            prependNodeToPath(childpath,newSrcNode)

                            if newSrcNode in sources:
                                finishedPaths.append(childpath)
                            else:
                                activePaths.append(childpath)
                    continue # delete parent path
                else:
                    print "Weird: undriven node encountered: " + str(activeNode.name) +\
                           "\n----------Path debug----------------\n\n "
                    printPathDelay(path)
                    continue # delete this path

            #has an active source
            else:
                newSrcNode = globs.technologyMappedNodes.getNodeByName(activeNode.source)
                prependNodeToPath(path,newSrcNode)

                #check if we've arrived at a source yet.
                if newSrcNode in sources:
                    finishedPaths.append(path)
                else:
                    activePaths.append(path)

    return finishedPaths


def calcPathDelays(paths):
    for path in paths:

        #calc the path delay and the number of edges without a delay
        calcPathDelay(path)

#calc and set the delay for a given path
def calcPathDelay(path):

    sourceNode = None
    destNode = None

    delay = [0.0,0.0,0.0]

    #for the iteration we use a window with node in the middle and sourceNode and destNode at the border
    for index,node in enumerate(path.path):

        #node is not at the end, update th4e destNode
        if index + 1 < len(path.path):
            destNode = path.path[index + 1]
        else:
            destNode = None

        #get the delay and add it
        (readPortDelay,ioPathDelay) = getDelayForNode(sourceNode,node,destNode)
        nodeDelay = numpy.add(readPortDelay,ioPathDelay)

        #update the edge counter
        if readPortDelay == [0.0,0.0,0.0]:
            print "connection " + node.name +" to " +  destNode.name + " has no delay"
            path.edgesWithoutDelay += 1


        #search for a global opin in the path (imux to opins will be otimized)
        #or imux connected to global inputs
        if ((sourceNode is None) and (node.source > -1) and (node.type == 3)) or ((sourceNode is not None) and (node.type == 10) and (node.source > -1) and (sourceNode.type == 4)):

                print 'Found global opin/ipin iomux ' + str(node.name)
                #add the node delay to the ordered layer attribut
                path.orderedDelay = numpy.add(nodeDelay,path.orderedDelay)

                #don't add the delay to the result when without OrderedLayer is turned on
                if globs.params.skipOrderedLayerTiming:

                    #update the sourceNode
                    sourceNode = node

                    continue

        #add the delay to the result
        delay = numpy.add(delay,nodeDelay)

        #update the sourceNode
        sourceNode = node


    #update the path delay
    path.delay = delay


##search for the critical path among all paths.
#use only the max component of the delay tuple
def findCriticalPath(paths):
    maxDelay = float("-inf")
    criticalPath = None

    for path in paths:

        if path.delay[2] > maxDelay:
            maxDelay = path.delay[2]
            criticalPath = path

    return criticalPath

##print the maximum delay together with the list of nodes and some other infos.
def printPathDelay(path):

    print "Path:"
    pathIDs = []

    for node in path.path:

        typeString= ''

        if node.type == 1:
            typeString= 'SINK'
        elif node.type == 2:
            typeString= 'SOURCE'
        elif node.type == 3:
            typeString= 'OPIN'
        elif node.type == 4:
            typeString= 'IPIN'
        elif node.type == 5:
            typeString= 'CHANX'
        elif node.type == 6:
            typeString= 'CHANY'
        elif node.type == 7:
            typeString= 'MUX'
        elif node.type == 8:
            typeString= 'ELUT'
        elif node.type == 9:
            typeString= 'FFMUX'
        elif node.type == 10:
            typeString= 'IOMUX'


        if typeString == 'ELUT':
            parentNode = node.parentNode
            lut = parentNode.LUT
            lutName = str(lut.output)
            pathIDs.append(str(node.name) + ' ( '+ typeString +' )' + \
                           'name: '+ lutName + ' loc: ' + str(node.location))
        else:
            pathIDs.append(str(node.name) + ' ( '+ typeString +' )')

    print " -> ".join(pathIDs)

    print "Delay:", str(path.delay)

#only print the path
def printPath(path):

    pathIDs = []
    print "Path:"
    for node in path.path:
        pathIDs.append(str(node.name))
    print " -> ".join(pathIDs)

##print the delays of all paths
def printAllPathDelays(paths):

    print "Delay of all paths:"
    for path in paths:
        printPathDelay(path)
        print ""


##print a comma seperate list of a path
# @param routingPath a routing path object you want to print
def printPathInFile (filename,routingPath):

    fh = open(filename,"w")

    for node in routingPath.path:

        if node.passTrough:
            continue

        Dump.dumpVerilogNameToFile(fh,node)

    fh.close()


# get the io path and read port delay for a node. therefore we used the source atrribute of this node
# @return a tuple (readPortDelay,ioPathDelay)
def getDelayForNode(sourceNode,node,destNode):

    readPortDelay = [0.0,0.0,0.0]
    ioPathDelay = [0.0,0.0,0.0]

    if node.passTrough:
        return ([0.0,0.0,0.0],[0.0,0.0,0.0])

    #current node is a lut node.
    #check if it use the unregistered or unregistered output.
    # - for the unregistered we have a read port delay and a io path delay
    #   and a valid source node.
    # - for the registered (use its flipflop) we have two cases:
    #   the path start or end with the flipflop. depending on the case
    #   we only use the read port delay or io path delay

    if node.isElut():

        if node.UseItsFlipflop():

            #end with a flipflop: destnode is a lut node and
            #we must include the read delay of the ff
            if (destNode is None):
                return (node.ffReadPortDelay,[0.0,0.0,0.0])

            #start with a flipflop. current node is a lut
            if (destNode is not None):
                return ([0.0,0.0,0.0],node.ffIODelay)

        #timing for a elut which use its unregistered output:
        #the source node will never be None, because path don't start
        #by a unregistered used lut.
        else:
            portIndex = node.inputs.index(sourceNode.name)

            #because the verilog is written downto, the first index is the last port.
            #correct the port index
            portIndex = (globs.host_size-1)- portIndex

            readPortDelay = node.readPortDelay[portIndex]
            ioPathDelay = node.ioPathDelay[portIndex]

            return (readPortDelay,ioPathDelay)


    #find the port index where the source is connected to

    #the node is a ffmux. We have to check which input of the mux
    #is used(registered or unregistered) and choose the right delay
    if node.isBleMux():

        #the registered output is the first input
        if sourceNode.UseItsFlipflop():
            portIndex = 0

        #the unregistered output is the second input
        else:
            portIndex = 1

    #the rest of the nodes get the port index from the source
    #(global routing muxes)
    else:

        #sourceNode is only not always set e.g when node is a startpoint.
        #get it. we only can't do this when we node is lut.
        #then the source attribute is not set
        sourceName = node.source
        sourceNode = globs.technologyMappedNodes.getNodeByName(node.source)

        portIndex = node.inputs.index(sourceNode.name)

    #because the verilog is written downto, the first index is the last port.
    #correct the port index
    portIndex = (globs.host_size-1)- portIndex

    #adjustment for delays
    #time to travel through the component + routing delay

    readPortDelay = node.readPortDelay[portIndex]
    ioPathDelay = node.ioPathDelay[portIndex]

    return (readPortDelay,ioPathDelay)


#dump every delay in detail
def dumpAllDelays(path):

    sourceNode = None
    destNode = None
    for index,node in enumerate(path.path):

        #node is not at the end, update th4e destNode
        if index + 1 < len(path.path):
            destNode = path.path[index + 1]
        else:
            destNode = None

        #get the delay and add it
        (readPortDelay,ioPathDelay) = getDelayForNode(sourceNode,node,destNode)

        print 'node name: ' + str(node.name) + ' readport: ' + str(readPortDelay[2]) + ' iopath: '+ str(ioPathDelay[2]) + \
              ' sum: ' + str(readPortDelay[2] + ioPathDelay[2])

        #update the sourceNode
        sourceNode = node


#print the critical path delay
def printCriticalPathDelay(criticalPath):

    #we split the path in two parts:
    #the ordered layer + the rest

    delayRest = [0.0,0.0,0.0]

    # now get the rest delay through subtraction
    if (not globs.params.skipOrderedLayerTiming):
        delayRest = numpy.subtract(criticalPath.delay,criticalPath.orderedDelay)

    #dump all delay:
    print 'dump all delays'
    dumpAllDelays(criticalPath)

    print "Critical path max delay is: " + str(criticalPath.delay[2]) + " " + globs.params.timeFormat
    print "Ordered delay : " + str(criticalPath.orderedDelay[2]) + " " + globs.params.timeFormat
    print "Rest delay is: " + str(delayRest[2]) + " " + globs.params.timeFormat

    print "f_worstcase is thus: " + str((1.0/ (criticalPath.delay[2] * globs.params.timeScale)) * 1/1000000 ) + " MHz"
    print "f_avg is thus: " + str((1.0/ (criticalPath.delay[1] * globs.params.timeScale)) * 1/1000000 ) + " MHz"
    print "f_bestcase is thus: " + str((1.0/ (criticalPath.delay[0] * globs.params.timeScale)) * 1/1000000 ) + " MHz"


##perform a timing analysis of the circuit in the mapped node graph.
def performTimingAnalysis():

    sources, sinks = findSinksAndSources()

    #searc all paths
    paths = trackPathsBackwards(sources,sinks)

    #update the delay and edgesWithoutDelay attribut for every path
    calcPathDelays(paths)

    for path in paths:
        if path.edgesWithoutDelay > 0:
            print "Path has " + str(path.edgesWithoutDelay) + " edges had no delay during the analysis."
            printPath(path)

    criticalPath = findCriticalPath(paths)

    if criticalPath == None:
        print "Error: No critical path found"
    else:
        print "Critical path found with " + str(criticalPath.pathlength) + " hops"

        #print the nodes of the critical path
        printPath(criticalPath)

        #print the delay
        printCriticalPathDelay(criticalPath)

        #export the critical path
        printPathInFile('criticalPath.txt',criticalPath)

        #now print all paths for debug purpose
        #printAllPathDelays(paths)

        #printPathDelay(criticalPath)
