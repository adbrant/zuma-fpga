from clos_routing  import *

import os
import random

#TODO: is this file deprecated? works it whith the new clos algo? 

random.seed(51)
route_clos([[random.randint(0,35) for i in range(6)] for j in range(8)],28,6,8)



for i in range(200, 2000):
	print '******************** New Round ***************************'
	print 'seed', i
	random.seed(i)
	
	list = []
	for j in range(8):
		rand = random.random()
		if rand < 0.2:
			list.append([])
		elif rand < 0.3:
			list.append([random.randint(0,35) for i in range(4)])
		elif rand < 0.5:
			list.append([random.randint(0,35) for i in range(5)])
		else:
			list.append([random.randint(0,35) for i in range(6)])
	print list
	route_clos(list,28,6,8)

	print '******************** End **********************************'
