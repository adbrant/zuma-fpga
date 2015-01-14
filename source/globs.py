from structs import *
import zuma_config

def init():

    #GLOBAL ROUTING STRUCTURES
    global chanx,chany,opin,ipin
    chanx = []
    chany = []
    opin = []
    ipin = []

    global nets,cluster_nodes,lastnetmapping
    global nodes
    ## a dictonary of net classes. key is the net name.
    ##build up in read_routing.
    ##the nets reflect the data of the routing file.
    ##see net class in struct.py
    nets = {}
    ##the node graph.
    ##index is the node id.
    nodes = []

    # The LUT can describe a passtrough from a fpga input
    # to a fpga output.
    # We save the mapping (input blif name, list of output blif names)
    # to find later in read_routing the corresponding sink node,
    # which has the output name in the name attribute
    # This is possible because the net name to this sink
    # is same as the blif fpga input name.
    lastnetmapping = {}

    global inputs,outputs,LUTs,latches,reverselatches
    ## list of blif names of the inputs. see read_blif
    inputs = []
    ## list of blif names of the outputs. see read_blif
    outputs = []
    ##A dictornary of LUT classes. key is the output blif name of the LUT.
    LUTs = {}
    ##A dictonary of latch classes. key is output blifname of the latch.
    ##set in read_blif
    latches = {}
    ##A dictonary of output blif names of latches.
    ##key is the input blifname of that latch,
    ##which is the output name of the lut.
    ##create the mapping lut -> latch
    ##set in read_blif
    reverselatches = {}

    global params
    ## these params will be overwritten in zuma_config.py.
    params = Arch()
    #Cluster inputs
    params.I = 16
    #LUTs per cluster
    params.N = 6
    #LUT Size
    params.K = 5
    #Width of the configuration port(in bits)
    params.config_width = 32

    global IOs,orderedInputs,orderedOutputs,clusters,switchbox,config_pattern
    #a dictornary of IO instances. key is the location (x,y). see load_graph
    IOs = dict()
    #ascending list of input node ids.
    #contain SOURCE node ids. 
    #set in load_graph
    orderedInputs = []
    #ascending list of output node ids.
    #contain SINK node ids
    #set in load_graph
    orderedOutputs = []
    #a dictonary of cluster objects.
    ##represent the virtual fpga. key is the location tuple (x,y)
    clusters = dict()
    # a dict of Sbox objetcs. key is the location tuple
    switchbox = dict()
    config_pattern = []

    global host_size,lut_contents,placement,clusterx,clustery,debug
    ##the lut size of a host lut,
    ##which is the physical input size of a lut on the board
    host_size = 6
    lut_contents = []
    placement = []
    #the maximal location coord.
    clusterx = 0
    clustery = 0
    debug = False

    global use_vpr7_syntax
    #VPR 7 uses different route.r syntax than VPR 6
    use_vpr7_syntax = False
##TODO:build a graph class
def addNode(node):
    node.id = len(nodes)
    nodes.append(node)

def load_params():
    global params
    params = zuma_config.params
