# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 17:54:48 2017

@author: Aziz
"""

import random
from functools import partial, wraps
import simpy


RANDOM_SEED = 45
NEW_CUSTOMERS = 10  # Total number of customers
INTERVAL_CUSTOMERS = 10.0  # Generate new customers roughly every x seconds
MIN_PATIENCE = 10  # Min. customer patience
MAX_PATIENCE = 100  # Max. customer patience
SIM_TIME = 0.1*60*60



class Customer(object):  
    def __init__(self, env, counters, name, time_in_bank):
        self.env = env
        self.service_time = 0
        self.wait_time = 0 
        self.counters = counters
        self.time_in_bank = time_in_bank
        self.name = name
        #env.process(self.customer())
        
    def customer(self):
        for counter in self.counters:
            arrive = self.env.now
            print('%7.4f %s: Here I am' % (arrive, self.name))
            with self.counters[counter].request() as req:
                patience = random.uniform(MIN_PATIENCE, MAX_PATIENCE)
                # Wait for the counter or abort at the end of our tether
                results = yield req | self.env.timeout(patience)
                #print(results)
        
                wait = self.env.now - arrive
                self.wait_time = self.wait_time + wait
        
                if req in results:
                    # We got to the counter
                   # print('%6.0f customers ahead' % (self.counters[counter].count))
                   # print('%7.4f %s: Waited %6.3f at %s' % 
                          #(self.env.now, self.name, wait, counter))
        
                    tib = random.expovariate(1.0 / self.time_in_bank)
                    self.service_time = self.service_time + tib
                    yield self.env.timeout(tib)
                    #print('%7.4f %s: Finished from %s' % (self.env.now, self.name, counter))
        
                else:
                    # We reneged
                    print('%6.0f customers ahead' % (self.counters[counter].count))
                    #print('%7.4f %s: RENEGED after %6.3f at  %s' % 
                          #(self.env.now, self.name, wait, counter))
#def delay():
#    yield env.timeout(15)
customers = []
def source(env, number, interval, counters):
    """Source generates customers randomly"""
    i = 0
    while True:
        c = Customer(env, counters, 'Customer%02d' % i, time_in_bank=12.0)
        customers.append(c)
        env.process(customers[i].customer())
        i = i+1
        t = random.expovariate(1.0 / interval)
        yield env.timeout(t)


class Counter(simpy.Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.start = 0
        self.end = 0
        self.busy = 0
        #self.name = ""

    def request(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        self.start = self._env.now
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        self.end = self._env.now
        self.busy = self.busy + (self.end - self.start)
        return super().release(*args, **kwargs)
# Setup and start the simulation
print('Bank renege')
#random.seed(RANDOM_SEED)

env = simpy.Environment()


# Start processes and run

#counters = [Counter(env, capacity = 1, "counter" + str(i)) for i in range(2)]
counters = {"counter" + str(i): Counter(env, capacity = 1) for i in range(2)}
    
env.process(source(env, 10, 10, counters))
#for i in range(10):
#    Customer(env, counters, 'Customer%02d' % i, time_in_bank=12.0)
    
env.run(until = SIM_TIME)
print(counters['counter0'].busy / SIM_TIME)
print(counters['counter1'].busy / SIM_TIME)

stats = []
for c in customers:
    stats.append([c.name, c.service_time, c.wait_time])
#print(stats)
    