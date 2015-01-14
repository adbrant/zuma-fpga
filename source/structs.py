#	ZUMA Open FPGA Overlay
#	Alex Brant
#	Email: alex.d.brant@gmail.com
#	2012
#	CAD Data Structure Definitions

import sys

## describe a node of the node graph
class Node():
    def __init__(self):
        
        ##the id of the node.
        self.id = -1

        ## a node can have one of the following types (attribute type):
        ##  1 - 'SINK'
        ##  2 - 'SOURCE'
        ##  3 - 'OPIN'
        ##  4 - 'IPIN'
        ##  5 - 'CHANX'
        ##  6 - 'CHANY'
        ##  7 - cluster input crossbar, a routing mux.
        ##  8 - an eLUT
        ##  9 - a mux of an ble with two inputs, the LUT and the flipflop, called ffmux
        ##  10 - ordered IO mux

        ## type 2 and 3 are translated to a LUTRAM MUX.
        self.type = -1
        ##list of the child node ids (have this node as an input).
        ##set in load_graph
        self.edges = []
        ##index in the clusters array
        self.location = []
        ##list of parent node ids, which
        ##this node get its inputs from. set in load_graph
        self.inputs = []
        ##this is the final node id, where
        ##to get its input from.
        ##This set the final routing.
        ##this attribute is only used in muxes
        self.source = -1
        ##is the node an eLUT.
        ##not activate for routing muxes.
        self.eLUT = False
        ##is the node an MUX in a ble
        self.ffmux = False
        ##reference to a LUT class object
        self.LUT = 0
        self.config_generated = False
        #This is the pad position, pin position or track number
        #depending its a driver of a pin on an I/O block, cluster
        #or a driver of a switchbox.
        #same attribute as the corresponding driver attribute.
        self.index = -1

        #TODO: missing attributes: dir
        
        #The blif name of the global input/output, e.g. top^out~0
        #This attribute is only set for SINK/SOURCE nodes 
        #which represent the global permutation muxes.
        #assigned in read_blif
        self.name = ''

class Arch():
    def __init__(self):
        self.I = -1
        self.K = -1
        self.N = -1
        self.UseClos = 0

##Describes a driver of path in a net.
##The paths of this net are also represented in the node graph.
##Need for a connection between pins of an I/O block or cluster,
##or a switchblock and a node of the path in the node graph.
class Driver:
    def __init__(self, id, index=0,dir=0):
        #id of the node
        self.id = id
        #direction only used when its a driver for switchboxes
        self.dir = dir
        #This is the pad position, pin position or track number
        #depending its a driver of a pin on an I/O block, cluster
        #or a driver of a switchbox.
        self.index = index
        #the name of the net
        self.net = 'open'

        #TODO:source attribute ist missing

#represent an internal representation of a latch read in the blif file.
class latch:
    def __init__(self):
        ##blif name of the output.
        self.output = ''
        ##blif names of the input.
        ##this can be seen as the name of the latch.
        self.input = ''

#represent an internal representation of a lut read in the blif file.
class LUT:
    def __init__(self):
        ##input width of the Lut
        self.size = 6
        ##blif name of the output.
        ##this can be seen as the name of the lut.
        self.output = ''
        ##blif names of the inputs of this lut.
        self.inputs = []
        ##blif configuration of the lut in the
        ##PLA blif format (k-input,output).
        ##build in buil_lut_contents()
        self.contents = ''
        ##indicates that the lut uses the Flipflop
        self.useFF = False

##a logic cluster element which consists of an interconnection block,
## implemented with routing muxes, and ble's,
## which consists of eLUTs, and FFMuxes.
class Cluster:
    def __init__(self):
        self.size = 8
        ## list of driver classes
        self.outputs = []
        ## list of driver classes
        self.inputs = []
        ## list of input netlist/net names e.g. top^in~4 open open.
        ## see read_netlist.
        ## Are ordered in a incrising instance number, because
        ## the ble's appear in a incrising instance order in
        ## the netlist file, where they are parsed from.
        ## Also used in build_lut_contents
        self.input_nets = []
        ## list of the netlist names of (the outputs of the) LUTs
        ## in this cluster
        ## (seems not to be blif names. see read_netlist)
        ## list of all ble instance names in a cluster netlist block
        ## Are ordered in a incrising instance number
        ## because of their appearing in the netlist
        ## also used in build_lut_contents
        ## for vpr7 support:
        ## in vpr6 the empty luts seems to be at the end of the cluster.
        ## now there are interlevaed so we have to paste 'open' keywords
        ## for empty LUTs to get names for the instance number
        ## of the LUT_input_nets.
        ## TODO: Maybe build a structure
        ## where these names are integrated.
        self.LUTs = []
        ## MxK array of the input tuples for ble's in a cluster :
        ## first dimension M: ble index.
        ## second dimension: K, pin position on this ble.
        ## input tuples have the structure : (mode, number)
        ## mode can be: 
        ## 1) input, for a input of the cluster.
        ## number then describe the input pin number
        ## 2) ble, for the input of a other ble of this cluster
        ## number than describe the instance number of the ble.
        ## 3) open if its open. number is -1
        ##
        ## tuples have the same structure as 
        ## NetlistParser.NetlistBle.inputs .
        ## see read_netlist and NetlistParser
        self.LUT_input_nets = []
        ##the same identifier as CLB.
        ##TODO: delete this attribute
        ##and change the read_netlist function.
        self.name = ''
        #name of the block in the netlist file
        self.CLB = ''
        ##NxK array of node ids of the interconnection block.
        ##first dimension is the ble index.
        ##second dimension is the pin position on this ble.
        ##represent a input node (inode) which has input edges
        ##to every ble in this cluster.
        self.LUT_input_nodes = []
        ##list of the possible ids of ble muxes nodes in this cluster.
        ##see build_global_routing_verilog
        self.LUT_FFMUX_nodes = []
        ##list of the eLUT nodes ids in this cluster.
        ##see build_global_routing_verilog
        ##also used in output_blif
        self.LUT_nodes = []

    def do_local_interconnect(self):
        global LUTs

    #get the blif/netlist name of the lut on the ble with index bleIndex
    #return the blif name or 'open' when the ble has no lut
    ##IMPORTANT: This function use information of the netlist,
    ##so it can be only applied after the call of readNetlist().
    def getLutName(self,bleIndex):
        try:
            lutName = self.LUTs[bleIndex]
        except IndexError:
            print 'ERROR: Index Error in getLutName:'
            print 'try to get lut name on ble index' , bleIndex, \
                'in cluster ', self.CLB
            print  'Availible lut names are ', \
                self.LUTs
            sys.exit(0)
        return lutName

    ##get the blif/netlist name
    ##which is connected as an input on the cluster
    ##pinPosition is the pin Position of the cluster Input.
    ##Note: this is not the interconnect input
    ##where you get this cluster inputs, and also the lut feeback
    ##IMPORTANT: This function use information of the netlist,
    ##so it can be only applied after the call of readNetlist().
    def getNameOnClusterInput(self,pinPosition):
        try:
            name = self.input_nets[pinPosition]
        except IndexError:
            print 'ERROR: Index Error in getNameOnClusterInput:'
            print 'try to get name connected to pin' , \
                pinPosition, \
                'in cluster ', self.CLB
            print  'Availible names are ', \
                self.input_nets
            sys.exit(0)
        return name

    ##get the inode id of a inode which is connected as an input
    #to the ble bleIndex and pin pinPosition
    def getInodeId(self,bleIndex,pinPosition):
        try:
            id = self.LUT_input_nodes[bleIndex][pinPosition]
        except IndexError:
            print 'ERROR: Index Error in getInodeId:'
            print 'try to get inode id connected to ble' , \
                bleIndex, \
                'on pin ' , pinPosition ,\
                'in cluster ', self.CLB
            print  'Availible inodes are ', \
                self.LUT_input_nodes
            sys.exit(0)
        return id

    #get the id of a ffmux node of a ble.
    def getFFMuxNodeId(self,bleIndex):
        try:
            id = self.LUT_FFMUX_nodes[bleIndex]
        except IndexError:
            print 'ERROR: Index Error in getFFMuxNode:'
            print 'try to get ffmux node id connected to ble' , \
                bleIndex, \
                'in cluster ', self.CLB
            print  'Availible ffmux node are ', \
                self.LUT_FFMUX_nodes
            sys.exit(0)
        return id

#An I/O block
class IO:
    def __init__(self):
        #list of driver instances.
        #These drivers drive the IPINs nodes in the node graph
        #build up in load_graph
        self.outputs = []
        #list of driver instances.
        #These drivers drive the OPINs nodes in the node graph
        #build up in load_graph
        self.inputs = []
        self.name = ''
        self.order = -1

#a trace in a net. see net class
class Trace:
    def __init__(self, type = '', location = (), index = -1):
        #type can have the follwing values:
        #'SINK' , 'SOURCE' , 'X', 'Y'
        self.type = type
        #the location of this trace. format: tuple (x,y)
        self.loc = location
        #the pad position, pin number or a tracknumber,
        #depending if this is an I/O trace,
        #a trace of a pin on a cluster or a trace of a channel
        self.index = index


##An internal representation for the nets of the routing file, see read_routing.
##These nets describe routes for the global routing.
##every net consist of a list of traces,
##start with a source and ends with a sink.
class Net:
    def __init__(self):
        ##value is a list of the format:
        ##[location coord x, location coord y,pad number].
        ##used for IPINs
        self.source = []
        #value is a list of the format:
        ##[location coord x, location coord y,pad number].
        ##used for OPINs
        self.sinks = []
        #list of assigned Traces instances. see add_ member functions
        self.trace = []
        #the name of the net.
        #same name as in the netlist and in the routing file
        #is taken from the routing file.
        self.name = ''

    #add a trace with the same values as in the sink attribute.
    #used for OPINs descriptions in the routing file
    #pin_num can be a pad number, for I/O pins
    #or the pin position for pins on a cluster
    def add_sink(self, x,y,pin_num):
        self.trace.append (Trace( 'SINK', (x,y),pin_num))

    #add a trace with the same values as in the source attribute.
    #used for IPINs descriptions in the routing file
    #pin_num can be a pad number, for I/O pins
    #or the pin position for pins on a cluster
    def add_source(self, x,y,pin_num):
        self.trace.append(Trace( 'SOURCE', (x,y),pin_num)   )

    #add a trace for a CHAN description in the routing file.
    #There are two possible descriptions:
        # 1) CHANX (2,0)  Track: 11
        # 2) CHANY (2,1) to (2,3)  Track: 21
    # dir is the direction: 'X' or 'Y',
    # x1,x2 is the first location, x2,y2 the second.
    # for description type 1) the second location has the values -1,-1
    # channel is the track number
    def add_section(self, dir, x1,y1,x2,y2, channel):
        self.trace.append(Trace(dir, (x1,y1,x2,y2), channel))


class SBox:
    def __init__(self):
        #the list of diver instances.
        #connection to mux nodes in the node graph
        self.driversx = []
        self.driversy = []
