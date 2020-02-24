
import xml.etree.ElementTree as ET
import globs
import numpy


def addVprSwitch(edge,switchesElement,newId,switchName,delay):
    strdelay = (str(delay) + "e-12")
    switchAttr = {'type':'mux', 'name':switchName,  'R':"0.000000", 'Cin':"0.000000e+00", 'Cout':"0.000000e+00", 'Cinternal':"0.000000e+00", 'Tdel':strdelay, 'mux_trans_size':"2.183570", 'buf_size':"32.753502" }
    #<switch type="mux" name="0" R="0.000000" Cin="0.000000e+00" Cout="0.000000e+00" Cinternal="0.000000e+00" Tdel="8.972000e-11" mux_trans_size="2.183570" buf_size="32.753502"/>

    switchElement = ET.SubElement(switchesElement,'switch',switchAttr)


def addRRSwitch(edge,switchesElement,newId,switchName,delay):

    #<switch id="1" name="0" type="mux"><timing Tdel="8.97200023e-11"/>
    #<sizing buf_size="32.7535019" mux_trans_size="2.18356991"/>
    #</switch>
    strdelay = (str(delay) + "e-12")
    switchAttr = {"id":str(newId), 'name':switchName, 'type':'mux'}

    switchElement = ET.SubElement(switchesElement,'switch',switchAttr)

    ET.SubElement(switchElement, 'timing', {"Tdel":strdelay})
    ET.SubElement(switchElement, 'sizing', {"buf_size":'32.7535019',"mux_trans_size":'2.18356991'})


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
        if sinkNode.type < 3:
            continue
        if sourceNode.type < 3:
            continue

        #update the switch Id in the edge
        edge.attrib["switch_id"] = str(newId)

        #get the timing from the sink. port and path delay
        portDelay = [0.0,0.0,0.0]
        ioPathDelay = [0.0,0.0,0.0]

        if sinkNode.ioPathDelay is not None:
            ioPathDelay = sinkNode.ioPathDelay[int(sourceId)]
        else:
            print "Error: no timing"
        if sinkNode.readPortDelay is not None:
            readPortDelay = sinkNode.readPortDelay[int(sourceId)]
        else:
            print "Error: no timing"
        #we use the average timing for now
        #average is the middle timing entry
        delay = numpy.add(ioPathDelay,readPortDelay)[1]

        #add switches with the corresponding delay to vpr and rr xml files
        addRRSwitch(edge,switchesElement,newId,switchName,delay)
        addVprSwitch(edge,switchesElementVpr,newId,switchName,delay)

    #write the modificaion back to the file
    tree.write('rr_graph2.xml')
    treeVpr.write('ARCH_vpr82.xml')

if __name__ == "__main__":
    # execute only if run as a script
    annotateBack()
