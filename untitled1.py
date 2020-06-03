#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 14:40:09 2020

@author: mhurst
"""
import matplotlib.pyplot as plt
import numpy as np

#calculate the spatial change
Degrees = np.arange(0.,361.,10.)

X = 10. * np.sin( np.radians( Degrees ) )
Y = 10. * np.cos( np.radians( Degrees ) )

plt.plot(0,0,'ko')
plt.plot(X,Y,'ro-')
plt.axis('equal')
plt.show()

Orientation = np.zeros(len(Degrees))

for i in range(0,len(Degrees)-1):
    dx = X[i] - 0
    dy = Y[i] - 0

    #Calculate the orientation of the line from ThisNode to NextNode
    if dx > 0 and dy > 0:
        Orientation[i] = np.degrees( np.arctan( dx / dy ) )
    elif dx > 0 and dy < 0:
        Orientation[i] = 180.0 + np.degrees( np.arctan( dx / dy ) )
    elif dx < 0 and dy < 0:
        Orientation[i] = 180.0 + np.degrees( np.arctan( dx / dy ) )
    elif dx < 0 and dy > 0:
        Orientation[i] = 360 + np.degrees( np.arctan( dx / dy ) )
        
    print(dx, dy, Orientation[i])
        
