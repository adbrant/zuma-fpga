import numpy
import globs


## get the delay of a path from one mapped node to another.
#Therefore sum up all port and io path delay on the way.
#@param source a mapped node reference of the source of the path
#@param target a mapped node reference of the taget of the path
#@param inputName input name of the corresponding pin of the given source node
#@param start signals the start of the path. The read port delay of first node
#             of the path isn't add to the returned result.
def getPathDelay(source,target,inputName,start = True):

    #get the port delay and the io path delay of the current source.
    #then add it to the overall delays

    #get the correct port index for the given input name pin
    #because the verilog is written downto, the first index is the last port.
    portIndex = source.inputs.index(inputName)
    portIndex = (globs.host_size-1)- portIndex
    #print 'port index' + str(portIndex) + ' of ' + str(source.name)

    #get the corresponding port delay of that input pin
    #if its the start node of the path we omit this delay
    portDelay = [0.0,0.0,0.0]
    ioPathDelay = [0.0,0.0,0.0]

    if (not start) and (not source.passTrough):
            portDelay = source.readPortDelay[portIndex]

    #now get the io path delay. skip passtrough nodes (they have no timing)
    if not source.passTrough:
        ioPathDelay = source.ioPathDelay[portIndex]

    #the delays are vectors (min,avg,max). add them with numpy
    result = numpy.add(portDelay,ioPathDelay)

    #terminate if we are at the end of the path
    if source.name == target.name:
        return result

    #else we add the delay of the next hop.

    nextInputName =  source.name
    #intermediate mapped nodes have only one edge
    nextSourceNode = globs.technologyMappedNodes.getNodeByName(source.edges[0])

    newResult = getPathDelay(nextSourceNode,target,nextInputName,False)
    result = numpy.add(newResult,result)


    return result


# got through all nodes of the nodegraph and annotate the io path delay and the port delay
def AnnotateTiming():

    for node in globs.nodes:

        #skip sources and sinks and deleted nodes.
        if node.type <= 2:
            continue

        #if the node is a pasthrough his mapped node is also one
        #skip it. Currently the node graph doesn't have a passTrough flag
        #TODO fix this
        if len(node.mappedNodes) == 1:
            name = node.mappedNodes[-1]
            mappedNode = globs.technologyMappedNodes.getNodeByName(name)
            if mappedNode.passTrough:
                continue

        #for every input get the path delay started
        #from the first lvl nodes to the last mapped node
        #and use these first lvl nodes for the port delay

        ioPathDelay = {}
        readPortDelay = {}

        #get all first lvl mapped nodes of this node.
        firstlvlNodes = globs.technologyMappedNodes.getFistLvlNodes(node)

        for firstlvlNode in firstlvlNodes:
            for inputName in firstlvlNode.inputs:

                #check if the input of this mapped node
                #is an input of the parent node. we need a edge to an outer node
                inputNode = globs.technologyMappedNodes.getNodeByName(inputName)
                if inputNode.parentNode.id == node.id:
                    continue

                #get the last mapped node of
                targetName = node.mappedNodes[-1]
                target = globs.technologyMappedNodes.getNodeByName(targetName)

                #if the node is a passtrough go down until the target and find the
                #first not passtrough node
                #TODO: can this happen?
                source = firstlvlNode
                sourceInputName = inputName

                if source.passTrough:
                    while(source.passTrough and (source.name != target.name)):
                        sourceInputName = source.name
                        source = globs.technologyMappedNodes.getNodeByName(source.edges[0])

                #now get the path delay timing
                pathDelay = getPathDelay(source,target,sourceInputName)

                #get the port delay. therfore we calc the correct port index
                portIndex = source.inputs.index(sourceInputName)
                portIndex = (globs.host_size-1)- portIndex
                portDelay = source.readPortDelay[portIndex]

                #add it to the dict
                ioPathDelay[inputNode.parentNode.id] = pathDelay
                readPortDelay[inputNode.parentNode.id] = portDelay

        #now add the path delay and port delay to the node
        node.ioPathDelay = ioPathDelay
        node.readPortDelay = readPortDelay
