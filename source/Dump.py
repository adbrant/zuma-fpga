from structs import *
import globs

#dump the node graph in a file and plot it when globs.params.graphviz is enabled
#param filename the file name where we dump the node graph in
def dumpGraph(filename):

    f = open(filename, 'w')

    #init stuff for graphviz plotting.

    #we tried to group the nodes by clusters and tried to highlight
    #the used wires by setting the rest transparent, but in the end it works
    #not so well ... It seems that graphviz is not the right tool for this task
    #but it's ok for now.

    if globs.params.graphviz:

        #to prevent to many dependencies, we just load it when we must
        import graphviz as gv
        graph= gv.Digraph(format='svg')

        #create subgraphs
        clusters = []
        pos = 1

        for i in range(0,globs.clusterx+1):
            clusterxList = []
            for j in range(0,globs.clustery+1):

                name = 'cluster_' + str(i) + '_' + str(j)
                cluster = gv.Digraph(name)

                cluster.node_attr.update(style='filled')
                cluster.body.append('label = '+ '\"' + name + '\"')
                cluster.body.append('color=blue')

                #sort the graph in the right order
                cluster.body.append('sortv=' + str(pos))
                pos += 1

                clusterxList.append(cluster)

            clusters.append(clusterxList)

        #graph.attr('node', style='filled')
        #graph.attr('node', fillcolor='#006699')

    #now we dump and plot the graph
    for node in globs.nodes:
        typeString= ''

        #node got removed
        if node.type == 0:
            continue

        if node.type == 1:
            typeString= 'SINK'
        elif node.type == 2:
            typeString= 'SOURCE'
        elif node.type == 3:
            typeString= 'OPIN'
        elif node.type == 4:
            typeString= 'IPIN'
        elif node.type == 5:
            typeString= 'CHANX'
        elif node.type == 6:
            typeString= 'CHANY'
        elif node.type == 7:
            typeString= 'IMUX'
        elif node.type == 8:
            typeString= 'ELUT'
        elif node.type == 9:
            typeString= 'FFMUX'
        elif node.type == 10:
            typeString= 'IOMUX'

        f.write( '------------- new node ---------------\n')
        f.write( 'id: '       + str( node.id) + '\n')
        f.write( 'type: '     + str( node.type)  + ' (' + typeString + ')\n')
        f.write( 'location: ' + str( node.location)+ '\n')
        f.write( 'edges: '    + str( node.edges)+ '\n')
        f.write( 'inputs: '   + str( node.inputs)+ '\n')
        f.write( 'source: '   + str( node.source)+ '\n')
        f.write( 'elut: '     + str( node.eLUT)+ '\n')
        f.write( 'ffmux: '    + str( node.ffmux)+ '\n')
        f.write( 'name: '     + str( node.name)+ '\n')


        #dump the corresponding lut
        if  (node.type == 8 and node.LUT != 0):
            f.write( 'content of this lut: \n')
            f.write(str(node.LUT.contents))
            f.write( '\ninput names: \n')
            for name in node.LUT.inputs:
                f.write( str(name) + ",\n")
            f.write( '\noutput name: \n')
            f.write( str(node.LUT.output) + ",\n")

        if globs.params.graphviz:


            #skip these nodes
            #if (typeString == 'SOURCE' or  typeString == 'SINK' or typeString == 'IOMUX'):
            #    continue


            currentGraph = None

            #pack all nodes except switches to clusters
            #if typeString != 'CHANX' and typeString != 'CHANY':
            currentGraph = clusters[node.location[0]][node.location[1]]
            #else:
                #currentGraph = graph


            #if node.type == 1:
                #graph.attr('node', fillcolor='white')
            #elif node.type == 2:
                #graph.attr('node', fillcolor='grey')
            #elif node.type == 3:
                #graph.attr('node', fillcolor='yellow')

            #graph.attr('node', label= typeString + ': ' + str(node.id))

            currentGraph.node(str(node.id),label= typeString + ': ' + str(node.id) + ', Loc: '+ str(node.location) )


            #the edges don't need the exact graph prefix
            for nodeId in node.inputs:

                if nodeId == node.source:
                    color = 'blue'
                else:
                    #set it a bit transparent
                    color = "#0000003f"

                graph.edge(str(nodeId), str(node.id),color=color)

    #render the graph
    if globs.params.graphviz:

        #append the subgraph
        for i,clusterxList in enumerate(clusters):
            for j,cluster in enumerate(clusterxList):
                graph.subgraph(clusters[i][j])

        graph.render(filename + 'Graphviz')


def dumpTechnologyGraph(filename):

    f = open(filename, 'w')

    if globs.params.graphviz:

        #to prevent to many dependencies, we just load it when we must
        import graphviz as gv
        graph= gv.Digraph(format='png')


        #create subgraphs
        clusters = []
        pos = 1

        for i in range(0,globs.clusterx+1):
            clusterxList = []
            for j in range(0,globs.clustery+1):

                name = 'cluster_' + str(i) + '_' + str(j)
                cluster = gv.Digraph(name)

                cluster.node_attr.update(style='filled')
                cluster.body.append('label = '+ '\"' + name + '\"')
                cluster.body.append('color=blue')

                #sort the graph in the right order
                cluster.body.append('sortv=' + str(pos))
                pos += 1

                clusterxList.append(cluster)

            clusters.append(clusterxList)

    for node in globs.technologyMappedNodes.getNodes():

        #node got removed
        if node.type == 0:
            continue

        typeString= ''

        if node.type == 1:
            typeString= 'SINK'
        elif node.type == 2:
            typeString= 'SOURCE'
        elif node.type == 3:
            typeString= 'OPIN'
        elif node.type == 4:
            typeString= 'IPIN'
        elif node.type == 5:
            typeString= 'CHANX'
        elif node.type == 6:
            typeString= 'CHANY'
        elif node.type == 7:
            typeString= 'IMUX'
        elif node.type == 8:
            typeString= 'ELUT'
        elif node.type == 9:
            typeString= 'FFMUX'
        elif node.type == 10:
            typeString= 'IOMUX'

        f.write( '------------- new node ---------------\n')
        f.write( 'name: '       + str( node.name) + '\n')
        f.write( 'type: '     + str( node.type)  + ' (' + typeString + ')\n')
        f.write( 'location: ' + str( node.location)+ '\n')
        f.write( 'edges: '    + str( node.edges)+ '\n')
        f.write( 'inputs: '   + str( node.inputs)+ '\n')
        f.write( 'source: '   + str( node.source)+ '\n')
        f.write( 'elut: '     + str( node.eLUT)+ '\n')
        f.write( 'ffmux: '    + str( node.ffmux)+ '\n')
        f.write( 'passtrough: '   + str( node.passTrough)+ '\n')

        f.write( 'readPortDelay: '   + str( node.readPortDelay)+ '\n')
        f.write( 'writePortDelay: '   + str( node.writePortDelay)+ '\n')
        f.write( 'ioPathDelay: '   + str( node.ioPathDelay)+ '\n')
        f.write( 'ffReadPortDelay: '   + str( node.ffReadPortDelay)+ '\n')
        f.write( 'ffIODelay: '   + str( node.ffIODelay)+ '\n')



        if globs.params.graphviz:

            #skip these nodes
            #if (typeString == 'SOURCE' or  typeString == 'SINK' or typeString == 'IOMUX'):
            #    continue

            currentGraph = clusters[node.location[0]][node.location[1]]
            currentGraph.node(node.name,label= typeString + ': ' + node.name + ', Loc: '+ str(node.location) )


            #the edges dont need the exact graph prefix
            for nodeName in node.inputs:

                if nodeName == node.source:
                    color = "#FF0000FF"
                    #layer = 'top'
                else:
                    #set it a bit ransperent
                    color = "#0000003F"
                    #color = 'black'
                    #layer = 'bottom'

                graph.edge( nodeName, node.name,color=color)


    if globs.params.graphviz:

        #append the subgraph
        for i,clusterxList in enumerate(clusters):
            for j,cluster in enumerate(clusterxList):
                graph.subgraph(clusters[i][j])

        graph.render(filename + 'Graphviz')

def dumpBitPattern(bitpattern):
    for (i,row) in enumerate(bitpattern):
        for (j,entry) in enumerate(row):
            print( 'Pos: ' + str(i) +',' + str(j) + ' content: ' + str(entry))
