import BuildVerilog
import BuildBitstream
import globs
from functools import partial


#replace the input/ouput names with fpga_input[]/fpga_output in abc_out.blif
#and write it to a new file
def writeCircuitVerificationBlif():

    #replace the fpga input and output names for an equivalence check with abc

    #build a list of
    replaceList = []

    #add in reverse order so long names would win over short.
    #important when an name is a prefix of another
    for index,inputName in enumerate(globs.inputs):
        replaceList.insert(0,[inputName,'fpga_inputs[' + str(index) +  ']'])

    for index,outputName in enumerate(globs.outputs):
        replaceList.insert(0,[outputName,'fpga_outputs[' + str(index) +  ']'])

    inputFile = open('abc_out.blif','r')
    outputFile = open('abc_out_v.blif','w')

    for line in inputFile:
        for pair in replaceList:
            line = line.replace(pair[0],pair[1])
        outputFile.write(line)

    inputFile.close()
    outputFile.close()

#generate the topmodule for the verification testsuite
def generateTopModule():

    #calc the number of input and ouputs.
    #TODO: find a cleaner way for this
    numinputs = 0
    numoutputs = 0
    for key in globs.IOs:

        numinputs = numinputs + len(globs.IOs[key].inputs)
        numoutputs = numoutputs + len(globs.IOs[key].outputs)


    #now write the topmodule
    topFile = open('top_module.v', 'w')

    topFile.write('''
    module top_module
    (
        fpga_inputs,
        fpga_outputs
    );
    ''')

    topFile.write("input [" + str(numinputs) + "-1:0] fpga_inputs;\n")
    topFile.write("output [" + str(numoutputs) + "-1:0] fpga_outputs;")

    topFile.write('''
    ZUMA_custom_generated #() zuma
    (
    .clk(1'b0),
    .fpga_inputs(fpga_inputs),
    .fpga_outputs(fpga_outputs),
    .config_data({''' + str(globs.params.config_width) + '''{1'b0}}),
    .config_en(1'b0),
    //.progress(),
    .config_addr({''' + str(globs.params.config_width) + '''{1'b0}}),
    .clk2(1'b0),
    .ffrst(1'b0)
    );

    endmodule
    ''')

    topFile.close()

## write the footer of the verilog file
#  @param f the file handle
def writeFooter(f):

    # write the config controller
    f.write('parameter NUM_CONFIG_STAGES = ' + \
        str(len(globs.config_pattern)) + ';')

    f.write('\nendmodule\n')

#to make things easier in the testsuite
def writeTestsuitePatch(f):

    f.write("assign wren = {4096{1'b0}};\n")
    f.write("assign wr_addr = 6'b000000;\n")


#write a wire in the verilog file for a node output.
#Therefore we use the name attribute which is unique identifier in the
#TechnologyNodeGraph
def writeWire(file,node):

    # an eLut have two outputs.
    # one registered and one unregistered output
    if node.eLUT:
        string = 'wire ' + 'node_' + node.name + '_reg;\n'
        string += 'wire ' + 'node_' + node.name + '_unreg;\n'
    # the rest have only one output
    else:
        string = 'wire ' + 'node_' + node.name + ';\n'

    file.write(string)


def writePassTroughNode(file,node):
    file.write('assign ' + 'node_' + node.name + ' = ' + 'node_' + node.inputs[0] + ';\n');


def writeLUTRAMHeader(f, node):

    #is it an eLUT or just a mux?
    if node.eLUT:

        #has a configuration, is used
        if node.bits is not None:

            #build the configuration bits
            bitsStr = ''.join(map(str,node.bits))

            f.write('elut_custom ' + \
                    ' #( ' + ".used(1),\n .LUT_MASK(64'b" +  bitsStr + ')\n) ' + 'LUT_' + node.name +  ' ( ' )

        #if not the default parameter values are used
        else:
            f.write('elut_custom ' + 'LUT_' + node.name + ' ( ' )

    #it is a routing mux
    else:

        #now write the header + configuration
        #TODO: implement glob.host_size for different mux sizes
        if (node.bits != None):
            bitsStr = ''.join(map(str,node.bits))
            f.write('lut_custom ' + \
                        ' #( ' + ".used(1),\n .LUT_MASK(64'b" +  bitsStr + ')\n) '  + 'MUX_' + node.name + ' ( ' )
        else:
            f.write('lut_custom ' + 'MUX_' + node.name + ' ( ' )



## A helper function for write_LUTRAM
#  returns a string '{ name1, name2 , ... }' for a given list of names
def list_to_vector(names):
    string = '{'
    for n in names:
        string = string + n + ','
    string = string[0:-1] + '}'
    return string


def writeLUTRAMInputs(f, node):

    #list of input wire names
    inputNames = []

    #get the stage number and stage offset offset
    #was set in BuildVerilog.py
    config_stage = node.stageNumber
    config_offset = node.stageOffset

    #is it a regular routing mux or a mux on a ble behind a lut(ffmux)?
    #the input of a ffmux is the name of the conncected lut.
    #remember that the corresponding LUTRAM of this lut have two outputs
    if node.ffmux:
        #the lut mux have only one input
        lutName = node.inputs[0]
        inputNames.append('node_' + lutName + '_reg')
        inputNames.append('node_' + lutName + '_unreg')

    #when not just use the provided names
    else:
        inputNames = ['node_' + name for name in node.inputs]

    ## assign an 0 driver to every unconnected input
    while len(inputNames) < globs.host_size:
        inputNames.append("1'b0")

    #connect the name of the input wires
    f.write('.dpra(' + list_to_vector(inputNames) + \
             '), // input [5 : 0] dpra\n')

    f.write('''
    .a(wr_addr), // input [5 : 0] a
    .d(wr_data[''' + str(config_offset) + ''']), // input [0 : 0]
    ''')

    f.write('''
    .clk(clk), // input clk
    .we(wren[''' + str(config_stage) + ''']), // input we
    ''')

    if node.eLUT:
        f.write('''
        .qdpo_clk(clk2), // run clk
        .qdpo_rst(ffrst), // input flip flop reset
        ''')

def writeLUTRAMOutputs(f, node):


    #connect the name of the output wires.
    #if its an elut than we have two output wires instead of one
    if node.eLUT:
        f.write( '.dpo(' + 'node_'+ node.name + \
             '_unreg), // unregistered output\n\n')

        f.write( '.qdpo(' + 'node_' + node.name + \
             '_reg)); // registered output\n\n')
    else:
        f.write( '.dpo(' + 'node_' + node.name + '));\n\n')


## write the verilog code for the LUTRAM.
# The LUTRAM can be a lutram of a routing mux, a ffmux or a eLUT or Ipin
def writeLUTRAM(f, node):

    writeLUTRAMHeader(f, node)
    writeLUTRAMInputs(f, node)
    writeLUTRAMOutputs(f, node)


def ConnectIO(f):

    #When using orderedIO we connect the rebranded sources/sinks with the fpga
    #inputs and outputs.
    #Otherwise we directly connect the IO opins and ipins
    #with the fpga inputs and outputs, skipping the IO sink/and sources

    if globs.params.orderedIO:
        #connect the iomux node wires with the fpga outputs
        for index,iomuxId in enumerate(globs.orderedOutputs):
            f.write('assign fpga_outputs[' + str(index) + \
                '] = ' + 'node_' + str(iomuxId) + ';\n')
    else:
        #connect the ipin node wires with the fpga outputs
        for key in globs.IOs:
            IO = globs.IOs[key]
            for index,ipin in enumerate(IO.outputs):
                f.write('assign fpga_outputs[' + str(index) + '] = ' + 'node_' + str(ipin.id) + ';\n')

    if globs.params.orderedIO:
        #connect the iomux node wires with the fpga inputs
        for index,iomuxId in enumerate(globs.orderedInputs):
            f.write('assign ' + 'node_' + str(iomuxId) + \
                ' = fpga_inputs[' + str(index) + '];\n')
    else:
        #connect the opin node wires with the fpga inouts
        for key in globs.IOs:
            IO = globs.IOs[key]
            for index,opin in enumerate(IO.inputs):
                f.write('assign ' + 'node_' + str(opin.id) + ' = fpga_inputs[' + str(index) + '];\n')



def writeConfiguration(node):

    #is it an eLUT or just a mux?
    if node.eLUT:

        #get the parent node in the nodegraph of this mapped node
        parentNode = node.parentNode

        #is it used, i.e is there a config availible?
        #When it is used pass the config as a verilog paramter
        if parentNode.LUT:

            # get the ble index of this lut
            cl = globs.clusters[parentNode.location]
            index = cl.getBleIndex(parentNode.LUT.output)

            #build the configuration bits
            bits = BuildBitstream.build_lut_contents(globs.host_size, parentNode.LUT, cl, index)
            #assign it to the node
            node.bits = bits

    #it is a routing mux
    #is it used, has it a set source attibute
    elif node.source > -1:

        #build the configuration bits
        #a ffmux has a special configuration
        if node.ffmux:

            print 'found ffmux'

            #get the lut that drive the mux in the nodegraph
            parentNode = node.parentNode
            elutnode = globs.nodes[parentNode.source]

            #check if the mux/ble is used
            #if the lut is not used we also dont use this ffmux
            if elutnode.LUT:

                #which input should the ffmux route?
                #when only the lut is used then 0 else the filpflop input
                if elutnode.LUT.useFF: #flipflop is used
                    bits = BuildBitstream.buildMuxBitstreamConfig(globs.host_size,0 )# registered / with FF
                else:
                    bits = BuildBitstream.buildMuxBitstreamConfig(globs.host_size,1 )# unregistered / without FF

                #assign it to the node
                node.bits = bits

            #print globs.host_size
            #print str(node.bits)

        #a regular routing mux
        else:
            offset = node.inputs.index(node.source)
            bits = BuildBitstream.buildMuxBitstreamConfig(globs.host_size,offset )
            #assign it to the node
            node.bits = bits


#check if they mapped nodes are used and write their configuration
#as well signale trough a flag that they are configured
def generateMappedNodesConfiguration():

    for node in globs.technologyMappedNodes.getNodes():

        #source and sinks were skipped. They are not used on clusters or IOs yet.
        if node.type < 3:
            continue

        #if the node is a passtrough node we use the assign optimization.
        #these are nodes with only one input except an lut,ffmux or ipin which
        #are a special case
        #they don't need a configuration
        elif node.passTrough:
            continue

        #get the iomuxes connect to the fpga inputs.
        #The output of these muxes are connected to every opin of the fpga input opins.
        #the output wire generate of these luts are then conneected to the fpga input wires.
        #So we only use it output wires for now but not the node.
        elif (node.type == 10) and (len(node.inputs) == 0):
            continue

        #this node is a part of a mux,lut,ffmux or ipin -> write a lutram
        else:
            #write the configuration for this node
            writeConfiguration(node)


#buld the lutrams and wires for the outer routing.
#generate lutrams for every node except the ones on a cluster which are elut ffmux opin and interconnect nodes.
#done
def buildOuterRouting(file,unprocessed):

    for node in globs.nodes:

        #source and sinks were skipped. They are not used as lutrams yet.
        if node.type < 3:
            continue

        #skip opins of clusters, but not those of IOs.
        if node.type == 3:
            #check if it is not on an edge. only skip cluster opins
            if (node.location[0] != 0) and \
               (node.location[1] != 0) and \
               (node.location[0] != globs.clusterx) and \
               (node.location[1] != globs.clustery):
               continue

        #skip elut ffmux and interconnect nodes
        if node.type  >= 7 and node.type  <= 9:
            continue

        #for an iomux of the fpga inputs we only generate the output wire
        #but not a configuration. See ConnectIO()
        if (node.type == 10) and (len(node.inputs) == 0):
            #the node have only one mapped node
            mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[0])
            writeWire(file,mappedNode)
            continue

        #else print all mapped child nodes and their wires to the file
        #while printing the instantiation to the main
        writeNodeGraphNodeInterface('instantiation',node,file)
        call = partial(writeNodeGraphNodeDescription,file= file,node = node,isOnCluster = False)
        unprocessed.append(call)

#print the wire and lutram instance
def writeMappedNode(file,node,isOnCluster):

    #write a wire for the node output.
    #because every node has only one unique output
    writeWire(file,node)

    #if the node is a passtrough node just use the assign optimization
    #these are nodes with only one input except an lut,ffmux or ipin which
    #are a special case
    if node.passTrough:
        writePassTroughNode(file,node)

    #this node is a part of a routing mux,lut,ffmux or ipin -> write a lutram
    else:
        #signal that this node is chosen to be in a cluster module
        node.isOnCluster = isOnCluster
        #now write the lut code
        writeLUTRAM(file,node)


###-----------------------------------------------------------------------------
###--------------general printer ---------------------------------------------------
###-----------------------------------------------------------------------------

#done
def generalInterface(type,file,moduleName,instanceName,inputNames,outputNames):

    #first the interface name
    interfaceString = moduleName + " " + instanceName + ' (\n'
    moduleInterfaceString  = 'module ' + moduleName + ' (\n'

    if type == 'instantiation':
        file.write( interfaceString )
    else:
        file.write( moduleInterfaceString)

    # inputs and output
    for inputName in inputNames:

        if isinstance(inputName,str):
            inputString = '.' + inputName + '(' + inputName + '),\n'
            moduleInputString = inputName + ',\n'
        elif isinstance(inputName,tuple):
            inputString = '.' + inputName[0] + '(' + inputName[0] + '),\n'
            moduleInputString = inputName[0] + ',\n'

        if type == 'instantiation':
            file.write( inputString )
        else:
            file.write( moduleInputString)


    #the output is just the node id
    for index,outputName in enumerate(outputNames):

        #isnt the last element
        if index < len(outputNames) -1:
            outputString = '.' + outputName + '(' + outputName + '),\n'
            moduleOuputString = outputName + ',\n'

        else:
            outputString = '.' + outputName + '(' + outputName + ')\n'
            moduleOuputString =  outputName

        if type == 'instantiation':
            file.write( outputString )
        else:
            file.write( moduleOuputString)


    #end the module instantiation
    file.write( ');\n')

    #now print the rest of the module desctiption to the module file
    if type == 'description':

        # inputs and output
        for inputName in inputNames:

            if isinstance(inputName,str):
                inputNodeString = 'input ' + inputName + ';\n'
            #tuple has name, size str
            elif isinstance(inputName,tuple):
                inputNodeString = 'input ' + inputName[1] + ' ' + inputName[0] + ';\n'
            file.write( inputNodeString )

        for outputName in outputNames:
            outputNodeString = 'output ' + outputName + ';\n'
            file.write( outputNodeString )

###-----------------------------------------------------------------------------
###--------------node graph printer --------------------------------------------
###-----------------------------------------------------------------------------
#done
def writeNodeGraphNodeInterface(type,node,file):

    #first the interface name
    moduleName = 'Mod_node_' + str(node.id)
    instanceName = 'mod_node_' + str(node.id)

    # inputs and output
    inputNames = [('wr_addr','[5:0]'),('wr_data','[32-1:0]'),('wren','[4096:0]'),'clk','clk2','ffrst']
    for inputNodeId in node.inputs:
        inputNodeName = 'node_' + str(inputNodeId)
        inputNames.append(inputNodeName)

    #the output is just the node id
    nodeName = 'node_' + str(node.id)
    outputNames = [ nodeName ]

    generalInterface(type,file,moduleName,instanceName,inputNames,outputNames)

    #if the node was instantiate we write an output wire
    if type == 'instantiation':

        #write the output wire of this node to the file.
        #therfore we use the last mapped node which output is the same as the
        #nodegraph node output
        mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[-1])
        writeWire(file,mappedNode)

#done
def writeNodeGraphNodeBody(node,file,isOnCluster):

    #now the mapped nodes as content
    for mappedNodeName in node.mappedNodes:

        mappedNode = globs.technologyMappedNodes.getNodeByName(mappedNodeName)
        writeMappedNode(file,mappedNode,isOnCluster)

#done
#write the module description to the file
def writeNodeGraphNodeDescription(file,node,isOnCluster):


    #write the node module instantiation + the start of the description in one strike
    writeNodeGraphNodeInterface('description',node,file)

    #now the body
    writeNodeGraphNodeBody(node,file,isOnCluster)

    #finally the end of the module
    file.write( 'endmodule\n')


###-----------------------------------------------------------------------------
###--------------interconnect printer ------------------------------------------
###-----------------------------------------------------------------------------

#done
def buildInterconInterface(type,file,cluster,location):

    #first the interface name
    x,y = location
    moduleName = 'Mod_interconn_' + str(x) + '_' + str(y)
    instanceName = 'mod_interconn_' + str(x) + '_' + str(y)

    # inputs and output
    inputNames = [('wr_addr','[5:0]'),('wr_data','[32-1:0]'),('wren','[4096:0]'),'clk','clk2','ffrst']
    outputNames = []

    # iterate through the drivers and grep the ipin nodes.
    for ipinDriver in cluster.inputs:
        #get the ipin node.
        ipin = globs.nodes[ipinDriver.id]
        ipinName = 'node_' + str(ipin.id)
        inputNames.append(ipinName)

    #also the muxes are inputs
    for bleIndex in range(globs.params.N):
        ffmuxId = cluster.LUT_FFMUX_nodes[bleIndex]
        ipinName = 'node_' + str(ffmuxId)
        inputNames.append(ipinName)

    for bleIndex in range(globs.params.N):
        for interconNodeId in cluster.LUT_input_nodes[bleIndex]:

            outputNames.append('node_' + str(interconNodeId))


    generalInterface(type,file,moduleName,instanceName,inputNames,outputNames)


#instantiate all interconnect node for the given cluster
#done
def buildInterconBody(file,cluster,unprocessed,blackbox):

    #if the blackBox should omit the genration
    if (blackbox and globs.params.blackBoxInterconnect):
        return

    #insatiate the inner nodes
    for bleIndex in range(globs.params.N):
        for interconNodeId in cluster.LUT_input_nodes[bleIndex]:

            #get the node
            interconNode = globs.nodes[interconNodeId]

            #write the node module instantiation and output wire
            writeNodeGraphNodeInterface('instantiation',interconNode,file)

            call = partial(writeNodeGraphNodeDescription,file= file ,node = interconNode,isOnCluster = True)
            unprocessed.append(call)

#done
def buildInterconDescription(file,cluster,location,unprocessed,blackbox):

    buildInterconInterface('description',file,cluster,location)
    buildInterconBody(file,cluster,unprocessed,blackbox)

    #finally the end of the module
    file.write( 'endmodule\n')


###-----------------------------------------------------------------------------
###--------------ble printer ---------------------------------------------------
###-----------------------------------------------------------------------------

#done
def buildBleInterface(type,file,cluster,location,bleIndex):

    #first the interface name
    x,y = location
    moduleName = 'Mod_ble_' + str(x) + '_' + str(y) + '_'+ str(bleIndex)
    instanceName = 'mod_ble_' + str(x) + '_' + str(y) + '_'+ str(bleIndex)

    #get the lut and ffmux node
    lutId = cluster.LUT_nodes[bleIndex]
    lutNode = globs.nodes[lutId]

    ffmuxId = cluster.LUT_FFMUX_nodes[bleIndex]
    ffmuxNode = globs.nodes[ffmuxId]

    # inputs and output
    inputNames = [('wr_addr','[5:0]'),('wr_data','[32-1:0]'),('wren','[4096:0]'),'clk','clk2','ffrst']
    outputNames = []

    for inputId in lutNode.inputs:
        inputNames.append('node_' + str(inputId))

    outputNames.append('node_' + str(ffmuxId))


    generalInterface(type,file,moduleName,instanceName,inputNames,outputNames)


#instantiate all interconnect node for the given cluster
#done
def buildBleBody(file,cluster,bleIndex,unprocessed,blackbox):

    #if the blackBox should omit the genration
    if (blackbox and globs.params.blackBoxBle):
        return

    #get the lut and ffmux node
    lutId = cluster.LUT_nodes[bleIndex]
    lutNode = globs.nodes[lutId]

    ffmuxId = cluster.LUT_FFMUX_nodes[bleIndex]
    ffmuxNode = globs.nodes[ffmuxId]

    #write the node module instantiation and output wire
    #writeNodeGraphNodeInterface('instantiation',lutNode,file)
    #call = partial(writeNodeGraphNodeDescription,file= file ,node = lutNode,isOnCluster = True)
    #unprocessed.append(call)
    writeNodeGraphNodeBody(lutNode,file,True)


    #writeNodeGraphNodeInterface('instantiation',ffmuxNode,file)
    #call = partial(writeNodeGraphNodeDescription,file= file ,node = ffmuxNode,isOnCluster = True)
    #unprocessed.append(call)
    writeNodeGraphNodeBody(ffmuxNode,file,True)


#done
def buildBleDescription(file,cluster,location,bleIndex,unprocessed,blackbox):

    buildBleInterface('description',file,cluster,location,bleIndex)
    buildBleBody(file,cluster,bleIndex,unprocessed,blackbox)

    #finally the end of the module
    file.write( 'endmodule\n')

###-----------------------------------------------------------------------------
###--------------cluster printer ---------------------------------------------------
###-----------------------------------------------------------------------------

#done
def buildClusterInterface(type,file,cluster,location):

    #first write a cluster header:
    (x,y) = location

    moduleName = 'Cluster_' + str(x) + '_' + str(y)
    instanceName = 'cluster_'+ str(x) + '_' + str(y)

    inputNames = [('wr_addr','[5:0]'),('wr_data','[32-1:0]'),('wren','[4096:0]'),'clk','clk2','ffrst']
    outputNames = []

    # iterate through the drivers and grep the ipin nodes.
    for ipinDriver in cluster.inputs:
        #get the ipin node.
        ipin = globs.nodes[ipinDriver.id]
        ipinName = 'node_' + str(ipin.id)
        inputNames.append(ipinName)

    # iterate through the drivers and grep the opin nodes.
    for index,opinDriver in enumerate(cluster.outputs,1):
        #get the ipin node.
        opin = globs.nodes[opinDriver.id]
        outputName = 'node_' + str(opin.id)
        outputNames.append(outputName)

    generalInterface(type,file,moduleName,instanceName,inputNames,outputNames)

#done
def buildClusterBody(file,cluster,location,unprocessed,blackbox):

    #if the blackBox should be the cluster we omit the genration
    if (blackbox and globs.params.blackBoxCluster):
        return

    #first build the interconnect
    if globs.params.hierarchyInterConnect:
        buildInterconInterface('instantiation',file,cluster,location)
        call = partial(buildInterconDescription,file,cluster,location,unprocessed,blackbox)
        unprocessed.append(call)
    else:
        buildInterconBody(file,cluster,unprocessed,blackbox)

    #then the bles
    for bleIndex in range(globs.params.N):

        if globs.params.hierarchyBle:
            buildBleInterface('instantiation',file,cluster,location,bleIndex)
            call = partial(buildBleDescription,file,cluster,location,bleIndex,unprocessed,blackbox)
            unprocessed.append(call)
        else:
            buildBleBody(file,cluster,bleIndex,unprocessed,blackbox)

    #then the output nodes
    for opinDriver in cluster.outputs:
        #get the ipin node.
        opin = globs.nodes[opinDriver.id]

        writeNodeGraphNodeInterface('instantiation',opin,file)
        call = partial(writeNodeGraphNodeDescription,file= file ,node = opin,isOnCluster = True)
        unprocessed.append(call)


#done
def buildClusterDescription(file,cluster,location,unprocessed,blackbox):

    buildClusterInterface('description',file,cluster,location)
    buildClusterBody(file,cluster,location,unprocessed,blackbox)

    #write the footer
    file.write( 'endmodule\n')

###-----------------------------------------------------------------------------
###--------------end printer ---------------------------------------------------
###-----------------------------------------------------------------------------

#done
#build the connection between the clbs and the outer routing
#therfore connect the cluster ipin and opin outputs with the interface
#Note: ipins are part of the outer routing and not part of the generated cluster.
#for opins we generate a wire for the connection with the outer routing
def buildClusterInterfaces(type,file):

    if type == 'instantiation':
        #for the opins of a cluster we generate a wire for the connection with the cluster module.
        for location in globs.clusters:
            cluster = globs.clusters[location]

            # iterate through the drivers and grep the opin nodes.
            for opinDriver in cluster.outputs:
                #get the ipin node.
                opin = globs.nodes[opinDriver.id]
                #write the wire
                file.write('wire ' + 'node_' + str(opin.id) + ';\n')

    #step through ipins and opins of a cluster and grep the coressponding technolog mapped nodes.
    #then write a connection for the interface
    for location in globs.clusters:
        cluster = globs.clusters[location]

        buildClusterInterface(type,file,cluster,location)

#build a special verilog cluster module for each cluster
#done
def buildClusterDescriptions(file,unprocessed,blackbox):


    #step through ipins and opins of each cluster and grep the coressponding technolog mapped nodes.
    #then write the corresponding interface
    for location in globs.clusters:
        cluster = globs.clusters[location]
        buildClusterDescription(file,cluster,location,unprocessed,blackbox)
#done
def buildClusterBodys(file,unprocessed,blackbox):

    for location in globs.clusters:
        cluster = globs.clusters[location]
        buildClusterBody(file,cluster,location,unprocessed,blackbox)



#mark nodes of the nodegraph consisting of only one mapped passtrough node as
#a nodegraph passtrough
def markPassTroughNodes():

    for node in globs.nodes:

        #skip deleted and source and sink nodes
        if node.type > 3:

            #have only one mapped passtrough node as a child->mark it
            if (len(node.inputs) == 1):

                mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[0])

                if mappedNode.passTrough:
                    node.passTrough = True


#process all delay build decscription function. This could spawn
#new description functions again, so we process the list until all functions
#are finished
def processQuededDesctiptions(unprocessed):

    #process the list until now more calls are spawned
    while len(unprocessed) > 0:

        #pop the first element and process it
        call = unprocessed.pop(0)
        call()


#build a verilog file with fixed configured LUTs and muxes to verficate the
#equivalence of the hardware overlay and the circuit
#@param verificationalBuild flags that the file is used for verification
def buildVerificationOverlay(fileName,verificationalBuild,blackBox):

    #To allow to configurate which parts of the fpga should be wrapped
    #by a module and which not, we have the following architecture:
    #each module element in the hirachy, e.g. the ble module provide two functions:
    #   - a build module interface function, which will be called for an instantiation
    #     of the module.
    #   - build module description function which should be called when the module
    #     description will be build. To build the module description it call
    #     the interface function (because the code is nearly the same as for the instantiation)
    #     and a body function where the content of the module is written.
    # the build module description functions often will be called delayed when the previous
    # modules (which are higher in the module hirachy) are finished their build.
    # to make this delayed call easier we have a list of unprocessed description functions
    # which are processed by the processQuededDesctiptions function until now more
    # description function has spawned.

    #the list of unprocessed description calls
    unprocessed= []

    #check the nodegraph for passtrough nodes
    #markPassTroughNodes()

    #write a configuration to the mapped nodes
    generateMappedNodesConfiguration()

    #generate a topmodule file for this verification overlay
    generateTopModule()

    #create the verilog file and a seperate module instantiation file if needed
    file = open(fileName, 'w')

    #start with the header
    BuildVerilog.writeHeader(file)

    #to make things easier in the testsuite
    if verificationalBuild:
        writeTestsuitePatch(file)

    #build in two steps: first the outer routing. then connect the clb module interface to the outer routing.
    #later we generate these used clb modules by processing the description calls
    buildOuterRouting(file,unprocessed)

    if globs.params.hierarchyCluster:
        buildClusterInterfaces('instantiation',file)
        call = partial(buildClusterDescriptions,file,unprocessed,blackBox)
        unprocessed.append(call)
    else:
        buildClusterBodys(file,unprocessed,blackBox)

    #conncet the opins/ipins with the fpga outputs/inputs
    ConnectIO(file)

    #finish the the main module
    #the verificational build don't instantiate the config controller
    if verificationalBuild:
        writeFooter(file)
    else:
        BuildVerilog.writeFooter(file)

    #process all queded desription calls
    processQuededDesctiptions(unprocessed)

    file.close()

    #rewrite the abc output file for equivalnce checks
    if verificationalBuild:
        writeCircuitVerificationBlif()
