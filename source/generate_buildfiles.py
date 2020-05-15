#	Preparation of input files for VTR tools
import sys
import zuma_config


def buildBles(tempArchFile):

    matrixDelayString = '<delay_matrix type="max" in_port="lut6.in" out_port="lut6.out">\n'

    for i in range(zuma_config.params.K):
            matrixDelayString += "0\n"

    matrixDelayString += "</delay_matrix>\n"


    for bleIndex in range(zuma_config.params.N):

        bleName = "ble" + str(bleIndex)

        tempArchFile.write('''
        <pb_type name="''' + bleName + '''" num_pb="1">
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
                  ''' + matrixDelayString +
                  '''
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
              <direct name="direct2" input="''' + bleName + '''.in" output="soft_logic.in"/>
              <direct name="direct3" input="''' + bleName + '''.clk" output="ff.clk"/>
              <mux name="mux1" input="ff.Q soft_logic.out[0:0]" output="''' + bleName + '''.out[0:0]">
                  <delay_constant max="0" in_port="soft_logic.out" out_port="''' + bleName + '''.out"/>
                  <delay_constant max="0" in_port="ff.Q" out_port="''' + bleName + '''.out"/>
              </mux>
             </interconnect>
          </mode>
        </pb_type>
        ''')

def buildClb(tempArchFile,location):

    tempArchFile.write(
    '''<pb_type name="clb''' + location + '''">

        <input name="I" num_pins="ZUMA_I"/>
        <output name="O" num_pins="ZUMA_N"/>
        <clock name="clk" num_pins="1"/>
        <!-- allow an easier parsing of the netlist -->
        <mode name="clb">
    ''')

    buildBles(tempArchFile)

    tempArchFile.write('<interconnect>\n')

    bleInputs = 'ble0.in'
    bleOutputs = 'ble0.out'
    bleClks = 'ble0.clk'

    for bleIndex in range(1,zuma_config.params.N):
        bleInputs += " ble" + str(bleIndex) + '.in'
        bleOutputs += " ble" + str(bleIndex) + '.out'
        bleClks += " ble" + str(bleIndex) + '.clk'

    matrixDelayString = ''
    for bleIndex in range(zuma_config.params.N):

        matrixDelayString += '<delay_matrix type="max" in_port="clb'+ location +'.I" out_port="ble' + str(bleIndex) + '.in">\n'

        for clbPinPosition in range(zuma_config.params.I):
            matrixDelayString += "0 "*zuma_config.params.K

        matrixDelayString += "</delay_matrix>\n"

    for bleIndex in range(zuma_config.params.N):

        matrixDelayString += '<delay_matrix type="max" in_port="' + bleOutputs + '" out_port="ble' + str(bleIndex) +  '.in">\n'

        for x in range(zuma_config.params.N):
            matrixDelayString += "0 "*zuma_config.params.K

        matrixDelayString += "</delay_matrix>\n"


    #now print the interconnect of the bles
    tempArchFile.write('''
            <complete name="complete1" input="clb''' + location +'''.I ''' + bleOutputs + '''" output="''' + bleInputs + '''">
            ''' + matrixDelayString +'''
            </complete>''')

    tempArchFile.write('''
            <complete name="complete2" input="clb''' + location +'''.clk" output="''' + bleClks + '''"/>
            <direct name="direct1" input="{''' + bleOutputs +  '''}" output="clb''' + location +'''.O">
            </direct>''')


    tempArchFile.write('''
          </interconnect>
        </mode>
      </pb_type>
      ''')

def buildIO(tempArchFile):

    tempArchFile.write('''
      <pb_type name="io">

        <input name="outpad" num_pins="1"/> <!--equivalent="false" -->
        <output name="inpad" num_pins="1"/>
        <clock name="ZUMA_CLOCK_NAME" num_pins="1"/>

        <!-- IOs can operate as either inputs or outputs -->
        <mode name="inpad">
          <pb_type name="inpad" blif_model=".input" num_pb="1">
            <output name="inpad" num_pins="1"/>
          </pb_type>
          <interconnect>
            <direct name="inpad" input="inpad.inpad" output="io.inpad"/>
          </interconnect>

        </mode>
        <mode name="outpad">
          <pb_type name="outpad" blif_model=".output" num_pb="1">
            <input name="outpad" num_pins="1"/>
          </pb_type>
          <interconnect>
            <direct name="outpad" input="io.outpad" output="outpad.outpad"/>
          </interconnect>
        </mode>

      </pb_type>
    ''')


def buildComplexBlocksSection(tempArchFile):


    tempArchFile.write('<complexblocklist>')

    buildIO(tempArchFile)

    for x in range(zuma_config.params.X):
        for y in range(zuma_config.params.Y):

            location = str(x+1) + '_' + str(y+1)
            buildClb(tempArchFile,location)


    tempArchFile.write('</complexblocklist>')

def buildHeader(tempArchFile):

    tempArchFile.write('''
    <architecture>

    <models>
    </models>

    <device>
        <sizing R_minW_nmos="4220.930176" R_minW_pmos="11207.599609"/>
        <area grid_logic_tile_area="0.0"/>
        <chan_width_distr>
            <x distr="uniform" peak="1.000000"/>
            <y distr="uniform" peak="1.000000"/>
        </chan_width_distr>
        <switch_block type="wilton" fs="3"/>
        <connection_block input_switch_name="0"/>
    </device>

    <switchlist>
        <!-- should we add the delay of the buffer here? -->
        <switch type="mux" name="0" R="0" Cin="0" Cout="0" Cinternal="0" Tdel="0.1e-15" mux_trans_size="0" buf_size="0"/>
    </switchlist>

    <segmentlist>
        <segment freq="1.000000" length="4" type="unidir" Rmetal="0.000000" Cmetal="0.000000e+00">
        <mux name="0"/>
        <sb type="pattern">1 1 1 1 1</sb>
        <cb type="pattern">1 1 1 1</cb>
        </segment>
    </segmentlist>
    ''')

def buildLayoutSection(tempArchFile):

    tempArchFile.write('''
    <layout>
        <fixed_layout name="dev1" width= "ZUMA_ARRAY_WIDTH" height= "ZUMA_ARRAY_HEIGHT">
          <perimeter type="io" priority="10"/>
    ''')

    for x in range(zuma_config.params.X):
        for y in range(zuma_config.params.Y):

            location = str(x+1) + '_' + str(y+1)

            tempArchFile.write('<single type="clb' + location + \
                             '" x="' + str(x+1) + \
                             '" y="' + str(y+1) + '"  priority="1"/>\n')

    tempArchFile.write('''
          <corners type="EMPTY" priority="20"/>
        </fixed_layout>
    </layout>
    ''')


def buildTileSection(tempArchFile):

    tempArchFile.write('''
    <tiles>
    <tile name="io">
      <sub_tile name="IO_TILE" capacity="2">
        <equivalent_sites>
          <site pb_type="io"/>
        </equivalent_sites>
        <input name="outpad" num_pins="1"/>
        <output name="inpad" num_pins="1"/>
        <clock name="ZUMA_CLOCK_NAME" num_pins="1"/>
        <fc in_type="ZUMA_FCIN_TYPE" in_val="ZUMA_FCIN_VAL" out_type="ZUMA_FCOUT_TYPE" out_val="ZUMA_FCOUT_VAL" />
        <pinlocations pattern="custom">
          <loc side="left">IO_TILE.outpad IO_TILE.inpad IO_TILE.ZUMA_CLOCK_NAME</loc>
          <loc side="top">IO_TILE.outpad IO_TILE.inpad IO_TILE.ZUMA_CLOCK_NAME</loc>
          <loc side="right">IO_TILE.outpad IO_TILE.inpad IO_TILE.ZUMA_CLOCK_NAME</loc>
          <loc side="bottom">IO_TILE.outpad IO_TILE.inpad IO_TILE.ZUMA_CLOCK_NAME</loc>
        </pinlocations>
      </sub_tile>
    </tile>
    ''')

    for x in range(zuma_config.params.X):
        for y in range(zuma_config.params.Y):

            location = str(x+1) + '_' + str(y+1)

            tempArchFile.write(
            '''<tile name="clb''' + location + '''">
              <sub_tile name="CLB_TILE" capacity="1">
                <equivalent_sites>
                    <site pb_type="clb''' + location + '''"/>
                </equivalent_sites>
                <input name="I" num_pins="ZUMA_I"/>
                <output name="O" num_pins="ZUMA_N"/>
                <clock name="clk" num_pins="1"/>
                <fc in_type="ZUMA_FCIN_TYPE" in_val="ZUMA_FCIN_VAL" out_type="ZUMA_FCOUT_TYPE" out_val="ZUMA_FCOUT_VAL" />
                <pinlocations pattern="spread"/>
              </sub_tile>
            </tile>
            ''')

    tempArchFile.write('</tiles>\n')

def buildFooter(tempArchFile):
    tempArchFile.write('  </architecture>')


#replace the config placeholders in a given file and write the result in an ouput file
def replacePlaceholders(sourceFileName,targetFileName,placeholders):

        o = open(targetFileName,"w") #open for write
        for line in open(sourceFileName):
            for pair in placeholders:
                line = line.replace(pair[0],pair[1])
            o.write(line)
        o.close()

def buildTimingArchFile(tempFileName,targetFileName,rep):

    #for the timing usage we have to build a temp architecture file
    #and then apply the placeholder regex

    tempArchFile = open(tempFileName,"w")

    buildHeader(tempArchFile)
    buildTileSection(tempArchFile)
    buildLayoutSection(tempArchFile)
    buildComplexBlocksSection(tempArchFile)
    buildFooter(tempArchFile)

    tempArchFile.close()


    replacePlaceholders(tempFileName,targetFileName,rep)



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

        sourceFileName = template_directory + '//' + file
        targetFileName = directory  + '//' + file
        replacePlaceholders(sourceFileName,targetFileName,rep)


    #the timing architecture need a seperate generation procedure and generate
    #the ARCH.xml in two steps in the target directory
    if (zuma_config.params.vprVersion == 8) and zuma_config.params.vprAnnotation:
        tempFileName = directory + '//' + 'ARCH_vpr8_temp.xml'
        targetFileName = directory + '//' + 'ARCH_vpr8.xml'
        buildTimingArchFile(tempFileName,targetFileName,rep)


if __name__ == '__main__':
    make_files(sys.argv[1], sys.argv[2],sys.argv[3])
