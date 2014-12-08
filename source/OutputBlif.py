from structs import *
from BuildBitstream import build_lut_contents
import globs

#writes the zuma_out.blif file to make equivalent checks.
#Therfore we translate the node graph to a blif file.
#the names of the nodes are the ids combined with brackets,
#except the output, which have there original blif names
def output_blif(filename):

    # a list of node ids where we track the nodes
    #we wrote to the file
    writtenList = []
    #a list of node ids to track the inputs of the written nodes
    #in the writtenList list
    #needed for blif closure in a later step, where we find nodes,
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

    #make a connection (by a passthorugh)
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
                if node.LUT.useFF:
                    if node.LUT.output in cl.LUTs:
                        index = cl.LUTs.index(node.LUT.output)
                    #TODO: Is reverselatch depricated?
                    else:
                        index = cl.LUTs.index(globs.reverselatches[node.LUT.output])
                else:
                    index = cl.LUTs.index(node.LUT.output)

                f.write(' .names ')
                #go through the input node id list and write these
                #inputs to the file.
                #also place this inputs to the referencedList for tracking
                for i in node.inputs:
                    f.write('[' + str(i) + '] ')
                    referencedList.append(i)

                #write the output id. the id of this lut
                #and place its id to the written list
                f.write('[' + str(cl.LUT_nodes[index]) + ']\n')
                writtenList.append(cl.LUT_nodes[index])

                #build and write the configurtation to the blif file
                bits = build_lut_contents(globs.host_size, node.LUT, cl, index)

                at_least_one = False
                for i in range(len(bits)):
                    if bits[i]:
                        for j in range(globs.params.K):
                            f.write (str(i>>(globs.params.K-j-1) & 1))
                        f.write(' ' +  str(bits[i]) + '\n')
                        at_least_one = True
                if not at_least_one:
                    for j in range(globs.params.K):
                        f.write ('-')
                    f.write(' 0\n')

            #doesnt have a valid configuration. skip it
            else:
                pass

            #keep track that this node was written?
            #TODO: depricated?
            #seems to be a copy paster error of another function?
            node.config_generated =     True
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
            if elutnode.LUT: #only include FFs after configured LUTs
                #The mux has has a config.
                #That means that this ble uses its flipflop
                #build a latch with the lut as an input and connect its output
                if node.LUT:
                    if elutnode.LUT.output in cl.LUTs:
                        index = cl.LUTs.index(elutnode.LUT.output)
                    #TODO: is reverselatch depricated?
                    else:
                        index = cl.LUTs.index(globs.reverselatches[elutnode.LUT.output])
                    f.write('.latch ')
                    f.write('[' + str(node.source) + '] ')
                    f.write('[' + str(cl.outputs[index].id) + ']'+ \
                            '  re top^clock 0\n')
                #no config.
                #only the lut is used. build a passtrough for that lut
                else:
                    
                    index = cl.LUTs.index(elutnode.LUT.output)
                    f.write(' .names ')
                    f.write('[' + str(node.source) + '] ')
                    f.write('[' + str(cl.outputs[index].id) + '] \n')
                    f.write('1 1\n')
                writtenList.append(cl.outputs[index].id)
                referencedList.append(node.source)

            continue

        #make simple passthrough logic
        f.write(' .names ')

        f.write('[' + str(node.source) + '] ' + \
                '[' + str(node.id) + '] ' + '\n')
        f.write('1 1\n')
        writtenList.append(node.id)
        referencedList.append(node.source)


    for key in globs.clusters:
        cl = globs.clusters[key]
        for n in range(globs.params.N):
            lut_id = cl.LUT_FFMUX_nodes[n]
            opin_id = cl.outputs[n].id

            f.write(' .names ')
            f.write('[' + str(opin_id) + '] ' + '[' + str(lut_id) + '] ' + '\n')
            f.write('1 1\n')
            writtenList.append(lut_id)
            referencedList.append(opin_id)

    #it could be that the same node id can be in the referenced list
    #twice or more, because two different nodes has the same node as input

    # Include undriven pins for blif closure
    for id in referencedList:
        if id not in writtenList:

            f.write(' .names [' + str(id) + '] \n\n')
            writtenList.append(id)

    f.write('.end\n\n')
