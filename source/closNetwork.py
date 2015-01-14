import globs
from structs import *

##This class represent a clos network
##composed of a two stage crossbar network.
##the input of the clos network is the input of the cluster
##and the feedback of the bles/luts of this cluster
##so the input consist of a list of ids with length I+N
##The output is the input for each pin of a lut.
##so the output is a list of mux ids, each id for an output

##In the following the term inode is used, representing a mux
##but called inode, because it is an element in the node graph
class ClosNetwork():
    def __init__(self):
        ##a list of node ids, composed of the ids of the input
        ##of the cluster and the ids of the feeedback from the
        ##bles, in detail the ids of the muxes of the ble.
        self.inputs = []
        ##a list of inodes ids. Representing the mux outputs
        ##of the crossbar
        self.outputs = []
        ##a list of all crossbar instances for both stages,
        ##used in this clos nework
        ##self.crossbars = []
        ##a list of crossbar instances used for the first stage
        self.stage1 = []
        ##a list of crossbar instances used for the first stage
        self.stage2 = []


## A crossbar consist of outputWidth muxes.
## the the input width of this mux, is the input width of the crossbar
## each mux/inode get the same input and route it to one specific
## output pin of the crossbar
class Crossbar():

    def __init__(self,inputs,inputWidth,outputWidth,location):
        ##the input width of this crossbar
        self.inputWidth = inputWidth
        ##the output width of the crossbar
        self.outputWidth = outputWidth
        ##a list of input node ids
        self.inputs = inputs
        ##a list of ouput inode ids. these inodes form the crossbar
        self.outputs = []
        ##cluster index in which cluster this crossbar is placed
        self.location = location
        #build the inodes and set the output
        self.buildInodes()

    #build the inodes and append them to the output id list
    def buildInodes(self):
        for i in range(self.outputWidth):
            inode = Node()
            #every mux get the same input. the input of the crossbar
            inode.inputs = self.inputs
            #a routing mux
            inode.type = 7
            #cluster index
            inode.location = self.location
            #add the node to the graph
            globs.addNode(inode)
            #add the id to the oputput list. was set trough add node
            self.outputs.append(inode.id)


##build a clos network and returns it.
##an important restriction is that the input width of the close Netwrok
##(number of lut feedbacks (numLuts) and clusterInputWidth) must be divideable
##by the input width of a lut (lutInputWidth).
##
## it also connect the close network with the lut and the cluster
## by setting the inputs of the lut nodes in the node graph and
## creating the backward references list LUT_input_nodes

##param numLuts number of the luts of the cluster
##param inputWidthLut the input width of each lut
##param inputWidthCluster the input width of the cluster
def buildClosNetwork(cluster,clusterIndex,inputWidthCluster,inputWidthLut):

    ##a list of the cluster input node ids and
    ##the lut feedback node ids(the mux ids of the ble)
    ##because inputs is a list of drivers, we collect the node ids
    clusterInputs = []
    for i in cluster.inputs:
        clusterInputs.append(i.id)
    inputs = clusterInputs + cluster.LUT_FFMUX_nodes

    #the number of luts in a cluster
    numLuts = len(cluster.LUT_nodes)

    closNetwork= ClosNetwork()
    #set the input of this network
    closNetwork.inputs = inputs

    # important restriction: divideable by lutInputWidth.see notes above
    # input to the close network is the cluster input and the lut feedback
    numFirstStageCrossbars = (inputWidthCluster + numLuts)/inputWidthLut

    #build the first stage
    for i in range(numFirstStageCrossbars):
        #slice out inputWidthLut slices for the input of the crossbar
        corssbarInputs = inputs[i*inputWidthLut: i*inputWidthLut+inputWidthLut]

        crossbar = Crossbar(corssbarInputs,inputWidthLut,inputWidthLut,clusterIndex)
        #append the crossbar to the internal lists
        closNetwork.stage1.append(crossbar)

    #build the second stage
    for i in range(inputWidthLut):
        #build the inputs for the this crossbar:
        #the i-th output of every crossbar of the first stage
        corssbarInputs = []
        for j in range(numFirstStageCrossbars):
            corssbarInputs.append(closNetwork.stage1[j].outputs[i])

        crossbar = Crossbar(corssbarInputs,numFirstStageCrossbars,numLuts,clusterIndex)
        #append the crossbar to the internal lists
        closNetwork.stage2.append(crossbar)

    #connect the luts of the cluster with the outputs of the crossbar
    numSecondStageCrossbars = len(closNetwork.stage2)
    for i in range(numLuts):
        crossbarOutputs = []

        # the cluster LUT_input nodes is a NXk array for a backward reference
        # to the mux for a given lut and pin
        #make a first dimension entry for the current lut
        cluster.LUT_input_nodes.append([])

        #same approach as the connection of the second stage
        #the i-th output of every crossbar of the second stage
        for j in range(numSecondStageCrossbars):
            inode = closNetwork.stage2[j].outputs[i]
            crossbarOutputs.append(inode)
            # the cluster LUT_input nodes is a NXk array for a backward reference
            # to the mux for a given lut and pin
            cluster.LUT_input_nodes[i].append(inode)

        #now establish the connection with the lut
        lutNode = globs.nodes[cluster.LUT_nodes[i]]
        lutNode.inputs = crossbarOutputs

        ## if we changed the connection to other function this list would be
        ## nice to have
        closNetwork.outputs.append(crossbarOutputs)

    return closNetwork
