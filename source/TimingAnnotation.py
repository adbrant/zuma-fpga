
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


def annotateBack():

    tree = ET.parse('rr_graph.xml')
    root = tree.getroot()

    treeVpr = ET.parse('ARCH_vpr8.xml')
    rootVpr = treeVpr.getroot()

    switchesElement = root.find("./switches")
    edges = root.findall("./rr_edges/edge")

    switchesElementVpr = rootVpr.find("./switchlist")


    for newId,edge in enumerate(edges,2) :

        sourceId = edge.attrib["src_node"]
        sinkId = edge.attrib["sink_node"]

        switchName =  sourceId + '_' + sinkId


        sinkNode = globs.nodes[int(sinkId)]
        sourceNode = globs.nodes[int(sourceId)]

        #if it is a source or a sink. skip it.
        #also deleted nodes are skipped
        #these node have connections in the nodegraph which are
        #not represented in the rr_graph (ordered layer)
        if sinkNode.type == 0 or sinkNode.type == 1:
            continue
        if sourceNode.type == 0 or sourceNode.type == 0:
            continue

        #update the switch Id in the edge
        edge.attrib["switch_id"] = str(newId)

        #get the timing from the sink. port and path delay
        portDelay = [0.0,0.0,0.0]
        ioPathDelay = [0.0,0.0,0.0]

        if sinkNode.ioPathDelay is not None:
            ioPathDelay = sinkNode.ioPathDelay[int(sourceId)]
        #else:
            #print "Error: no timing"
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


    #now propagate the lut timing
    cmplxBlockElement = rootVpr.find("./complexblocklist")

    for location,clb in globs.clusters.items():
        x,y = location
        strlocation = str(x) +'_' + str(y)
        clusterElement = cmplxBlockElement.find("./pb_type[@name='clb"+ strlocation + "']")
        #no find the delays
        lutDelayElements = clusterElement.findall(".//delay_matrix[@in_port='lut6.in']")
        completeDelayElementsClb = clusterElement.findall(".//delay_matrix[@in_port='clb"+ strlocation +".I']")
        completeDelayElementsBle = clusterElement.findall(".//delay_matrix[@in_port='ble[" + str(globs.params.N -1) + ":0].out']")
        directDelayElements =  clusterElement.findall('.//delay_constant')

        for bleIndex,lutDelayElement in enumerate(lutDelayElements):

            newText = ''
            for blePinPosition in range(globs.params.K):
                newText += str(clb.delayBle[(bleIndex,blePinPosition)][2]) + "e-12 "
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
                    newText += str(clb.delayBleOutToBleIn[(sourceBleIndex,targetBleIndex,targetPinPosition)][2]) + "e-12 "
                newText += '\n'

            completeDelayElementBle.text = newText
        #----------------------
        for bleIndex,directDelayElement in enumerate(directDelayElements):

            newTime = str(clb.delayBleOutToClbOut[(bleIndex)][2]) + "e-12"

            directDelayElement.set('max', newTime)
            directDelayElement.set('min', newTime)

    #write the modificaion back to the file
    tree.write('rr_graph_timing.xml')
    treeVpr.write('ARCH_vpr8_timing.xml')

##anotate the delay after the lut to the clusters output
def annotateBleOutToClbOut(clb):

    #iterate thourgh the outputs(opins), grab the corresponding ffmux
    #and calc the delay

    #init the list were we save the delay for each output pin
    delay = {}

    #the opins can be accessed through the drivers list
    for bleIndex,driver in enumerate(clb.outputs):

        #get the opin of this driver
        opinId = driver.id
        opin = globs.nodes[opinId]

        #get the ffmux. opins have only one input
        ffmuxId = opin.inputs[0]
        ffmux = globs.nodes[ffmuxId]

        #get the the lut id
        lutId = ffmux.inputs[0]

        #now calc the delay and add it to the dict
        #skip the opin delay. opins are passtrough nodes on a cluster
        #delayOpin = numpy.add(opin.ioPathDelay[ffmuxId],opin.readPortDelay[ffmuxId])

        delayffmux = numpy.add(ffmux.ioPathDelay[lutId],ffmux.readPortDelay[lutId])
        delay[bleIndex] = delayffmux

    #append the delay to the cluster
    clb.delayBleOutToClbOut = delay

##anotate the delay after the lut output to another lut input on the same cluster
def annotateBleOutToBleIn(clb):

    #get the delay for every combination of every lut output to any lut input pin
    #in that cluster

    delay = {}

    for sourceBleIndex,sourceBleId in enumerate(clb.LUT_nodes):

        #get the source elut node
        sourceBle = globs.nodes[sourceBleId]

        #get the ffmux of the source:
        ffmuxId = sourceBle.edges[0]
        ffmux = globs.nodes[ffmuxId]

        #get the delay for the ffmux
        delayffmux = numpy.add(ffmux.ioPathDelay[sourceBleId],ffmux.readPortDelay[sourceBleId])

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
                delay[key] = numpy.add(delayffmux,delayIntercon)

    #append the delay to the cluster
    clb.delayBleOutToBleIn = delay

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
def annotateBle(clb):

    delay = {}

    for bleIndex in range(globs.params.N):
        for blePinPosition in range(globs.params.K):

            #get the elut node
            elutId = clb.LUT_nodes[bleIndex]
            elutNode = globs.nodes[elutId]

            #get the input id for accessing port delay
            inputId = elutNode.inputs[blePinPosition]

            #now get the delay
            delayElut = numpy.add(elutNode.ioPathDelay[inputId],elutNode.readPortDelay[inputId])

            #add the delay to the dict
            key = (bleIndex,blePinPosition)
            delay[key] = delayElut

    #append the delay to the cluster
    clb.delayBle = delay

##annotate each cluster with a couple of delay dictionaries to represent the internal delays.
# we used the same method as for the global routing graph
# to bundle the port delay with the io path delay for each pin on the internal elements (mux,ble, ...).
# Therefore it was the easiest way, for the later backpropagation in the xml file,
# to divide the internal delay into four parts:
# - from the clb pin through the interconnect network to the ble input (but ommiting the ble input)
# - from the lut input through the lut (port delay + io paht delay).
# - from the lut output to the cluster output.
# - from the lut ouput back to anather ble input by passing the interconnect network again.
def annotateClusterTiming():

    for clb in globs.clusters.values():
        annotateBleOutToClbOut(clb)
        annotateBleOutToBleIn(clb)
        annotateClbInToBleIn(clb)
        annotateBle(clb)

if __name__ == "__main__":
    # execute only if run as a script
    annotateBack()
