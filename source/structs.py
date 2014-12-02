#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	CAD Data Structure Definitions

#this corresponds to a routing node or eLUT
class Node():
	def __init__(self):
		self.id = -1
		self.edges = []
		self.location = []
		self.inputs = []
		self.source = -1
		self.eLUT = False
		self.LUT = 0#eLUT object
		self.config_generated = False
	
class Arch():
	def __init__(self):
		self.I = -1
		self.K = -1
		self.N = -1
		self.UseClos = 0
		
		
class Driver:
	def __init__(self, id, index=0,dir=0):
		
		self.id = id
		self.dir = dir
		self.index = index
		self.net = 'open'
	
		
class LUT:
	def __init__(self):
		self.size = 6
		self.output = ''
		self.inputs = []
		self.contents = ''
	def write_to_blif():
		#write to blif format as a LUT
		string = ''
		
		string = string + '.names'
		for i in inputs:
			string = string + i
		string = string + output + '\n'

		for pos, val in enum(content):
			if val is '1':
				string = string +  bin(pos) + ' 1\n'

class Cluster:
	def __init__(self):
		self.size = 8
		self.outputs = []
		self.inputs = []
		self.input_nets = []
		self.LUTs = []
		self.LUT_input_nets = []
		self.name = ''
		self.CLB = ''
		self.LUT_input_nodes = []
		
		self.LUT_nodes = []
		
	def do_local_interconnect(self):
		global LUTs
		
		
		
class IO:
	def __init__(self):
		self.outputs = []
		self.inputs = []
		self.name = ''
		
class Trace:
	def __init__(self, type = '', location = (), index = -1):
		self.type = type
		self.loc = location
		self.index = index
class Net:
	def __init__(self):
		self.source = []
		self.sinks = []
		self.trace = []
		self.name = ''
		
	def add_sink(self, x,y,pin_num):
		#self.sinks.append([x,y,pin_num])
		self.trace.append (Trace( 'SINK', (x,y),pin_num))
		
	def add_source(self, x,y,pin_num):
		#self.sinks.append([x,y,pin_num])	
		self.trace.append(Trace( 'SOURCE', (x,y),pin_num)	)	
	def add_section(self, dir, x1,y1,x2,y2, channel):
		self.trace.append(Trace(dir, (x1,y1,x2,y2), channel))
		

			
		
class SBox:
	def __init__(self):
		self.driversx = []		#NSEW
		self.driversy = []
