#	ZUMA Open FPGA Overlay
#	Configuration File
from structs import *
#ZUMA Architecture Configuration
params = Arch()

#Width of the configuration port
params.config_width = 32
#Cluster inputs
params.I = 16
#LUTs per cluster
params.N = 6
#LUT Size
params.K = 5
#outing Channel Length
params.L = 2
#Routing Channel Width
params.W = 52
#ArrayDimensions
params.X = 2
params.Y = 2
#Cluster input and output flexibilities
params.fc_in = 6
params.fc_in_type = 'abs'
params.fc_out = 10
params.fc_out_type = 'abs'

def get_params():
	global params
	return params