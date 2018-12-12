from structs import *
import zuma_config

## init the global variables.
def init():

    #GLOBAL ROUTING STRUCTURES
    global chanx,chany,opin,ipin
    chanx = []
    chany = []
    opin = []
    ipin = []

    global clock,reset,debug,bit_to_blif
    clock = False
    reset = False
    debug = False
    bit_to_blif = False

    global nets,cluster_nodes,lastnetmapping
    global nodes
    ## a dictionary of net classes. key is the net name.
    ## build up in read_routing.
    ## the nets reflect the data of the routing file.
    ## see net class in struct.py
    nets = {}
    ## the node graph.
    ## index is the node id.
    nodes = []

    ## The LUT can describe a passthrough from a fpga input
    ## to a fpga output.
    ## We save the mapping (input blif name, list of output blif names)
    ## to find later in read_routing the corresponding sink node,
    ## which has the output name in the name attribute
    ## This is possible because the net name to this sink
    ## is same as the blif fpga input name.
    lastnetmapping = {}

    global inputs,outputs,LUTs,latches
    ## list of blif names of the inputs. see read_blif
    inputs = []
    ## list of blif names of the outputs. see read_blif
    outputs = []
    ##A dictionary of LUT classes. key is the output blif name of the LUT.
    LUTs = {}
    ##A dictionary of latch classes. key is output blifname of the latch.
    ##set in read_blif
    latches = {}

    ## these params will be overwritten in zuma_config.py.
    global params
    
    #init the architecture
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
    ##a dictionary of IO instances. key is the location (x,y). see load_graph
    IOs = dict()
    ##ascending list of input node ids.
    ##contain SOURCE node ids. 
    ##set in load_graph
    orderedInputs = []
    ##ascending list of output node ids.
    ##contain SINK node ids
    ##set in load_graph
    orderedOutputs = []
    ##a dictionary of cluster objects.
    ##represent the virtual fpga. key is the location tuple (x,y)
    clusters = dict()
    ## a dictionary of Sbox objects. key is the location tuple
    switchbox = dict()
    ## describe the placement of nodes.
    ## A 2d list of node ids. first dimension are the stages.
    ## second dimension are the lutram indices of this stage.
    ## content will also be saved in config_pattern.txt
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

    global connectionMatrix
    ##adjacency matrix filled with delay information used for timing analysis
    connectionMatrix = []

    ##technology mapped node graph
    global technologyMappedNodes
    technologyMappedNodes = TechnologyNodeGraph()


##TODO:build a graph class
def addNode(node):
    node.id = len(nodes)
    nodes.append(node)

def load_params():
    global params
    params = zuma_config.params
