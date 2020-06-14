#	ZUMA Open FPGA Overlay
#	Configuration File
from structs import *
#ZUMA Architecture Configuration
params = Arch()

#Width of the configuration port and addresses (in bits)
params.config_width = 32
params.config_addr_width = 32
#Cluster inputs
params.I = 28
#LUTs per cluster
params.N = 8
#LUT Size
params.K = 6
#Routing Channel Length
params.L = 2
#Routing Channel Width
params.W = 104
#ArrayDimensions
params.X = 2
params.Y = 2
#Cluster input and output flexibilities
params.fc_in = 6
params.fc_in_type = 'abs'
params.fc_out = 10
params.fc_out_type = 'abs'

#choose a vpr version. 6,7,8 is supported
params.vprVersion = 8

#close network support
params.UseClos = False
#Should the parser build large permutation around all IO to fix their position in the fpga_input/fpga_output arrays?
params.orderedIO = True

#check the equivalence of the generated overlay with the user circuit
#need a path to yosys in the toolpath.py
#WARNING: is only supported for vpr version 8
params.verifyOverlay = False
params.useClock = False

#if you want to use a packed overlay for verification and build
params.packedOverlay = False

#for each nodegraph node we can enable if we use a module instation instead
#of printing just the mapped nodes in the verilog file
params.hierarchyNode = False
params.hierarchyInterConnect = False
params.hierarchyBle = False
params.hierarchyCluster = True

#a generation of a black box verilog file where the clusters are not specified.
#Used to reorganize things with rapidWrite
params.blackBox = False
params.blackBoxBle = True
params.blackBoxCluster = False
params.blackBoxInterconnect = True

#if you want to dump the node graph and mapped node graph in a readable format.
#EXPERIMENTAL:If graphviz is turned on there is also a graphical dump of the node graph.
#WARNING:graphviz could freeze the build process if the graph is too big.
params.dumpNodeGraph = True
params.graphviz = False

#provide a list of unconfigured nodes with their verilog names
params.dumpUnconfiguredNodes = False



#activate the timing analysis. See ../TIMING README
params.sdf = True
#path of the two sdf files needed for timing analysis. see ../TIMING README
#the second one sdfFlipflopFileName is only needed when ise is used for the sdf export
#but not vivado
params.sdfFileName = "../../../example/adder.sdf"
params.sdfFlipflopFileName = "../final_with_buffer.sdf"
#time scale of your timing information. here its ps
params.timeScale = 1.0/1000000000000
params.timeFormat = "ps"

#tell the parser which tool you used to export the sdf.
#possible is "ise" or "vivado"
params.sdfUsedTool = "vivado"

#We only want to extract some specific cells of the sdf file add them to this list
#This prevent the SDF parser to label wrong cells as lut or flipflops
params.knownCellTypes = ['FDRE','FDCE','FDSE','RAMD64E','X_RAMD64_ADV','X_FF']


#when you use vivado this is the celltype name where the interconnections
#are located. We extract the interconnection delays and add them as port delays
params.sdfInterconnectCellType = "zuma_wrapper"

#used for the timing analysis.
#The prefix of the components which is the path of your zuma instance
#in the sdf file.
#E.g the component zuma_top/zuma_i is translated to zuma_top_zuma_i_ in the sdf file.
params.instancePrefix = "XUM/"

#signals if the timing of the ordered layer should be used for the critical path calculation
# this makes only sense when params.orderedIO is turned True
params.skipOrderedLayerTiming = True
params.skipOuterRoutingTiming = False
params.skipInnerRoutingTiming = False

#use vpr8 in a second run to place and route in vpr8 with the timing from the sdf file
#back annotated to the vpr files
params.vprAnnotation = True
params.setupTime = "4e-12"
params.holdTime = "2.0e-9"

#to have a finder control of the timing annotation:
params.annotateOuterRouting = True
params.annotateInnerRouting = True
