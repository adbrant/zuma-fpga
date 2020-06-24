from structs import *
from BuildBitstream import build_lut_contents
import globs

def convertReverseLutContent(contentLine):

    result = []

    for bit in contentLine:
        if bit == '1':
            result.append(1)
        else:
            result.append(0)
    return result

#get a new lut content for a given bitstream
def bistreamToLutContent(bitstream,node):

    content = []

    #idea: every lut has K input nodes.
    #we have the bitstream which we can access the output bit
    #by bitstream[ input pattern = 0011000 ].
    #we build the lut content by increasing the line number 000000, 000001 , 000010 ,...
    #for the used inputs and get the bitstream index by using the line number.
    #the ouput bit of the bistream is than used for the ouput of the content line

    #get the number of virtual used pins.
    numVirtualPins = globs.params.K

    #else build the lut content
    for contentLineNum in range(pow(2,numVirtualPins)):

        #when the host lut size is bigger than the virtual lut size
        #the lower inputs are set to a static 0 input in the overlay.
        #therefore we have to shift the adress, because the bitstream
        #was generate for a host_size bit adress.
        if globs.host_size > numVirtualPins:
            index = (contentLineNum << globs.host_size - numVirtualPins)
        elif globs.host_size == numVirtualPins:
            index = contentLineNum
        else:
            print "ERROR: your host lut size is smaller than your virtual lut size"
            sys.exit(1)

        #get the bit ouput
        bit = bitstream[index]

        #get a binary string version of the content line number.
        strBinContenLineNum = format(contentLineNum,'0' + str(numVirtualPins) + 'b')

        #finally add a content line. only outputs with a 1 are added
        if bit == 1:
            content.append(strBinContenLineNum + ' ' + str(bit))

    #luts which used all inputs but only print 0 get a special treatment:
    if len(content) == 0:
        content.append('-'*numVirtualPins + ' ' + '0')

    return content

##Writes the zuma_out.blif file to make equivalent checks.
#Therefore we translate the node graph to a blif file.
#the names of the nodes are the ids combined with brackets,
#except the outputs, which have there original blif names
def output_blif(filename):

    # a list of node ids to track the nodes
    # we wrote to the file.
    writtenList = []
    #a list of node ids to track the inputs of the written nodes
    #in the writtenList list.
    #Needed for blif closure in a later step, where we find nodes,
    #which were not written to the blif file but needed as an input
    referencedList = []

    #write BLIF of zuma design for verification
    f = open(filename, 'w')
    f.write('.model top\n')

    #write the blif input and output names to the file
    string = '.inputs '
    for i in globs.inputs:
        string = string + str(i) + ' '
    string = string + '\n'
    f.write(string)


    string = '.outputs '
    for i in globs.outputs:
        string = string + str(i) + ' '
    string = string + '\n'
    f.write(string)

    #make a connection (by a passthrough)
    #between the node id and output/input name.
    #the nodes will be later read again,
    #and at that point the function will build passthrough's
    #between the source and the node id.
    #so finally we then have e.g. the path :
    #output.source->output.id->output.name
    if globs.params.orderedIO:

        #assign correct nodes to IOs
        for id in globs.orderedOutputs:
            output = globs.nodes[id]
            if len(output.name) > 0:
                print 'FPGA output', output.name
                f.write(' .names ')

                f.write('[' + str(output.id) + '] ' + \
                              str(output.name) + ' ' + '\n')
                f.write('1 1\n')
                referencedList.append(output.id)


        for id in globs.orderedInputs:
            input = globs.nodes[id]
            if len(input.name) > 0:
                print 'FPGA input', input.name

                f.write(' .names ')

                f.write('' + str(input.name) + ' ' + \
                       '[' + str(input.id) + '] ' + '\n')
                f.write('1 1\n')
                writtenList.append(input.id)

    else:

        #assign correct nodes to IOs
        for key in globs.IOs:
            IO = globs.IOs[key]
            for output in globs.IOs[key].outputs:
                if len(output.net) > 0 and output.net != 'open':
                    print 'FPGA output', output.net

                    f.write(' .names ')

                    f.write('[' + str(output.id) + '] '  +\
                                  str(output.net) + ' ' + '\n')
                    f.write('1 1\n')
                    referencedList.append(output.id)


            for input in globs.IOs[key].inputs:
                if len(input.net) > 0 and input.net != 'open':
                    print input.net

                    f.write(' .names ')

                    f.write('' + str(input.net) + ' ' + \
                           '[' + str(input.id) + '] ' + '\n')
                    f.write('1 1\n')
                    writtenList.append(input.id)

    #now walk though the node graph and print the rest.
    for node in globs.nodes:
        #the node is an elut. check if it has a valid configuration and print it
        if node.eLUT:
            if node.LUT: #has a configuration
                cl = globs.clusters[node.location]

                #get the ble index of the elut
                index = cl.getBleIndexOnId(node.id)

                f.write(' .names ')
                #go through the input node id list and write these
                #inputs to the file.
                #also place this inputs to the referencedList for tracking
                for i in node.inputs:
                    f.write('[' + str(i) + '] ')
                    referencedList.append(i)

                #write the output id which is the id of this lut
                #and add its id to the written list

                f.write('[' + str(node.id) + ']\n')
                writtenList.append(node.id)


                #build and write the configuration to the blif file
                if globs.bit_to_blif:
                    bits = convertReverseLutContent(node.LUT.bits[0]) #list of bit list
                    if globs.debug:
                        print 'reverse lut ', str(node.id) , ' content: ', str(bits)
                else:
                    bits = build_lut_contents(globs.host_size, node.LUT, cl, index)
                    if globs.debug:
                        print 'normal lut ', str(node.id) , ' content: ' ,  str(bits)

                #print "host size:", globs.host_size
                content = bistreamToLutContent(bits,node)
                for line in content:
                    f.write(str(line)+ '\n')

            #doesnt have a valid configuration. skip it
            else:
                pass

            continue

        #skip unconnected muxes. only muxes have a valid source attribut.
        if node.source < 0:
            continue

        #this is a mux of a ble
        if node.ffmux:
            #above statement ensures that this node is driven
            cl = globs.clusters[node.location]
            elutnode = globs.nodes[node.source]
            #index of the lut in the clusters LUTs list.
            index = -1

            #only include FFs after configured LUTs
            #This works because the lut can be:
            # 1) a normal lut with a configuration
            #    given in the blif file
            # 2) a passtrough lut for the flipflop,
            #    if only the flipflop is used on that ble.
            #    the name of the passtrough lut is than
            #    the name of the latch
            if elutnode.LUT:

                #get the ble index of the lut.
                index = cl.getBleIndexOnId(elutnode.id)

                #The ble uses its flipflop
                #build a latch with the lut as an input and connect its output
                if elutnode.LUT.useFF:

                    f.write('.latch ')
                    f.write('[' + str(node.source) + '] ')
                    #f.write('[' + str(cl.outputs[index].id) + ']'+ \
                    f.write('[' + str(node.id) + ']'+ \
                            '  re top^clock 0\n')
                #no config.
                #only the lut is used. build a passtrough for that lut
                else:

                    f.write(' .names ')
                    f.write('[' + str(node.source) + '] ')
                    #f.write('[' + str(cl.outputs[index].id) + '] \n')
                    f.write('[' + str(node.id) + '] \n')
                    f.write('1 1\n')
                #writtenList.append(cl.outputs[index].id)
                writtenList.append(node.id)
                referencedList.append(node.source)

            continue

        #make simple passthrough logic
        f.write(' .names ')

        f.write('[' + str(node.source) + '] ' + \
                '[' + str(node.id) + '] ' + '\n')
        f.write('1 1\n')
        writtenList.append(node.id)
        referencedList.append(node.source)


    #This should now be automatically fixed by having the correct source on ffmux nodes
    #for key in globs.clusters:
    #    cl = globs.clusters[key]
    #    for n in range(globs.params.N):
    #        lut_id = cl.LUT_FFMUX_nodes[n]
    #        opin_id = cl.outputs[n].id
    #
    #        f.write(' .names ')
    #        f.write('[' + str(opin_id) + '] ' + '[' + str(lut_id) + '] ' + '\n')
    #        f.write('1 1\n')
    #        writtenList.append(lut_id)
    #        referencedList.append(opin_id)

    #it could be that the same node id can be in the referenced list
    #twice or more, because two different nodes has the same node as input

    # Include undriven pins for blif closure
    for id in referencedList:
        if id not in writtenList:

            f.write(' .names [' + str(id) + '] \n\n')
            writtenList.append(id)

    f.write('.end\n\n')
