#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 14:30:57 2020

@author: mhurst
"""

import numpy as np
import matplotlib.pyplot as plt

x = np.arange(0,10000.,10.)

Amplitude = 1000.
Wavelength = 10000.
y = Amplitude*np.sin((2.*np.pi/Wavelength)*x)

plt.plot(x,y,'k-')
plt.axis('equal')

# Give each transect unique ID
TransectCount = 0

# Parameters for tracing along length
CumulativeLength = 0.0
NextPosition = Spacing

# Track spacing and generate profile at desired distances
for i in range(1, len(x)):

    #Update the cumulative length of the line
    dx = x[i]-x[i-1]
    dy = y[i]-y[i-1]
    Distance = np.sqrt(dx**2.+dy**2.)
    CumulativeLength += Distance

    # get orientation and angle of imaginary circle
    LastOrientation = self.Orientation[i-1]
    TempOrientation = self.Orientation[i]
    dOrientation = TempOrientation - LastOrientation
    
    #this logic will be flawed so is a place holder
    if dOrientation > 180:
        dOrientation -= 360
    
    # get a minimum arc length for delta orientation
    MinArcLength = 2*np.pi*NoIntersectionDistance*(dOrientation/360.)

    # Test to see if we're going to create a cross section
    while CumulativeLength > NextPosition:

        #calculate point for section
        DistanceToStepBack = CumulativeLength - NextPosition
        dX = DistanceToStepBack * np.sin( np.radians( TempOrientation ) )
        dY = DistanceToStepBack * np.cos( np.radians( TempOrientation ) )
        
        # find the point for the transect along the line
        PointX = self.Nodes[i+1].X - dX
        PointY = self.Nodes[i+1].Y - dY

        #Create cross section line
        #Get line orientation
        if TempOrientation < 0:
            TransectOrientation = TempOrientation + 90.
        else:
            TransectOrientation = TempOrientation - 90.

        """ if self.ID == "3":
            print(TempOrientation)
            print(TransectOrientation)

            X1 = PointX + TransectLength2Sea * np.sin( np.radians( TransectOrientation ) )
            Y1 = PointY + TransectLength2Sea * np.cos( np.radians( TransectOrientation ) )
            X2 = PointX - TransectLength2Land * np.sin( np.radians( TransectOrientation ) )
            Y2 = PointY - TransectLength2Land * np.cos( np.radians( TransectOrientation ) )
            
            plt.plot(X1,Y1,'bo')
            plt.plot(X2,Y2,'ro')
            plt.plot([X1,X2],[Y1,Y2],'k--')
            plt.show()
            sys.exit() """

        #Calculate start and end nodes and generate Transect
        X1 = PointX + TransectLength2Sea * np.sin( np.radians( TransectOrientation ) )
        Y1 = PointY + TransectLength2Sea * np.cos( np.radians( TransectOrientation ) )
        X2 = PointX - TransectLength2Land * np.sin( np.radians( TransectOrientation ) )
        Y2 = PointY - TransectLength2Land * np.cos( np.radians( TransectOrientation ) )
        self.Transects.append( Transect( Node(PointX, PointY), Node(X1, Y1), Node(X2, Y2), str(self.ID), str(TransectCount) ) )

        # update to find next transect
        TransectCount += 1
        NextPosition += Spacing





plt.show()