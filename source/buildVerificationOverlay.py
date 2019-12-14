import BuildVerilog
import globs

#write a wire in the verilog file for a node output.
#Therefore we use the name attribute which is unique identifier in the
#TechnologyNodeGraph
def writeWire(file,node):

    # an eLut have two outputs.
    # one registered and one unregistered output
    if node.eLUT:
        string = 'wire ' + node.name + '_reg;\n'
        string += 'wire ' + node.name + '_unreg;\n'
    # the rest have only one output
    else:
        string = 'wire ' + node.name + ';\n'

    file.write(string)


def writePassTroughNode(file,node):
    file.write('assign ' + node.name + ' = ' node.inputs[0] + ';\n');



## A helper function for write_LUTRAM
#  returns a string '{ name1, name2 , ... }' for a given list of names
def list_to_vector(names):
    string = '{'
    for n in names:
        string = string + n + ','
    string = string[0:-1] + '}'
    return string

## write the verilog code for the LUTRAM.
# The LUTRAM can be a lutram of a routing mux, a ffmux or a eLUT or Ipin
def write_LUTRAM(f, node):

    inputNames = []

    #for the verification overlay we dont use the staging configuration
    config_stage = 0
    config_offset = 0

    #is it a regular mux or a mux on a ble?
    #the first input is the name of the LUTRAM wire of the lut.
    #remember that this LUTRAM have two outputs
    if node.ffmux:
        #the lut mux have only one input
        lutName = node.inputs[0]
        inputNames.append(lutName + '_unreg')
        inputNames.append(lutName + '_reg')

    #when not just use the provided names
    else:
        inputNames = node.inputs

    ## assign an 0 driver to every unconnected input
    while len(inputNames) < globs.host_size:
        inputNames.append("1'b0")

    #is it an eLUT or just a mux?
    if node.eLUT:
        string ='elut_custom ' + 'LUT_' + node.name + ' ('
    else:
        string ='lut_custom ' + 'MUX_' + node.name + ' ('

    string +='''
    .a(wr_addr), // input [5 : 0] a
    .d(wr_data[''' + str(config_offset) + ''']), // input [0 : 0]
    '''
    f.write(string)

    #connect the name of the input wires
    string = '.dpra(' + list_to_vector(inputNames) + \
         '), // input [5 : 0] dpra'
    f.write(string)

    f.write('''
    .clk(clk), // input clk
    .we(wren[''' + str(config_stage) + ''']), // input we
    ''')
    #connect the name of the output wires.
    #if its an elut than we have two output wires instead of one
    if node.eLUT:
        f.write( '.dpo(' + node.name + \
             '_unreg), // unregistered output')

        f.write('''
        .qdpo_clk(clk2), // run clk
        .qdpo_rst(ffrst), // input flip flop reset
        ''')
        f.write( '.qdpo(' + node.name + \
             '_reg)); // registered output\n\n')
    else:
        f.write( '.dpo(' + node.name + '));\n\n')



def ConnectIO(f):

    #When using orderedIO we connect the rebranded sources/sinks with the fpga
    #inputs and outputs.
    #Otherwise we directly connect the IO opins and ipins
    #with the fpga inputs and outputs, skipping the IO sink/and sources

    if globs.params.orderedIO:
        #connect the iomux node wires with the fpga outputs
        for iomuxId,index in enumerate(globs.orderedOutputs):
            f.write('assign fpga_outputs[' + str(index) + \
                '] = ' + str(iomuxId) + ';\n')
    else:
        #connect the ipin node wires with the fpga outputs
        for key in globs.IOs:
            IO = globs.IOs[key]
            for ipin,index in enumerate(IO.outputs):
                f.write('assign fpga_outputs[' + str(index) + '] = ' + str(ipin.id) + ';\n')

    if globs.params.orderedIO:
        #connect the iomux node wires with the fpga inputs
        for iomuxId,index in enumerate(globs.orderedInputs):
            f.write('assign ' + str(iomuxId) + \
                ' = fpga_inputs[' + str(index) + '];\n')
    else:
        #connect the opin node wires with the fpga inouts
        for key in globs.IOs:
            IO = globs.IOs[key]
            for opin,index in enumerate(IO.inputs):
                f.write('assign ' + str(opin.id) + ' = fpga_inputs[' + str(index) + '];\n')


#build a verilog file with fixed configured LUTs and muxes to verficate the
#equivalence of the hardware overlay and the circuit
def buildVerificationOverlay(fileName):

    #start with the header
    file = open(fileName, 'w')
    BuildVerilog.writeHeader(file)


    for node in globs.technologyMappedNodes.getNodes():

        #source and sinks were skipped. They are not used on clusters or IOs yet.
        if node.type < 3:
            continue

        #write a wire for the node output.
        #because every node has only one unique output
        writeWire(file,node)

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
    BuildVerilog.writeFooter(file)
