from structs import *
import globs
import math
import Dump

## build a bitstream for a mux. see ZUMA paper.
# @param width The input width of the mux.
# @param offset The fix input selector of the mux.
# @return The configuration bits
def buildMuxBitstreamConfig(width, offset):
    length = int(math.pow(2,width))
    bits = []
    offset2 = width - 1 - offset #reverse order
    for i in range(length):
        if (i >> offset2) % 2:
            bits.append('1')
        else:
            bits.append('0')

    return bits


##build a bitstream for an eLut
# @param bleIndex The position of the lut in the cluster
# @param LUT The lut instance
# @param width The width of the lut
# @return a bitstream of the lut content
def build_lut_contents(width, LUT, cluster,bleIndex):
    length = int(math.pow(2,width))


    #first we need to map our blif names in LUT.inputs to their used pin position

    #this list describe the input mapping e.g. for a 6er lut: [3,2,6,1,0,5,4],
    #where the position is given by the position of the blif/netlist name
    #in the list LUT.inputs and the value is the used pin position on the lut.
    pins = []

    #get the used input pins positions on the lut.
    #At the moment we just have the names connected to unknown pin positions
    for name in LUT.inputs:
        #search it in the pin position dict build in ReadNetlist.
        try:
            pinPosition = LUT.pinPositions[name]
            #save the pin position for the mapping
            pins.append(pinPosition)

        except KeyError:
            print 'error in build_lut_contents: pin ', name , \
                'in Lut ',  LUT.output ,' not found'

    #the final configuration. contains one config bit for each address
    #see the description below
    bits = []
    #for all possible addresses 0000,0001,00011 etc we have to set
    # one and only one config bit.
    # this config bit will be generated in each loop for ascending addresses
    for i in range(length):
        #is this position 0 or 1
        bit_vals = []
        setting = 0

        #provide the following bit representation of the address,
        #eg: i=4: bit_vals = [0,0,0,1,0,0] by a width of 6
        for j in range(width):
            bit_vals.append((i>>(width-j-1))%2)

        #now for the given address i, we have to find this address
        #in the content lines of blif.
        #the second entry in the line is then
        #the bit set (setting) of our config bit.
        for line in LUT.contents:

            #is this line false?
            matchingline = 1
            if line[1] is '1':
                setting = 0
                for p, val in enumerate(line[0]):
                    #need pin num of pos, filter empty luts
                    if len(pins) == 0:
                        continue
                    pin = pins[p]
                    if val is '-':
                        pass
                    elif bit_vals[pin] is int(val):
                        pass
                    else:
                        matchingline = 0
                        break
                #we found the address and it has a 1 bit setting
                if matchingline:
                    setting = 1
            elif line[1] is '0':
                setting = 1
                for p, val in enumerate(line[0]):
                    #need pin num of pos, filter empty luts
                    if len(pins) == 0:
                        continue
                    pin = pins[p]
                    if val is '-':
                        pass
                    elif bit_vals[pin] is int(val):
                        pass
                    else:
                        matchingline = 0
                        break
                #we found the address and it has a 0 bit setting
                if matchingline:
                    setting = 0
            else:
                assert(0)

            #because we found the corresponding content line we
            #can break up the search
            if matchingline:
                break
        #append the given config bit to the configuration
        bits.append(setting)

    return bits


##build a bitstream consisting of LUTRAMs config bits and save it in a .hex file
# @param filename The filename of the bitstream .hex file.
def build_bitstream(filename):

    #this function has two parts: first it adds
    #the LUTRAM config bits for eLuts and muxes
    #in an array called bit_pattern.
    #Uses buildMuxBitstreamConfig for generating the config bits of the muxes.
    #Uses build_lut_contents for generating the config bits of the eLuts.
    #In the second part the function write this config bits in a hex file
    #with a bit protocol stuff wrapped around.

    #Config_pattern describe the placement of the nodes by its nodeId.
    #see build_global_routing_verilog()

    last_node = -1
    #number of config bits of the LUTRAM.
    lut_len = int(math.pow(2, globs.host_size))

    # a 2 dimensional list of configurations for each lutram.
    # each row is a stage, consist of at most params.config_width
    # configurations for LUTRAMS that are configured in parallel.
    # every column is the 2^host_size bit configuration of a LUTRAM.
    # for a unconfigured LUTRAM the column entry is a empty list
    bit_pattern = []

    placed_luts = []

    # first section. fill the config bit array bit_pattern.

    #config_pattern: an array consiting of node ids,
    #for its structure see also configpattern.txt in the generated files directory.
    for row in globs.config_pattern:
        #for each row of write data
        bit_row = []
        for col in row:
            #for each LUTRAM


            if col is last_node:
                #for muxes that span multiple lutrams
                continue


            last_node = col
            node = globs.nodes[col]

            #The node is an eLut, which is a generic lut in the zuma design.
            if node.eLUT:
                if node.LUT: #has a configuration
                    cl = globs.clusters[node.location]

                    # get the ble index of this lut
                    # and save it in the variable index

                    # the lut can be:
                    # 1) a normal lut with a configuration
                    #    given in the blif file
                    # 2) a passthrough lut for the flipflop,
                    #    if only the flipflop is used on that ble.
                    #    the name of the passtrough lut is than
                    #    the name of the latch

                    index = cl.getBleIndex(node.LUT.output)


                    #build the configuration bits
                    #and append it to the configuration array
                    bits = build_lut_contents(globs.host_size, node.LUT, cl, index)
                    bit_row.append(bits)

                    if globs.debug:
                        print "ELUT id: " + str(node.id) +  "," + str(bits)

                    placed_luts.append(node.LUT.output)

                else:
                    bit_row.append([])
                    if globs.debug:
                        print "ELUT id: " + str(node.id) +  "," + str([])

                node.config_generated =     True
                continue

            if node.ffmux:
                #the source attribute for mappped nodes was already done
                #in the updateMappedFFMuxSource() function

                #get the lut that drive the mux
                elutnode = globs.nodes[node.source]

                #check if the mux/ble is used
                if elutnode.LUT:
                    if elutnode.LUT.useFF: #flipflop is used
                        bit_row.append(buildMuxBitstreamConfig(globs.host_size,0 )) # registered / with FF
                        bits = buildMuxBitstreamConfig(globs.host_size,0 )
                    else:
                        bit_row.append(buildMuxBitstreamConfig(globs.host_size,1 )) # unregistered / without FF
                        bits = buildMuxBitstreamConfig(globs.host_size,1 )
                #the mux/ble isn't used
                else:
                    bit_row.append([])
                    bits = []
                node.config_generated =     True
                if globs.debug:
                    print "FFMUX id: " + str(node.id) +  "," + str(bits)
                continue


            num_luts =  int(math.ceil((len(node.inputs)-globs.host_size)/(globs.host_size-1.0)) + 1)

            #sometimes we have to calc num_lut again for large muxes.
            if num_luts > globs.host_size + 1:
                level_size = len(node.inputs)
                num_luts = 0
                while level_size > 1:
                    level_size = int(math.ceil((level_size*1.0) / globs.host_size))
                    num_luts += level_size

            index = -1
            if node.source is -1: #not driven
                bits = []
                for i in range(num_luts):
                    bit_row.append([])
                    bits.append([])

                if globs.debug:
                    print "ROUTING MUX id: " + str(node.id) +  "," + str(bits)

                node.config_generated = True
                continue

            if node.source not in node.inputs:
                print 'error at node' , node.id, node.source, node.inputs
                break

            #if the mux fit in one host lut, build the configuration with buildMuxBitstreamConfig()
            if num_luts is 1:
                offset = node.inputs.index(node.source)
                bit_row.append(buildMuxBitstreamConfig(globs.host_size,offset ))
                bits = buildMuxBitstreamConfig(globs.host_size,offset )
                if globs.debug:
                    print "ROUTING MUX id: " + str(node.id) +  "," + str(bits)
                    print "Source: " + str(node.source) + " selector " + str(node.inputs.index(node.source)) + " list: " + str(node.inputs)

                #append the offset to the mappedNode
                #has only one mapped Node
                mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[0])
                source = mappedNode.inputs[offset]
                mappedNode.source = source

            #When the mux doesn't fit into one host lut
            #TODO: why can't we merge this approach with the next one?
            else:
                #build multilutram mux
                index = node.inputs.index(node.source)

                bits = []

                # two levels of LUTRAMs.
                # In the first level divide the inputs
                # equally over maximal #hostsize LUTRAMS
                # The second level then gets the outputs
                # of these first level LUTRAMs
                if num_luts <= globs.host_size + 1:
                    # mux_size <= globs.host_size * globs.host_size => tighly packed
                    last_index = -1

                    #try to get the first level LUTRAM that handles the source.
                    #configure this lut as the right passthrough
                    #the rest will be unconfigured
                    for n in range(num_luts - 1):

                        #This is the right first level lutram
                        if index in range(n*globs.host_size, (n+1)*globs.host_size):

                            offset = index - n*globs.host_size

                            bit_row.append(buildMuxBitstreamConfig(globs.host_size, offset ))
                            bits.append(buildMuxBitstreamConfig(globs.host_size,offset ))
                            last_index = n

                            #append the offset to the mappedNode
                            mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[n])
                            source = mappedNode.inputs[offset]
                            mappedNode.source = source

                        # this is one of the unneeded lutrams.
                        # Won't be configured.
                        else:
                            bit_row.append([])
                            bits.append([])

                    #configure the secon level lutram
                    if last_index  is -1:
                        offset = index-(num_luts-1)*globs.host_size+(num_luts-1)
                        config = buildMuxBitstreamConfig(globs.host_size,offset)

                        #append the offset to the mappedNode
                        mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[num_luts-1])
                        source = mappedNode.inputs[offset]
                        mappedNode.source = source

                        bit_row.append(config)
                        bits.append(config)
                    else:
                        offset = last_index

                        bit_row.append(buildMuxBitstreamConfig(globs.host_size,offset))
                        bits.append(buildMuxBitstreamConfig(globs.host_size,offset))

                        #append the offset to the mappedNode
                        mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[num_luts-1])
                        source = mappedNode.inputs[offset]
                        mappedNode.source = source

                    if globs.debug:
                        print "ROUTING MUX id: " + str(node.id) + "," + str(bits)
                        print "Source: " + str(node.source) + " selector " + str(node.inputs.index(node.source)) + " list: " + str(node.inputs)

                else:

                    bits = []

                    # mux_size > globs.host_size * globs.host_size => strictly layered
                    level_size = len(node.inputs)
                    level_size = int(math.ceil((level_size*1.0) / globs.host_size))
                    # First level (input nodes)

                    #to track the index of the current mapped node
                    mappedNodeIndex = 0

                    last_index = index
                    while (level_size > 1):
                        index = last_index
                        last_index = -1
                        for n in range(level_size):
                            if index in range(n*globs.host_size, (n+1)*globs.host_size):
                                offset = index - n*globs.host_size

                                bit_row.append(buildMuxBitstreamConfig(globs.host_size,offset ))
                                bits.append(buildMuxBitstreamConfig(globs.host_size,offset ))

                                #append the offset to the mappedNode
                                mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[mappedNodeIndex])
                                source = mappedNode.inputs[offset]
                                mappedNode.source = source

                                last_index = n
                            else:
                                bit_row.append([])
                                bits.append([])

                            mappedNodeIndex = mappedNodeIndex +1

                        if last_index  is -1:
                            print 'Error, node', node.id, 'should be driven, but index', index, 'not found'
                            assert(0)

                        level_size = int(math.ceil((level_size*1.0) / globs.host_size))

                    # Last level (Combination node)
                    #TODO: Check n here
                    offset = last_index

                    bit_row.append(buildMuxBitstreamConfig(globs.host_size, offset))
                    bits.append(buildMuxBitstreamConfig(globs.host_size, offset))

                    #append the offset to the mappedNode
                    mappedNode = globs.technologyMappedNodes.getNodeByName(node.mappedNodes[mappedNodeIndex])
                    source = mappedNode.inputs[offset]
                    mappedNode.source = source

                    if globs.debug:
                        print "ROUTING MUX id: " + str(node.id) + "," + str(bits)
                        print "Source: " + str(node.source) + " selector " + str(node.inputs.index(node.source)) + " list: " + str(node.inputs)

            node.config_generated = True
        bit_pattern.append(bit_row)

    #check we've done all configuration
    unconfiged = []
    for node in globs.nodes:
        if node.config_generated is False and len(node.inputs) > 1 and node.type > 2:
            unconfiged.append(node.id)
            for row in globs.config_pattern:
                if node.id in row:
                    pass


    if len(unconfiged) > 0:
        print 'Nodes skipped in bitstream' ,  unconfiged

    #global LUTs
    for key in globs.LUTs:
        if key not in placed_luts:
            if len(globs.LUTs[key].inputs) > 1:
                print 'error LUT not cofigured' , key

            else:
                print key, globs.LUTs[key].inputs

    import struct

    if globs.debug:
        Dump.dumpBitPattern(bit_pattern)
    # second section. write bit_pattern to file.

    # hex file line format:
    #:04001c00218000003f
    #':'
    #'04'       config data size in bytes
    #'001c'     current address
    #'00'       record type (00:data, 01:EOS)
    #'21800000' configuration data
    #'3f'       checksum: (256 - (sum_of_bytes % 256))%256

    # the configuiration is done in stages (rows of the bit pattern).
    # In each stage we configured
    # globs.params.config_width LUTRAMS in parallel.
    # This is done in the following way:
    # See the first 2^host_size config words in the bitstream
    # as the 2^host_size bit configuration for config_width LUTRAMS.
    # When you stack them, each i-th column in the j-th row
    # contain the j-th bit of the config for the i-th LUTRAM
    # so every column contain the bits for one LUTRAM

    #binfile is the bitstream file
    binfile = open(filename, 'wb')
    sysfile = open('config_script.tcl', 'wb')

    sysfile.write('master_write_8 0x01000000 [')

    def hex_n(i,n):
        st = hex(i)[2:]
        while len(st) < n:
            st = '0' + st
        if len(st) > n:
            print '\noverflow for hex conversion of',i,'length',n
            print 'perhaps params.config_addr_width is too small?\n'
            assert(0)
            st = st[len(st)-n:]
        return st

    #write the first line of the hex file

    #number of bytes which are configured in parallel
    bytes_per_row = globs.params.config_width/8

    # write number of virtual inputs to file before bitstream
    #TODO:Depreacted, is ignored by the mif generation script.

    num_virtual_inputs = 0
    for key in globs.IOs:
        IO = globs.IOs[key]
        for input in globs.IOs[key].inputs:
            if len(input.net) > 0 and input.net != 'open':
                num_virtual_inputs += 1

    checksum = bytes_per_row+2
    line = hex_n(num_virtual_inputs,bytes_per_row*2)
    for i in range(len(line)/2):
        byte = line[i*2:i*2+2]
        num = int(byte, 16)
        checksum = checksum + num
    line = line + hex_n((256 - (checksum % 256))%256,2)
    line = ':' + hex_n(bytes_per_row,2) + hex_n(0, globs.params.config_addr_width/4) + '02' + line + '\n'
    binfile.write(line)

    #write the rest of the lines of the bistream

    byte_data = ''
    current_addr = 0
    # Go through each stage (a row in the bit_pattern)
    # and write the configuration of the LUTRAMs
    # in #(LUTRAM config size, lut_len) config words in the bitstream,
    # each row for one bit, and each column for one LUTRAM.
    for row in bit_pattern:
        #write #(LUTRAM config size) configuration words
        for i in range(lut_len):
            string = ''

            #go through the lutrams (columns in bit_pattern) of this stage.
            #write the i-th bit of the configuration of one LUTRAM
            #in the corresponding column of the configuration word.
            for entry in row:

                #if this LUTRAM has a configuration
                if len(entry) is lut_len:
                    #some error checking
                    if str(entry[i]) not in ['0','1']:
                        print 'error in bits', entry[i]
                    #append the i-th bit to the config word
                    string = string + str(entry[i])

                #there's no configuration for the current LUTRAM
                elif len(entry) is 0:
                    string = string + '0'

                # TODO: when is this branch taken?
                # a not full configured lut seems wrong.
                else:
                    string = string + '0'
                    print 'row length is', len(entry), lut_len, entry

            #when the stage was not fully used (empty lutrams).
            #fill the last positions in the config word with 0.
            while len(string) < globs.params.config_width:
                string = string +'0'

            #now write the config word to the file,
            #with some protocol stuff around

            checksum = 0
            line = ''

            #write the config size field
            line = line + hex_n(bytes_per_row,2) #number of bytes
            checksum = checksum + bytes_per_row

            #write the address field
            line = line + hex_n(current_addr, globs.params.config_addr_width/4) #number of bytes
            line = line + '00' #record type (data)
            #increment the address
            current_addr = current_addr + bytes_per_row

            #write the configuration field
            for i in range(int(bytes_per_row)):
                byte = int(string[i*8:(i+1)*8],2)
                #char = chr(byte)
                #byte_data = byte_data+char
                #data = struct.pack('i', byte)

                #sysfile.write(hex(byte) + ' ')
                #binfile.write(data)
                line = line + hex_n(byte,2)

            checksum = 0
            for i in range(len(line)/2):
                byte = line[i*2:i*2+2]
                num = int(byte, 16)
                checksum = checksum + num

            #write the checksum and the ':'
            line = line + hex_n((256 - (checksum % 256))%256,2)
            line = ':' + line + '\n'
            binfile.write(line)

    binfile.write(':00' + hex_n(0, globs.params.config_addr_width/4) + '01FF\n')
    sysfile.write(']\n')
