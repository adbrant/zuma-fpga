from structs import *
import globs
import re



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

    fh = open(filename,"r")
    line = fh.readline()

    inputoffset = 0

    # Parse the source blif file
    while len(line) > 0:

        if line.find(".model") > -1:
            line = fh.readline()

        #get the blif names of the inputs and assign them to
        #nodes(name attribute) in the node graph.
        elif line.find(".inputs") > -1:
            #read items until no more backslashes appear
            items = line.strip().split(' ')[1:]

            while items[-1] == '\\':
                items = items[:-1]
                nextline = fh.readline()
                items = items + nextline.strip().split(' ')

            for item in items:
                # append the blif name to the global input list
                globs.inputs.append(item.strip())
                if item.strip() == 'top^clock':
                    continue
                if item.strip() == 'top^reset':
                    # set reset to the first input pin
                    i = 0
                    inputoffset += 1
                elif item.strip() == 'top^in':
                    # just one input
                    i = 0
                else:
                    nums = re.findall(r'\d+', item)
                    nums = [int(i) for i in nums ]
                    i = nums[-1] + inputoffset
                # assign the name to the nodes in the node graph
                globs.nodes[globs.orderedInputs[i]].name = item.strip()
                print 'found input ',globs.nodes[globs.orderedInputs[i]].name ,'in blif file, assign to node id:',globs.orderedInputs[i]

            line = fh.readline()

        #get the blif names of the outputs and assign them to
        #nodes(name attribute) in the node graph
        elif line.find(".outputs") > -1:
            #read items until no more backslashes appear
            items = line.strip().split(' ')[1:]
            while items[-1] == '\\':
                items = items[:-1]
                nextline = fh.readline()
                items = items + nextline.strip().split(' ')

            for item in items:
                # append the blif name to the global output list
                globs.outputs.append(item.strip())
                if item.strip() == 'top^out':
                    # just one output
                    i = 0
                else:
                    nums = re.findall(r'\d+', item)
                    nums = [int(i) for i in nums ]
                    i = nums[-1]
                # assign the name to the nodes in the node graph
                globs.nodes[globs.orderedOutputs[i]].name = item.strip()


            line = fh.readline()

        #get the latches and place an new latch instance in the latches dict.
        elif line.find(".latch") > -1:
            #read items until no more backslashes
            items = line.strip().split(' ',1)[1].strip().split(' ')

            while items[-1] == '\\':
                items = items[:-1]
                nextline = fh.readline()
                items = items + nextline.strip().split(' ')
            innet = items[0]
            outnet = items[1]
            newLatch = latch()
            newLatch.input = innet
            newLatch.output = outnet

            globs.latches[outnet] = newLatch

            line = fh.readline()

        #got a lut. create a LUT instance and place it in the LUTs dict.
        elif line.find(".names") > -1:

            #read items until no more backslashes appear
            items = line.strip().split(' ')[1:]

            while items[-1] == '\\':
                items = items[:-1]
                nextline = fh.readline()
                items = items + nextline.strip().split(' ')

            #these are the names of the input nets and output nets
            innets = items[:-1]
            outnet = items[-1]

            #create a lut instance
            newLUT = LUT()
            #assign the input and output blif names
            newLUT.output = outnet
            newLUT.inputs = innets

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
            if outnet in globs.outputs and len(innets) == 1:

                inputName = innets[0]
                outputName = outnet
                #There is no entry for the fpga input yet
                if inputName not in globs.lastnetmapping:
                    #create a empty list
                    globs.lastnetmapping[inputName] = []

                #append the output name
                globs.lastnetmapping[inputName].append(outputName)

            line = fh.readline()
            items = line.split()
            contents = []

            #ABC format of the content of a logic gate:
            #1) if the content consist of only a 1 or 0, then we have
            #   a constant 1 or 0 as the output
            #2) else we have at least one a PLA description line
            #   like 0101-1 1 or 01- 0

            #internal representation:
            # For 1) we store a tuple ('-', constant output value)
            # and for 2) we store the two given values:
            # (k-input,output value)
            while items[-1] == '1' or items[-1] == '0' :
                #option 1)
                #just a single output value
                if (len(items) < 2):
                    contents.append(('-',items[0]))
                #option 2)
                else:
                    contents.append((items[0],items[1]))

                line = fh.readline()
                items = line.split()

            #assign the new content
            newLUT.contents = contents
            globs.LUTs[outnet] = newLUT
        else:
            line = fh.readline()

    # Mark which LUTs are using latches
    for key in globs.latches:
        globs.LUTs[globs.latches[key].input].useFF = True
