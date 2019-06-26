"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

import numpy as np
import numpy.ma as ma
import sys

#import figure plotting stuff here not globally!
import matplotlib
#matplotlib.use('agg')
import matplotlib.pyplot as plt

# import other custom classes
from Node import *

class Transect:
    """
    Description of object goes here

    """
    def __init__(self, ID, CoastNode, StartNode, EndNode):
        
        self.ID = ID
        
        # transect positioning
        self.CoastNode = CoastNode
        self.StartNode = StartNode
        self.EndNode = EndNode
        self.Orientation = self.CalculateOrientation(self.StartNode, self.EndNode)
        self.Length = self.CalculateLength(self.StartNode, self.EndNode)
        
        # transect data
        self.NoValues = None
        self.DistanceSpacing = None
        self.Distance = None
        self.Elevation = None
        self.ElevationMin = None
        self.ElevationMax = None

        # cliff metrics
        self.Cliff = False
        self.CliffTopInd = None
        self.CliffToeInd = None
        self.CliffHeight = None
        self.CliffSlope = None

        # barrier metrics
        self.Barrier = False
        self.FrontHeight = None
        self.FrontTopNode = None
        self.FrontToeNode = None
        self.BackHeight = None
        self.BackTopNode = None
        self.BackToeNode = None
        self.ToeWidth = None
        self.TopWidth = None
        self.FrontSlope = None
        self.BackSlope = None
        self.BarrierVolume = None
    
    def __str__(self):
        String = "Transect Object:\nID: %s\n" % (str(self.ID))
        String += "StartNode: "
        String += self.StartNode.__str__()
        String += "EndNode: "
        String += self.EndNode.__str__()
        return String

    def CalculateOrientation(self, Node1, Node2):
        
        """
        
        Maybe this could be a more general function external to class?
        
        MDH
        
        """
        
        #calculate the spatial change
        dx = Node2.X - Node1.X
        dy = Node2.Y - Node1.Y

        #Calculate the orientation of the line
        #N.B. this will depend on where the start segment is
        #so that 270 is esseintially the same as 90 but depends
        #which end of the line the cycle starts at
        if dx > 0 and dy > 0:
            Orientation = np.degrees( np.arctan( dx / dy ) )
        elif dx > 0 and dy < 0:
            Orientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy < 0:
            Orientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy > 0:
            Orientation = 360 + np.degrees( np.arctan( dx / dy ) )
            
        return Orientation
    
    def CalculateLength(self, Node1, Node2):
        
        """
        
        Maybe this could be a more general function external to class?
        
        MDH
        
        """
        
        #calculate the spatial change
        dx = Node2.X - Node1.X
        dy = Node2.Y - Node1.Y
        
        return np.sqrt(dx**2 + dy**2.)

    def FindCliff(self):

        """

        Function to identify whether the coastal transect has a cliff
        and find the position of a cliff on a coastal transect
        records the position of the cliff top and cliff toe

        MDH, June 2019

        """
        # cliffed coast will have elevations > 10 m
        # this threshold could be flexible in future
        if np.max(self.Elevation) < 10.:
            self.Cliff = False
            return

        # Find the last point on the Transect
        MaxInd = np.transpose(self.Elevation.nonzero())[-1][0]
        self.CliffTopInd = MaxInd
            
        # Find first real elevation location in masked array
        MinInd = np.transpose(self.Elevation.nonzero())[0][0]
        self.CliffToeInd = MinInd

        # flag for changing position
        CliffPositionChangeFlag = True

        while CliffPositionChangeFlag:

            # reset flag
            CliffPositionChangeFlag = False

            # FIRST CLIFF TOP

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if self.Distance[self.CliffTopInd] == self.Distance[MinInd]:
                print(self.ID)
                print("Divide by zero!")
                sys.exit()

            Angle = np.degrees(np.arctan((self.Elevation[MaxInd]-self.Elevation[self.CliffToeInd]) 
                                        / (self.Distance[MaxInd]-self.Distance[self.CliffToeInd])))
            
            # Get detrended elevation
            ElevDetrend = ((self.Elevation-self.Elevation[self.CliffToeInd])+(self.Distance[self.CliffToeInd]-self.Distance) \
                            * np.tan(np.radians(Angle)))

            # mask values beyond the peak elevation and seaward of the toe
            Mask = self.Elevation.mask.copy()
            Mask[0:self.CliffToeInd] = True
            Mask[MaxInd:] = True
            ElevDetrend = ma.masked_where(Mask,ElevDetrend)
            
            # Find Maximum detrended elevation. Must be positive to be considered a change in cliff top position
            if ((np.argmax(ElevDetrend) < self.CliffTopInd) and (ElevDetrend[np.argmax(ElevDetrend)] > 0.001)):
                #print("Cliff Position change from", self.Distance[self.CliffTopInd], "to", self.Distance[np.argmax(ElevDetrend)])
                self.CliffTopInd = np.argmax(ElevDetrend)
                CliffPositionChangeFlag = True
                # if self.CliffTopInd == 290:
                #     print("Angle is", Angle)
                #     plt.subplot(211)
                #     plt.plot(self.Distance[np.invert(Mask)],self.Elevation[np.invert(Mask)])
                #     plt.subplot(212)
                #     plt.plot(self.Distance,ElevDetrend)
                #     plt.show()
                #     sys.exit()
                # # if self.CliffTopInd == 0:
                #     print(Angle)
                #     print(ElevDetrend)
                #     sys.exit()
            
            # THEN CLIFF TOE

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if self.Distance[self.CliffTopInd] == self.Distance[MinInd]:
                print(self.ID)
                print("Divide by zero getting toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((self.Elevation[self.CliffTopInd]-self.Elevation[MinInd]) 
                                        / (self.Distance[self.CliffTopInd]-self.Distance[MinInd])))
            
            # Get detrended elevation
            ElevDetrend = ((self.Elevation-self.Elevation[MinInd]) + (self.Distance[MinInd] - self.Distance) \
                            * np.tan(np.radians(Angle)))

            # mask values beyond the cliff top
            Mask = self.Elevation.mask.copy()
            Mask[self.CliffTopInd:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
                            
            # Find Minimum detrended elevation, must be negative to be considered a low (probably never a worry)
            if ((np.argmin(ElevDetrend) > self.CliffToeInd) and (ElevDetrend[np.argmin(ElevDetrend)] < -0.001)):
                #print("Cliff Toe change from", self.Distance[self.CliffToeInd],"to", self.Distance[np.argmin(ElevDetrend)])
                self.CliffToeInd = np.argmin(ElevDetrend)
                CliffPositionChangeFlag = True
            
            # else:
            #     print("")
            #     print(self.CliffToeInd, np.argmin(ElevDetrend))
            #     plt.subplot(211)
            #     plt.plot(self.Distance[np.invert(Mask)],self.Elevation[np.invert(Mask)])
            #     plt.subplot(212)
            #     plt.plot(self.Distance,ElevDetrend)
            #     plt.show()
            #     sys.exit()

        # Check if found a cliff
        self.CliffHeight = self.Elevation[self.CliffTopInd]-self.Elevation[self.CliffToeInd]
        self.CliffSlope = self.CliffHeight/(self.Distance[self.CliffTopInd]-self.Distance[self.CliffToeInd])
        
        if (self.CliffSlope > 0.55) or (self.CliffHeight > 15.):
            self.Cliff = True
                    
        else:
            self.Cliff = False

    def FindBarrier(self):
        
        """

        Description goes here

        MDH, June 2019

        """

        # Check if a cliff is present and only analyse topography up to the cliff toe
        # when looking for a barrier
        Mask = self.Elevation.mask.copy()
        if self.Cliff:
            Mask[self.CliffToeInd:] = True

        # mask below sea level
        Mask[self.Elevation < 0] = True

        # apply mask
        ElevMasked = ma.masked_where(Mask, self.Elevation)
        DistanceMasked = ma.masked_where(Mask, self.Distance)

        # Find the highest point of the barrier
        MaxInd = np.argmax(ElevMasked)
        self.FrontTopInd = MaxInd

        # Find first real elevation location in masked array
        FirstInd = np.transpose(ElevMasked.nonzero())[0][0]
        self.FrontToeInd = FirstInd
        
        # Find last real elevation location in masked array
        LastInd = np.transpose(ElevMasked.nonzero())[-1][0]

        # flag for changing position
        BarrierPositionChangeFlag = True

        while BarrierPositionChangeFlag:

            # reset flag
            BarrierPositionChangeFlag = False

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[MaxInd] == DistanceMasked[self.FrontToeInd]:
                print(self.ID)
                print("Divide by zero getting top!")
                sys.exit()

            # Get Angle to detrend towards the coast
            Angle = np.degrees(np.arctan((ElevMasked[MaxInd]-ElevMasked[self.FrontToeInd]) 
                                        / (DistanceMasked[MaxInd]-DistanceMasked[self.FrontToeInd])))
        
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.FrontToeInd])+(DistanceMasked[self.FrontToeInd]-DistanceMasked) \
                                * np.tan(np.radians(Angle)))

            # mask values beyond the peak
            Mask = ElevMasked.mask.copy()
            Mask[0:self.FrontToeInd] = True
            Mask[MaxInd+1:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            
            # Find Maximum detrended elevation. 
            # if at end of transect then not a barrier
            if (np.argmax(ElevDetrend) == LastInd) or (MaxInd == LastInd):
                self.Barrier = False
                return

            # Must be positive to be considered a change in cliff top position
            elif ((np.argmax(ElevDetrend) < self.FrontTopInd) and (ElevDetrend[np.argmax(ElevDetrend)] > 0.001)):
                #print("\nBarrier front top change from", self.Distance[self.FrontTopInd], "to", self.Distance[np.argmax(ElevDetrend)])
                self.FrontTopInd = np.argmax(ElevDetrend)
                BarrierPositionChangeFlag = True
                
            
            # THEN Barrier TOE


            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[self.FrontTopInd] == DistanceMasked[FirstInd]:
                print(self.ID)
                print("Divide by zero getting toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((ElevMasked[self.FrontTopInd]-ElevMasked[FirstInd]) 
                                        / (DistanceMasked[self.FrontTopInd]-DistanceMasked[FirstInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[FirstInd]) \
             + (DistanceMasked[FirstInd] - DistanceMasked) * np.tan(np.radians(Angle)))

            # mask values beyond the barrier front top
            Mask = ElevMasked.mask.copy()
            Mask[self.FrontTopInd:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            
            # Find Minimum detrended elevation, must be negative to be considered a low (probably never a worry)
            if ((np.argmin(ElevDetrend) > self.FrontToeInd) and (ElevDetrend[np.argmin(ElevDetrend)] < -0.001)):
                #print("barrier front toe change from", self.Distance[self.FrontToeInd],"to", self.Distance[np.argmin(ElevDetrend)])
                self.FrontToeInd = np.argmin(ElevDetrend)
                BarrierPositionChangeFlag = True

        # Check if found a cliff by mistake
        self.FrontHeight = self.Elevation[self.FrontTopInd]-self.Elevation[self.FrontToeInd]
        self.FrontSlope = self.FrontHeight/(self.Distance[self.FrontTopInd]-self.Distance[self.FrontToeInd])
        
        if self.FrontSlope > 0.55:
            print("\nSteeper than 35 degrees, therefore likely a cliff!")
            #self.Cliff = True
        
        elif self.FrontHeight > 15.:
            print("\nHigher than 15 m, therefore likely a cliff!")
            #self.Cliff = True
        
        if not self.FrontTopInd > self.FrontToeInd:
            self.Barrier = False
            print(self.FrontTopInd, self.FrontToeInd)
            print("NOT A BARRIER 1")
            return

        # NOW DEFINE THE BACK BARRIER
        
        # default back barrier positions
        self.BackTopInd = self.FrontTopInd
        Mask = ElevMasked.mask.copy()
        Mask[0:self.FrontTopInd] = True
        MinInd = np.argmin(ma.masked_where(Mask, ElevMasked))
        self.BackToeInd = MinInd

        # flag for changing position
        BarrierPositionChangeFlag = True

        while BarrierPositionChangeFlag:

            # reset flag
            BarrierPositionChangeFlag = False

            # Get Angle to detrend towards away from the coast
            # catch divide by zero
            if DistanceMasked[self.BackToeInd] == DistanceMasked[self.FrontTopInd]:
                print("Divide by zero getting toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((ElevMasked[MinInd]-ElevMasked[self.FrontTopInd])
                                        / (DistanceMasked[MinInd]-DistanceMasked[self.FrontTopInd])))
           
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.FrontTopInd])+(DistanceMasked[self.FrontTopInd]-DistanceMasked) \
                            * np.tan(np.radians(Angle)))

            # mask values up to the peak
            Mask = ElevMasked.mask.copy()
            Mask[0:self.FrontTopInd] = True
            ElevDetrend = ma.masked_where(Mask,ElevDetrend)

            # Find Maximum detrended elevation. Must be positive to be considered a change in barrier back top position
            if ((np.argmax(ElevDetrend) > self.BackTopInd) and (ElevDetrend[np.argmax(ElevDetrend)] > 0.001)):
                #print("barrier back top change from", self.Distance[self.BackTopInd], "to", self.Distance[np.argmax(ElevDetrend)])
                self.BackTopInd = np.argmax(ElevDetrend)
                BarrierPositionChangeFlag = True
                
            # THEN Barrier TOE

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[self.BackTopInd] == DistanceMasked[FirstInd]:
                print(self.ID)
                print("Divide by zero getting toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((ElevMasked[MinInd]-ElevMasked[self.BackTopInd]) 
                                        / (DistanceMasked[MinInd]-DistanceMasked[self.BackTopInd])))
            if np.isnan(Angle):
                print("\nAngle is a NaN")

            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.BackTopInd]) + (DistanceMasked[self.BackTopInd] - DistanceMasked) \
                            * np.tan(np.radians(Angle)))

            # mask values beyond the barrier front top
            Mask = ElevMasked.mask.copy()
            Mask[0:self.BackTopInd] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
                            
            # Find Minimum detrended elevation, must be negative to be considered a low (probably never a worry)
            if ((np.argmin(ElevDetrend) < self.BackToeInd) and (ElevDetrend[np.argmin(ElevDetrend)] < -0.001)):
                #print("barrier back toe change from", self.Distance[self.BackToeInd],"to", self.Distance[np.argmin(ElevDetrend)])
                self.BackToeInd = np.argmin(ElevDetrend)
                BarrierPositionChangeFlag = True
            
        #Check top is not at the end, bottom is ok to be at end
        # again not sure what this is acheiving
        if self.BackTopInd > self.BackToeInd:
            self.Barrier = False
            print("")
            print(self.BackTopInd, self.BackToeInd)
            print("NOT A BARRIER 2")
            sys.exit()
            return

        # if (self.ID == str("1")):
        #     plt.plot(self.Distance,self.Elevation)
        #     plt.plot(self.Distance[self.FrontTopInd],self.Elevation[self.FrontTopInd],'ks',ms=10)
        #     plt.plot(self.Distance[self.FrontToeInd],self.Elevation[self.FrontToeInd],'ks',ms=10)
        #     plt.plot(self.Distance[self.BackTopInd],self.Elevation[self.BackTopInd],'ro',ms=5)
        #     plt.plot(self.Distance[self.BackToeInd],self.Elevation[self.BackToeInd],'ro',ms=5)
        #     plt.show()
        #     sys.exit()

        # Calculate Barrier Height, front and back
        self.FrontHeight = self.Elevation[self.FrontTopInd]-self.Elevation[self.FrontToeInd]
        self.BackHeight = self.Elevation[self.BackTopInd]-self.Elevation[self.BackToeInd]
                
        # Calculate Barrier Width, top and bottom
        self.ToeWidth = self.Distance[self.FrontToeInd]-self.Distance[self.BackToeInd]
        self.TopWidth = self.Distance[self.FrontTopInd]-self.Distance[self.BackTopInd]

        # Calculate Slope, front and back
        self.FrontSlope = self.FrontHeight/(self.Distance[self.FrontTopInd]-self.Distance[self.FrontToeInd])
        self.BackSlope = self.BackHeight/(self.Distance[self.BackTopInd]-self.Distance[self.BackToeInd])

        # Volume m3/m
        self.BarrierVolume =  (self.Distance[self.BackToeInd] * self.Elevation[self.BackTopInd] \
                                     - self.Distance[self.BackTopInd] * self.Elevation[self.BackToeInd]) 
        self.BarrierVolume += (self.Distance[self.BackTopInd] * self.Elevation[self.FrontTopInd] \
                                    - self.Distance[self.FrontTopInd] * self.Elevation[self.BackTopInd])
        self.BarrierVolume += (self.Distance[self.FrontTopInd] * self.Elevation[self.FrontToeInd] \
                                    - self.Distance[self.FrontToeInd] * self.Elevation[self.FrontTopInd])
        self.BarrierVolume += (self.Distance[self.FrontToeInd] * self.Elevation[self.BackToeInd] \
                                    - self.Distance[self.BackToeInd] * self.Elevation[self.FrontToeInd])
        self.BarrierVolume /= 2.

        # switch flag to indicate a barrier has been found
        self.Barrier = True

    def ExtractBarrierWidth(self, Elev):

        """
        Extract barrier width at a given elevation (e.g. extreme water level)

        MDH, June 2019
        """

        # check barrier analysis has been conducted
        if not self.BarrierVolume:
            self.AnalyseMorphology()
        
        # vector at fixed elevation running the length of the transect
        X1, Y1 = self.Distance[0], Elev
        X2, Y2 = self.Distance[-1], Elev
        dX12 = X2-X1
        dY12 = Y2-Y1
        
        # count and record locations of intersection
        IntersectionCounter = 0
        IntesectionIndices = []
        InterpolateFraction = []

        for i in range(0,self.NoNodes):

            # cut and paste interesction analysis
            # do we want this to be a separate function somewhere?
            # Loop through transects and count no of intersections with the coastline
            # get transect line ends        
            X3,Y3 = self.Distance[i], self.Elevation[i]
            X4,Y4 = self.Distance[i+1], self.Elevation[i+1]
            
            dX34 = X4-X3
            dY34 = Y4-Y3
            
            #Find the cross product of the two vectors
            XProd = dX12*dY34 - dX34*dY12
                
            if (XProd != 0):
                if (XProd > 0):
                    XProdPos = 1
                else:
                    XProdPos = 0
                    
                #assign third test segment
                dX31 = X1-X3
                dY31 = Y1-Y3
                    
                #get cross products
                S = dX12*dY31 - dY12*dX31;
                T = dX34*dY31 - dY34*dX31;
                
                #logic for collision occurence
                if ((S < 0) == XProdPos):
                    continue
                elif ((T < 0) == XProdPos):
                    continue
                elif ((S > XProd) == XProdPos):
                    continue
                elif ((T > XProd) == XProdPos):
                    continue
                else:
                    IntersectionCounter += 1
                    IntersectionIndices.append(i)
                    InterpolateFraction.append(T)

        # calculate width and volume at this elevation
        if InterectionCounter > 1:
            
            # Calculate Wdith
            self.CustomWidth = self.Distance[IntersectionIndices[1]] + InterpolateFraction[1]*self.DistanceSpacing \
                                - self.Distance[IntersectionIndices[0]] + InterpolateFraction[0]*self.DistanceSpacing

            # Calculate Volume
            self.CustomVolume = np.sum(self.Elevation[IntersectionIndices[0:2]]-Elev)*self.DistanceSpacing

    def Plot(self, PlotFolder):
        """
        
        MDH, June 2019

        """
        # create figure
        fig = plt.figure(1,figsize=(6,3))
                
        # create 4 subplots
        ax = plt.subplot(111)
                
        # temp fix to masked array legacy problem
        self.Distance = ma.masked_where(self.Elevation.mask,self.Distance)

        # plot raw data
        ax.plot(self.Distance, self.Elevation,'k-',lw=1.,zorder=11)
                
        # plot range
        ax.fill_between(self.Distance, self.ElevationMin, self.ElevationMax, color=[0.8,0.8,0.8], zorder=10)
        
        # add cliff details here
        if self.Cliff:
            
            # plot top to toe
            CliffColour = [0.6,0.4,0.1]
            ax.plot(self.Distance[self.CliffToeInd:self.CliffTopInd], self.Elevation[self.CliffToeInd:self.CliffTopInd], '-', c=CliffColour, zorder=12)
            ax.plot(self.Distance[self.CliffTopInd], self.Elevation[self.CliffTopInd], 'ko', mfc=CliffColour, zorder=13)
            ax.plot(self.Distance[self.CliffToeInd], self.Elevation[self.CliffToeInd], 'ko', mfc=CliffColour, zorder=13)
            
        # # add barrier details here
        if self.Barrier:
        
            # create array for filling in geometry
            DistFill = self.Distance[self.FrontToeInd:self.BackToeInd]
            ElevFill = self.Elevation[self.FrontToeInd:self.BackToeInd]
            LowerFill = np.linspace(ElevFill[0],ElevFill[-1],len(ElevFill)) 
        
            # plot the barrier profile and points
            ax.fill_between(DistFill, ElevFill, LowerFill, color=[1.0,0.7,0.7], zorder=9)
            ax.plot(DistFill, ElevFill, 'r-', zorder=12)
            ax.plot(self.Distance[self.FrontTopInd], self.Elevation[self.FrontTopInd], 'ro', ms=5, zorder=13)
            ax.plot(self.Distance[self.FrontToeInd], self.Elevation[self.FrontToeInd], 'ro', ms=5, zorder=13)
            ax.plot(self.Distance[self.BackTopInd], self.Elevation[self.BackTopInd], 'ro', ms=5, zorder=13)
            ax.plot(self.Distance[self.BackToeInd], self.Elevation[self.BackToeInd], 'ro', ms=5, zorder=13)
        
        # label axes
        ax.set_aspect(4.)
        ax.set_ylabel("Elevation (m)")
        ax.set_xlabel("Distance (m)")

        # save the figure        
        fig.savefig(PlotFolder+"Transect_"+str(self.ID)+".png", dpi=300)

        # close the figure
        plt.close(fig)

    def get_XY(self):
        
        """
        Returns X and Y coordinates of start and end nodes

        MDH, June 2019
        
        """

        X = [self.StartNode.X, self.EndNode.X]
        Y = [self.StartNode.Y, self.EndNode.Y]
        
        return np.array(X), np.array(Y)

    def get_CliffPosition(self):

        if not self.Cliff:
            sys.exit("Transect.get_CliffPosition: Not a cliff!")

        # calculate X and Y
        CliffTopDist = self.Distance[self.CliffTopInd]
        CliffToeDist = self.Distance[self.CliffToeInd]
        
        # Calculate position of cliff top
        X1 = self.StartNode.X + CliffTopDist * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y + CliffTopDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of cliff toe
        X2 = self.StartNode.X + CliffToeDist * np.sin( np.radians( self.Orientation ) )
        Y2 = self.StartNode.Y + CliffToeDist * np.cos( np.radians( self.Orientation ) )
        
        return Node(X1, Y1), Node(X2, Y2)