# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 14:55:13 2019

@author: mh322u
"""

import time
import sys
from IPython.display import clear_output

for i in range(5):
    time.sleep(1)
    print(i,  time.time(), end="\r")
    clear_output()