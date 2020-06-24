# use this if you want to include modules from a subforder
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"VprParsers")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)


import structs
import globs
import re

import BlifParser


## Parse the source blif file, which was generated from the
## user logic verliog file by odin + abc,
## and transfer the information to internal structures.
# The blif file contain the the complete logic
# on a lut and flipflop level, so the file give use the configuration
# of the luts and the connection of these luts and their flipflops.
# These elements may be later on different clusters,
# but the clusters are not represented in this file.

# Parse the source blif file and transfer the information
# to internal internal structures:
# *) get the blif names of the fpga inputs and outputs
#    and assign them to the nodes (name attribute) in the node graph.
#    Also append these names to the globs.inputs and globs.outputs list.
# *) create lut and latch representations and append them to the globs.LUTs
#    and globs.latches dicts.
# *) store the configuration of the luts in an internal format.
def read_BLIF(filename):

    blifFile = BlifParser.parseBlif(filename)

    #assign the inputs and outputs
    for input in blifFile.inputs:

        # append the blif name to the global input list
        globs.inputs.append(input.blifName)

        # assign the name to the nodes in the node graph. skip the clock here
        if input.blifName != 'top^clock':

            nodeId = globs.orderedInputs[input.ioIndex]
            node =  globs.nodes[nodeId]
            node.name = input.blifName
            print 'found input ',node.name ,'in blif file, assign to node id:',nodeId

    for output in blifFile.outputs:

        # append the blif name to the global output list
        globs.outputs.append(output.blifName)

        # assign the name to the nodes in the node graph.
        nodeId = globs.orderedOutputs[output.ioIndex]
        node =  globs.nodes[nodeId]
        node.name = output.blifName

    for latch in blifFile.latches:

        newLatch = structs.latch()
        newLatch.input = latch.inputNet
        newLatch.output = latch.outputNet

        globs.latches[newLatch.output] = newLatch

    for name in blifFile.names:
        print str(name.content)

        #create a lut instance
        newLUT = structs.LUT()
        #assign the input and output blif names
        newLUT.output = name.outputNet
        newLUT.inputs = name.inputNets
        newLUT.contents = name.content

        globs.LUTs[newLUT.output] = newLUT

        # The LUT can describe a passthrough from a fpga input
        # to a fpga output.
        # We save the mapping (input name, list of output names)
        # to find later in read_routing the corresponding sink node,
        # which has the output name in the name attribute
        # This is possible because the net name to this sink
        # is same as the blif fpga input name.

        # Important: We assume here that abc build the
        # passthrough in a increasing order of the output pins
        # And that Vpr route the output pins in the same order.
        # TODO: is that true?
        if newLUT.output in globs.outputs and len(newLUT.inputs) == 1:

            inputName = newLUT.inputs[0]
            outputName = newLUT.output
            #There is no entry for the fpga input yet
            if inputName not in globs.lastnetmapping:
                #create a empty list
                globs.lastnetmapping[inputName] = []

            #append the output name
            globs.lastnetmapping[inputName].append(outputName)

    # Mark which LUTs are using latches
    for key in globs.latches:
        globs.LUTs[globs.latches[key].input].useFF = True
