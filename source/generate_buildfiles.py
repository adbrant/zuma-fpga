#	Preparation of input files for VTR tools
import sys
import zuma_config

def buildClbTilePattern(rep):

    tilePattern = ""

    for x in range(zuma_config.params.X):
        for y in range(zuma_config.params.Y):

            location = str(x+1) + '_' + str(y+1)

            tilePattern += \
            '''<tile name="clb''' + location + '''">
              <equivalent_sites>
                <site pb_type="clb''' + location + '''"/>
              </equivalent_sites>
            <input name="I" num_pins="ZUMA_I"/>
            <output name="O" num_pins="ZUMA_N"/>
            <clock name="clk" num_pins="1"/>
            <fc in_type="ZUMA_FCIN_TYPE" in_val="ZUMA_FCIN_VAL" out_type="ZUMA_FCOUT_TYPE" out_val="ZUMA_FCOUT_VAL" />
            <pinlocations pattern="spread"/>
            </tile>
            '''

    rep.append(['CLBTILES',tilePattern])


def buildLayoutPattern(rep):

    layoutPattern = ""

    for x in range(zuma_config.params.X):
        for y in range(zuma_config.params.Y):

            location = str(x+1) + '_' + str(y+1)

            layoutPattern += '<single type="clb' + location + \
                             '" x="' + str(x+1) + \
                             '" y="' + str(y+1) + '"  priority="1"/>'

    rep.append(['CLBLAYOUT',layoutPattern])

def buildClbPbTypePattern(rep):

    pbTypePattern = ""

    for x in range(zuma_config.params.X):
        for y in range(zuma_config.params.Y):

            location = str(x+1) + '_' + str(y+1)

            pbTypePattern += \
            '''<pb_type name="clb''' + location + '''">

                <input name="I" num_pins="ZUMA_I"/>
                <output name="O" num_pins="ZUMA_N"/>
                <clock name="clk" num_pins="1"/>
                <!-- allow an easier parsing of the netlist -->
                <mode name="clb">
                  <pb_type name="ble" num_pb="ZUMA_N">
                    <input name="in" num_pins="ZUMA_K"/>
                    <output name="out" num_pins="1"/>
                    <clock name="clk" num_pins="1"/>
                    <mode name="ble">
                      <pb_type name="soft_logic" num_pb="1">
                        <input name="in" num_pins="ZUMA_K"/>
                        <output name="out" num_pins="1"/>
                        <mode name="n1_lut6">
                          <pb_type name="lut6" blif_model=".names" num_pb="1" class="lut">
                            <input name="in" num_pins="ZUMA_K" port_class="lut_in"/>
                            <output name="out" num_pins="1" port_class="lut_out"/>
                            ''' + location +'''LUTDELAYMATRIX
                          </pb_type>
                          <interconnect>
                            <direct name="direct1" input="soft_logic.in[ZUMA_K_m_1:0]" output="lut6[0:0].in[ZUMA_K_m_1:0]"/>
                            <direct name="direct2" input="lut6[0:0].out" output="soft_logic.out[0:0]"/>
                          </interconnect>
                        </mode>
                      </pb_type>
                      <pb_type name="ff" blif_model=".latch" num_pb="1" class="flipflop">
                        <input name="D" num_pins="1" port_class="D"/>
                        <output name="Q" num_pins="1" port_class="Q"/>
                        <clock name="clk" num_pins="1" port_class="clock"/>
                      </pb_type>
                      <interconnect>
                        <direct name="direct1" input="soft_logic.out[0:0]" output="ff.D"/>
                        <direct name="direct2" input="ble.in" output="soft_logic.in"/>
                        <direct name="direct3" input="ble.clk" output="ff.clk"/>
                        <mux name="mux1" input="ff.Q soft_logic.out[0:0]" output="ble.out[0:0]">
                            <delay_constant max="0" in_port="soft_logic.out" out_port="ble.out"/>
                            <delay_constant max="0" in_port="ff.Q" out_port="ble.out"/>
                        </mux>
                       </interconnect>
                    </mode>
                  </pb_type>

                  <interconnect>
                    <complete name="complete1" input="clb''' + location +'''.I ble[ZUMA_N_m_1:0].out" output="ble[ZUMA_N_m_1:0].in">
                    ''' + location +'''COMPLETE1DELAYMATRIX
                    </complete>
                    <complete name="complete2" input="clb''' + location +'''.clk" output="ble[ZUMA_N_m_1:0].clk"/>
                    <direct name="direct1" input="ble[ZUMA_N_m_1:0].out" output="clb''' + location +'''.O">
                    </direct>
                  </interconnect>
                </mode>
            </pb_type>
              '''

            buildDelayPattern(rep,location)

    rep.append(['CLBPBTYPES',pbTypePattern])

def buildDelayPattern(rep,location):

    #build the matrix delay string
    matrixDelayString = '<delay_matrix type="max" in_port="lut6.in" out_port="lut6.out">\n'

    for i in range(zuma_config.params.K):
            matrixDelayString += "0\n"

    matrixDelayString += "</delay_matrix>\n"

    rep.append([location +'LUTDELAYMATRIX',matrixDelayString])


    #complete1
    matrixDelayString = ''
    for bleIndex in range(zuma_config.params.N):

        matrixDelayString += '<delay_matrix type="max" in_port="clb'+ location +'.I" out_port="ble[' + str(bleIndex) + '].in">\n'

        for clbPinPosition in range(zuma_config.params.I):
            matrixDelayString += "0 "*zuma_config.params.K

        matrixDelayString += "</delay_matrix>\n"

    for bleIndex in range(zuma_config.params.N):

        matrixDelayString += '<delay_matrix type="max" in_port="ble[' +str(zuma_config.params.N -1) + ':0].out" out_port="ble[' + str(bleIndex) +  '].in">\n'

        for x in range(zuma_config.params.N):
            matrixDelayString += "0 "*zuma_config.params.K

        matrixDelayString += "</delay_matrix>\n"

    rep.append([location +'COMPLETE1DELAYMATRIX',matrixDelayString])


    #direct delay
    #matrixDelayString = ''

    #for bleIndex in range(zuma_config.params.N):
    #    matrixDelayString += '<delay_constant max="0" in_port="ble[' + str(bleIndex) + '].out" out_port="clb'+ location +'.O[' + str(bleIndex) + ']"/>\n'


    #rep.append([location +'DIRECTDELAYMATRIX',matrixDelayString])

def buildTimingArchFile(directory, template_directory,sourceFileName,targetFileName,rep):

    #for the timing usage we have a special architecture file with
    #special placeholders

    buildClbTilePattern(rep)
    buildLayoutPattern(rep)
    buildClbPbTypePattern(rep)

    #write the patterns to the arch file in two runs
    o = open(directory  + '//' + targetFileName + 'temp',"w") #open for write
    for line in open(template_directory + '//' + sourceFileName):
        for pair in rep:
            line = line.replace(pair[0],pair[1])
        o.write(line)
    o.close()

    o = open(directory  + '//' + targetFileName,"w") #open for write
    for line in open(directory  + '//' + targetFileName + 'temp'):
        for pair in rep:
            line = line.replace(pair[0],pair[1])
        o.write(line)
    o.close()


def make_files(directory, template_directory,clockName):
    print "MAKEFILE:" + str(directory)

    #which vpr version
    if (zuma_config.params.vprVersion == 8) and zuma_config.params.vprAnnotation:
        filelist = ['abccommands.vpr8','vpr8.sh','vpr8_timing.sh']
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

    #support of a custom clock name
    #if no clock is given the standard name clock is used
    if clockName is not None:
        rep.append(['ZUMA_CLOCK_NAME',clockName])
    else:
        rep.append(['ZUMA_CLOCK_NAME',"clock"])

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

    #the timing architecture need a seperate generation procedure
    if (zuma_config.params.vprVersion == 8) and zuma_config.params.vprAnnotation:
        buildTimingArchFile(directory,
                            template_directory,
                            'ARCH_vpr8_timing.xml',
                            'ARCH_vpr8.xml',
                            rep)

if __name__ == '__main__':
    make_files(sys.argv[1], sys.argv[2],sys.argv[3])
