# used for the unit tests to import the globs module
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"../")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import globs


class PlacementBlock:
    def __init__(self,location,name):
        ##the location tuple of the block
        self.location = location
        ##the netlist name
        self.name = name


##parser the placement file
#@return a list of placement blocks objects
def parsePlacement(filename):

    fh = open(filename,"r")

    blocks = []

    #skip the header, containing the cluster array size
    line = fh.readline()
    while len(line) > 0 :

        if line == '#----------\t--\t--\t------\t------------\n':
            break
        line = fh.readline()

    line = fh.readline()

    #now read the placement of the clusters
    #file structure:
    #block_name (in the netlist file) x y subblk block_number

    while len(line) > 0:
        entries = line.split()

        #create a block object and append it to the list
        location = (int(entries[1]), int(entries[2]))
        name = entries[0]
        block = PlacementBlock(location,name)
        blocks.append(block)

        line = fh.readline()

    return blocks

#you should provide a zuma config in your source file for this test.
def simpleTest():

    globs.init()
    globs.load_params()

    blocks = parsePlacement('place.p.vpr7')
    for block in blocks:
        print block.location
        print block.name

    print 'now vpr8'

    blocks = parsePlacement('place.p.vpr8')
    for block in blocks:
        print block.location
        print block.name


def main():
    simpleTest()

if __name__ == '__main__':
    main()
