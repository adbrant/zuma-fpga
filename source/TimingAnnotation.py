
import xml.etree.ElementTree as ET
import globs
import numpy


def addVprSwitch(edge,switchesElement,newId,switchName,delay):
    strdelay = (str(delay) + "e-12")
    switchAttr = {'type':'mux', 'name':switchName,  'R':"0", 'Cin':"0", 'Cout':"0", 'Cinternal':"0", 'Tdel':strdelay, 'mux_trans_size':'0', 'buf_size':'0' }
    #<switch type="mux" name="0" R="0.000000" Cin="0.000000e+00" Cout="0.000000e+00" Cinternal="0.000000e+00" Tdel="8.972000e-11" mux_trans_size="2.183570" buf_size="32.753502"/>

    switchElement = ET.SubElement(switchesElement,'switch',switchAttr)


def addRRSwitch(edge,switchesElement,newId,switchName,delay):

    #<switch id="1" name="0" type="mux"><timing Tdel="8.97200023e-11"/>
    #<sizing buf_size="32.7535019" mux_trans_size="2.18356991"/>
    #</switch>
    strdelay = (str(delay) + "e-12")
    switchAttr = {"id":str(newId), 'name':switchName, 'type':'mux'}

    switchElement = ET.SubElement(switchesElement,'switch',switchAttr)

    ET.SubElement(switchElement, 'timing', {'Cin':"0", 'Cinternal':"0", 'Cout':"0", 'R':"0","Tdel":strdelay})
    ET.SubElement(switchElement, 'sizing', {"buf_size":'0',"mux_trans_size":'0'})

#the outer timing annotation is done by adding virtual delay muxes for each edge in the node graph.
#to add these virtual switches we must add them in the rr_graph file as well in the aritecture description.
#need the edges xml node of the rr_graph, the switch tag of the rr_graph and of the architecture file.
def annotateOuterTiming(edges,switchesElement,switchesElementVpr):

    for newId,edge in enumerate(edges,2) :

        sourceId = edge.attrib["src_node"]
        sinkId = edge.attrib["sink_node"]

        switchName =  sourceId + '_' + sinkId


        sinkNode = globs.nodes[int(sinkId)]
        sourceNode = globs.nodes[int(sourceId)]

        #if it is a source or a sink. skip it.
        #also deleted nodes are skipped
        #TODO: are sink and source nodes used?

        if sinkNode.type == 0 or sinkNode.type == 1:
            continue
        if sourceNode.type == 0 or sourceNode.type == 2:
            continue

        #also skip timing delay caused by the ordered layer nodes
        #we don't know which input will be chosen.
        #we can not only forget about the read port delay and still use the iopath
        #because a opin can be implement by several luts and therefore havge different
        # io path delays depending which input was chosen

        #skip the edges from ipins to layer nodes or layer nodes to opins
        if sinkNode.type == 10 or sourceNode.type == 10:
            continue

        #update the switch Id in the edge
        edge.attrib["switch_id"] = str(newId)

        #get the timing from the sink. port and path delay
        readPortDelay = [0.0,0.0,0.0]
        ioPathDelay = [0.0,0.0,0.0]

        if sinkNode.ioPathDelay is not None:
            ioPathDelay = sinkNode.ioPathDelay[int(sourceId)]
        #else:
            #print "Error: no timing"

        #skip the read port dealy for opins connected to the ordered layer
        if sinkNode.readPortDelay is not None:
            readPortDelay = sinkNode.readPortDelay[int(sourceId)]
        #else:
            #print "Error: no timing"

        #we use the worst case timing for now
        #worst case is the last timing entry
        delay = numpy.add(ioPathDelay,readPortDelay)[2]

        #add switches with the corresponding delay to vpr and rr xml files
        addRRSwitch(edge,switchesElement,newId,switchName,delay)
        addVprSwitch(edge,switchesElementVpr,newId,switchName,delay)

def annotateInnerTiming(cmplxBlockElement):

    for location,clb in globs.clusters.items():
        x,y = location
        strlocation = str(x) +'_' + str(y)
        clusterElement = cmplxBlockElement.find("./pb_type[@name='clb"+ strlocation + "']")
        #no find the delays
        lutDelayElements = clusterElement.findall(".//delay_matrix[@in_port='lut6.in']")

        latcheslutToFF = clusterElement.findall(".//delay_constant[@in_port='soft_logic.out[0:0]']")
        latchesClockToQ = clusterElement.findall(".//T_clock_to_Q")

        if globs.params.extractSetupHold:
            latchesSetup = clusterElement.findall(".//T_setup")
            latchesHold  = clusterElement.findall(".//T_hold")
        else:
            latchesSetup = []
            latchesHold = []
            
        ffmuxDelayElementsLut = clusterElement.findall(".//mux/delay_constant[@in_port='soft_logic.out']")
        ffmuxDelayElementsFF =  clusterElement.findall(".//mux/delay_constant[@in_port='ff.Q']")

        if not globs.params.UseClos:
            completeDelayElementsClb = clusterElement.findall(".//delay_matrix[@in_port='clb"+ strlocation +".I']")
        else:
            completeDelayElementsClb = []

        bleOutputs = 'ble0.out'
        for bleIndex in range(1,globs.params.N):
            bleOutputs += " ble" + str(bleIndex) + '.out'

        if not globs.params.UseClos:
            completeDelayElementsBle = clusterElement.findall(".//delay_matrix[@in_port='"+ bleOutputs + "']")
        else:
            completeDelayElementsBle = []
        #directDelayElements =  clusterElement.findall('.//direct/delay_constant')

        for bleIndex,lutDelayElement in enumerate(lutDelayElements):

            newText = ''
            for blePinPosition in range(globs.params.K):
                delayLut = clb.delayBle[(bleIndex,blePinPosition)]

                newText += str(delayLut[2]) + "e-12 "
                newText += '\n'

            lutDelayElement.text = newText
        #------------
        for bleIndex,completeDelayElementClb in enumerate(completeDelayElementsClb):

            newText = ''

            for clbPinPosition in range(globs.params.I):

                #take th worst case time
                for blePinPosition in range(globs.params.K):
                    newText += str(clb.delayClbInToBleIn[(clbPinPosition,bleIndex,blePinPosition)][2]) + "e-12 "
                newText += '\n'

            completeDelayElementClb.text = newText
        #----------------------
        for targetBleIndex,completeDelayElementBle in enumerate(completeDelayElementsBle):

            newText = ''

            for sourceBleIndex in range(globs.params.N):

                #take th worst case time
                for targetPinPosition in range(globs.params.K):
                    newText += str(clb.delayMuxOutToBleIn[(sourceBleIndex,targetBleIndex,targetPinPosition)][2]) + "e-12 "
                newText += '\n'

            completeDelayElementBle.text = newText
        #----------------------
        for bleIndex,directDelayElement in enumerate(ffmuxDelayElementsLut):

            newTime = str(clb.delayBleOutToMuxOut[(bleIndex,'unregistered')][2]) + "e-12"

            directDelayElement.set('max', newTime)
        #----------------------
        for bleIndex,directDelayElement in enumerate(ffmuxDelayElementsFF):

            newTime = str(clb.delayBleOutToMuxOut[(bleIndex,'registered')][2]) + "e-12"

            directDelayElement.set('max', newTime)
        #----------------------
        for bleIndex,latch in enumerate(latcheslutToFF):

            (lutToFF,clockToQ) = clb.delayLatch[bleIndex]
            newTime = str(lutToFF[2]) + "e-12"
            latch.set('max', newTime)
        #----------------------
        for bleIndex,latch in enumerate(latchesClockToQ):

            (lutToFF,clockToQ) = clb.delayLatch[bleIndex]
            newTime = str(clockToQ[2]) + "e-12"
            latch.set('max', newTime)

        #----------------------
        for bleIndex,latch in enumerate(latchesSetup):

            (setupDelay,holdDelay) = clb.setupHoldDelay[bleIndex]
            #negative values are not used in vpr
            setupTime = abs(setupDelay[2])
            newTime = str(setupTime) + "e-12"
            latch.set('value', newTime)
        #----------------------
        for bleIndex,latch in enumerate(latchesHold):

            (setupDelay,holdDelay) = clb.setupHoldDelay[bleIndex]
            #negative values are not used in vpr
            holdTime = abs(holdDelay[2])
            newTime = str(holdTime) + "e-12"
            latch.set('value', newTime)



def annotateBack():

    tree = ET.parse('rr_graph.xml')
    root = tree.getroot()

    treeVpr = ET.parse('ARCH_vpr8.xml')
    rootVpr = treeVpr.getroot()

    switchesElement = root.find("./switches")
    edges = root.findall("./rr_edges/edge")

    switchesElementVpr = rootVpr.find("./switchlist")

    if globs.params.annotateOuterRouting:
        annotateOuterTiming(edges,switchesElement,switchesElementVpr)


    #now propagate the lut timing
    cmplxBlockElement = rootVpr.find("./complexblocklist")

    if globs.params.annotateInnerRouting:
        annotateInnerTiming(cmplxBlockElement)

    #write the modificaion back to the file
    tree.write('rr_graph_timing.xml')
    treeVpr.write('ARCH_vpr8_timing.xml')

##anotate the delay after the lut to the mux output
def annotateBleOutToMuxOut(clb):

    #init the list were we save the delay for each ffmux
    delay = {}

    #iterate thorugh the ffmux and clac the delays.
    #note that a ffmux has two inputs from a lut (unregistered/registered).
    #one combinatorial input and one from the flipflop
    for bleIndex,ffmuxId in enumerate(clb.LUT_FFMUX_nodes):

        #get the ffmux.
        ffmux = globs.nodes[ffmuxId]

        #get the lut id
        bleId = ffmux.inputs[0]

        delayUnregistered = numpy.add(ffmux.ioPathDelay[(bleId,'unregistered')],ffmux.readPortDelay[(bleId,'unregistered')])
        delayRegistered = numpy.add(ffmux.ioPathDelay[(bleId,'registered')],ffmux.readPortDelay[(bleId,'registered')])

        delay[(bleIndex,'unregistered')] = delayUnregistered
        delay[(bleIndex,'registered')] = delayRegistered

    #append the delay to the cluster
    clb.delayBleOutToMuxOut = delay

##anotate the delay after the ffmux output to another lut input on the same cluster
def annotateMuxOutToBleIn(clb):

    #get the delay for every combination of every ffmux output to any lut input pin
    #in that cluster

    delay = {}

    for sourceBleIndex,ffmuxId in enumerate(clb.LUT_FFMUX_nodes):

        #get the ffmux of the source:
        ffmux = globs.nodes[ffmuxId]

        #now get the path to every other pin of every other lut in the cluster
        for targetBleIndex,targetBleId in enumerate(clb.LUT_nodes):

            #get the traget elut node
            targetBle = globs.nodes[targetBleId]

            for pinPoisiton,InterconNodeId in enumerate(targetBle.inputs):

                #get the iterconnect node (inode)
                interconNode = globs.nodes[InterconNodeId]

                #now calc the delay from the source lut output to the target lust input
                delayIntercon = numpy.add(interconNode.ioPathDelay[ffmuxId],interconNode.readPortDelay[ffmuxId])

                key = (sourceBleIndex,targetBleIndex,pinPoisiton)
                delay[key] = delayIntercon

    #append the delay to the cluster
    clb.delayMuxOutToBleIn = delay

def annotateClbInToBleIn(clb):

    #get the delay from every clb pin position to every lut pin
    #therefore we iterate through the interconnect nodes and need predecessor ipin node
    #the get the right port delay

    delay = {}

    #grep the predecessor ipin
    for clbPinPosition,driver in enumerate(clb.inputs):

        ipinId = driver.id

        #now get the intercon node
        for bleIndex in range(globs.params.N):
            for blePinPosition in range(globs.params.K):

                interconNodeId = clb.LUT_input_nodes[bleIndex][blePinPosition]
                interconNode = globs.nodes[interconNodeId]

                #now get the interconn delay
                delayIntercon = numpy.add(interconNode.ioPathDelay[ipinId],interconNode.readPortDelay[ipinId])

                #add the delay to the dict
                key = (clbPinPosition,bleIndex,blePinPosition)
                delay[key] = delayIntercon

    #append the delay to the cluster
    clb.delayClbInToBleIn = delay

#annotate the lut delay (port delay and io path) for every lut
#the ble save the following information: (delayLut,lutToFF,clocktoq)
#  -delayLut ist the readport delay and the iopath of the lut
#  -lutToFF is is the delay of the connection from the lut to the ff
#  -clocktoq is the delay from the clock to the ff output
def annotateBle(clb):

    delay = {}
    latchDelay = {}
    setupHoldDelay = {}

    for bleIndex in range(globs.params.N):

        #get the elut node
        elutId = clb.LUT_nodes[bleIndex]
        elutNode = globs.nodes[elutId]

        for blePinPosition in range(globs.params.K):

            #get the input id for accessing port delay
            inputId = elutNode.inputs[blePinPosition]

            #now get the delay
            delayLut = numpy.add(elutNode.ioPathDelay[inputId],elutNode.readPortDelay[inputId])

            #add the delay to the dict
            key = (bleIndex,blePinPosition)
            delay[key] = delayLut

        #now get the flip flop timing:
        lutToFF = elutNode.ffReadPortDelay
        clockToQ = elutNode.ffIODelay
        #lutToFF = [0.0,0.0,0.0]
        #clockToQ = [0.0,0.0,0.0]
        setupDelay = elutNode.ffSetupDelay
        holdDelay = elutNode.ffHoldDelay


        latchDelay[bleIndex] = (lutToFF,clockToQ)
        setupHoldDelay[bleIndex] = (setupDelay,holdDelay)


    #append the delay to the cluster
    clb.delayBle = delay
    clb.delayLatch = latchDelay
    clb.setupHoldDelay = setupHoldDelay

##annotate each cluster with a couple of delay dictionaries to represent the internal delays.
# we used the same method as for the global routing graph
# to bundle the port delay with the io path delay for each pin on the internal elements (mux,ble, ...).
# Therefore it was the easiest way, for the later backpropagation in the xml file,
# to divide the internal delay into four parts:
# - from the clb pin through the interconnect network to the ble input (but ommiting the ble input)
# - from the lut input through the lut output (port delay + io paht delay).
# - from the lut output to the ffmux output.
# - from the ffmux ouput back to anather ble input by passing the interconnect network again.
def annotateClusterTiming():

    for clb in globs.clusters.values():
        annotateBleOutToMuxOut(clb)

        #we cant annotate the interconnect when the close network is used.
        #vpr use only complete interconnect networks
        if not globs.params.UseClos:
            annotateMuxOutToBleIn(clb)
            annotateClbInToBleIn(clb)

        annotateBle(clb)

if __name__ == "__main__":
    # execute only if run as a script
    annotateBack()
