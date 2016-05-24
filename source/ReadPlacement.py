from structs import *
import globs

## Parse the placement file and transfer the information to internal structures.
# The placement file contains the location of the different cluster
# and their netlist names.
# These names are later used in the netlist file,
# which describe the inner routing of each cluster.
# So we parse this names for the later parsing of the netlist.
# @param filename The filename of the placement file, e.g place.p.
def read_placement(filename):

    fh = open(filename,"r")

    #skip the header, containing the cluster array size
    line = fh.readline()
    while len(line) > 0 :
        if line.split(' ')[0] == 'Array':
            #global clusterx, clustery
            pass

        if line == '#----------\t--\t--\t------\t------------\n':
            break
        line = fh.readline()

    line = fh.readline()

    #now read the placement of the clusters
    #file structure:
    #block_name (in the netlist file) x y subblk block_number

    while len(line) > 0:
        entries = line.split()
        # skip ios
        if int( entries[1] )in [0, globs.clusterx] \
        or int( entries[2] ) in [0, globs.clustery]:
            pass
        #write the name of the block in an Cluster object
        else:
            #write the netlist name in the correct location of the cluster array
            globs.clusters[(int(entries[1]), int(entries[2])) ].CLB = entries[0] #name

        line = fh.readline()
