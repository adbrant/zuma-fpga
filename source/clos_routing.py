#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#	Clos Routing and Generation



from structs import *
def build_clos(n_inputs, n_outputs, n,m,r, in_ids, nodelist,location):
	
	stage1nodes = []
	#first stage
	for i in range(r):#r crossbar
		for j in range(n): #m outputs
			clos_node =  node()
			for k in range(m):
				clos_node.inputs.append(in_ids[i*m+k])
			clos_node.id = len(nodelist+1)
			clos_node.location = location
			stage1nodes.append(clos_node)
			nodelist.append(clos_node)

	stage2nodes = []
	for i in range(m):#m crossbar
		for j in range(r): #m outputs
			clos_node =  node()
			for k in range(r):
				clos_node.inputs.append(stage2nodes[j*n+i].id)
			clos_node.id = len(nodelist+1)
			clos_node.location = location
			stage1nodes.append(clos_node)
			nodelist.append(clos_node)
			
	return [stage1nodes,stage2nodes] 
	
	
def route_clos(routing_vector,n,r,m):
	from parse_vpr import *

	#only setup for nxn networks right now	
	P = [[],[]] #permutation connections
	for lut in routing_vector:
		for i in lut:
			P[0].append(len(P[1]))
			P[1].append(i)
			
	#number of connections from first to third stage switch		
	H = [[0 for j in range(r)] for i in range(r)]		
	for j in range(r):
		for pin in routing_vector[j]:
			#input switch number
			i = int(pin/n)
			H[i][j] = H[i][j] + 1 

	#first stage is 8 6-by-6 crossbars (2 will be unused, for 6 6x6)
	stage1 = [[-1 for j in range(m)] for i in range(r)]
	#second stage is 6 8-by-8 crossbars (last 2 inputs will be unused for 6 6x8 crossbars(
	stage2 = [[-1 for j in range(r)] for i in range(m)]
	#last stage is 8 6x6 crossbars (actually eluts)
	#go through each pin
	success = 0
	supercount = 0
	import time
	starttime = time.clock()
	while success is 0:
		supercount = supercount +1
	
		in_to_out = [[] for i in range(36)]
		
		for i in range(len(routing_vector)):
			for pin in routing_vector[i]:
				in_to_out[pin].append(i)
				
		unrouted = []
		
		pins_to_route = [ i for i in range(len(in_to_out))]
		import random
		
		random.shuffle(pins_to_route)
		count = 0
		for pin in pins_to_route:
			random.shuffle(in_to_out[pin])
		while success is 0 and count < 80:
			unrouted = []
			count = count + 1
			
			nlist = [ i for i in range(m)]		
			random.shuffle(nlist)
			random.shuffle(pins_to_route)
			for pin in pins_to_route :
				x1 = int(pin/n)	
				
				
				for dest in in_to_out[pin]:		
					s1 = -1
					s2 = -1

					for i in nlist:
						if stage1[x1][i] is -1 or stage1[x1][i] is pin: #unused		
							#see if this will route to desired mux
							if stage2[i][dest] is -1 or stage2[i][dest] is pin: #unused
								stage1[x1][i] = pin
								stage2[i][dest] = pin
								s1 = i
								s2 = dest
								break
					if s1 is -1:
						
						unrouted.append((pin, dest))
			pins_to_route = []
			
			if len(unrouted) is 0:
				success = 1
				
			for pin, dest in unrouted:
				#rip up other routed pins to make room
				for i in range(1 + int(count/20)): #unroute more pins as we do more iterations
					pin_to_unroute = -1
					x1 = int(pin/n)	
					list = [ i for i in range(m)]
					random.shuffle(list)
					if random.random() < 0.6:
						for i in list:
							if stage2[i][dest] is -1:
								pin_to_unroute = stage1[x1][i]						
								break
					if random.random() < 0.06:
						pin_to_unroute = random.choice(range(36))
		
					if pin_to_unroute < 0:
						pin_to_unroute = stage2[random.randint(0,m-1)][dest]
					
					for i in range(r):
						for j in range(m):
							if stage1[i][j] is pin_to_unroute:
								stage1[i][j] = -1
							if stage2[j][i] is pin_to_unroute:
								stage2[j][i] = -1
					
					pins_to_route.append(pin_to_unroute)
				
				pins_to_route.append(pin)
				
				
	return [stage1, stage2]

	