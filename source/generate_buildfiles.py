#	Preparation of input files for VTR tools
import sys
import zuma_config

def make_files(directory, template_directory):
    print "MAKEFILE:" + str(directory)

    #which vpr version
    if (zuma_config.params.vprVersion == 8) and zuma_config.params.vprAnnotation:
        filelist = ['ARCH_vpr8.xml', 'abccommands.vpr8','vpr8.sh','vpr8_timing.sh']
    elif zuma_config.params.vprVersion == 8:
        filelist = ['ARCH_vpr8.xml', 'abccommands.vpr8', 'vpr8.sh']
    elif (zuma_config.params.vprVersion == 7):
        filelist = ['ARCH_vpr7.xml', 'abccommands', 'vpr7.sh']
    elif (zuma_config.params.vprVersion == 6):
        filelist = ['ARCH_vpr6.xml', 'abccommands', 'vpr6.sh']
    else:
        print "ERROR: Unsupported vpr version: " + str(zuma_config.params.vprVersion)
        sys.exit(1)

    rep = []

    #tiling pattern changed in vpr8
    if (zuma_config.params.vprVersion == 8):
        rep.append(['ZUMA_ARRAY_WIDTH',str(zuma_config.params.X+2)])
        rep.append(['ZUMA_ARRAY_HEIGHT',str(zuma_config.params.Y+2)])
    else:
        rep.append(['ZUMA_ARRAY_WIDTH',str(zuma_config.params.X)])
        rep.append(['ZUMA_ARRAY_HEIGHT',str(zuma_config.params.Y)])


    #for the timing usage we have a special architecture file with
    #special placeholders
    if (zuma_config.params.vprVersion == 8):

        if zuma_config.params.vprAnnotation:
            #build the matrix delay string
            matrixDelayString = '<delay_matrix type="max" in_port="lut6.in" out_port="lut6.out">\n'
            for i in range(zuma_config.params.K):
                matrixDelayString += "261e-12\n"
            matrixDelayString += "</delay_matrix>\n"

            rep.append(['DELAYMATRIX',matrixDelayString])

        else:
            rep.append(['DELAYMATRIX',''])


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

if __name__ == '__main__':
    make_files(sys.argv[1], sys.argv[2])
