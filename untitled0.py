# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 09:54:34 2019

@author: mh322u
"""

from tqdm import trange
from time import sleep

for i in trange(4, desc='1st loop'):
    for j in trange(5, desc='2nd loop'):
        for k in trange(50, desc='3nd loop', leave=False):
            sleep(0.01)