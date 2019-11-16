# use this if you want to include modules from a subforder.
# used for the unit tests to import the struct module
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"../")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import structs
import re
import const
import xml.etree.ElementTree as ET


#parse the type string and return the proper int value
def getNodeType(typeString):

    type = -1

    if (typeString == 'SINK'):
        type = 1
    elif (typeString == 'SOURCE'):
        type = 2
    elif (typeString == 'OPIN'):
        type = 3
    elif (typeString == 'IPIN'):
        type = 4
    elif (typeString == 'CHANX'):
        type = 5
    elif (typeString == 'CHANY'):
        type = 6
    else:
        assert(0)

    return type

##parse the rr_graph.echo file
#param filename the path to the rr_graph file.
# @return a tuple (clusterx,clustery,nodegraph) where
#   clusterx,clustery are the maximal x and y local coordinates and nodegraph
#   is a NodeGraph object
def parseGraph(filename):

    #init the return stuff
    clusterx = 0
    clustery = 0

    nodeGraph = structs.NodeGraph()

    #open the graph.echo file
    fh = open(filename,"r")

    #parse the lines of the following format:

    #      id  type   location   index       direction        driver
    #Node: 0   SINK   (0, 1)     Ptc_num: 0  Direction: OPEN  Drivers: OPEN

    #parse the file and build up the node graph
    while 1:
        line = fh.readline() # read node type, location, ...
        if not line:
            break
        str = line.split()
        #print id, int(str[1])
        #assert(id is int(str[1]))
        n = structs.Node()
        #set the id.
        n.id = int(str[1])

        #set the type
        n.type = getNodeType(str[2])

        nums = re.findall(r'\d+', line)
        nums = [int(i) for i in nums ]

        #get the location and the index.
        #The index is the pad position, pin position or track number
        #depending its a pin on an I/O block, cluster or a channel.
        #Depending on this node type the values are on different positions
        #in the file.
        if n.type < 5 or len(nums) < 5:
            n.location = (nums[1],nums[2])
            n.index = nums[3]
        else:
            n.location = (nums[1],nums[2],nums[3],nums[4])
            n.index = nums[5]

        #set the direction of the node.
        if n.type > 4:
            dir = line.split(' ')[-3]
            if dir == 'INC_DIRECTION':
                #north or east
                if n.type is 5:
                    n.dir = const.E
                else:
                    n.dir = const.N
            else:
                if n.type is 5:
                    n.dir = const.W
                else:
                    n.dir = const.S

        #read the edge ids and append them to
        #the edge list of the  node
        line = fh.readline() # read edges
        nums = re.findall(r'\d+', line)
        #assign the ids
        n.edges = [int(i) for i in nums[1:]]

        #skip the rest of the information
        line = fh.readline() # skip switch types
        line = fh.readline() # skip (occupancy?) and capacity
        line = fh.readline() # skip R and C
        line = fh.readline() # skip cost index
        line = fh.readline() # skip newline dividing records

        #clusterx,clustery are the maximal value of location coords.
        #find these maximal location coords
        clusterx = max(clusterx,n.location[0])
        clustery = max(clustery,n.location[1])

        #append the node to the node graph
        #supply an id to check if this id was add before
        nodeGraph.add(n,n.id)

    return (clusterx,clustery,nodeGraph)

##parse the rr_graph.echo file
#param filename the path to the rr_graph file.
# @return a tuple (clusterx,clustery,nodegraph) where
#   clusterx,clustery are the maximal x and y local coordinates and nodegraph
#   is a NodeGraph object
def parseGraphXml(filename):

    #init the return stuff
    clusterx = 0
    clustery = 0

    nodeGraph = structs.NodeGraph()

    #now parse the xml file
    tree = ET.parse(filename)
    root = tree.getroot()
    nodes = root.findall('./rr_nodes/node')

    for node in nodes:

        #create a node for the NodeGraph and copy the attributes:
        n = structs.Node()

        #set the id
        n.id = int(node.get('id'))

        #get the type
        n.type = getNodeType(node.get('type'))

        #get the location and the index.
        #The index is the pad position, pin position or track number
        #depending its a pin on an I/O block, cluster or a channel.
        #for channels with length greater one
        #we have different start and end locations
        location = node.find('loc')
        n.index = int(location.get('ptc'))

        if n.type < 5:
            xCoord = int(location.get('xlow'))
            yCoord = int(location.get('ylow'))
            n.location = (xCoord,yCoord)
        #we have a channel get start and end location
        else:
            xStart = int(location.get('xlow'))
            yStart = int(location.get('ylow'))
            xEnd = int(location.get('xhigh'))
            yEnd = int(location.get('yhigh'))
            n.location = (xStart,yStart,xEnd,yEnd)

        #set the direction of the node.
        if n.type > 4:
            dir = node.get('direction')
            if dir == 'INC_DIR':
                #north or east
                if n.type is 5:
                    n.dir = const.E
                else:
                    n.dir = const.N
            else:
                if n.type is 5:
                    n.dir = const.W
                else:
                    n.dir = const.S

        #set the edges
        #therefore we have to search all edges with this id as a source
        edges = root.findall('./rr_edges/edge[@src_node=\'' + str(n.id) + '\']')
        for edge in edges:
            #append it to the node edge list
            edgeId = int(edge.get('sink_node'))
            n.edges.append(edgeId)

        #clusterx,clustery are the maximal value of location coords.
        #find these maximal location coords
        clusterx = max(clusterx,n.location[0])
        clustery = max(clustery,n.location[1])

        #append the node to the node graph
        #provide an id to check if this id was add before
        nodeGraph.add(n,n.id)


    return (clusterx,clustery,nodeGraph)

def simpleTest():
    (clusterx,clustery,nodeGraph) = parseGraphXml('rr_graph.echo')
    for node in nodeGraph.nodes:
        print node.id

#some simple unit Test
def main():
    simpleTest()

if __name__ == '__main__':
    main()
