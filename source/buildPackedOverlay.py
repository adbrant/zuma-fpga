import BuildVerilog
import BuildBitstream
import globs

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
def buildOuterRouting(file,modulesFile):

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
        writeNode(file,modulesFile,node,False)

#buld the lutrams and wires for nodes in a clb for a given location.
#generate lutrams for every elut ffmux opin and interconnect node.
def buildInnerRouting(file,modulesFile,location):

    for node in globs.nodes:

        #source and sinks were skipped. They are not used as lutrams yet.
        if node.type < 3:
            continue

        #skip ipins and channels
        if node.type  >= 4 and node.type  <= 6:
            continue

        #skip iomuxes
        if node.type == 10:
            continue

        #skip nodes not part of this cluster
        if node.location != location:
            continue

        #else print all mapped child nodes and their wires to the file
        writeNode(file,modulesFile,node,True)

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

#write the module instantiation to the file and the module description to the modulesFile
def writeNodeGraphNode(file,modulesFile,node,isOnCluster):

    #write the output wire of this node to the file.
    #therfore we use the last mapped node which output is the same as the
    #nodegraph node output
    mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[-1])
    writeWire(file,mappedNode)

    #write the node module instantiation + the start of the description in one strike

    #first the interface name
    interfaceString = 'Mod_node_' + str(node.id) + ' mod_node_' + str(node.id) + '(\n'
    moduleInterfaceString  = 'module Mod_node_' + str(node.id) + '(\n'
    file.write( interfaceString )
    modulesFile.write( moduleInterfaceString)

    # inputs and output
    for inputNodeId in node.inputs:
        inputNodeName = 'node_' + str(inputNodeId)
        inputNodeString = '.' + inputNodeName + '(' + inputNodeName + '),\n'
        moduleInputNodeString = inputNodeName + ',\n'
        file.write( inputNodeString )
        modulesFile.write( moduleInputNodeString )

    #the output is just the node id
    nodeName = 'node_' + str(node.id)
    outputNodeString = '.' + nodeName + '(' + nodeName + ')\n'
    moduleOuputString =  nodeName
    file.write( outputNodeString )
    modulesFile.write( moduleOuputString )

    #end the module instantiation
    file.write( ');\n')
    modulesFile.write( ');\n')

    #now print the rest of the module desctiption to the module file

    # inputs and output
    for inputNodeId in node.inputs:
        inputNodeName = 'node_' + str(inputNodeId)
        inputNodeString = 'input ' + inputNodeName + ';\n'
        modulesFile.write( inputNodeString )

    nodeName = 'node_' + str(node.id)
    outputNodeString = 'output ' + nodeName + ';\n'
    modulesFile.write( outputNodeString )

    #now the mapped nodes as content
    for mappedNodeName in node.mappedNodes:

        mappedNode = globs.technologyMappedNodes.getNodeByName(mappedNodeName)
        writeMappedNode(modulesFile,mappedNode,isOnCluster)

    #finally the end of the module
    modulesFile.write( 'endmodule\n')

#write all wires and the mapped node instances of a nodegraph node in the verilog file
def writeNode(file,modulesFile,node,isOnCluster):

    #switches heck if interface or not
    #write Node Interface
    #add nodes in the modules list
    #optinal: print wire
    if globs.params.outerNodesModules and not isOnCluster:
        writeNodeGraphNode(file,modulesFile,node,isOnCluster)

    elif globs.params.interconnectModules and node.type == 7:
        writeNodeGraphNode(file,modulesFile,node,isOnCluster)

    else:
        #else: print it directly
        for mappedNodeName in node.mappedNodes:

            mappedNode = globs.technologyMappedNodes.getNodeByName(mappedNodeName)
            writeMappedNode(file,mappedNode,isOnCluster)


#build the connection between the clbs and the outer routing
#therfore connect the cluster ipin and opin outputs with the interface
#Note: ipins are part of the outer routing and not part of the generated cluster.
#for opins we generate a wire for the connection with the outer routing
def buildClusterInterfaces(f):

    #for the opins of a cluster we generate a wire for the connection with the cluster module.
    for location in globs.clusters:
        cluster = globs.clusters[location]

        # iterate through the drivers and grep the opin nodes.
        for opinDriver in cluster.outputs:
            #get the ipin node.
            opin = globs.nodes[opinDriver.id]
            #write the wire
            f.write('wire ' + 'node_' + str(opin.id) + ';\n')

    #step through ipins and opins of a cluster and grep the coressponding technolog mapped nodes.
    #then write a connection for the interface
    for location in globs.clusters:
        cluster = globs.clusters[location]

        #first write a cluster header:
        (x,y) = location
        f.write( '    Cluster_' + str(x) + '_' + str(y) + ' cluster_'+ str(x) + '_' + str(y) + '(\n')
        f.write( '    .wr_addr(wr_addr),\n' )
        f.write( '    .wr_data(wr_data),\n' )
        f.write( '    .wren(wren),\n' )
        f.write( '    .clk(clk),\n' )
        f.write( '    .clk2(clk2),\n' )
        f.write( '    .ffrst(ffrst),\n' )

        # iterate through the drivers and grep the ipin nodes.
        for ipinDriver in cluster.inputs:
            #get the ipin node.
            ipin = globs.nodes[ipinDriver.id]
            #connect it with the interface
            f.write( '    .node_' + str(ipin.id) +'(' + 'node_' + str(ipin.id) + '),\n')

        # iterate through the drivers and grep the opin nodes.
        for index,opinDriver in enumerate(cluster.outputs,1):
            #get the ipin node.
            opin = globs.nodes[opinDriver.id]
            #connect it with the interface
            f.write( '    .node_' + str(opin.id) +'(' + 'node_' + str(opin.id) + ')')
            if index != len(cluster.outputs):
                f.write( ',\n')

        #write the footer
        f.write( '    );\n')

#build a special verilog cluster module for each cluster
def buildClusterDescriptions(f,modulesFile,blackBox):


    #step through ipins and opins of each cluster and grep the coressponding technolog mapped nodes.
    #then write the corresponding interface
    for location in globs.clusters:
        cluster = globs.clusters[location]

        #first write a cluster header:
        (x,y) = location
        f.write( 'module  Cluster_' + str(x) + '_' + str(y) + '(\n')
        f.write( '    wr_addr,\n' )
        f.write( '    wr_data,\n' )
        f.write( '    wren,\n' )
        f.write( '    clk,\n' )
        f.write( '    clk2,\n' )
        f.write( '    ffrst,\n' )

        # iterate through the drivers and grep the ipin nodes.
        for ipinDriver in cluster.inputs:
            #get the ipin node.
            ipin = globs.nodes[ipinDriver.id]
            #connect it with the interface
            f.write( '    node_' + str(ipin.id) + ',\n')

        # iterate through the drivers and grep the opin nodes.
        for index,opinDriver in enumerate(cluster.outputs,1):
            #get the ipin node.
            opin = globs.nodes[opinDriver.id]
            #connect it with the interface
            f.write( '    node_' + str(opin.id))
            #the last entry got no delimiter
            if index != len(cluster.outputs):
                f.write( ',\n')

        #write the input footer
        f.write( '    );\n')

        #now repeat the same pattern
        #TODO: use parameter config with
        f.write( '    input [5:0] wr_addr;\n' )
        f.write( '    input [32-1:0] wr_data;\n' )
        f.write( '    input [4096:0] wren;\n' )
        f.write( '    input clk;\n' )
        f.write( '    input clk2;\n' )
        f.write( '    input ffrst;\n' )

        # iterate through the drivers and grep the ipin nodes.
        for ipinDriver in cluster.inputs:
            #get the ipin node.
            ipin = globs.nodes[ipinDriver.id]
            #connect it with the interface
            f.write( '    input node_' + str(ipin.id) + ';\n')

        # iterate through the drivers and grep the opin nodes.
        for opinDriver in cluster.outputs:
            #get the ipin node.
            opin = globs.nodes[opinDriver.id]
            #connect it with the interface
            f.write( '    output node_' + str(opin.id) + ';\n')

        #now we have finished the interface. build the content
        #iterate through all nodes and build those with the right location
        if not blackBox:
            buildInnerRouting(f,modulesFile,location)

        #write the footer
        f.write( 'endmodule\n')

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


#build a verilog file with fixed configured LUTs and muxes to verficate the
#equivalence of the hardware overlay and the circuit
#@param verificationalBuild flags that the file is used for verification
def buildVerificationOverlay(fileName,verificationalBuild,blackBox):

    #check the nodegraph for passtrough nodes
    #markPassTroughNodes()

    #write a configuration to the mapped nodes
    generateMappedNodesConfiguration()

    #generate a topmodule file for this verification overlay
    generateTopModule()

    #create the verilog file and a seperate module instantiation file if needed
    file = open(fileName, 'w')
    modulesFile = open('modules' + fileName, 'w')

    #start with the header
    BuildVerilog.writeHeader(file)

    #to make things easier in the testsuite
    if verificationalBuild:
        writeTestsuitePatch(file)

    #build in two steps: first the outer routing. then connect the clb module interface to the outer routing.
    #later we genearte these used clb modules
    buildOuterRouting(file,modulesFile)
    buildClusterInterfaces(file)

    #conncet the opins/ipins with the fpga outputs/inputs
    ConnectIO(file)

    #finish the the main module
    #the verificational build don't instantiate the config controller
    if verificationalBuild:
        writeFooter(file)
    else:
        BuildVerilog.writeFooter(file)

    #generate the clb modules
    buildClusterDescriptions(file,modulesFile,blackBox)

    file.close()
    modulesFile.close()

    #rewrite the abc output file for equivalnce checks
    if verificationalBuild:
        writeCircuitVerificationBlif()
