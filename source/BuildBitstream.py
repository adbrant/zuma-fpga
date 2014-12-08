from structs import *
import globs
import math

## build a lutram mux configuration. see ZUMA paper.
# param width the input width of the mux.
# param offset the fix input selector of the mux.
def build_passthrough(width, offset):
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
##param bleIndex The position of the LUT in cluster
##param LUT The Lut instance
##param width The width of the lut
##return a bitstream of the lut content
def build_lut_contents(width, LUT, cluster,bleIndex):
    length = int(math.pow(2,width))


    #first we need to map our input pins to the ports from the blif

    #this list describe the mapping eg. [3,2,6,1,0,5,4]
    #where the position is given by the blif/netlist name,
    #and the value is the used pin position on the lut.
    pins = []

    #get the used input pins positions on the Lut.
    #At the moment we just have the names connected to unknown pin positions
    for name in LUT.inputs:
        pin_name = ''
        found = False
        # search the pin number on the Lut of the input name.
        # search the input name with the informations 
        # in the input_nets list of this lut for each pin.
        for pinPosition, (tag,index) in enumerate(cluster.LUT_input_nets[bleIndex]):

            ##first check if the LUT name is in this cluster
            ##or in another cluster.
            ##depending on this you use other lists to search in

            ##the LUT is in this cluster
            if tag == 'ble':
                lutName = cluster.getLutName(index)
            ##the LUT is in another cluster
            elif tag == 'input':
                lutName = cluster.getNameOnClusterInput(index)
            ##this pin has no input, continue the search
            elif tag == 'open':
                continue
            else:
                assert(0)
            #found the input name.
            #now we have name and the pin numer where its connected
            if lutName == name:
                #save the pin number for the mapping
                pins.append(pinPosition)

                found = True
                break

        if not found:
            print 'error in build_lut_contents: pin ', name , \
                'in Lut ',  LUT.output ,' not found'

    #when we use a clos network the routing algo
    #may switched the pin positions
    #therefore the list newPinPositions of the format:
    #[ble Index] [list of (old pin position, new pin position)]
    #points to the actual pin positions
    if globs.params.UseClos:
        #go through the pins list and update the positions
        for pinIndex,oldPinPosition in enumerate(pins):
            newPosition = -1
            #search the old pin position in the
            #newPinPosition list
            for newPinPositionTuple in cluster.newPinPositions[bleIndex]:
                #found the pin position. update the pin position
                if newPinPositionTuple[0] == oldPinPosition:
                    #this value indicates a match
                    newPosition = newPinPositionTuple[1]
                    #update the pin position
                    pins[pinIndex] = newPosition

            #pin was not found. throw an error
            if newPosition == -1:
                print 'error in build_lut_contents: pin ', \
                oldPinPosition , \
                ' was not found in newPinPosition list ', \
                cluster.newPinPositions[bleIndex]

    #the final configuration. contains one config bit for each adress
    #see the description below
    bits = []
    #for all possible adresses 0000,0001,00011 etc we have to set
    # one and only one config bit.
    # this config bit wil be generated in each loop for ascending adresses
    for i in range(length):
        #is this postition 0 or 1
        bit_vals = []
        setting = 0

        #provide the following bit representation of the adress,
        #eg: i=4: bit_vals = [0,0,0,1,0,0] by a width of 6
        for j in range(width):
            bit_vals.append((i>>(width-j-1))%2)

        #now for the given adress i, we have to find this adress
        #in the content lines of blif.
        #the second entry in the line is then
        #the bit set (setting) of our config bit.
        for line in LUT.contents:

            #is this line false?
            matchingline = 1
            if line[1] is '1':
                setting = 0
                for p, val in enumerate(line[0]):
                    #need pin num of pos, fliter empty luts
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
                ##we found the adress and it has a 1 bit setting
                if matchingline:
                    setting = 1
            elif line[1] is '0':
                setting = 1
                for p, val in enumerate(line[0]):
                    #need pin num of pos, fliter empty luts
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
                ##we found the adress and it has a 0 bit setting
                if matchingline:
                    setting = 0
            else:
                assert(0)

            #because we found the corresponding content line we
            #can break up the search
            if matchingline:
                #print bit_vals, pins, line
                break
        #append the given config bit to the configuration
        bits.append(setting)

    return bits


##build a bitstream consiting of LUTRAMs config bits and save it in a .hex file
# param filename The filename of the bitsream .hex file.
def build_bitstream(filename):

    #this function has two parts: first it adds
    #the single LUTRAM config bits for eLuts and LUTRAM Muxes
    #in an array called bit_pattern.
    #Uses build_passthrough for generating the config bits of the LUTRAM Muxes.
    #Uses build_lut_contents for generating the config bits of the eLuts.
    #In the scond part the function write this config bits in a hex file
    #with a bit protocol stuff wrapped around.

    #Config_pattern describe the placement of the nodes by its nodeId.
    #see build_global_routing_verilog()

    last_node = -1
    lut_len = int(math.pow(2, globs.host_size))
    bit_pattern = []

    placed_luts = []

    # first section. fill the config bit array bit_pattern.

    #config_pattern: an array consiting of node ids,
    #for its structure see also configpattern.txt in the generated files dir.
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

                    # the lut use its flipflop
                    if node.LUT.useFF:
                        # the lut that use its flipflop can be:
                        # 1) a normal lut with a configuration
                        #    given in the blif file
                        # 2) a passtrough lut for the flipflop,
                        #    if only the flipflop is used on that ble.
                        #    the name of the passtrough lut is than
                        #    the name of the latch
                        # 3) Dunno TODO: why we need the second branch?

                        # option 1,2)
                        if node.LUT.output in cl.LUTs:
                            index = cl.LUTs.index(node.LUT.output)

                        # option 3)
                        else:
                            #use the latch name to get the lut name
                            #via the reverselatch list,
                            #which describe a mapping: latchname->lutname

                            #TODO: is this branch still needed?
                            index = cl.LUTs.index(globs.reverselatches[node.LUT.output])

                    #a lut that don't use its flipflop
                    else:
                        index = cl.LUTs.index(node.LUT.output)

                    #build the configuration bits
                    #and append it to the configuration array
                    bits = build_lut_contents(globs.host_size, node.LUT, cl, index)
                    bit_row.append(bits)

                    placed_luts.append(node.LUT.output)

                else:
                    bit_row.append([])

                node.config_generated =     True
                continue

            if node.ffmux:
                if node.LUT: #mux has a configuration / flipflop is used
                    bit_row.append(build_passthrough(globs.host_size,0 )) # registered / with FF
                else:
                    bit_row.append(build_passthrough(globs.host_size,1 )) # unregistered / without FF
                node.config_generated =     True
                continue

                
            num_luts =  int(math.ceil((len(node.inputs)-globs.host_size)/(globs.host_size-1.0)) + 1)
            if num_luts > globs.host_size + 1:
                level_size = len(node.inputs)
                num_luts = 0
                while level_size > 1:
                    level_size = int(math.ceil((level_size*1.0) / globs.host_size))
                    num_luts += level_size

            index = -1
            if node.source is -1: #not driven
                for i in range(num_luts):
                    bit_row.append([])
                    
                node.config_generated = True
                continue
                
            if node.source not in node.inputs:
                print 'error at node' , node.id, node.source, node.inputs
                break
                    
            if num_luts is 1: 
                bit_row.append(build_passthrough(globs.host_size,node.inputs.index(node.source) ))
            
            #The node is an LUTRAM mux.
            else:
                #build multilutram mux
                index = node.inputs.index(node.source)
                
                
                if num_luts <= globs.host_size + 1:
                    # mux_size <= globs.host_size * globs.host_size => tighly packed
                    last_index = -1
                    for n in range(num_luts - 1):
                        if index in range(n*globs.host_size, (n+1)*globs.host_size):
                            bit_row.append(build_passthrough(globs.host_size,index - n*globs.host_size ))
                            last_index = n
                        else:
                            bit_row.append([])
                    if      last_index  is -1:
                        config = build_passthrough(globs.host_size,index-(num_luts-1)*globs.host_size+(num_luts-1))
                        bit_row.append(config)
                    
                        if node.id == 323:
                            print node.id, index, num_luts, globs.host_size, index-(num_luts-1)*globs.host_size+(num_luts-1)
                            print config
                    else:
                        bit_row.append(build_passthrough(globs.host_size,last_index))
                        
                else:
                    # mux_size > globs.host_size * globs.host_size => strictly layered
                    level_size = len(node.inputs)
                    level_size = int(math.ceil((level_size*1.0) / globs.host_size))
                    # First level (input nodes)
                    last_index = index
                    while (level_size > 1):
                        index = last_index
                        last_index = -1
                        for n in range(level_size):
                            if index in range(n*globs.host_size, (n+1)*globs.host_size):
                                bit_row.append(build_passthrough(globs.host_size,index - n*globs.host_size ))
                                last_index = n
                            else:
                                bit_row.append([])
                        if      last_index  is -1:
                            print 'Error, node', node.id, 'should be driven, but index', index, 'not found'
                            assert(0)
                        level_size = int(math.ceil((level_size*1.0) / globs.host_size))
                        
                    # Last level (Combination node)
                    #TODO: Check n here
                    bit_row.append(build_passthrough(globs.host_size, last_index))
                
            node.config_generated = True
        bit_pattern.append(bit_row)
    
    #check weve done all configuration
    unconfiged = []
    for node in globs.nodes:
        if node.config_generated is False and len(node.inputs) > 1 and node.type > 2:
            unconfiged.append(node.id)
            for row in globs.config_pattern:
                if node.id in row:
                    pass#print node.id, row
            
            
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
    
    # second section. write bit_pattern to file.
    
    # hex file line format:
    #:04001c00218000003f
    #':'
    #'04'       config data size in bytes
    #'001c'     current address
    #'00'       record type (00:data, 01:EOS)
    #'21800000' configuration data
    #'3f'       checksum: (256 - (sum_of_bytes % 256))%256
    
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
    
    bytes_per_row = globs.params.config_width/8
    # write number of virtual inputs to file before bitstream
    #global IOs
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
    for row in bit_pattern:
        for i in range(lut_len):
            string = ''
            #write lut configuration in string?
            for entry in row:
                
                if len(entry) is lut_len:
                    if str(entry[i]) not in ['0','1']:
                        print 'error in bits', entry[i]
                    string = string + str(entry[i])
                elif len(entry) is 0:
                    string = string + '0'
                else:
                    string = string + '0'
                    print 'row length is', len(entry), lut_len, entry
            while len(string) < globs.params.config_width:
                string = string +'0'
            #print string
            
            checksum = 0
            line = ''
            
            #write the config size field
            line = line + hex_n(bytes_per_row,2) #number of bytes
            checksum = checksum + bytes_per_row
            
            #write the adress field
            line = line + hex_n(current_addr, globs.params.config_addr_width/4) #number of bytes
            line = line + '00' #record type (data)
            #increment the adress
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
