# use this if you want to include modules from a subforder
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"VprParsers")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import structs
import globs
import time
import closNetwork
import Dump
import RRGraphParser
import copy

#clean the graph
#vpr7 and especially vpr8 produces sinks/source with only one ipin/opin
#connected and this opins/ipins are undriven. Also there exists undriven ipin/opin
#with a connection to an active sink/source.
#These nodes are completly useless and will be removed from the graph.
def removeUndrivenNodes():

    #in a first round kill undriven ipins.
    #then we could kill the now undriven sources and sinks in a second run

    #find the undriven nodes and kill them
    for n in globs.nodes:

        if n.type is 3: #OPIN.

            #check if he's undriven
            if len(n.edges) == 0:

                #dismount him from his source. there should be only one source edge

                #sanity check. only one sink edge
                if len(n.inputs) != 1:
                    print 'error multiply edges for an input'
                    sys.exit(0)

                #dismount him
                sourceId = n.inputs[0]
                source = globs.nodes[sourceId]
                source.edges.remove(n.id)

                #now kill the node
                n.inputs = []
                n.edges = []
                n.type = 0


        if n.type is 4: #IPIN
            #check if he's undriven
            if len(n.inputs) == 0:

                #dismount him from his sink. there should be only one sink edge

                #sanity check. only one sink edge
                if len(n.edges) != 1:
                    print 'error multiply edges for an input'
                    sys.exit(0)

                #dismount him
                sinkId = n.edges[0]
                sink = globs.nodes[sinkId]
                sink.inputs.remove(n.id)

                #now kill the node
                n.inputs = []
                n.edges = []
                n.type = 0


    #now kill the undriven sources and sinks

    for n in globs.nodes:

        if n.type is 1: #SINK
            #test if the sink node is undriven or has only one
            #undriven child

            #if it is undriven remove it from the graph
            if len(n.inputs) == 0:
                #type null signals an removed nodes
                #TODO: change the node graph to a dictionary
                n.inputs = []
                n.edges = []
                n.type = 0

        elif n.type is 2: #SOURCE

            #test if the source node is undriven or has only one
            #undriven child

            #if it is undriven remove it from the graph
            if len(n.edges) == 0:
                #type null signals an removed nodes
                #TODO: change the node graph to a dictionary
                n.inputs = []
                n.edges = []
                n.type = 0


## build the simple network.
# In the simple network, every pin of a ble get
# its own inode, which can route from every input
# of the IIB. This can be a cluster input or a lut feedback.
def buildSimpleNetwork(cluster,key):

    # make inodes for internal cluster connection
    for lut in range(globs.params.N):
        cluster.LUT_input_nodes.append([])
        for pin in range(globs.params.K):#input nodes

            inode = structs.Node()
            inode.type = 7

            # append all cluster inputs as an input
            for clusterInput in cluster.inputs:
                inode.inputs.append(clusterInput.id)
            #apend all ffmuxes as an input
            for ffmux in cluster.LUT_FFMUX_nodes:
                inode.inputs.append(ffmux)

            inode.location = key
            # append the node dict
            globs.addNode(inode)
            #append the input node to the cluster.
            cluster.LUT_input_nodes[lut].append(inode.id)
            #connect the inode with the elut node
            elut = globs.nodes[cluster.LUT_nodes[lut]]
            elut.inputs.append(inode.id)




##builds for each cluster the inner structure (ble's+ IIB).
#The interconnection block can be implemented
#by a simple network or a clos network.
def build_inner_structure():

    count = len(globs.nodes)
    for key in globs.clusters:
        cluster = globs.clusters[key]

        #build lut and ffmux nodes and append them to the
        #node graph

        for lut in range(globs.params.N):
            #actual eLUT
            elut = structs.Node()
            elut.type = 8
            elut.location = key
            elut.eLUT = True
            # append to the node dict
            globs.addNode(elut)
            # write its id to the LUT_nodes list
            cluster.LUT_nodes.append(elut.id)

            ffmux = structs.Node()
            ffmux.type = 9
            ffmux.ffmux = True
            ffmux.inputs.append(elut.id)
            ffmux.location = key

            #LUT node drives this node.
            #Because we used the registered and unregisterd output, the source
            #of the mux is always the lut.
            #the routing will be handled by the useFF flag. when its on its use
            #channel 2 otherwise channel 1(the lut)
            #so therefore we can set the final routing always to the lut
            ffmux.source = elut.id

            #append the ffmux node to the node graph
            globs.addNode(ffmux)
            #append it to the cluster list
            cluster.LUT_FFMUX_nodes.append(ffmux.id)

            # Reconnect the corresponding cluster output opin in the node graph:
            # Disconnect it from the source node
            # Connect it to the ffmux
            opin_id = cluster.outputs[lut].id
            globs.nodes[opin_id].inputs = [ffmux.id]
            globs.nodes[opin_id].source = ffmux.id

        # we can use the clos or simple network
        if globs.params.UseClos:
            print ' ----------- build clos network ----------------'
            cluster.clos = closNetwork.buildClosNetwork(cluster, \
                       key, globs.params.I,globs.params.K)
        else:
            print ' ----------- build simple network --------------'
            buildSimpleNetwork(cluster,key)


## This function builds up the virtual fpga.
# First it reads the graph.echo file and build up the outer structure of the
# virtual fpga, consisting of the clusters, I/O Pins, and switchboxes.
# It also builds up the node graph and inits the connections to the
# outer structure through the driver objects.
# Second it builds the inner structure (IIB + ble's) for each cluster.
# @param filename the path to the graph.echo file
def load_graph(filename):

    #parse the routing ressource graph file
    if globs.params.vpr8:
        (clusterx,clustery,nodeGraph) = RRGraphParser.parseGraphXml(filename)
    else:
        (clusterx,clustery,nodeGraph) = RRGraphParser.parseGraph(filename)

    #TODO: WORKAROUND for now we copy the nodes node by node. later we will
    #use also a global NodeGraph instance
    #TODO: replace clusterx with params
    globs.nodes = copy.deepcopy(nodeGraph.nodes)
    globs.clusterx = clusterx
    globs.clustery = clustery

    #end up parsing.
    #now build the outer structure.

    #initialize the cluster grid, switchbox and IOs array.

    #initialize the clusters.
    #clusters are on all locations except (0,x) , (y,0) which are IOs
    for x in range(1, globs.clusterx):
        for y in range(1, globs.clustery):
            globs.clusters[(x,y)] = structs.Cluster()

    #every location get a switch box
    for x in range(0, globs.clusterx):
        for y in range(0, globs.clustery):
            globs.switchbox[(x,y)] = structs.SBox()

    #build the I/O blocks

    #build blocks from (0,1) - (0,clustery-1),
    #and (clusterx,1) - (clusterx,clusterx-1)
    for x in [0, globs.clusterx]:
        #TODO: TW: Removed unnecessary range extension
        for y in range(1, globs.clustery):
            globs.IOs[(x,y)] = structs.IO()

    #build blocks from (1,0) - (clusterx-1,0),
    #and (1,clustery) - (clusterx-1,clustery)
    for y in [0, globs.clustery]:
        #TODO: TW: Removed unnecessary range douplication
        for x in range(1, globs.clusterx):
            globs.IOs[(x,y)] = structs.IO()


    # set the input ids for every node in the graph
    for n in globs.nodes:
        for e in n.edges:
            globs.nodes[e].inputs.append(n.id)

    #counters for a later echo.
    global_outputs = 0
    global_inputs  = 0

    #dump the loaded graph, allows to compare it with later versions
    if globs.params.dumpNodeGraph:
        Dump.dumpGraph('loadedGraph')

    #remove undriven sources and sinks as well as their ipins/opins
    #these are not used nodes generate by vpr for some reasons i dont know
    removeUndrivenNodes()

    #append the source and sink nodes to the orderedInput
    #and orderedOutput list
    #init the drivers for the I/O blocks and switchboxes.
    for n in globs.nodes:

        # reuse SINKs and SOURCEs for ordered global IO
        if n.type is 1: #SINK
            continue
        elif n.type is 2: #SOURCE
            continue

        # for OPINs and IPINs a notable assumption was made
        # that they are listed in increasing order in the file,
        # while the SOURCEs and SINKs can be spread over
        # this file.
        # TODO: Is that always true?

        # This is important because the orderedInput and orderedOutput lists
        # are append the corresponding source and sink nodes
        # for that OPINs and IPINs in their order.


        # The inputs for OPINs are SOURCE Nodes,
        # the edges of IPINs are SINK nodes

        #node is an OPIN
        elif n.type is 3:
            # OPIN of a global IO pad is an FPGA input

            # check if this is a input pin on a I/O block,
            # by checking if the location is on the edge of the fpga
            if n.location[0] in [0, globs.clusterx] \
            or n.location[1] in [0, globs.clustery]:
                #init a corresponding driver for this node.
                globs.IOs[n.location].inputs.append(structs.Driver(n.id, n.index))

                # add the SOURCE node id to the orderedInputs list
                # The SOURCE node id is only inputs[0],
                # because an fpga input pin have only
                # one SOURCE node (one input).
                globs.orderedInputs.append(n.inputs[0])
                global_inputs += 1

            #this is a clusters output pin
            #append it to the ouput list
            else:
                globs.clusters[n.location].outputs.append(structs.Driver(n.id,n.index))
                #print 'clust output', n.location, n.id

        #node is an IPIN
        elif n.type is 4:
            # IPIN of a global IO pad is an FPGA output

            # global output without predecessor can be ignored

            #TODO: THIS should be DEPRECATED because of the function call
            #removeUndrivenNodes()
            if len(n.inputs) == 0: #dont get input from dangling node
                print 'dropping node', n.id, 'from', n.location

            else:
                # check if this is a ouput pin on a I/O block,
                # by checking if the location is on the edge of the fpga
                if n.location[0] in [0, globs.clusterx] \
                or n.location[1] in [0, globs.clustery]:

                    #init a corresponding driver for this node.
                    globs.IOs[n.location].outputs.append(structs.Driver(n.id,n.index))

                    #TODO: why only edge[0]. okay there can be only one.
                    #when not you have multiple drivers for that output pin
                    #or this pin have them as an input?

                    #add the SINK node id to the orderedOutputs list
                    globs.orderedOutputs.append(n.edges[0])
                    global_outputs += 1

                #this is a clusters output pin
                #append it to the ouput list
                else:
                    globs.clusters[n.location].inputs.append(structs.Driver(n.id, n.index))

        #node is a CHANNEL
        elif n.type is 5 or n.type is 6:
            #get the corresponding switchbox for that node
            source = n.location[0:2]
            sbox = globs.switchbox[source]
            #append the driver to this node to the switchbox
            if n.type is 5:
                sbox.driversx.append(structs.Driver(n.id, n.index, n.dir))
            else:
                sbox.driversy.append(structs.Driver(n.id, n.index, n.dir))

    print "Global IO: out", global_outputs, "and in", global_inputs

    # build a list of ids for all IPINs and OPINs nodes of the graph
    # go through the locations and copy the ids
    # of the IPINS and OPins of that location
    allOutputNodes = []
    allInputNodes = []
    for key in globs.IOs:
        io = globs.IOs[key]

        # append the IPIN node. yes the IPIN :)
        for i in io.outputs:
            allOutputNodes.append(i.id)

        # append the OPIN node.
        for i in io.inputs:
            allInputNodes.append(i.id)

    # create global I/O permutation muxes for the fpga inputs.
    # Therefore transform the source and sink nodes to I/O permutation muxes

    # go through all OPINs nodes step by step.
    # grab their corresponding SOURCE node and add the other
    # available OPINs as an edge to that source
    for i,node in enumerate(allInputNodes):
        # get the corresponding SOURCE node of that OPIN
        # it is the same id as the input of the OPIN
        source = globs.nodes[globs.orderedInputs[i]]
        source.name = ''
        # Disabling this should automatically disable
        # the permutation MUXes and their configuration...
        if globs.params.orderedIO:
            source.type = 10
            #change the location of that source
            source.location = (0, 0)
            # add the other OPINS as an edge for that source
            for input in allInputNodes:
                # if its not the initial edge (the initial OPIN),
                # add this OPIN
                if input != source.edges[0]:
                    #add the opin
                    source.edges.append(input)
                    # also set the source node as an input to that OPIN
                    globs.nodes[input].inputs.append(source.id)

    # create global I/O permutation muxes for the fpga outputs.
    # go through all IPINs nodes step by step.
    # grab their corresponding SINK node and add the other
    # available IPINs as an input to that sink
    for i,node in enumerate(allOutputNodes):
        # get the corresponding SINK node of that IPIN
        # it is the same id as the edge of the IPIN
        sink = globs.nodes[globs.orderedOutputs[i]]
        sink.name = ''
        # Disabling this should automatically disable
        # the permutation MUXes and their configuration...
        if globs.params.orderedIO:
            sink.type = 10
            #change the location of that sink
            sink.location = (globs.clusterx, globs.clustery)
            for output in allOutputNodes:
                # if its not the initial input (the initial IPIN),
                # add this IPIN
                if output != sink.inputs[0]:
                    #add the ipin
                    sink.inputs.append(output)
                    # also set the sink node as an edge to that IPIN
                    globs.nodes[output].edges.append(sink.id)


    print "All input nodes: ",  allInputNodes
    print "All output nodes: ",  allOutputNodes

    #build the inner structure
    build_inner_structure()
