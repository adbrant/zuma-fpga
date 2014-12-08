import os, sys, inspect

# use this if you want to include modules from a subforder
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"VprParsers")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import globs
from structs import *
from NetlistParser import parseNetlist
#from clos_routing import build_clos
from clos_routing import route_clos


##find the cluster by its CLB attribute
##search the clb name in the internal cluster list
##return the cluster object if found, else None
##param name The CLB name you want to find
def getClusterByName(name):

    for key in globs.clusters:
        if (globs.clusters[key].CLB == name):
            cluster = globs.clusters[key]
            return cluster
    return None

##check if the given net is in the input driver list of the cluster
##return True if the net is in the list otherwise False
def isNetInInputDriverList(net,cluster):
    for i in cluster.inputs:
        if i.net == net:
            return True
    #net was not found
    return False

##Append the inputs of a given ble to the clusters LUT_input_nets array.
def copyBleInputs(netlistBle,cluster):

    #the LUT_input_nets list has an entry for each ble.
    cluster.LUT_input_nets.append([])
    #copy the input tuples
    for netlistInput in netlistBle.inputs:
        cluster.LUT_input_nets[-1].append(netlistInput )

##copy the input netlist names and check
##if its in the input driver list of the current cluster
def copyClusterInputs(netlistCluster,cluster):
    #copy the input netlist names and check
    #if its in the input driver list of the current cluster
    for netlistInput in netlistCluster.inputs:
        #copy the input netlist name
        cluster.input_nets.append(netlistInput)
        #check if net is in the input driver list of the cluster
        if (netlistInput != 'open'):
            if not (isNetInInputDriverList(netlistInput,cluster)):
                print 'net not found, cluster', cluster.name, netlistInput

##copy a open keyword to the clusters LUTs list, so the instance numbers
##of the netlists points to the right ble names. see structure.py
def setupEmptyLut(cluster):
    #apend the lut to the clusters LUTs list
    cluster.LUTs.append('open' )

##copy the Lut to the clusters LUTs list.
##also update the nodes graph
def copyLut(netlistBle,cluster,bleIndex):

    lutname = netlistBle.lut.name
    #check if the lut output name is in the global Lut list
    if not (lutname in globs.LUTs):
        print 'Error in read_netlist: cannot find LUT', lutname
        return

    #apend the lut to the clusters LUTs list
    cluster.LUTs.append(lutname )
    #update the nodes graph
    globs.nodes[cluster.LUT_nodes[bleIndex]].eLUT = True
    globs.nodes[cluster.LUT_nodes[bleIndex]].bits = globs.LUTs[lutname].contents
    globs.nodes[cluster.LUT_nodes[bleIndex]].LUT = globs.LUTs[lutname]


#if this ble uses it flipflop but not its lut
#we have to build a passtrough lut
#because the fliflop dont uses the output of the lut of this ble
def copyFlipFlopBuildPasstrough(netlistBle,cluster,bleIndex):

    #in the mom we must add this Lut with the fliflop name
    #TODO: Is this with the new read_netlist important?
    #      change this for further versions
    latchName = netlistBle.flipflop.name
    #check if the lut output name is in the global Lut list
    if not (latchName in globs.latches):
        print 'Error in read_netlist: cannot find FF', latchName
        return

    #because we use the flipflop but not the lut, we need to change
    #the lut on this ble to a passthrough lut,
    #because we use the registered output of the lut for the flipflops.
    #so its just a passthrough lut which uses its flipflop
    #the name of the passtrough lut is the same as the latch

    #In addtion this flipflop is driven by a lut on another ble.
    #we have to switch of the useFF flag for this original lut

    #add the passtrough lut name (same as latchName)
    #to the clusters lut list
    cluster.LUTs.append(latchName)

    globs.nodes[cluster.LUT_nodes[bleIndex]].eLUT = True
    passThroughLUT = LUT()
    passThroughLUT.contents = []
    passThroughLUT.contents.append(('1',  '1'))
    passThroughLUT.output = latchName
    #the passtrough lut gets the original lut as an input
    passThroughLUT.inputs.append(globs.latches[latchName].input)
    passThroughLUT.useFF = True
    globs.nodes[cluster.LUT_nodes[bleIndex]].bits = passThroughLUT.contents
    globs.nodes[cluster.LUT_nodes[bleIndex]].LUT = passThroughLUT
    globs.LUTs[latchName] = passThroughLUT
    # As the FF is here with a dummy LUT,
    #we have to switch off the FF for the original LUT again
    globs.LUTs[globs.latches[latchName].input].useFF = False



#finish the clos network routing by applying the right source to the mux
# and build a newPinPositions List for the Lut, because the routing algo
#switch the vpr lut input pin positions
def finishClosNetworkRouting(RoutingVector,cluster):

    k = globs.params.K
    I = globs.params.I
    N = globs.params.N
    routing = route_clos(RoutingVector,I,k,N)

    #go through all inodes, which ids are in the stage1 and stage2 list.
    #turn on the right source switch to them

    #crossbars of stage1. format is:
    #[crossbar index] [crossbar output pin index] = cluster input pin number
    for crossbarIndex,crossbar in enumerate(routing[0]):
        #go through the input pin numbers
        for outputPinIndex,inputPinIndex in enumerate(crossbar):
            #the output must have a legal routing
            if inputPinIndex > -1:
                stageInodeId = cluster.clos.stage1[crossbarIndex].outputs[outputPinIndex]
                #get the right node id. look in the cluster input or lut feedback list
                #depending on the index
                #this was an input from the cluster input
                if inputPinIndex < globs.params.I:
                    nodeId = cluster.inputs[inputPinIndex].id
                #this must be a lut feedback
                else:
                    nodeId = cluster.getFFMuxNodeId(inputPinIndex - globs.params.I)
                #assign the source attribut
                globs.nodes[stageInodeId].source = nodeId

    #crossbars of stage2. format is:
    #[crossbar index] [crossbar output pin index] = cluster input pin number

    #find the corresponding 1 stage crossbar through the input number
    #connect the right output of this crossbar
    for crossbarIndex, crossbar in enumerate(routing[1]):
        for outputPinIndex,inputPinIndex in enumerate(crossbar):
            #find the 1 stage crossbar
            stage1Index = int(inputPinIndex/k)
            #connect the output
            # every i-the 1 stage crossbar is on the ith input of a second
            # stage crossbar
            if inputPinIndex > -1:
                nodeId = cluster.clos.stage2[crossbarIndex].outputs[outputPinIndex]
                stage1NodeId = cluster.clos.stage1[stage1Index].outputs[crossbarIndex]
                globs.nodes[nodeId].source = stage1NodeId

    #create the new RoutingVector for comparsions to the original
    newRoutingVector = [[-1 for j in range(globs.params.K)] for i in range(globs.params.N)]
    #assign the new InputPins to the new routing vector
    #note: the ith output of the j-th crossbar of the second stage ist
    #the j-th input of the i-th ble
    for crossbarIndex, crossbar in enumerate(routing[1]):
        for outputPinIndex,inputPinIndex in enumerate(crossbar):
            newRoutingVector[outputPinIndex][crossbarIndex] = inputPinIndex

    #create the newPinPositions list,
    #for appling the right lut content in the later stages
    #has the format: list: [ble Index] [list of (old pin position, new pin position)]
    newPinPositions = []
    #go trough the new Routing Vector and compare it woth the new one.
    for bleIndex , ble in enumerate(RoutingVector):
        #append a new ble dim
        newPinPositions.append([])
        for oldPinPosition,inputPinIndex in enumerate(ble):
            #skip unused Pins
            if inputPinIndex == -1:
                continue
            #the new position in the new routing vector
            newPinPosition = newRoutingVector[bleIndex].index(inputPinIndex)
            #append the tuple
            newPinPositions[bleIndex].append( (oldPinPosition,newPinPosition) )

    #save the information in the cluster object
    cluster.newPinPositions = newPinPositions

#apply the right id to the source attributes of the muxes (inodes)
def finishNormalRouting(RoutingVector,cluster):

    #go through the routing vector and set the source attribut
    for bleIndex, ble in enumerate(RoutingVector):
        for lutPinPosition,inputPinIndex in enumerate(ble):
            #skip unrouted pins
            if inputPinIndex == -1:
                continue
            #this was an input from the cluster input
            if inputPinIndex < globs.params.I:
                globs.nodes[cluster.getInodeId(bleIndex,lutPinPosition)].source \
                    = cluster.inputs[inputPinIndex].id
            #this must be a lut feedback
            else:
                #because the LUT_FFMUX_nodes is only for luts, we have to subtract I
                #from the interconnect input pin index
                globs.nodes[cluster.getInodeId(bleIndex,lutPinPosition)].source \
                    = cluster.getFFMuxNodeId(inputPinIndex - globs.params.I)

##finsish the routing by apply the right path for every mux
##of the internal routing. the muxes are represented by so called inodes
##and the reference to the inodes is done by the LUT_input_nodes list.
##to apply the path the source attribut of the inode object is set to
##the right node id
##Therefore we provide the RoutingVector list  as an internal
##representation of the interconnect routing with the format:
## [ble index][pin position on the lut] = input pin of the interconnect
##note that the inteconnect input has the first I pins of the cluster and
##after that the output of the muxes of the N luts.
def finishRouting():

    for key in globs.clusters:
        cluster = globs.clusters[key]

        #we use this vector for the close network routing
        RoutingVector = []

        for bleIndex,bleInputList in enumerate(cluster.LUT_input_nets):
            #for every lut, make a new entry in the routing vector
            RoutingVector.append([])

            for pinNumber,(name,number) in enumerate(bleInputList):
                #get an input from a ble of this cluster.
                #number is  the index of the ble instance
                if name == 'ble':
                        RoutingVector[-1].append(globs.params.I+number)
                #get an input of the clusters Input crossbar.
                #number is  the index of the input pin of the cluster
                elif name == 'input':
                        RoutingVector[-1].append(number)
                ##this pin is not driven
                elif name == 'open':
                        RoutingVector[-1].append(-1)
                else:
                    print 'error in read_netlist: unidentified net', name

        #finish the close network
        #print 'Route cluter ', cluster.CLB, 'with Routing Vector ', RoutingVector
        #print 'Lut_input_nets ' , cluster.LUT_input_nets

        if globs.params.UseClos:
            finishClosNetworkRouting(RoutingVector,cluster)
        else:
            finishNormalRouting(RoutingVector,cluster)

#Unify node names for LUTs with FFs
def unifyNames():

    for key in globs.LUTs:
        #Unify node names for LUTs with FFs
        for i, lut in enumerate(globs.LUTs[key].inputs):
            if lut not in globs.LUTs and lut in globs.latches:
                globs.LUTs[key].inputs[i] = globs.latches[lut].input

    for key in globs.clusters:
        cl = globs.clusters[key]
        #Unify node names for LUTs with FFs
        for i, lut in enumerate(cl.input_nets):
            if lut not in globs.LUTs and lut in globs.latches:
                cl.input_nets[i] = globs.latches[lut].input


# Parse the netlist file.
# This file contain the interconnect routing information,
# which cluster input or lutfeedback is routed to which lut on a cluster.
# This file is used to apply this routing
# to the muxes of the interconnection block.
# The file also contain some placement information of bles, lut and fliflops
# together with their names.
# So we used that information to make a connection
# to the luts and fliplopfs of the blif file, and their nodes in the node graph.
# The file give use also a hint,
# which fliflops, luts and even ble are used an which not.
def read_netlist(filename):

    #parse the netlist file and write the result to the cluster list
    netlistClusters = parseNetlist(filename)

    #copy the result in our internal structures
    for netlistCluster in netlistClusters:
        print 'cluster: ' +  netlistCluster.name

        #get the internal cluster object for this netlist cluster
        cluster = getClusterByName(netlistCluster.name)
        #if its not in the internal cluster list
        if (cluster is None):
            print 'error in read_netlist: cant find cluster name: ' \
                + netlistCluster.name + 'in internal cluster list'

        #copy the input netlist names and check
        #if its in the input driver list of the current cluster
        copyClusterInputs(netlistCluster,cluster)

        #copy the bles information to the internal structures
        for bleIndex,netlistBle in enumerate(netlistCluster.bles):

            #append the inputs of the ble to the LUT_input_nets array
            copyBleInputs(netlistBle,cluster)

            #if this ble used its lut, append it to the clusters LUTs list
            #and copy it in the node graph.
            if not (netlistBle.lut is None):
                copyLut(netlistBle,cluster,bleIndex)
            else:
                #for vpr7 we need open keyword in the LUts list.
                #see structure.py
                setupEmptyLut(cluster)

                #if this ble uses it flipflop but not its lut
                #we have to build a passTrough lut
                #because the fliflop dont uses the output of the lut of this ble
                if not (netlistBle.flipflop is None):
                   copyFlipFlopBuildPasstrough(netlistBle,cluster,bleIndex)

    #now we are finished with the netlist result parsing. build the rest.

    for key in globs.clusters:
        cl = globs.clusters[key]

        #attach the latches where appropriate
        ##for luts that uses latches (useFF) configure a passTrough (MUX) Lut
        for node in cl.LUT_FFMUX_nodes:
            ##get the elut node before this ffmux
            elutnode = globs.nodes[globs.nodes[node].inputs[0]]
            #LUT node drives this node
            #because we used the regiostered and unregisterd output, the source
            #of the mux is always the lut.
            #the routing will be handeled by the useFF flag. when its on its use
            #channel 2 otherwise channel 1(the lut)
            #so therfore we can set the final rotuing always to the lut
            globs.nodes[node].source = elutnode.id
            elut = elutnode.LUT
            #only build a mux passtrough lut for used bles
            #that use its flipflop
            if elut:
                if elut.useFF:
                    passThroughLUT = LUT()
                    globs.nodes[node].LUT = passThroughLUT

    ##check if a Lut in globs.LUTs have a valid configuration
    ##append all luts with a configuration to the placed luts
    ##check if all LUTs are placed now
    placed_luts = []
    for key in globs.clusters:
        cl = globs.clusters[key]
        for node in cl.LUT_nodes:
            if globs.nodes[node].LUT:
                placed_luts.append(globs.nodes[node].LUT.output)

    for key in globs.LUTs:
        if key not in placed_luts:
            if len(globs.LUTs[key].inputs) > 1:
                print 'error in read_netlist: LUT not placed', key

            else:
                print 'read_netlist: empty lut not placed', key, globs.LUTs[key].inputs

    #fix the names
    unifyNames()
    #finish the routing
    finishRouting()
