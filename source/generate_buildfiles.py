#	ZUMA Open FPGA Overlay
#	Alex Brant
#	Email: alex.d.brant@gmail.com
#	2012
#	Preparation of input files for VTR tools


import zuma_config
def make_files(directory, template_directory):
    print directory

    #use vpr6
    if (zuma_config.params.vpr8):
        filelist = ['ARCH_vpr8.xml', 'abccommands', 'vpr8.sh']
    #seems we want to use vpr7
    elif (zuma_config.params.vpr7):
        filelist = ['ARCH_vpr7.xml', 'abccommands', 'vpr.sh']
    else:
        filelist = ['ARCH.xml', 'abccommands', 'vpr.sh']

    rep = []
    if (zuma_config.params.vpr8):
        rep.append(['ZUMA_ARRAY_WIDTH',str(zuma_config.params.X+2)])
        rep.append(['ZUMA_ARRAY_HEIGHT',str(zuma_config.params.Y+2)])
    else:
        rep.append(['ZUMA_ARRAY_WIDTH',str(zuma_config.params.X)])
        rep.append(['ZUMA_ARRAY_HEIGHT',str(zuma_config.params.Y)])

    rep.append(['ZUMA_FCIN_TYPE',str(zuma_config.params.fc_in_type)])
    rep.append(['ZUMA_FCOUT_TYPE',str(zuma_config.params.fc_out_type)])
    rep.append(['ZUMA_FCIN_VAL',str(zuma_config.params.fc_in)])
    rep.append(['ZUMA_FCOUT_VAL',str(zuma_config.params.fc_out)])
    rep.append(['ZUMA_I',str(zuma_config.params.I)])
    rep.append(['ZUMA_N_m_1',str(zuma_config.params.N - 1)])
    rep.append(['ZUMA_K_m_1',str(zuma_config.params.K - 1)])
    rep.append(['ZUMA_N',str(zuma_config.params.N)])
    rep.append(['ZUMA_K',str(zuma_config.params.K)])
    rep.append(['ZUMA_CHAN_W',str(zuma_config.params.W)])
    for file in filelist:
        o = open(directory  + '//' + file,"w") #open for write
        for line in open(template_directory + '//' + file):
            for pair in rep:
                line = line.replace(pair[0],pair[1])
            o.write(line)
        o.close()

import sys


make_files(sys.argv[1], sys.argv[2])
