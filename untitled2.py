# -*- coding: utf-8 -*-
"""
Created on Sat Jun 29 16:00:26 2019

@author: mh322u
"""

# import some modules
import threading
from queue import Queue
import time

print_lock = threading.Lock()

def exampleJob(worker):
    time.sleep(0.5)
    
    with print_lock:
        print(threading.current_thread.__name__, worker)

def threader():
    while True:
        worker = q.get()
        exampleJob(worker)
        q.task_done()

q = Queue()

start = time.time()

for x in range(32):
    
    t = threading.Thread(target = threader)
    
    t.daemon = True
    
    t.start()
    

for worker in range(32):
    
    q.put(worker)
    
q.join()

end = time.time()

print("Entire job took:", end-start)
