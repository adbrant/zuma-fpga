import os, sys, inspect
from copy import deepcopy
import numpy


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
        self.delayList = []
        self.path = [ ]
        self.pathlength = 0

    def __init__(self, node):
        #the delay with min avg and max delay
        self.delay = [0.0,0.0,0.0]
        #for debug purpose.
        #a list of the used delays
        self.delayList = []
        self.path = [ node ]
        self.pathlength = 0


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
        #get one output mux node
        IOMuxOutputNode = globs.nodes[globs.orderedOutputs[0]]

        opinIdList += IOMuxInputNode.edges
        ipinIdList += IOMuxOutputNode.inputs

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
        if ipinNode.source >= 0:
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

    #the delay of the hop
    #delay tuple has the form: (min,average,max)
    delay = [0.0,0.0,0.0]

    #passThrough nodes have no delay
    if not destNode.passTrough:

        #the destination is a mux. We have to check which input of the mux
        #is used(registered or unregistered) and choose the right delay
        if destNode.isBleMux():

            #the mux uses the registered input.
            if newSrcNode.UseItsFlipflop():
                #the registered output is the first input
                portIndex = 0
                #get the setup time for the flipflop.
                #the delay on the read port is not important here,
                #because the path starts on the end of the flipflop
                delay = numpy.add(newSrcNode.ffIODelay,delay)
                #for debug purpose add it to the list
                path.delayList.append(newSrcNode.ffIODelay)

            #otherwise we use the unregistered port
            else:
                #the unregistered output is the second input
                portIndex = 1

        #if the destination is a elut we must include the read delay of the ff
        if destNode.isElut():
            if destNode.UseItsFlipflop():
                delay = numpy.add(newSrcNode.ffReadPortDelay,delay)
                #for debug purpose add it to the list
                path.delayList.append(newSrcNode.ffReadPortDelay)

        #because the verilog is written downto, the first index is the last port.
        #correct the port index
        portIndex = (globs.host_size-1)- portIndex

        #adjustment for delays
        #time to travel through the component + routing delay

        portDelay = destNode.readPortDelay[portIndex]
        ioPathDelay = destNode.ioPathDelay[portIndex]
        #for debug purpose add it to the list
        path.delayList.append(destNode.readPortDelay[portIndex])
        path.delayList.append(destNode.ioPathDelay[portIndex])

        tmpDelay = numpy.add(ioPathDelay,portDelay)
        #add it to the current delay
        delay = numpy.add(delay,tmpDelay)

        #check if there is a delay information of the route.
        #the iopath delay is always available
        if portDelay == [0.0,0.0,0.0]:

            print "connection " + newSrcNode.name +" to " +  destNode.name + " has no delay"
            return 1

        else:
            #add it on the path delay
            path.delay = numpy.add(path.delay,delay)

    return 0


##calculate the path delay for all paths, going backwards from sinks to sources.
def trackPathsBackwards(sources,sinks):
    activePaths = initActivePaths(sinks)

    #now find the critical path
    edgesWoDelay = 0
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
                            edgesWoDelay += prependNodeToPath(childpath,newSrcNode)

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
                edgesWoDelay += prependNodeToPath(path,newSrcNode)

                #check if we've arrived at a source yet.
                if newSrcNode in sources:
                    finishedPaths.append(path)
                else:
                    activePaths.append(path)

    return finishedPaths, edgesWoDelay


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

    print "Delay list:"
    #print reversed list
    print str(path.delayList[::-1])

##print the delays of all paths
def printAllPathDelays(paths):

    print "Delay of all paths:"
    for path in paths:
        printPathDelay(path)
        print ""


##print a comma seperate list of a path
# @param routingPath a routing path object you want to print
def printSDFPathtoFile (filename,routingPath):

    fh = open(filename,"w")


    for node in routingPath.path:

        if node.eLUT:
            prefix = 'LUT_'
        else:
            prefix = 'MUX_'

        if node.passTrough:
            continue

        if node.isOnCluster:
            (x,y) = node.location
            fh.write(  globs.params.instancePrefix + 'cluster_'+ str(x) + '_' + str(y) +'/' + prefix +  str(node.name) + '\n')

        else:
            fh.write( globs.params.instancePrefix + prefix + str(node.name) + '\n')

    fh.close()


##perform a timing analysis of the circuit in the mapped node graph.
def performTimingAnalysis():

    sources, sinks = findSinksAndSources()

    paths, edgesWoDelay = trackPathsBackwards(sources,sinks)
    print str(edgesWoDelay) + " edges had no delay during the analysis."

    criticalPath = findCriticalPath(paths)
    if criticalPath == None:
        print "Error: No critical path found"
    else:
        print "Critical path found with " + str(criticalPath.pathlength) + " hops"
        print "Path:"
        pathIDs = []
        for node in criticalPath.path:
            pathIDs.append(str(node.name))
        print " -> ".join(pathIDs)
        print
        print "Critical path delay is: " + str(criticalPath.delay[2]) + " " + globs.params.timeFormat
        print "f_worstcase is thus: " + str((1.0/ (criticalPath.delay[2] * globs.params.timeScale)) * 1/1000000 ) + " MHz"
        print "f_avg is thus: " + str((1.0/ (criticalPath.delay[1] * globs.params.timeScale)) * 1/1000000 ) + " MHz"
        print "f_bestcase is thus: " + str((1.0/ (criticalPath.delay[0] * globs.params.timeScale)) * 1/1000000 ) + " MHz"

        printSDFPathtoFile('criticalPath.txt',criticalPath)

        #now print all paths for debug purpose
        #printAllPathDelays(paths)

        #printPathDelay(criticalPath)
