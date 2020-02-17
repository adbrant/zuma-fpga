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

    #get the corresponding port delay of that input pin
    #if its the start node of the path we omit this delay
    if (not start):
        portDelay = source.readPortDelay[portIndex]

    #now get the io path delay.
    ioPathDelay = source.ioPathDelay[portIndex]

    #the delays are vectors (min,avg,max). add them with numpy
    result = numpy.add(portDelay,ioPathDelay)

    #terminate if we are at the end of the path
    if source.name == target.name:
        return result

    #else we add the delay of the next hop.

    nextInputName =  source.name
    #intermediate mapped nodes have only one edge
    nextSourceNode = globs.technologyMappedNodes.getNodeByName(source.edge[0])

    newResult = getPathDelay(nextSourceNode,target,nextInputName,False)
    result = numpy.add(newResult,result)


    return result


# got through all nodes of the nodegraph and annotate the io path delay and the port delay
def AnnotateTiming():

    for node in globs.nodes:

        #skip sources and sinks and deleted nodes.
        if node.type <= 2:
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
                #is an input of the parent node
                inputNode = globs.technologyMappedNodes.getNodeByName(inputName)
                if inputNode.parentNode.id != node.id:

                        #get the delay for this input
                        target = node.mappedNodes[-1]
                        source = firstlvlNode
                        pathDelay = getPathDelay((source,target,inputName)

                        #add it to the dict
                        ioPathDelay[inputNode.parentNode.id] = pathDelay

                        #get the port delay. therfore we calc the correct port inde
                        portIndex = source.inputs.index(inputName)
                        portIndex = (globs.host_size-1)- portIndex
                        portDelay = source.readPortDelay[portIndex]

                        readPortDelay[inputNode.parentNode.id] = portDelay

        #now add the path delay and port delay to the node
        node.ioPathDelay = ioPathDelay
        node.portDelay = readPortDelay
