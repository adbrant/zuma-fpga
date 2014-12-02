from structs import *
#ZUMA Architecture Configuration
params = Arch()
params.I = 16
params.N = 6
params.K = 5
params.L = 2
params.W = 52
params.X = 25
params.Y = 25
params.config_width = 32
params.fc_in = 6
params.fc_in_type = 'abs'
params.fc_out = 10
params.fc_out_type = 'abs'

def get_params():
	global params
	return params