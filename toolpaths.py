import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

vtrDir = dir_path + '/external/vtr'
#optinal yosys dir: used for the verifivation of the generated verilog ZUMA Overlay
#if params.verifyOverlay = True is set in the zuma_config
yosysDir = dir_path + '/external/yosys'
