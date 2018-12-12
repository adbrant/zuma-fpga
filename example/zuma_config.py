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

#use vpr 7
params.vpr7 = True
#close network support
params.UseClos = False
#Should the parser build large permutation around all IO to fix their position in the fpga_input/fpga_output arrays?
params.orderedIO = True

#if you want to dump the node graph and mapped node graph in a readable format.
#EXPERIMENTAL:If graphviz is turned on there is also a graphical dump of the node graph.
#WARNING:graphviz could freeze the build process if the graph is too big.
params.dumpNodeGraph = False
params.graphviz = False


#activate the timing analysis. See ../TIMING README
params.sdf = False
#path of the two sdf files needed for timing analysis. see ../TIMING README
params.sdfFileName = "../final_no_buffer.sdf"
params.sdfFlipflopFileName = "../final_with_buffer.sdf"
#time scale of your timing information. here its ps
params.timeScale = 1.0/1000000000000
params.timeFormat = "ps"

#used for the timing analysis.
#The prefix of the components which is the path of your zuma instance 
#in the sdf file. 
#E.g the component zuma_top/zuma_i is translated to zuma_top_zuma_i_ in the sdf file.
params.instancePrefix = "zuma_top_zuma_i_"