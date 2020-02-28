# use this if you want to include modules from a subforder.
# used for the unit tests to import the globs module
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"../")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import xml.etree.ElementTree as xml
import re
import globs

class NetlistCluster():
    def __init__(self):
        ##the netlist name of the Cluster.
        self.name = ""
        ## a list of netlist names.
        self.inputs = []
        ## a list of ble classes.
        self.bles = []

class NetlistBle():
    def __init__(self):
        ## a list of a input tuples: (mode, number)
        ##mode can be:
        ## 1) input, for a input of the cluster.
        ## number then describe the input pin number
        ## 2) ble, for the input of a other ble of this cluster
        ## number than describe the instance number of the ble.
        ## 3) open if its open. number is -1
        self.inputs = []
        ## a reference to a NetlistLut class
        self.lut = None
        ## a reference to a NetlistFlipflop class
        self.flipflop = None

class NetlistLut():
     def __init__(self):
         ##the netlist name of the lut.
         ##Is specified as the same as the netlist output name by vpr.
         self.name = ""

class NetlistFlipflop():
     def __init__(self):
         ##the netlist name of the Flipflop.
         ##Is specified as the same as the netlist output name by vpr
         self.name = ""

##parse the netlist file.
# return a list of NetlistCluster elements.
# @param filename The netlist file generated by vpr.
def parseNetlist(filename):

    netTree = xml.parse(filename)
    root = netTree.getroot()

    #parse the clusters and return the cluster object list
    return parseClusters(root)

def parseClusters(root):

    #result list of cluster objects
    netlistClusters = []

    #use Xpath notation for searching
    #get all cluster blocks
    clusterNodes = root.findall(".//block[@mode='clb']")

    for clusterNode in clusterNodes:
        netlistCluster = NetlistCluster()
        netlistCluster.name = clusterNode.get('name')

        inputs = clusterNode.findall('inputs')

        # write the cluster input names to the netlistCluster object.
        #TODO: why do we only take the last tag
        for i in inputs:
            for j in i.getiterator():
                netlistCluster.inputs = j.text.split()

        #now parse the bles in this cluster.
        ##the method will append them to the ble list ot this cluster
        parseBles(clusterNode,netlistCluster)

        #append the cluster to the result list
        netlistClusters.append(netlistCluster)

    return netlistClusters

##in vpr7 there can be empty ble tags.
##in vpr 6 these tags has a valid input structure filled with open ports.
##We have to setup this empty structure
def setupEmptyNetlistBle(netlistBle):
    for pinPosition in range(globs.params.K):
        #append an open pin representation
        netlistBle.inputs.append(('open',-1))


def parseBles(clusterNode,netlistCluster):
    #try to fin the ble nodes.
    #in vpr 7 the mode is not used for empty bles.
    #also the structure of an empty ble has changed a bit
    if globs.params.vprVersion == 8 or globs.params.vprVersion == 7:
        #TODO: this should be done wirh more error checking
        #maybe check the attribute instance
        bleNodes = clusterNode.findall("./block")
    elif globs.params.vprVersion == 6:
        #TODO: why go through all levels. we just need the
        #the first childs.
        bleNodes = clusterNode.findall(".//block[@mode='ble']")
    else:
        print "ERROR: Unsupported Vpr Version: " + str(globs.params.vprVersion)
        sys.exit(1)

    for bleNode in bleNodes:
        netlistBle = NetlistBle()

        #check if the ble is empty. this could be the case in vpr7
        if globs.params.vprVersion == 8 or globs.params.vprVersion == 7:
            #get all childs
            childs =  bleNode.findall('.//*')
            #there are no childs. build a empty bleNetlist
            if len(childs) == 0:
                print 'found an empty ble in a vpr7 way'
                setupEmptyNetlistBle(netlistBle)
                #append the ble to the cluster object
                netlistCluster.bles.append(netlistBle)
                #there is no need in checking the rest of this node
                continue

        #parse the input structure and append the
        #pin representation to the netlistBle input list
        parseBleInput(bleNode,netlistBle)

        #parse the lut and the flipflop of this ble
        #and append it to the ble object
        parseLut(bleNode,netlistBle)
        parseFlipflop(bleNode,netlistBle)
        #append the ble to the cluster object
        netlistCluster.bles.append(netlistBle)

##parse the input structure of a ble
def parseBleInput(bleNode,netlistBle):
    #find the input tags
    inputs = bleNode.findall('inputs')

    #parse the input netlist name of the ble.
    #it can have serval values which are now parsed
    for i in inputs:
        for j in i.getiterator():

            netlistInputs = j.text.split()
            for netlistInput in netlistInputs:

                nums = re.findall(r'\d+', netlistInput)

                #get an input from a ble of this cluster.
                #get the index of the ble instance
                if (netlistInput[0:3] == 'ble'):
                    netlistBle.inputs.append( ('ble', int(nums[0])))

                #get an input of a entity from another cluster.
                #get the Input pin Number of the cluster
                elif (netlistInput[0:3] == 'clb'):
                    ##if the vpr annotation is used, the cluster has a location prefix
                    if globs.params.vprAnnotation:
                        netlistBle.inputs.append( ('input', int(nums[2])))
                    else:
                        netlistBle.inputs.append( ('input', int(nums[0])))
                ##this pin is not driven
                elif (netlistInput[0:3] == 'ope'):
                    netlistBle.inputs.append( ('open', -1))

def parseLut(bleNode,netlistBle):
    #find the lut node. this is not the leaf.
    lutParentNode = bleNode.find(".//block[@mode='lut6']")
    if (lutParentNode is None):
        #in vpr 7 the lut block can be avoided if the ble is empty
        if globs.params.vprVersion == 8 or globs.params.vprVersion == 7:
            return

        print 'error in parseNetlist/paresLut: cannot find lut6 block' \
            +' in ble: ' +  bleNode.get('name')
        return

    #now find the leaf
    lutNode = lutParentNode.find("./block[@instance='lut[0]']")

    #there is no lut primitive. some error checking
    if (lutNode is None):
        if not (lutParentNode.get('name') == 'open'):
            print 'error in parseNetlist/paresLut: ble : ' \
                + bleNode.get('name') + ' dont use its lut, but isnt open'
            return
        else:
            print 'ble : ' + bleNode.get('name') + ' dont use its lut'

    #found a lut. append Lut object to ble.
    else:
        netlistLut = NetlistLut()
        netlistLut.name = lutNode.get('name')
        netlistBle.lut = netlistLut


def parseFlipflop(bleNode,netlistBle):
    #find the fliflop node.
    flipflopNode = bleNode.find(".//block[@instance='ff[0]']")
    #there must a flipflop tag
    if (flipflopNode is None):
        #in vpr 7 the flipflop block can be avoided if the ble is empty
        if globs.params.vprVersion == 8 or globs.params.vprVersion == 7:
            return

        print 'error in parseNetlist/paresFlipflop: cannot find fliflop block' \
            + ' in ble: ' +  bleNode.get('name')
        return
    #its there but isnt used
    if (flipflopNode.get('name') == 'open'):
         print 'ble : ' + bleNode.get('name') + ' dont use its flipflop'
    #there is a used flipflop. append it to the ble object
    else:
        netlistFlipflop = NetlistFlipflop()
        netlistFlipflop.name = flipflopNode.get('name')
        netlistBle.flipflop = netlistFlipflop

#you should provide a zuma config in your source file for this test.
def simpleTest():

    globs.init()
    globs.load_params()

    clusters = parseNetlist('netlistTest.net')
    for cluster in clusters:
        print 'cluster: ' +  cluster.name

        for input in cluster.inputs:
            print 'cluster input: ' + input

        bleCount = 1
        for ble in cluster.bles:
            print 'analyse ble ' + str(bleCount)

            for (name,number) in ble.inputs:
                print 'ble input: ' + name + ' ' + str(number)

            if (ble.lut is None):
                print 'no lut'
            else:
                print 'has lut: ' + ble.lut.name

            if (ble.flipflop is None):
                print 'no flipflop'
            else:
                print 'has flipflop: ' + ble.flipflop.name
            bleCount= bleCount +1
    print 'end test'

    print 'vpr8 test'

    clusters = parseNetlist('netlist.net.vpr8')
    for cluster in clusters:
        print 'cluster: ' +  cluster.name

        for input in cluster.inputs:
            print 'cluster input: ' + input

        bleCount = 1
        for ble in cluster.bles:
            print 'analyse ble ' + str(bleCount)

            for (name,number) in ble.inputs:
                print 'ble input: ' + name + ' ' + str(number)

            if (ble.lut is None):
                print 'no lut'
            else:
                print 'has lut: ' + ble.lut.name

            if (ble.flipflop is None):
                print 'no flipflop'
            else:
                print 'has flipflop: ' + ble.flipflop.name
            bleCount= bleCount +1
    print 'end test'

def main():
    simpleTest()

if __name__ == '__main__':
    main()
