from structs import *
import globs
import time
import re
import const
import closNetwork
import Dump

## build the simple network.
# In the simple network, every pin of a ble get
# its own inode, which can route from every input
# of the IIB. This can be a cluster input or a lut feedback.
def buildSimpleNetwork(cluster,key):

    # make inodes for internal cluster connection
    for lut in range(globs.params.N):
        cluster.LUT_input_nodes.append([])
        for pin in range(globs.params.K):#input nodes

            inode = Node()
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
            elut = Node()
            elut.type = 8
            elut.location = key
            elut.eLUT = True
            # append to the node dict
            globs.addNode(elut)
            # write its id to the LUT_nodes list
            cluster.LUT_nodes.append(elut.id)

            ffmux = Node()
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

    #parse the lines of the following format:

    #      id  type   location   index       direction        driver
    #Node: 0   SINK   (0, 1)     Ptc_num: 0  Direction: OPEN  Drivers: OPEN

    #open the graph.echo file
    fh = open(filename,"r")

    #counter for tracking the current id node.
    id = 0

    #parse the file and build up the node graph
    while 1:
        line = fh.readline() # read node type, location, ...
        if not line:
            break
        str = line.split()
        #print id, int(str[1])
        #assert(id is int(str[1]))
        n = Node()
        #set the id.
        n.id = int(str[1])
        if (str[2] == 'SINK'):
            n.type = 1
        elif (str[2] == 'SOURCE'):
            n.type = 2
        elif (str[2] == 'OPIN'):
            n.type = 3
        elif (str[2] == 'IPIN'):
            n.type = 4
        elif (str[2] == 'CHANX'):
            n.type = 5
        elif (str[2] == 'CHANY'):
            n.type = 6
        else:
            assert(0)


        nums = re.findall(r'\d+', line)
        nums = [int(i) for i in nums ]

        #get the location and the index.
        #The index is the pad position, pin position or track number
        #depending its a pin on an I/O block, cluster or a channel.
        #Depending on this node type the values are on different positions
        #in the file.
        if n.type < 5 or len(nums) < 5:
            n.location = (nums[1],nums[2])
            n.index = nums[3]
        else:
            n.location = (nums[1],nums[2],nums[3],nums[4])
            n.index = nums[5]

        #set the direction of the node.
        if n.type > 4:
            dir = line.split(' ')[-3]
            if dir == 'INC_DIRECTION':
                #north or east
                if n.type is 5:
                    n.dir = const.E
                else:
                    n.dir = const.N
            else:
                if n.type is 5:
                    n.dir = const.W
                else:
                    n.dir = const.S

        #read the edge ids and append them to
        #the edge list of the  node
        line = fh.readline() # read edges
        nums = re.findall(r'\d+', line)
        #assign the ids
        n.edges = [int(i) for i in nums[1:]]

        #skip the rest of the information
        line = fh.readline() # skip switch types
        line = fh.readline() # skip (occupancy?) and capacity
        line = fh.readline() # skip R and C
        line = fh.readline() # skip cost index
        line = fh.readline() # skip newline dividing records

        #clusterx,clustery are the maximal value of location coords.
        #find these maximal location coords
        globs.clusterx = max(globs.clusterx,n.location[0])
        globs.clustery = max(globs.clustery,n.location[1])

        #append the node to the global node graph
        globs.nodes.append(n)

        #check if the node was append in a previous loop.
        #current node should be the last node in the list.
        if globs.nodes[n.id] is not n:
            print 'graph error', len(globs.nodes), n.id

        #increase the current node id
        id = id + 1

    #end up parsing.
    #now build the outer structure.

    #initialize the cluster grid, switchbox and IOs array.

    #initialize the clusters.
    #clusters are on all locations except (0,x) , (y,0) which are IOs
    for x in range(1, globs.clusterx):
        for y in range(1, globs.clustery):
            globs.clusters[(x,y)] = Cluster()

    #every location get a switch box
    for x in range(0, globs.clusterx):
        for y in range(0, globs.clustery):
            globs.switchbox[(x,y)] = SBox()

    #build the I/O blocks

    #build blocks from (0,1) - (0,clustery-1),
    #and (clusterx,1) - (clusterx,clusterx-1)
    for x in [0, globs.clusterx]:
        #TODO: TW: Removed unnecessary range extension
        for y in range(1, globs.clustery):
            globs.IOs[(x,y)] = IO()

    #build blocks from (1,0) - (clusterx-1,0),
    #and (1,clustery) - (clusterx-1,clustery)
    for y in [0, globs.clustery]:
        #TODO: TW: Removed unnecessary range douplication
        for x in range(1, globs.clusterx):
            globs.IOs[(x,y)] = IO()


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

    #append the source and sink nodes to the orderedInput
    #and orderedOutput list
    #init the drivers for the I/O blocks and switchboxes.
    for n in globs.nodes:

        # reuse SINKs and SOURCEs for ordered global IO
        if n.type is 1: #SINK
            pass
        elif n.type is 2: #SOURCE
            pass

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
                globs.IOs[n.location].inputs.append(Driver(n.id, n.index))

                # add the SOURCE node id to the orderedInputs list
                # The SOURCE node id is only inputs[0],
                # because an fpga input pin have only
                # one SOURCE node (one input).
                globs.orderedInputs.append(n.inputs[0])
                global_inputs += 1

            #this is a clusters output pin
            #append it to the ouput list
            else:
                globs.clusters[n.location].outputs.append(Driver(n.id,n.index))
                #print 'clust output', n.location, n.id

        #node is an IPIN
        elif n.type is 4:
            # IPIN of a global IO pad is an FPGA output

            # global output without predecessor can be ignored
            if len(n.inputs) == 0: #dont get input from dangling node
                print 'dropping node', n.id, 'from', n.location

            else:
                # check if this is a ouput pin on a I/O block,
                # by checking if the location is on the edge of the fpga
                if n.location[0] in [0, globs.clusterx] \
                or n.location[1] in [0, globs.clustery]:

                    #init a corresponding driver for this node.
                    globs.IOs[n.location].outputs.append(Driver(n.id,n.index))

                    #TODO: why only edge[0]. okay there can be only one.
                    #when not you have multiple drivers for that output pin
                    #or this pin have them as an input?

                    #add the SINK node id to the orderedOutputs list
                    globs.orderedOutputs.append(n.edges[0])
                    global_outputs += 1

                #this is a clusters output pin
                #append it to the ouput list
                else:
                    globs.clusters[n.location].inputs.append(Driver(n.id, n.index))

        #node is a CHANNEL
        elif n.type is 5 or n.type is 6:
            #get the corresponding switchbox for that node
            source = n.location[0:2]
            sbox = globs.switchbox[source]
            #append the driver to this node to the switchbox
            if n.type is 5:
                sbox.driversx.append(Driver(n.id, n.index, n.dir))
            else:
                sbox.driversy.append(Driver(n.id, n.index, n.dir))

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
