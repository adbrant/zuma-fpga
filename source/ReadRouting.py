# use this if you want to include modules from a subforder
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"VprParsers")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)


import globs
import RoutingParser
#import pdb

## Parse the routing file.
# The routing file contains the global routing of the fpga,
# so we apply this routing by setting the right input id
# to the source attribute of the muxes of the global routing.
def read_routing(filename ):

    #parse the routing net file to get a list of used nets
    nets = RoutingParser.parseRouting(filename)

    #assign the nets to the global net dictionary
    for net in nets:
        globs.nets[net.name] = net

    #we now should have all routed signals in nets

    #For each net, we will step through the traces,
    #defining the path for this route.
    #We apply this path to the nodes in the node graph,
    #by setting the source attribute of each node of a path.
    #Because of the representation of a trace, which does include the location,
    #we use the driver elements of these locations
    #to get the corresponding node in the node graph.
    #so we use the drivers of the pins of the cluster or I/O elements or the
    #drivers of a switchbox.
    for n in globs.nets.values():

        #the list of the current found nodes for this path
        #for each trace we add the corresponding node to this list.
        nodelist = []

        if len(n.source) == 0:
            print "net has no source, assuming global net (clock)"
            continue

        #this is the node id for the previous trace.
        #this will be need if we want to change the source attribute
        #of the current found node
        last_node = 0

        #check if the location of the source is at the edge of the fpga
        #if this is true than the source of the net is an I/O pin
        #try to get the node id of the source of this net
        #by checking the drivers of the IOs structure
        if n.source[0] in [0, globs.clusterx] or \
           n.source[1] in [0, globs.clustery]:
            for input in globs.IOs[tuple(n.source[0:2])].inputs:
                if input.index is n.source[2]:
                    #set the node id,which is used as a source by the next node
                    last_node = input.id
                    break
        #the source is not an IO pin => the source must be a pin of a cluster
        #Get the node id of the source of this net
        #by using the output driver list of the cluster
        else:
            #set the node id,which is used as a source by the next node
            last_node = globs.clusters[tuple(n.source[0:2])].outputs[n.source[2] - globs.params.I].id

        #append the the source node to the nodelist
        nodelist.append(last_node)

        # Just a counter for the IO sinks.
        # we must track the current sink count, to get the right entry
        # in the lastnetmapping list
        ioSinkCounter = -1

        #now go through all traces,
        #find the drivers and the corresponding nodes.
        #then change the source attribute to the last found node
        for trace in n.trace:


            #a list of possible drivers of a switchbox for this trace.
            #used for X/Y channel traces.
            #is parsed at the end of of this loop
            drivers = []

            #X/Y channel trace are parsed at the end fo this loop.
            #only add the drivers of the switchbox to the driver list
            if trace.type == 'X':
                drivers = globs.switchbox[tuple(trace.loc[0:2])].driversx

            #X/Y channel trace are parsed at the end fo this loop.
            #only add the drivers of the switchbox to the driver list
            elif trace.type == 'Y':
                drivers = globs.switchbox[tuple(trace.loc[0:2])].driversy

            #the trace is a sink.
            #check if its a pin on I/O or on a cluster and get the driver.
            #Then change the source attribute of the corrresponding node.
            elif trace.type == 'SINK':

                #just some debugging
                #pdb.set_trace()

                #NOTE: for a sink we do not update the last_node id
                #because the next route will not connect to this node

                #the location is on the edge. The sink is an I/O pin
                if trace.loc[0] in [0, globs.clusterx] or \
                   trace.loc[1] in [0, globs.clustery]:

                    #try to find the driver of the IO pin in the IO output list.
                    found = False

                    #got a IO sink. increase the counter
                    ioSinkCounter = ioSinkCounter +1

                    #TODO: why do we need the enumeration? i is never used.
                    for i,  output in enumerate(globs.IOs[trace.loc].outputs):

                        #compare the pad numbers
                        if output.index is trace.index:
                            #found the driver
                            #set the source and net attribute of the driver
                            #and then set the source attribute
                            #of the corresponding node
                            #TODO: is the source and net attribute of the driver
                            #used anywhere?
                            output.source = last_node
                            output.net = n.name
                            globs.nodes[output.id].source = last_node

                            #If this is a net between a fpga input and a fpga output:
                            #Try to use the lastnetmapping in this case
                            #to get the blif name of the corresponding SINK node
                            #for the current IPIN ouput node,
                            #by searching the net name in this mapping.
                            #This blif name is than used to get the instance of the sink node
                            #via the orederedOuputs list.

                            # In detail the lastnetmapping
                            # save the mapping (fpga input name, list of fpga output names).

                            # This mapping deliver us the intended result
                            # because the net name is same as the blif fpga input name.

                            #get the blif name of the corresponding SINK node
                            if n.name in globs.lastnetmapping:
                                outputNameList = globs.lastnetmapping[n.name]
                                name = outputNameList[ioSinkCounter]

                            #else we use the regular net name
                            else:
                                name = n.name

                            if last_node not in globs.nodes[output.id].inputs:
                                print 'error routing', output.id, last_node
                            #get the corresponding SINK node.
                            #Assign the current IPIN node as a source for that sink.
                            else:

                                if globs.params.orderedIO:
                                    for orderedoutput_id in globs.orderedOutputs:
                                        orderedoutput = globs.nodes[orderedoutput_id]
                                        if orderedoutput.name == name:
                                            orderedoutput.source = output.id
                                            found = True
                                            break
                            break

                    #did not found the driver
                    if found == False:
                        print 'Error finding FPGA output', \
                               n.name, 'at', trace.loc

                #not an IOs pin => the sink is a pin on a cluster
                else:
                    #try to find the driver in the clusters input driver list.
                    for input in globs.clusters[trace.loc].inputs:
                        #compare the pin positions
                        if input.index is trace.index:
                            if input.id  in globs.nodes[last_node].edges:
                                #found the driver
                                #set the source and net attribute of the driver
                                #and then set the source attribute
                                #of the corresponing node
                                #TODO: is the source and net attribute
                                #of the driver used anywhere?
                                input.source = last_node
                                input.net = n.name
                                globs.nodes[input.id].source = last_node
                            else:
                                print n.name, trace.loc, input.index
                                print 'error node', last_node, input.id
                                print nodelist
                                assert(0)

                continue

            #the trace is a source.
            #check if its a pin on I/O or on a cluster and get the driver.
            #Then change the source attribute of the corrresponding node.
            else:
                #the location is on the edge. The source is an I/O pin
                if trace.loc[0] in [0, globs.clusterx] or \
                   trace.loc[1] in [0, globs.clustery]:

                    #try to find the driver of the IO pin in the IO input list.
                    found = False

                    for input in globs.IOs[trace.loc].inputs:
                        if input.index is trace.index:
                            #found the driver
                            #set the source and net attribute of the driver
                            #and then set the source attribute
                            #of the corresponing node
                            #TODO: is the source and net attribute
                            #of the driver used anywhere?
                            input.net = n.name

                            #a new trace will be processsed soon,
                            #change id of the last processed node.
                            last_node = input.id

                            #set the the source attribute of the frist opin to the
                            #right iomux when orderIO is activate

                            #TODO: i dont see why this is only valid
                            #for ordered id. The list orderedInputs also
                            #contains all sources when the option is disabled

                            #but it seems to produce some errors
                            #in the outputBlif routine when this is done always

                            #if globs.params.orderedIO:
                            for orderedinput_id in globs.orderedInputs:
                                orderedinput = globs.nodes[orderedinput_id]
                                if orderedinput.name == input.net:
                                    if globs.params.orderedIO:
                                        globs.nodes[last_node].source = orderedinput_id
                                    else:
                                        #WORKAROUND: use a flag to indicate
                                        #primary io pin
                                        #fixes like looking for the name
                                        #of the source dont work.

                                        #note: the opin has no edges to the found source
                                        #because the names are not set to the right sources
                                        #its only important that there is a source
                                        #with that netname. then the viewed node
                                        #(lastnode) is the right opin.

                                        globs.nodes[last_node].primaryOpin = True;
                                    found = True
                                    break

                            break

                    #did not found the driver
                    if found == False:
                        print 'Error finding FPGA input', \
                               n.name, 'at', trace.loc

                #not an IOs pin => the source is a pin on a cluster
                else:
                    #cluster
                    for output in globs.clusters[tuple(trace.loc)].outputs:
                        if output.index is trace.index:
                            last_node = output.id

                continue

            #now process the driver for X/Y channels:
            #first find the right driver
            for d in drivers:
                if d.index is trace.index:
                    driver = d
                    break

            #was this driver and the corresponding node processed before?
            #if it was processed, skip it.
            if driver.id in nodelist:
                pass

            #now we have the driver
            #set the source and net attribute of the driver
            #and then set the source attribute
            #of the corresponding node
            #TODO: is the source and net attribute
            #of the driver used anywhere?
            else:
                #some error checking
                if driver.id  in globs.nodes[last_node].edges:
                    #set the attributes.
                    driver.source = last_node
                    driver.net = n.name
                    globs.nodes[driver.id].source = last_node

                else:
                    print "error routing", last_node, driver.id, \
                          globs.nodes[last_node].edges

                #append the node to the nodelist
                nodelist.append(driver.id)

            #a new trace will be processed,
            #change id of the last processed node.
            last_node = driver.id
