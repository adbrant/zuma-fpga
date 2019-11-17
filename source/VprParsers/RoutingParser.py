# use this if you want to include modules from a subforder.
# used for the unit tests to import the globs module
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"../")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import structs
import globs
import re

## get the track number in the routing file in a CHANX/Y line
def getchan(line):

    about = line.split()
    if globs.params.vpr8:
        return int(about[-3])
    else:
        return int(about[-1])


##parse the routing file
#@return list of Net objects
def parseRouting(filename ):

    fh = open(filename,"r")

    #for vpr8 we have to skip the first line
    if globs.params.vpr8:
        fh.readline()

    lines = fh.readlines()

    #the returned net list
    nets = []

    #size of the array. Not used now
    x = int(lines[0].split(' ')[2])+1
    y = int(lines[0].split(' ')[4])+1

    #maximum track number
    channels = 0

    #find the maximum track number
    for line in lines:

        if line.find("CHAN") > -1:
            about = line.split()
            #get the track number
            c1 = getchan(line)
            #get the max tack number
            if c1 + 1 > channels:
                channels = c1 + 1

    #current parsed net
    routing_net = None

    #in vpr7 there are two items: node and node number at the start of every line
    if globs.params.vpr7 or globs.params.vpr8:
        offset = 1
    else:
        offset = 0

    #now let us parse the routing file and add the read nets
    #to the global net dictionary.
    #NOTE: we skip the sources and sink nodes
    #and use the opins and ipin nodes instead as a start and a endpoint of the net
    #TODO: name them opin and ipin in the trace.type
    for i,line in enumerate(lines):

        #extract all numbers of the curretn line. used by the following cases
        nums = re.findall(r'\d+', line)
        nums = [int(i) for i in nums ]

        if line.find("Net") > -1:
            #get the name of the net. same name as in the netlist file
            name = line.split('(')[1].split(')')[0]

            #init the net and append it to the global net dict.
            routing_net = structs.Net()
            routing_net.name = name
            nets.append(routing_net)

        if line.find("OPIN") > -1:

            #assign the location
            x1 = nums[0+offset]
            y1 = nums[1+offset]

            #get the pad number
            pin = nums[2+offset]

            #pad number not assigned yet
            if len(routing_net.source) is 0:
                routing_net.source = [x1,y1,pin]

            #append it to the trace list
            routing_net.add_source(x1,y1,pin)

        if line.find("IPIN") > -1:

            #assign the location
            x1 = nums[0+offset]
            y1 = nums[1+offset]

            #get the pad number
            pin = nums[2+offset]

            #assign the location and pad number
            routing_net.sinks = [x1,y1,pin] # TODO:TW: Test if this is relevant
            #append it to the trace list
            routing_net.add_sink(x1,y1,pin)

        if line.find("CHANX") > -1:

            #assign the location
            x1 = nums[0+offset]
            y1 = nums[1+offset]
            x2 = -1
            y2 = -1
            #There are two possible descriptions:
            # 1) CHANX (2,0)  Track: 11
            # 2) CHANY (2,1) to (2,3)  Track: 21
            # check if its the second option
            if len(nums) >= (5+offset):
                x2 = nums[2+offset]
                y2 = nums[3+offset]

            #get the track number
            c1 = getchan(line)
            #append it to the trace list
            routing_net.add_section('X', x1,y1,x2,y2, c1)


        if line.find("CHANY") > -1:

            #assign the location
            x1 = nums[0+offset]
            y1 = nums[1+offset]
            x2 = -1
            y2 = -1
            #There are two possible descriptions:
            # 1) CHANX (2,0)  Track: 11
            # 2) CHANY (2,1) to (2,3)  Track: 21
            # check if its the second option
            if len(nums) >= (5+offset):
                x2 = nums[2+offset]
                y2 = nums[3+offset]

            #get the track number
            c1 = getchan(line)
            #append it to the trace list
            routing_net.add_section('Y', x1,y1,x2,y2, c1)

    return nets

#you should provide a zuma config in your source file for this test.
def simpleTest():

    globs.init()
    globs.load_params()

    nets = parseRouting('route.r.vpr7')

    for net in nets:
        print '\n ------ net ---------'
        print net.name
        print net.source
        print net.sinks
        for trace in net.trace:
            print '\n --- trace ---'
            print trace.type
            print trace.loc
            print trace.index

    #now vpr8
    print '\n----------now vpr8----------------\n'
    globs.params.vpr8 = True

    nets = parseRouting('route.r.vpr8')

    for net in nets:
        print '\n ------ net ---------'
        print net.name
        print net.source
        print net.sinks
        for trace in net.trace:
            print '\n --- trace ---'
            print trace.type
            print trace.loc
            print trace.index


def main():
    simpleTest()

if __name__ == '__main__':
    main()
