#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	Preparation of input files for VTR tools


from zuma_config import *
def make_files(directory, template_directory):
	print directory
	filelist = ['ARCH.xml', 'abccommands', 'vpr.sh']
	
	params = get_params()
	
	rep = []
	rep.append(['ZUMA_ARRAY_WIDTH',str(params.X)])
	rep.append(['ZUMA_ARRAY_HEIGHT',str(params.Y)])
	rep.append(['ZUMA_FCIN_TYPE',str(params.fc_in_type)])
	rep.append(['ZUMA_FCOUT_TYPE',str(params.fc_out_type)])
	rep.append(['ZUMA_FCIN_VAL',str(params.fc_in)])
	rep.append(['ZUMA_FCOUT_VAL',str(params.fc_out)])
	rep.append(['ZUMA_I',str(params.I)])
	rep.append(['ZUMA_N_m_1',str(params.N - 1)])
	rep.append(['ZUMA_K_m_1',str(params.K - 1)])
	rep.append(['ZUMA_N',str(params.N)])
	rep.append(['ZUMA_K',str(params.K)])	
	rep.append(['ZUMA_CHAN_W',str(params.W)])
	for file in filelist:
		o = open(directory  + '//' + file,"w") #open for write
		for line in open(template_directory + '//' + file):
			for pair in rep:
				line = line.replace(pair[0],pair[1])   
			o.write(line) 
		o.close()
		
import sys


make_files(sys.argv[1], sys.argv[2])