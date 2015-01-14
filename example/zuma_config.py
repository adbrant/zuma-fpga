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
#outing Channel Length
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
params.vpr7 = False
#close network support
params.UseClos = False
#Should the parser build large permutation around all IO to fix their position in the fpga_input/fpga_output arrays?
params.orderedIO = True

