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

    inputFile = open('clock_fixed.blif','r')
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

    f.write('\nendmodule')

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

    #for the verification overlay we dont use the staging configuration
    config_stage = 0
    config_offset = 0

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


#build a verilog file with fixed configured LUTs and muxes to verficate the
#equivalence of the hardware overlay and the circuit
def buildVerificationOverlay(fileName):

    #write a configuration to the mapped nodes
    generateMappedNodesConfiguration()

    #generate a topmodule file for this verification overlay
    generateTopModule()

    #write the verilog file
    #start with the header
    file = open(fileName, 'w')

    BuildVerilog.writeHeader(file)
    #to make things easier in the testsuite
    writeTestsuitePatch(file)

    for node in globs.technologyMappedNodes.getNodes():

        #source and sinks were skipped. They are not used on clusters or IOs yet.
        if node.type < 3:
            continue

        #write a wire for the node output.
        #because every node has only one unique output
        writeWire(file,node)

        #for an iomux of the fpga inputs we only generate the output wire
        #but not a configuration.
        if (node.type == 10) and (len(node.inputs) == 0):
            continue

        #if the node is a passtrough node just use the assign optimization
        #these are nodes with only one input except an lut,ffmux or ipin which
        #are a special case
        if node.passTrough:
            writePassTroughNode(file,node)
            continue

        #this node is a part of a mux,lut,ffmux or ipin -> write a lutram
        else:
            writeLUTRAM(file,node)

    #conncet the opins/ipins with the fpga outputs/inputs
    ConnectIO(file)

    #finish the verilog file
    writeFooter(file)

    file.close()

    #rewrite the abc output file for equivalnce checks
    writeCircuitVerificationBlif()
