
import xml.etree.ElementTree as ET


def addVprSwitch():
    pass

def addRRSwitch(edge,switchesElement,newId):

    #<switch id="1" name="0" type="mux"><timing Tdel="8.97200023e-11"/>
    #<sizing buf_size="32.7535019" mux_trans_size="2.18356991"/>
    #</switch>

    sourceId = edge.attrib["src_node"]
    sinkId = edge.attrib["sink_node"]

    switchName =  sourceId + '_' + sinkId
    switchAttr = {"id":str(newId), 'name':switchName, 'type':'mux'}

    switchElement = ET.SubElement(switchesElement,'switch',switchAttr)

    ET.SubElement(switchElement, 'timing', {"Tdel":'8.97200023e-11'})
    ET.SubElement(switchElement, 'sizing', {"buf_size":'32.7535019',"mux_trans_size":'2.18356991'})


def annotateBack():

    tree = ET.parse('rr_graph.xml')
    root = tree.getroot()

    switchesElement = root.find("./switches")
    edges = root.findall("./rr_edges/edge")

    for newId,edge in enumerate(edges,2) :

        #update the switch Id in the edge
        edge.attrib["switch_id"] = str(newId)

        #add switches for the new Id
        addRRSwitch(edge,switchesElement,newId)
        addVprSwitch()

    #write the modificaion back to the file
    tree.write('rr_graph2.xml')

if __name__ == "__main__":
    # execute only if run as a script
    annotateBack()
