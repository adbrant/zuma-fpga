from structs import *
import globs
import binascii
import math
import sys

global byteWordCounter
byteWordCounter = 0


##create an empty lut content
def emptyConfig() :
    config = []
    lutSize = int(math.pow(2, globs.host_size))
    for i in range(lutSize):
        config.append('0')

    return config

##check if the lut content is empty
def emptyLut(lut):

    for pos in range(len(lut)):
        if lut[pos] != '0':
            return False

    return True

##return the configuration of the lut as a string.
# if its empty it returns []
def configToStr(config):
    result = []
    
    for lut in config:
        if emptyLut(lut):
            result.append([])
        else:
            result.append(lut)

    return str(result)

##print the given node information
def printNode(type,id,config):
    global byteWordCounter
    
    print ("Node Parser: "+ type +" , id " + \
           str(id) + " With configuration : " + \
           configToStr(config))
    byteWordCounter = byteWordCounter + len(config)

##A class for the bitstream configuration of a node in the node graph.
class NodeConfiguration:

    def __init__(self,id,config):
        ##the id of the node
        self.id = id
        ##The list of lutram configurations for the node.
        ##This could be a list of several lutram config bits(also list),
        ##depending on how many lutrams were nedded for this node.
        self.config = config

##convert a hex string into a binary string
def hexToBit(hexval):
        '''
        Takes a string representation of hex data with
        arbitrary length and converts to string representation
        of binary.  Includes padding 0s
        '''
        thelen = len(hexval)*4
        binval = bin(int(hexval, 16))[2:]
        while ((len(binval)) < thelen):
            binval = '0' + binval
        return str(binval)

## Load the configuration of the lutrams from the bitstream in a list.
# return the configuration as a list of lutram configurations per stage.
# it extract the configuration of the lutrams stage by stage.
def loadConfig(filename):

    #a list of lutram configurations. each entry is a lutram
    config = []

    #read the file
    lines = [line.strip() for line in open(filename)]

    #number of config bits of the LUTRAM.
    lutConfigSize = int(math.pow(2, globs.host_size))

    #slice the config into stage chunks
    stageChunks = [lines[i:i + lutConfigSize] for i in range(0, len(lines), lutConfigSize)]

    #parse the stage and append the configurations 
    #to the global config list
    for stage in stageChunks:

        if globs.debug:
            print stage

        #a list of lutram configurations.
        #TODO: change name in stageConfig
        lutConfig = [ [] for i in range(globs.params.config_width)]
       
        
        #parse the lutram configurations
        for byteWord in stage:

            #convert the hex word to a bit config word
            configWord = hexToBit(byteWord)
            global byteWordCounter
            if globs.debug:
                print "Byteword " + str(byteWord), " , " + str(configWord)  + " at " + str(byteWordCounter) 

            #append the configuration bit to each lutram
            for i in range(len(configWord)):
                lutConfig[i].append(configWord[i])

        #append the configuration of the lutrams of this stage
        #on the global configuration
        if globs.debug:
            print "lutConfig " + str(len(lutConfig))
            for lut in lutConfig:
                print str(lut) + " , " +str(len(lut))

        config.append(lutConfig)

    return config


## read the selector information from the lut's bitstream config.
# The selector is the index of the input pin which is used for the mux.
# The selector index begins by 0 and goes to host_size-1
# for e.g. for a 6er lut the following bitstreams are used:
# 5: 0101010101 ...
# 4: 001100110011...
# 3: 0000111100001111 ...
# 2: 0000000011111111 ....
# 1: 00000000000000001111111111111111000 ...
# 0: 00000000000000000000000000000000111111...
# @return return the selector index as a integer.
def readSelector(lutConfig):
    
    indexFirstOne = lutConfig.index('1')
    
    #because its start with 0 we can get the selector 
    # 2^reverseselector = first one by calc the logarithm
    reverseselector = math.log(indexFirstOne,2)

    selector = (globs.host_size-1) - reverseselector
    return int(selector)


## Parse the configuration of a elut node and 
## append the information to the node graph.
# @param nodeConf A NodeConfiguration object 
def parseElut(nodeConf):

    #get the node in the node graph
    node = globs.nodes[nodeConf.id]

    if globs.debug:
        printNode("ELUT",nodeConf.id,nodeConf.config)
      
    #empty eluts are sometimes important for equivalence check.
    #if they are used but empty the will be add by the
    #parsing of the mux.

    #should only have one lutram for now
    if emptyLut(nodeConf.config[0]):
        if globs.debug:
            print "lut isn't used. breakup"
        return

    #build the corresponding lut for saving the config
    node.LUT = LUT()
    node.LUT.bits = nodeConf.config

## Parse the configuration of a ffmux node and 
## append the information to the node graph.
# @param nodeConf A NodeConfiguration object 
def parseFFMux(nodeConf):

    #get the node in the node graph
    node = globs.nodes[nodeConf.id]
    
    if globs.debug:
        printNode("FFMUX",nodeConf.id,nodeConf.config)
    
    #whole ble isn't used
    if emptyLut(nodeConf.config[0]):
        if globs.debug:
            print "ble isn't used. breakup"
        return


    #get the elut node before this ffmux
    elutnode = globs.nodes[node.inputs[0]]

    #because we used the registered and unregistered output, the source
    #of the mux is always the lut.
    #the routing will be handled by the useFF flag. when its on its use
    #channel 2 otherwise channel 1(the lut)
    #so therefore we can set the final rotuing always to the lut
    node.source = elutnode.id
        
    #check if the elut is used. should be read before.
    #the elut was empty but is used. create an empty lut content
    if not elutnode.LUT:
        elutnode.LUT = LUT()
        elutnode.LUT.bits = emptyConfig()
   
    #only lut was taken
    if readSelector(nodeConf.config[0]) == 0:
        if globs.debug:
            print "don't use ff"
        elutnode.LUT.useFF = True

    #flipflop is used
    else:
        if globs.debug:
            print "use ff"
        elutnode.LUT.useFF = False


## Parse the configuration of a mux node and 
## append the information to the node graph.
# @param nodeConf A NodeConfiguration object 
def parseMux(nodeConf):
    
    #get the node in the node graph
    node = globs.nodes[nodeConf.id]
    
    if globs.debug:
        printNode("ROUTING MUX",nodeConf.id,nodeConf.config)

    if len(nodeConf.config) < 1:
        print "error, wrong mux config size"
        sys.exit(0)

    elif len(nodeConf.config) == 1:
        if emptyLut(nodeConf.config[0]):
            if globs.debug:
                print "routing mux isn't used. breakup"
            return

        selector = readSelector(nodeConf.config[0])

    else:
        if globs.debug:
            print "very long config"

        thightlyPacked = False

        if len(nodeConf.config) <= globs.host_size + 1:
            if globs.debug:
                print 'thightly packed'
            thightlyPacked = True


        #try to find the first non empty lut in the first level 
        #where we can get the selector index from

        #index of the first non empty lut
        index = -1

        #number of first level luts
        numLutsFirstLvl = math.ceil( len(node.inputs)*1.0 / globs.host_size)

        #search the index of the first non empty lut
        for pos in range(len(nodeConf.config)) :            
            if not emptyLut(nodeConf.config[pos]):
               index = pos
               break

        #all luts are empty
        if index == -1:
            if globs.debug:
                print "routing mux isn't used. breakup" 
            return

        if thightlyPacked:

            selector = (index)*globs.host_size + \
                    readSelector(nodeConf.config[index])

            #if the inputs of the last lut are used directly.
            #the real first level has all luts empty and the lut of the second lvl was used
            #for the remaining inputs.
            #seems only to be in the thigly packed branch

            num_luts = len(nodeConf.config)

            #check if the last lut is only used. the rest was empty
            #reminder: index startx with 0

            if (index  ==  num_luts-1):
                numLutsFirstLvl = num_luts-1
                selector =  ((numLutsFirstLvl)*globs.host_size -1) + (readSelector(nodeConf.config[index]) +1  - (numLutsFirstLvl))
        else:

            selector = (index)*globs.host_size + \
                    readSelector(nodeConf.config[index])

    #some debug infos
    if globs.debug:
        print "lut selector: " + str(selector)
    

    node.source = node.inputs[selector]

## fix channel nodes which have only one input 
## and are hardwired in the verilog file
def fixReducedChannels():
    
    for node in globs.nodes:
        if len(node.inputs) == 1 and not node.ffmux:
                
            #is it a channel?
            if node.type is 5 or node.type is 6:
                node.source = node.inputs[0]

## assign the blif names to the input (IPINS) and output (OPINS) nodes 
## of the node graph.
# TODO: is this working for non ordered io nodes, 
# when params.orderedIO is disabled?
def buildIO():

    #NOTE: orderInput and orderOuput contain source and sink nodes

    #NOTE: When params.orderedIO is enabled we change the sink and source nodes 
    #to permutation mux nodes.
    #So all io inputs nodes of the fpga (opin nodes) have a input edge
    #from every source node(now a permutation mux).
    #Also every fpga io output node (ipin node) has an edge to every sink node
    #(now also a permutation mux)

    #track the highest output/input number
    maxOutputNum = -1
    maxInputNum = -1

    #NOTE: in vpr7, when there is only one output, the blif name has no number
    
    #find the highest output number
    for index,id in enumerate(globs.orderedOutputs):
            node = globs.nodes[id]

            #node is used as a output
            if node.source != -1:
                maxOutputNum = index
    
    #set the name attributes of the nodes
    for index,id in enumerate(globs.orderedOutputs):
            node = globs.nodes[id]
            
            #only one input
            if maxOutputNum == 0:
                name = "top^out"
            else:
                name = "top^out~" + str(index)

            if node.source != -1:
                node.name = name

    #build the output list
    if maxOutputNum == 0:
        name = "top^out"
        globs.outputs.append(name)
    else:
        for index in range(maxOutputNum +1):
            name = "top^out~" + str(index)
            globs.outputs.append(name)

    #now the inputs

    #is a clock used. is the circuit sequential.
    #is globs.clock is enabled by cmd line in zumaBlifToBits
    if (globs.clock):
         globs.inputs.append("top^clock")

    #set the name attributes of the inputs
    for index,id in enumerate(globs.orderedInputs):
            node = globs.nodes[id]
            
            #is a reset signal used?
            #globs.reset is activate by cmd line in zumaBlifToBits
            if (globs.reset):
                if index == 0:
                    name = "top^reset"
                else:
                    name = "top^in~" + str(index-1) 
            else:
                name = "top^in~" + str(index)
            
            for edgeId in node.edges:
                edgeNode = globs.nodes[edgeId]
                #have the source as an input. is used
                if edgeNode.source == id:
                    node.name = name
                    maxInputNum = index
                    break

    #if the number of inputs is given by a parameter, overwrite it.
    if globs.maxInputNum != -1:
        if globs.maxInputNum < maxInputNum:
            print "WARNING: the given input number is smaller than the actual used number of inputs."
        
        #overwrite the number of inputs
        maxInputNum = globs.maxInputNum

    #create the global input list
    for index in range(maxInputNum +1):
        if (globs.reset):
            if index == 0:
                name = "top^reset"
            else:
                name = "top^in~" + str(index-1)
        else:
            name = "top^in~" + str(index)
    
        globs.inputs.append(name)

## parse the node configuration and set the corresponding attributes
## in the node graph.
# @param nodeConf A nodeConfiguration object
def parseNode( nodeConf):

    
    #get the node in the node graph
    node = globs.nodes[nodeConf.id]

     #the node is an elut.
    if node.eLUT:
        parseElut(nodeConf)

    #this is a mux of a ble
    elif node.ffmux:
        parseFFMux(nodeConf)

    #node is a routing mux
    else:
       parseMux(nodeConf)

## Scan a config pattern row and return a list of config information tuples 
##(nodeId,number of used lutrams)
def scanConfigPatternLine(row):

    #A list of tuples (nodeId,number of used lutrams)
    result = []
    #track the current nod ID
    currentNodeId = -1
    #the number of used lutrams of the current node
    NumLutrams = -1

    for nodeId in row:
        if (nodeId != currentNodeId):
            NumLutrams = row.count(nodeId)
            result.append( (nodeId, NumLutrams))
            
            currentNodeId = nodeId
           
    return result

## scan the config patern object and return a list of nodeConfiguration objects
def scanConfigPattern(configPattern,config):

    # a list of nodeConfiguration objects
    result = []

    for stageNum,row in enumerate(configPattern):
        #return a list of (nodeId,length)
        nodes = scanConfigPatternLine(row)

        for node in nodes:
            #first entry is the node id
            nodeId = node[0]
            #number of used lutrams for this node
            nodeNumLutrams = node[1]
            #copy the lutram config of the node
            nodeConfig = config[stageNum][0:nodeNumLutrams]
            #remove the lutrams configuration from the global config
            del config[stageNum][0:nodeNumLutrams]

            result.append(NodeConfiguration(nodeId, nodeConfig))

    return result

## Parse the bitstream of the virtual fpga.
# @param filename the bitstream of the virtual fpga in its mif format
def parseBitstream(filename):

    #get the configuration of the lutrams
    config = loadConfig(filename)

    #get the node Configurations
    nodes = scanConfigPattern(globs.config_pattern,config)

    #now parse the configurations and set the right attributes.
    for node in nodes:
        parseNode(node)

    #now build correct names for the output
    buildIO()

    #fix reduced channels
    fixReducedChannels()

## test function for a unit test
def testLoadConfig(filename):

    globs.init()
    
    config = loadConfig(filename)
    for lutConfig in config:
        print lutConfig

## unit test
def main():
    testLoadConfig('../example/output.hex.mif')

## unit test
if __name__ == '__main__':
    main()
