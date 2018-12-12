#	ZUMA Open FPGA Overlay
#	Alex Brant 
#	Email: alex.d.brant@gmail.com
#	2012
#   Clos Routing and Generation
    
import math
import random
import sys

def route_clos(routing_vector,I,k,N):
    
    #In the current tested state, I+N must be divisible by k
    if (((I+N) % k) != 0):
        print "\n\n--------------  ERROR -----------------------"
        print "In the current state, only values for I and N" + \
              " are supported where I+N is dividable by k"
        print  "---------------------------------------------"
        sys.exit(0)

    #set the count of first stage crossbars
    P = int(math.ceil( (N + I)/ k))
    
    #first stage: r=P crossbars with k=m input pins
    #this list describe the mapping, between the output pins of this stage
    #and the interconnection block input pins.
    #so we have P lists in this list with k outputs containing the 
    #input pin number
    stage1 = [[-1 for j in range(k)] for i in range(P)]
    
    #second stage: m=k crossbars with P=r input pins
    stage2 = [[-1 for j in range(N)] for i in range(k)]
    
    #tracks if the routing algo was sucessfully
    success = 0
    #a count to prevent infinite loops.
    #break up the outer loop and ends the routing trial.
    #TODO: implement a configurable globs.params variable for this supercount.
    supercount = 0

    while success is 0 and supercount < 180:

        supercount = supercount +1

        #just a change of the representation of the routing vector.
        #make a list for every used pin of the clos network input,
        #append the ble index for this pin.
        # give the relation: input pin -> ble number

        in_to_out = [[] for i in range(I+N)]
        
        #len routing vector is N. the number of bles.
        for bleIndex in range(len(routing_vector)):
            #the source pin number. 
            #pin is referred to the clos network input pin number
            for pin in routing_vector[bleIndex]:
                #skip unrouted pins
                if (pin != -1):
                    in_to_out[pin].append(bleIndex)
                
        unrouted = []
        
        #made a list 0,1,2,.. to I+N 
        #describe the input pin numbers in a sequence we try to route them
        #start with the first number and end with the last.
        #therefore we will shuffle this index list.
        pins_to_route = [ i for i in range(len(in_to_out))]
        
        #permute the list
        random.shuffle(pins_to_route)
        #a counter to prevent infinite loops
        count = 0
        #permute the target ble numbers of a pin
        for pin in pins_to_route:
            random.shuffle(in_to_out[pin])
        while success is 0 and count < 80:

            #a list of unrouted input pins. 
            #format : list of tuple (input pin number, target ble index)
            unrouted = []
            count = count + 1
            
            #a list 0,1,2 ... to k=m
            #describe the output pin numbers of a crossbar 
            nlist = [ i for i in range(k)]      
            random.shuffle(nlist)
            #the last try to route was not successfull. maybe we try it in an other sequence
            #therefore we shuffle the index list of pins we want try to route.
            random.shuffle(pins_to_route)
            #try to route the input pins step by step
            for pin in pins_to_route :
                #get the crossbar number of the first stage for this input pin
                x1 = int(pin/k)     
                
                #get the targeted ble index numbers
                for dest in in_to_out[pin]:
                    #index of the output pin of the first stage crossbar, used for the routing
                    #only set when the complete routing trough both stages was successful
                    s1 = -1
                    #index of the output pin of the second stage crossbar, used for the routing
                    s2 = -1
                    #try to find a free output pin of the first stage crossbar to route the track
                    for i in nlist:
                        #remember: x1 is the crossbar number of the first stage.
                        # i is the output pin of this crossbar
                        # pin is the input pin number
                        #dest is the targeted ble number
                        
                        #output of the first stage crossbar is free or already used for that pin
                        if stage1[x1][i] is -1 or stage1[x1][i] is pin: #unused         
                            #see if this will route to desired mux
                            #the output pin of the corresponding second stage crossbar is free
                            # or already used for this pin
                            if stage2[i][dest] is -1 or stage2[i][dest] is pin: #unused
                                #this two output pins of both crossbars are used for the
                                #given input pin. save this input pin number
                                stage1[x1][i] = pin
                                stage2[i][dest] = pin
                                #variable to track if this ble was not routable
                                s1 = i
                                s2 = dest
                                break
                    #there was no possible output pin in the first or second stage crossbar 
                    #to route this input pin number
                    if s1 is -1:
                        #save this unrouted pin together with the dest ble index
                        unrouted.append((pin, dest))
            pins_to_route = []
            
            #all pin have been routed
            if len(unrouted) is 0:
                success = 1

            #there are unrouted input pins
            for pin, dest in unrouted:
                
                #rip up other routed pins to make room
                for iterations in range(1 + int(count/20)): #unroute more pins as we do more iterations
                    pin_to_unroute = -1
                    #select the first stage crossbar of the unrouted input pin
                    x1 = int(pin/k)     
                    # build a list from [ 0,1 to k-1]
                    #the outputs indexes of the crossbar we want to throw out some tracks
                    nlist = [ i for i in range(k)]
                    random.shuffle(nlist)
                    
                    #this branch paste -1 in the unroute list. beaks the algo
                    #if random.random() < 0.6:
                    #   for i in nlist:
                    #       #the stage 2 crossbars output pin to the dest ble is not used
                    #       #so we have an input pin number we want to unroute
                    #       if stage2[i][dest] is -1:
                    #           pin_to_unroute = stage1[x1][i]                      
                    #           break
                    #just take a random input pin to reroute. should be I+N
                    
                    #if random.random() < 0.06:
                    #   pin_to_unroute = random.choice(range(I+N))
                    
                    pin_to_unroute = random.choice(range(I+N))

                    #there are still unrouted pins but no selection of pins to unroute
                    #take one random crossbar of the second stage
                    #and select the pin which leads to the dest ble
                    
                    #can also break the algo through -1
                    #if pin_to_unroute < 0:
                    #   pin_to_unroute = stage2[random.randint(0,k-1)][dest]

                    #we have selected an input pin to reroute but we must 
                    #cancel the routings in the crossbars for this pin
                    for i in range(P):
                        for j in range(k):
                            if stage1[i][j] is pin_to_unroute:
                                stage1[i][j] = -1
                    for i in range(k):
                        for j in range(N):
                            if stage2[i][j] is pin_to_unroute:
                                stage2[i][j] = -1
                    #now we can append the unrouted pin in the route todo list
                    
                    pins_to_route.append(pin_to_unroute)
                #also append the still not routed pin
                pins_to_route.append(pin)
    
    if success is 0:
        print "\n\n--------------  ERROR -----------------------"
        print 'Routing Algo was not able to route the network'
        print "---------------------------------------------"
        sys.exit(0)

    return [stage1, stage2]
