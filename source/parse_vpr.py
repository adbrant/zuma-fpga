#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	VPR parsing and bitstream generation


import copy
import math
import re
from structs import *

#GLOBAL ROUTING STRUCTURES
chanx = []
chany = []
opin = []
ipin = []
inputs = []
outputs = []
LUTs = {}
params = Arch()
params.I = 16
params.N = 6
params.K = 5
params.config_width = 32
IOs = dict()
clusters = dict()
switchbox = dict()
config_pattern = []
host_size = 5
lut_contents = []
placement = []
clusterx = 0
clustery = 0
debug = False
nets = {}
nodes = []
cluster_nodes = []

def load_params():
	global params
	from zuma_config import *
	
	params = get_params()
def load_graph(filename):
	
	fh = open(filename,"r")
	global nodes
	nodes = []
	from const import *
	id = 0
	global clusterx, clustery
	while 1:
		line = fh.readline()
		if not line:
			break
		str = line.split()
		#print id, int(str[1])
		#assert(id is int(str[1]))
		n = Node()		
		n.id = int(str[1])
		if (str[2] == 'SINK'):
			n.type = 1
		elif (str[2] == 'SOURCE'):
			n.type = 2
		elif (str[2] == 'OPIN'):
			n.type = 3
		elif (str[2] == 'IPIN'):
			n.type = 4
		elif (str[2] == 'CHANX'):
			n.type = 5
		elif (str[2] == 'CHANY'):
			n.type = 6
		else:
			assert(0)
		
		
		nums = re.findall(r'\d+', line)
		nums = [int(i) for i in nums ]
	
		import time

		if n.type < 5 or len(nums) < 5:
			n.location = (nums[1],nums[2])
			n.index = nums[3]
		else:
			n.location = (nums[1],nums[2],nums[3],nums[4])
			n.index = nums[5]
			
		if n.type > 4:
			dir = line.split(' ')[-3]
			if dir == 'INC_DIRECTION':
				#north or east
				if n.type is 5:
					n.dir = E
				else:
					n.dir = N
			else:
				if n.type is 5:
					n.dir = W
				else:
					n.dir = S
		line = fh.readline()	
		nums = re.findall(r'\d+', line)
		n.edges = [int(i) for i in nums[1:]]
		#print 'node:', n.id, nums, 'edges', n.edges
		#time.sleep(1)
		line = fh.readline()
		line = fh.readline()
		line = fh.readline()
		line = fh.readline()
		line = fh.readline()
		
		
		
		clusterx = max(clusterx,n.location[0]) 
		clustery = max(clustery,n.location[1]) 
		nodes.append(n)
		if nodes[n.id] is not n:
			print 'graph error', len(nodes), n.id
		id = id + 1
	
	global switchbox
	global IOs
	global clusters
	
	for x in range(1, clusterx):
		for y in range(1, clustery):
			clusters[(x,y)] = Cluster()
	for x in range(0, clusterx):
		for y in range(0, clustery):
			switchbox[(x,y)] = SBox()		
	for x in [0, clusterx]:
		for y in range(0, clustery):
			IOs[(x,y)] = IO()
			
	for y in [0, clustery]:
		for x in range(0, clusterx):
			IOs[(x,y)] = IO()			
			
	
	for n in nodes:
		#print n.id, n.location
		for e in n.edges:
			nodes[e].inputs.append(n.id)
	for n in nodes:
		#collapse IPIN/OPINS with sinks/sources 
		#Fill patterns in connetion boxes and switches
		#create reverse edges for MUXing
		
		if n.type is 1: #SINK
			pass
		elif n.type is 2: #SOURCE
			pass
		elif n.type is 3: #OPIN
			if n.location[0] in [0, clusterx] or n.location[1] in [0, clustery]:
				#edge, thee are IOS
				IOs[n.location].inputs.append(Driver(n.id, n.index))
			else:
				#cluster
				clusters[n.location].outputs.append(Driver(n.id,n.index))
				print 'clust output', n.location, n.id
		elif n.type is 4: #IPIN
			if n.location[0] in [0, clusterx] or n.location[1] in [0, clustery]:
				#edge, thee are IOS
				if len(n.inputs) > 0: #dont get input from dangling node
					IOs[n.location].outputs.append(Driver(n.id))
				else:
					#IOs[n.location].outputs.append(Driver(n.id))
					print 'dropping node', n.id, 'from', n.location
			else:
				#cluster
				if len(n.inputs) > 0: #dont get input from dangling node
					clusters[n.location].inputs.append(Driver(n.id, n.index))
				else:
					print 'dropping node', n.id, 'from', n.location
		elif n.type is 5 or n.type is 6: #CHANX
			source = n.location[0:2]
			sbox = switchbox[source]
			if n.type is 5:
				sbox.driversx.append(Driver(n.id, n.index, n.dir))
			else:
				sbox.driversy.append(Driver(n.id, n.index, n.dir))
			for e in n.edges:
				nodes[e].type



		
def splitnums(string):
	string = string.replace('(','')
	string = string.replace(')','')
	return string.split(',')
	
	
def getchan(line):

	about = line.split()
	return int(about[-1])
	if line.find("inode") > -1:
		about = line.split()
		return int(about[5])
	
	else:
		about = line.split()
		return int(about[5])


		
		
		
		

		
		
def get_switch_pattern():
    # Loads the tracks_connected_to_pin array with an even distribution of     *
    # switches across the tracks for each pin.  For example, each pin connects *
    # to every 4.3rd track in a channel, with exactly which tracks a pin       *
    # connects to staggered from pin to pin.                                   */

    pass


def expandLUT(contents, size):
	#LUT content is compressed with '-' as dont cares
	#return string with truth table for every entry
	newcontent = []
		
	oldlines = contents	
	for i in range(size):
		#expand lines with don't cares to 2 lines
		newlines = []
		for line in oldlines:
			if line[i] is '-':
				line0 = copy.deepcopy(line)
				line1 = copy.deepcopy(line)
				line0[i] = '0'
				line1[i] = '1'
				newlines.append(line0)
				newlines.append(line1)
			else:
				newlines.append(line)
		
		oldlines = newlines
		
	lines = oldlines
	string = '0'*pow(2,size)

	for line in lines:
		string[int(line,2)] = 1
		
	return string		
	
def read_BLIF(filename):
	#read in blif file, store contents of LUTs for later use
	fh = open(filename,"r")
	line = fh.readline()
	global inputs, outputs, LUTs, debug	
	while len(line) > 0:
		
		if line.find(".model") > -1:
			line = fh.readline()
		
		elif line.find(".inputs") > -1:
			#read items until no more backslashes
			items = line.split(' ')[1:]
			#print items
			while items[-1] == '\\\n':
				items = items[:-1]
				nextline = fh.readline()
				items = items + nextline.split(' ')
			
			
			
			for item in items:
				inputs.append(item.strip())
			#inputs = inputs + items
			
			line = fh.readline()
			#print 'inputs', inputs
		elif line.find(".outputs") > -1:
			#read items until no more backslashes
			items = line.split(' ')[1:]
			while items[-1] == '\\\n':
				items = items[:-2]
				nextline = fh.readline()
				items = items + nextline.split(' ')
			for item in items:
				outputs.append(item.strip())
			
			line = fh.readline()
			
			
		elif line.find(".names") > -1:
			#these are the names of the input nets and output net
			items = line.split()[1:]
			innets = items[:-1]
			outnet = items[-1]
			newLUT = LUT()
			
			newLUT.output = outnet
			newLUT.inputs = innets
			line = fh.readline()
			items = line.split()
			contents = []
			#print items
			
			while items[-1] == '1' or items[-1] == '0' :
				contents.append((items[0],items[1])) 
				
				line = fh.readline()
				items = line.split()
				
			newLUT.contents = contents
			print newLUT.output,newLUT.inputs , newLUT.contents
			global LUTs
			LUTs[outnet] = newLUT
			
			#line = fh.readline()
		else:
			line = fh.readline()
	
	
	for i in LUTs:
		L = LUTs[i]
		print 'read blif', L.output, L.inputs,L.contents
		
		

			
			
			
def read_netlist(filename):
	import xml.etree.ElementTree as xml
	
	netTree = xml.parse(filename)
	root = netTree.getroot()
	inputs = root.findall('inputs')
	
	blocks = root.findall('block')
	global nodes, IOs, clusters, switchbox,clusterx, clustery, params, config_pattern
	for block in blocks:

		if block.get('mode') == 'clb':
			#here we have a clb
			#print block.get('name')
			cluster = 0
			loc = 0
			for key in clusters:
				if clusters[key].CLB == block.get('name'):
					cluster = clusters[key]
					loc = key
					break
			#print block.get('name') , loc
			cluster.name = block.get('name') 
			inputs = block.findall('inputs')
			for i in inputs:
				for j in i.getiterator():				
					cluster.input_nets = j.text.split()
				
			#print cl.inputs
			subblocks = block.findall('block')
			for sb in subblocks:
				if sb.get('mode') == 'ble':
					cluster.LUTs.append( sb.get('name'))
					cluster.LUT_input_nets.append([])
					inputs = sb.findall('inputs')
					for i in inputs:
						for j in i.getiterator():				
							net_names = j.text.split()
							for name in net_names:
								nums = re.findall(r'\d+', name)
								
								if name[0:3] == 'ble':
									cluster.LUT_input_nets[-1].append( ('ble', int(nums[0])))
								elif name[0:3] == 'clb':
									cluster.LUT_input_nets[-1].append( ('input', int(nums[0])))
								elif name[0:3] == 'ope':
									cluster.LUT_input_nets[-1].append( ('open', -1))
								else:
									print 'error unidentified net', name
			#print cl.LUTs
			
			#print block.get('name'), 
		#we don't need any info about IOs from this file
	
	
	
	
	

	for key in clusters:
		clust = clusters[key]
		#print key, clust.name, clust.input_nets, clust.LUTs
		
		#now we can build the local routing settings
		for net in clust.input_nets: #checking the routing matches our nets
			ind = -1
			if net == 'open':
				continue
			found = False	
			for i in clust.inputs:
				if i.net == net:
					found = True
					ind = clust.inputs.index(i)
			if not found:
				print 'net not found, cluster', key, net
				
				
		if 	params.UseClos:
			#build routing vector
			vector = []
			for i, LUT in enumerate(clust.LUT_input_nets):			
				for pin in range(params.K):
					net_id = LUT[pin]
					if net_id[0] == 'ble':
						vector.append(params.I+net_id[1])
					elif net_id[0] == 'input':
						vector.append(net_id[1])
					elif net_id[0] == 'open':
						vector.append(-1)
					else:
						assert(0)
						
			
			from clos_routing import build_clos
			routing = route_clos(vector, params.K, params.N, params.K)
			i = 0
			for xbar in routing[0]:
				for switch in xbar:
					nodes[clust.clos[0][i]].source = switch
					i = i + 1	
			for xbar in routing[1]:
				for switch in xbar:
					nodes[clust.clos[1][i]].source = switch
					i = i + 1	
		else:
			#for each LUT input, set input number:
			for i, LUT in enumerate(clust.LUT_input_nets):
			
				for pin in range(params.K):
					net_id = LUT[pin]
					if net_id[0] == 'ble':
						nodes[clust.LUT_input_nodes[i][pin]].source = clust.LUT_nodes[net_id[1]] 
					elif net_id[0] == 'input':
						
						nodes[clust.LUT_input_nodes[i][pin]].source = clust.inputs[net_id[1]].id
					elif net_id[0] == 'open':
						pass
					else:
						assert(0)
		# for each eLUT, set the bit configuration:
		for i, LUT in enumerate(clust.LUTs):
			lutname = LUT
			#print lutname
			global LUTs
			if lutname in LUTs:
				nodes[clust.LUT_nodes[i]].eLUT = True
				nodes[clust.LUT_nodes[i]].bits = LUTs[lutname].contents
				nodes[clust.LUT_nodes[i]].LUT = LUTs[lutname]
			else:
				print 'Error cannot find LUT', lutname 
				for l in LUTs:
					print l
				assert(0)
			#find this LUT configuration in the
		
	placed_luts = []
	for key in clusters:
		cl = clusters[key]
		
		#print key,
		for node in cl.LUT_nodes:
			if nodes[node].LUT:
				placed_luts.append(nodes[node].LUT.output) 
				#print nodes[node].LUT.output,
		#print ''
	#confirm no LUTs are missing from BLIF
	for key in LUTs:
		if key not in placed_luts:
			if len(LUTs[key].inputs) > 1:
				print 'error LUT not placed', key
			
			else:
				print 'empty lut not placed', key, LUTs[key].inputs
		'''
	for element in netTree.getiterator():
		if 'mode' in element.keys():
			print element.get('mode')
	for input in inputs:
		print input.text
	'''	

		
		
def read_placement(filename):		
	
	fh = open(filename,"r")
	
	line = fh.readline()
	while len(line) > 0 :
		if line.split(' ')[0] == 'Array':
			global clusterx, clustery

		if line == '#----------	--	--	------	------------\n':
			break
		line = fh.readline()
	
	line = fh.readline()
	global clusters, placement, clusterx,clustery

	
	
	while len(line) > 0:
		entries = line.split()
		#if 'i' in entries[0] or 'o' in entries[0]:
		if int( entries[1] )in [0, clusterx] or int( entries[2] ) in [0, clustery]:
			pass #skip ios
		else:
			
			clusters[(int(entries[1]), int(entries[2])) ].CLB = entries[0] #name and location 
			#placement[int(entries[1])][int(entries[2])] = entries[0]
		
		line = fh.readline()
			
	
	
	"""	
	for row in placement:
		pprint = ''
		for place in row:
			pprint = pprint + place + '\t'
			
		print pprint
	"""
	
	


		
def read_routing(filename ):
	fh = open(filename,"r")
	igot = fh.readlines()
	
	#size of the array
	x = int(igot[0].split(' ')[2])+1
	y = int(igot[0].split(' ')[4])+1
	width = x
	channels = 0
	opins = 0
	ipins = 0
	
	#find channel width
	for i,line in enumerate(igot):

		if line.find("CHAN") > -1:
			about = line.split()
			c1 = getchan(line)
			if c1 + 1 > channels:
				channels = c1 + 1	

	in_net = False
	chanx = [[[[] for i in range(channels)] for col in range(width)] for row in range(width)]
	chany = [[[[] for i in range(channels)] for col in range(width)] for row in range(width)]
	opin = [[[[] for i in range(opins)] for col in range(width)] for row in range(width)]
	ipin = [[[[] for i in range(ipins)] for col in range(width)] for row in range(width)]
	
	


	lastchan = [-1, -1,-1,-1]
	thischan = [-1, -1,-1,-1]
	intrace = False
	signal = ''
	
	#we will build a net for each traced signal
	global nets
	routing_net = 0
	for i,line in enumerate(igot):
		if line.find("Net") > -1:
			signal = line.split('(')[1].split(')')[0]
			
			routing_net = Net()
			nets[signal] = routing_net
			routing_net.name = signal
		if line.find("OPIN") > -1:
		
			about = line.split()
			nums = splitnums(about[1])
			x1 = int(nums[0])
			y1 = int(nums[1])
	

			nums = splitnums(about[3])
			pin = int(nums[0])
			if len(routing_net.source) is 0:
				routing_net.source = [x1,y1,pin] 	
				routing_net.add_source(x1,y1,pin)
			else:
				routing_net.add_source(x1,y1,pin)
		if line.find("IPIN") > -1:
		
			about = line.split()
			nums = splitnums(about[1])
			x1 = int(nums[0])
			y1 = int(nums[1])
	

			nums = splitnums(about[3])
			pin = int(nums[0])
			
			routing_net.add_sink(x1,y1,pin)
			
				
			
		if line.find("CHANX") > -1:
			about = line.split()
			nums = splitnums(about[1])
			x1 = int(nums[0])
			y1 = int(nums[1])
			x2 = -1
			y2 = -1
			if len(about) >= 6:
				nums = splitnums(about[3])
				x2 = int(nums[0])
				y2 = int(nums[1])		
			
				
			c1 = getchan(line)	
			routing_net.add_section('X', x1,y1,x2,y2, c1)
			
			
		if line.find("CHANY") > -1:
			about = line.split()
			
			nums = splitnums(about[1])
			x1 = int(nums[0])
			y1 = int(nums[1])
			
			x2 = -1
			y2 = -1
			if len(about) >= 6:
				nums = splitnums(about[3])
				x2 = int(nums[0])
				y2 = int(nums[1])
			
			c1 = getchan(line)
		
			routing_net.add_section('Y', x1,y1,x2,y2, c1)
		
	#we now should have all routed signals in nets
	
	global swithbox, nodes, clusters, IOs, params, clusterx, clustery
	for n in nets.values():
		#print 'net: ',n.name
		nodelist = []
		
		if n.source[0] in [0, clusterx] or n.source[1] in [0, clustery]:
			#edge, thee are IOS
			for input in IOs[tuple(n.source[0:2])].inputs:
				if input.index is n.source[2]:
					last_node = input.id
					break
		else:
			#cluster
			last_node = clusters[tuple(n.source[0:2])].outputs[n.source[2] - params.I].id
		nodelist.append(last_node)
	
		#print len(n.trace)
		for trace in n.trace:
		
	
			#find sbox or sink
			#[dir, x1,y1,x2,y2, channel])
			drivers = []
			

			if trace.type == 'X':
				#print trace[-1], len(switchbox[tuple(trace[1:3])].driversx)
				drivers = switchbox[tuple(trace.loc[0:2])].driversx
				
			elif trace.type == 'Y':
				drivers = switchbox[tuple(trace.loc[0:2])].driversy
			elif trace.type == 'SINK':

				
				if trace.loc[0] in [0, clusterx] or trace.loc[1] in [0, clustery]:
					#edge, these are IOS
					
					
					for output in IOs[trace.loc].outputs:
						if output.index is trace.index:
							output.source = last_node
							output.net = n.name
							nodes[output.id].source = last_node
							
							if last_node not in nodes[output.id].inputs:
								print 'error routing', output.id, last_node
							break
							
					
				else: #cluster	
					for input in clusters[trace.loc].inputs:
						if input.index is trace.index:
							if input.id  in nodes[last_node].edges:
							
								input.source = last_node
								input.net = n.name		
								nodes[input.id].source = last_node
							else:
								print n.name, trace.loc, input.index 
								print 'error node', last_node, input.id
								print nodelist
								assert(0)
				continue
			else: #SOURCE
				if trace.loc[0] in [0, clusterx] or trace.loc[1] in [0, clustery]:
					#edge, these are IOS
					found = False
					for input in IOs[trace.loc].inputs:
						if input.index is trace.index:
							input.net = n.name
							last_node = input.id
							found = True
							break
							
					if found == False:
						print 'Error finding FPGA input', n.name, 'at', trace.loc
				else:
					#cluster
					for output in clusters[tuple(trace.loc)].outputs:
						if output.index is trace.index:
							last_node = output.id
			
				continue
			#chanx or y 	
			for d in drivers:
				if d.index is trace.index:
					driver = d
					break
			if driver.id in nodelist:
				pass
			else:
				if driver.id  in nodes[last_node].edges:
					#success!
					driver.source = last_node
					driver.net = n.name
					nodes[driver.id].source = last_node
					
				else:
					print "error routing", last_node, driver.id, nodes[last_node].edges
				nodelist.append(driver.id)
			last_node = driver.id
			



def list_to_vector(names):
	string = '{'
	for n in names:
		string = string + n + ','
	string = string[0:-1] + '}'
	return string
	

			
def build_global_routing_verilog(filename):
	f = open(filename, 'w')
	global nodes, IOs, clusters, switchbox,clusterx, clustery, params, config_pattern, host_size
	numinputs = 0
	numoutputs = 0
	for key in IOs:
	
		numinputs = numinputs + len(IOs[key].inputs)
		numoutputs = numoutputs + len(IOs[key].outputs)
		
	header = """
	`include "define.v"
	//XUMA global routing Entity
	//automatically generated by script 
	module XUMA_custom_generated
	#(
	"""
	f.write(header)

	f.write('parameter N_NUMLUTS = ' + str(params.N) + ',\n')
	f.write('parameter I_CLINPUTS = ' + str(params.I) + ',\n')
	f.write('parameter K_LUTSIZE  = ' + str(params.K) + ',\n')
	f.write('parameter CONFIG_WIDTH  = ' + str(params.config_width)+ '\n')

	config_width = params.config_width
	config_row = []
	header2 = """
	 )
	(
	clk,
	fpga_inputs,
	fpga_outputs,
	config_data,
	config_en,
	progress, 
	config_addr
	);
	"""
	f.write(header2)
	
	string = 'input [' + str(numinputs) +'-1:0]fpga_inputs;\n'
	f.write(string)
	string = 'input [' + str(32) +'-1:0]config_data;\n'
	f.write(string)
	string = 'input [CONFIG_WIDTH-1:0]config_addr;\n'
	f.write(string)
	string = 'input config_en;\n'
	f.write(string)
	string = 'output [ ' +  str(numoutputs)+ '-1:0]fpga_outputs;\n'
	f.write(string)
	string = 'output [15:0] progress;\n'
	f.write(string)
	f.write('wire [4096:0] wren;\n')
	f.write('wire [5:0]wr_addr;\n')
	f.write('wire [CONFIG_WIDTH-1:0] wr_data;\n')
	f.write('input clk;\n')


	
	
	f.write('assign wr_data = config_data;\n');
	config_row = []	
	build_all = True #build the clusters
	global cluster_nodes

	
	registers = []
	count = len(nodes)
	
	for key in clusters:
		cluster = clusters[key]	
		if 	params.UseClos:
			#make nodes for internal cluster crossbar
			#make nodes for each lut input
			
			lut_outs = []
			import clos_routing
			import math
			
			#build the clos network for this cluster
			num_in = params.N + params.I
			num_out = params.N*params.I
			size = max(num_in, num_out)
			n = params.K
			m = params.K
			r = params.N
			inputs = []
			for i in cluster.LUT_input_nodes[lut]:
				inputs.append(i)
					
			location = nodes[inputs[0]]
			cluster.clos = clos_routing.build_clos(num_in, num_out, n,m,r, inputs, nodes, location)
			
			lut_outs = []		
			for lut in range(params.N):				
				#actual eLUT
				inode = Node()
				inode.type = 8
				for i in cluster.clos[1][lut*params.k:(lut+1)*params.k -1]:
					inode.inputs.append(i.id)
				inode.location = key
				inode.id = count
				inode.eLUT = True
				nodes.append(inode)
				count = count + 1
				lut_outs.append(inode.id)
				cluster.LUT_nodes.append(inode.id)
			


		else:
			#make nodes for internal cluster connection
			#make nodes for each lut input
			for lut in range(params.N):
				templist = []
				cluster.LUT_input_nodes.append([])
				for pin in range(params.K):#input nodes
					
					inode = Node()
					inode.type = 7
					
					for i in cluster.inputs:
						inode.inputs.append(i.id)
					
					inode.location = key
					inode.id = count
					nodes.append(inode)
					count = count + 1
					templist.append(inode.id)
					cluster.LUT_input_nodes[lut].append(inode.id)
		
			lut_outs = []		
			for lut in range(params.N):				
				#actual eLUT
				inode = Node()
				inode.type = 8
				for i in cluster.LUT_input_nodes[lut]:
					inode.inputs.append(i)
				inode.location = key
				inode.id = count
				inode.eLUT = True
				nodes.append(inode)
				count = count + 1
				lut_outs.append(inode.id)
				cluster.LUT_nodes.append(inode.id)
				
		
		for lut in range(params.N):
			for pin in range(params.K):
				id = cluster.LUT_input_nodes[lut][pin]					
				for lut2 in range(params.N):
					nodes[id].inputs.append(cluster.LUT_nodes[lut2])
			
		
	for node in nodes:
		#create nets
		string = 'wire node_' + str(node.id) + ';\n'
		f.write(string)
		
	for key in clusters:
		cl = clusters[key]
		for n in range(params.N):
			lut_id = cl.LUT_nodes[n]
			opin_id = cl.outputs[n].id
			f.write('assign node_' + str(opin_id) + ' = node_' + str(lut_id) + ';\n')
			
	total_luts = 0	
	for node in nodes:
		if len(node.inputs) < 1:
			#print node.id
			
			
			continue
		node_prefix = 'node_'	
		if len(node.inputs) == 1:
			#print node.id
			if node.type is 5 or node.type is 6: #other cases (IOs) are already dealt with
				f.write('assign ' + node_prefix + str(node.id) + ' = ' + node_prefix + str(node.inputs[0]) + ';\n');
				#todo is this needed?
				pass
			continue
		#create muxes
		n = node
		
		
		mux_prefix = 'mux_'
		if node.type < 3:
			continue
		elif n.type is 3: #OPIN
			if n.location[0] in [0, clusterx] or n.location[1] in [0, clustery]:
				#edge, thee are IOS
				f.write('//FPGA input at ' + str(n.location) + '\n')
			else:
				#cluster
				f.write('//cluster output at ' + str(n.location) + '\n')
		elif n.type is 4: #IPIN
			if n.location[0] in [0, clusterx] or n.location[1] in [0, clustery]:
				#edge, thee are IOS
				f.write('//FPGA output at ' + str(n.location) + '\n')
			else:
				#cluster
				f.write('//cluster input at ' + str(n.location) + '\n')
		elif n.type is 5 or n.type is 6: #CHANX
			if n.type is 5:
				f.write('//sbox driver x at  ' + str(n.location) + '\n')
			else:
				f.write('//sbox driver y at ' + str(n.location) + '\n')
		else:
			f.write('//internal cluster node at  ' + str(n.location) + '\n')
			mux_prefix = 'c_mux_'
			
		f.write('//size: ' + str(len(n.inputs)) + 'inputs: ' + str(n.inputs) + '\n')

		mux_size = len(node.inputs)
		
		def write_LUTRAM(f, name, input_names, output_name,  config_offset, config_stage):
			global host_size
			while len(input_names) < host_size:
				input_names.append("1'b0")
			string ='''
			lut_custom ''' + name + ''' (
			.a(wr_addr), // input [5 : 0] a
			.d(wr_data[''' + str(config_offset) + ''']), // input [0 : 0] 
			'''
			f.write(string)
						
			string = '.dpra(' + list_to_vector(input_names) + '), // input [5 : 0] dpra'
			f.write(string)
						
			f.write('''
			.clk(clk), // input clk
			.we(wren[''' + str(config_stage) + ''']), // input we
			''')
			
			f.write( '.dpo(' + output_name + '));\n')
			
			
		import math	
		num_luts = int(math.ceil((mux_size-host_size)/(host_size-1.0)) + 1)
		total_luts = num_luts + total_luts
		if num_luts + len(config_row) >= config_width:
			config_pattern.append(config_row)
			config_row = []
				
		if mux_size <= host_size:
			write_LUTRAM(f, mux_prefix + str(node.id), [(node_prefix + str(i)) for i in node.inputs], node_prefix + str(node.id), 
				len(config_row), len(config_pattern) )
			config_row.append( node.id)
		

			
		elif mux_size <= host_size*host_size:
			#find number of LUTs needed
			# max lutsize = 6+5*(n-1)
			
			num_luts = int(math.ceil((mux_size-host_size)/(host_size-1.0)) + 1)
			count = 0
			mux_nodes = []			
			for n in range(num_luts - 1):
				node_name = node_prefix + str(node.id) + '_' + str(count)
				f.write( '\t\t\twire ' + node_name + ';\n')
				mux_nodes.append(node_name)
				write_LUTRAM(f, mux_prefix + str(node.id) + '_' + str(count), [(node_prefix + str(i)) for i in node.inputs[count:count+host_size]], node_name,
						len(config_row), len(config_pattern) )
				count = count + host_size				
				config_row.append( node.id)
			write_LUTRAM(f, mux_prefix + str(node.id), mux_nodes + [(node_prefix + str(i)) for i in node.inputs[count:]], node_prefix + str(node.id) ,
				len(config_row), len(config_pattern) )	
			config_row.append( node.id)
		else:
			#need to code if we ever need this			
			print 'MUX', node.id, 'too large', mux_size			
			assert(0)
		
	
	config_pattern.append(config_row)
	
	configfile = open('configpattern.txt', 'w')
	for row in config_pattern:
		for item in row:
			configfile.write(str(item)+ ' ')
			
		configfile.write('\n')
	
	configfile.close()
	print 'total luts: ', total_luts	
	#print 	config_pattern
	for key in clusters:
		cluster = clusters[key]	
		if 	build_all:
			pass
				
		else:
			string = '''
			logic_cluster_custom
			#(
				.INPUTS(I_CLINPUTS),
				.OUTPUTS(N_NUMLUTS),
				.LUTSIZE(K_LUTSIZE),
				.NUMLUTS(N_NUMLUTS)
			 )
			'''
			
			f.write(string)
			
			f.write('cluster_'+ str(key[0]) + '_' + str(key[1]))
			
			f.write('''		
			(
			.clk(clk),
			''')
			

			string = '.data_inputs({'
			for i in cluster.inputs:			
				string = string + 'node_' + str(i.id) + ','
			string = string[0:-1]
			string = string + ' }),\n'
			f.write(string)

			string = '.data_outputs({'
			for i in cluster.outputs:			
				string = string + 'node_' + str(i.id) + ','
			string = string[0:-1]
			string = string + ' }),'
			f.write(string)

			f.write('''.wr_addr(wr_addr),
			.wr_data(wr_data),
			.wren(wren)
			);\n\n''')
		
	count = 0	
	for key in IOs:
		IO = IOs[key]
		for i in IO.outputs:
			f.write('assign fpga_outputs[' + str(count) + '] = node_' + str(i.id) + ';\n')
			count = count+1
	count = 0	
	for key in IOs:
		IO = IOs[key]
		for i in IO.inputs:
			f.write('assign node_' + str(i.id) + ' = fpga_inputs[' + str(count) + '];\n')
			count = count+1	


	f.write('parameter NUM_CONFIG_STAGES = ' + str(len(config_pattern)) + ';')
	string = """
	config_controller_simple
	#(
		.WIDTH(CONFIG_WIDTH),
		.STAGES(NUM_CONFIG_STAGES),
		.LUTSIZE(K_LUTSIZE)
	 )
	 configuration_ctrl
	(
		.clk(clk),		
		.reset(1'b0),
		.wren_out(wren),
		.progress(progress),
		.wren_in(config_en),
		.addr_in(config_addr),
		.addr_out(wr_addr)
	);
	"""		
	f.write(string)
	f.write('endmodule')
	
def build_passthrough(width, offset):
	length = int(math.pow(2,width))
	bits = []
	offset2 = width - 1 - offset #reverse order
	for i in range(length):
		if (i >> offset2) % 2:
			bits.append('1')
		else:
			bits.append('0')
	
	#print bits	
	return bits
	

	
def build_lut_contents(width, LUT, cluster,pos):
	length = int(math.pow(2,width))
	
	
	#first we need to map our input pins to the ports from the blif
	
	pins = []
	#print 'LUT', LUT.output
	for name in LUT.inputs:
		pin_name = ''
		found = False
		for i, net in enumerate(cluster.LUT_input_nets[pos]):
			if net[0] == 'ble':
				pin_name = cluster.LUTs[net[1]]
			elif net[0] == 'input':
				pin_name = cluster.input_nets[net[1]]
			elif net[0] == 'open':
				continue
			else:
				#print net[0]
				assert(0)
			if pin_name == name:
				#we have a winner
				pins.append(i)
				#print 'input', name, 'source',net[0], net[1], 'input pin', i
				found = True
				break
				
		if not found:
			print 'error in', LUT.output, name
			
	bits = []
	for i in range(length):
		#is this postition 0 or 1
		bit_vals = []
		setting = 0
		
		for j in range(width):
			bit_vals.append((i>>(width-j-1))%2)
		
		for line in LUT.contents:
			
			#is this line false?
			correct = 1
			if line[1] is '1':
				for p, val in enumerate(line[0]):
					#need pin num of pos
					pin = pins[p]
					if val is '-':
						pass
					elif bit_vals[pin] is int(val): 
						pass
					else:
						correct = 0
						break
			elif line[1] is '0':
				z_correct = 0
				for p, val in enumerate(line[0]):
					#need pin num of pos
					pin = pins[p]
					if val is '-':
						pass
					elif bit_vals[pin] is int(val): 
						pass
					else:
						z_correct = 1
						break
				correct = z_correct and correct
			else:
				assert(0)
				
			#print i, pins,bit_vals, line, 	correct
			if correct:
				#print bit_vals, pins, line
				setting = 1
				break
			
		bits.append(setting)
		
	#print LUT.output, cluster.name, pos
	#print bits
	return bits

		
def build_bitstream(filename):
	global config_pattern, nodes, host_size, clusters, params
	last_node = -1
	lut_len = int(math.pow(2, host_size))
	bit_pattern = []
	
	placed_luts = []
	for row in config_pattern:
		#for each row of write data
		bit_row = []
		for col in row:
			#for each LUTRAM
			

			if col is last_node:
				#for muxes that span multiple lutrams
				continue
				
				
			last_node = col	
			node = nodes[col]
			
			if node.eLUT:			
				if node.LUT: #has a configuration
					cl = clusters[node.location]
					index = cl.LUTs.index(node.LUT.output)
					print 'Logic lut', node.LUT.output, index, cl.LUTs, node.LUT.contents, node.LUT.inputs

					bits = build_lut_contents(host_size, node.LUT, cl, index)
					bit_row.append(bits)

					placed_luts.append(node.LUT.output)	
					
				else:
					bit_row.append([])
				
				node.config_generated =	True
				continue
			
			
				
			num_luts =  int(math.ceil((len(node.inputs)-host_size)/(host_size-1.0)) + 1)
			index = -1
			if node.source is -1: #not driven
				for i in range(num_luts):
					bit_row.append([])
					
				node.config_generated = True
				continue
				
			if node.source not in node.inputs:
				print 'error at node' , node.id, node.source, node.inputs
				break
					
			if num_luts is 1: 
				bit_row.append(build_passthrough(host_size,node.inputs.index(node.source) ))

			else:
				#build multilutram mux
				index = node.inputs.index(node.source)
				
				
				last_index = -1
				for n in range(num_luts - 1):
					if index in range(n*host_size, (n+1)*host_size):
						bit_row.append(build_passthrough(host_size,index - n*host_size ))
						last_index = n
					else:
						bit_row.append([])
				if 	last_index	is -1:
					config = build_passthrough(host_size,index-(num_luts-1)*host_size+(num_luts-1))
					bit_row.append(config)
					
					if node.id == 323:
						print node.id, index, num_luts, host_size, index-(num_luts-1)*host_size+(num_luts-1)
						print config
				else:
					bit_row.append(build_passthrough(host_size,last_index))
			node.config_generated = True
		bit_pattern.append(bit_row)
	
	#check weve done all configuration
	unconfiged = []
	for node in nodes:
		if node.config_generated is False and len(node.inputs) > 1 and node.type > 2:
			unconfiged.append(node.id)
			for row in config_pattern:
				if node.id in row:
					pass#print node.id, row
			
			
	if len(unconfiged) > 0:		
		print 'Nodes skipped in bitstream' ,  unconfiged

	global LUTs
	for key in LUTs:
		if key not in placed_luts:
			if len(LUTs[key].inputs) > 1:
				print 'error LUT not cofigured' , key	
				
			else:
				print key, LUTs[key].inputs
	#build hex file

	import struct
	
	
	binfile = open(filename, 'wb')
	sysfile = open('config_script.tcl', 'wb')
	
	sysfile.write('master_write_8 0x01000000 [')
	byte_data = ''
	bytes_per_row = params.config_width/8
	current_addr = 0
	for row in bit_pattern:
		for i in range(lut_len):
			string = ''
			for entry in row:
				
				if len(entry) is lut_len:
					if str(entry[i]) not in ['0','1']:
						print 'error in bits', entry[i]
					string = string + str(entry[i])
				elif len(entry) is 0:
					string = string + '0'
				else:
					string = string + '0'
					print 'row length is', len(entry), lut_len, entry
			while len(string) < params.config_width:
				string = string +'0'
			#print string
			
			def hex_n(i,n):
				st = hex(i)[2:]
				while len(st) < n:
					st = '0' + st
				if len(st) > n:
					print 'overflow for hex conversion of',i,'length',n
					st = st[len(st)-n:]
				return st
				
			checksum = 0
			line = ''
			
			line = line + hex_n(bytes_per_row,2) #number of bytes
			checksum = checksum + bytes_per_row
			line = line + hex_n(current_addr,4) #number of bytes
			line = line + '00' #record type (data)
			current_addr = current_addr + bytes_per_row
			for i in range(int(bytes_per_row)):
				byte = int(string[i*8:(i+1)*8],2)
				#char = chr(byte)
				#byte_data = byte_data+char
				#data = struct.pack('i', byte)
				
				#sysfile.write(hex(byte) + ' ')
				#binfile.write(data)
				line = line + hex_n(byte,2) 
			
			checksum = 0
			for i in range(len(line)/2):
				byte = line[i*2:i*2+2]
				num = int(byte, 16)
				checksum = checksum + num
				
			
			line = line + hex_n((256 - (checksum % 256))%256,2)
			line = ':' + line + '\n'
			binfile.write(line)
	binfile.write(':00000001FF\n')
	sysfile.write(']\n')



def output_blif(filename):
	#write BLIF of zuma design for verification
	f = open(filename, 'w')
	f.write('.model top\n')
	global inputs, outputs, nodes, clusters, params
	
	string = '.inputs '
	for i in inputs:
		string = string + str(i) + ' '
	string = string + '\n'
	f.write(string)
	
		
	string = '.outputs '
	for i in outputs:
		string = string + str(i) + ' '
	string = string + '\n'	
	f.write(string)	
	
	global IOs
	
	
	#assign correct nodes to IOs
	for key in IOs:
		IO = IOs[key]
		for output in IOs[key].outputs:
			if len(output.net) > 0 and output.net != 'open':
				print 'FPGA output', output.net
	
				f.write(' .names ') 
			
				f.write('[' + str(output.id) + '] ' + '' + str(output.net) + ' ' + '\n')
				f.write('1 1\n')
				
				
		for input in IOs[key].inputs:
			if len(input.net) > 0 and input.net != 'open':
				print input.net
	
				f.write(' .names ') 
			
				f.write('' + str(input.net) + ' ' + '[' + str(input.id) + '] ' + '\n')
				f.write('1 1\n')		
				
				
	# build global routing assignments for each MUX or LUT
	for node in nodes:
		if node.eLUT:			
			if node.LUT: #has a configuration
				cl = clusters[node.location]
				index = cl.LUTs.index(node.LUT.output)
				
				f.write(' .names ')
				for i in node.inputs:
					 f.write('[' + str(i) + '] ')
				f.write('[' + str(cl.outputs[index].id) + ']\n')	 
			
				bits = build_lut_contents(host_size, node.LUT, cl, index)
				
				for i in range(len(bits)):
					if bits[i]:
						for j in range(params.K):
							f.write (str(i>>(params.K-j-1) & 1))
						f.write(' ' +  str(bits[i]) + '\n')
				

			else:
				pass
			
			node.config_generated =	True
			continue
		
		if node.source < 0:
			continue
		#make simple passthru logic
		f.write(' .names ') 
		
		f.write('[' + str(node.source) + '] ' + '[' + str(node.id) + '] ' + '\n')
		f.write('1 1\n')

		
	for key in clusters:
		cl = clusters[key]
		for n in range(params.N):
			lut_id = cl.LUT_nodes[n]
			opin_id = cl.outputs[n].id
			f.write(' .names ') 
			f.write('[' + str(opin_id) + '] ' + '[' + str(lut_id) + '] ' + '\n')
			f.write('1 1\n')
	print nodes[506].id,  nodes[506].inputs
		
