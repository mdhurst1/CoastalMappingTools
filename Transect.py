"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

import numpy as np
import numpy.ma as ma
import os, sys

#import figure plotting stuff here not globally!
import matplotlib
#matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams, cm

# import other custom classes
from Node import *

# Customise figure font style
# Set up fonts for plots
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['arial']
rcParams['font.size'] = 10
rcParams['text.usetex'] = True

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
        self.ElevStd = None

        # cliff metrics
        self.Cliff = False
        self.CliffTopInd = None
        self.CliffToeInd = None
        self.CliffHeight = None
        self.CliffSlope = None
        self.Rocky = False

        # intertidal
        self.SlopeRoughness = None
        self.ElevationRoughness = None

        # barrier metrics
        self.Barrier = False
        self.FrontHeight = None
        self.FrontTopInd = None
        self.FrontToeInd = None
        self.BackHeight = None
        self.BackTopInd = None
        self.BackToeInd = None
        self.CrestInd = None
        self.CrestElevation = None
        self.ToeWidth = None
        self.TopWidth = None
        self.FrontSlope = None
        self.BackSlope = None
        self.BarrierVolume = None

        # other barrier metrics for extreme water levels
        self.MHWS = None
        self.ExtremeWaterLevels = ["","",""]
        self.Intersection = None
        self.IntersectionIndices = None
        self.InterpolateFractions = None
        self.FrontNode = None
        self.BackNode = None
        self.ExtremeFrontNodes = ["","",""]
        self.ExtremeBackNodes = ["","",""]
        self.ExtremeDistance = None
        self.ExtremeIndices = ["","",""]
        self.ExtremeDistances = ["","",""]
        self.ExtremeInterpFractions = ["","",""]
        self.ExtremeWidth = None
        self.ExtremeWidths = ["","",""]
        self.ExtremeVolume = None
        self.ExtremeVolumes = ["","",""]
    
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
        
        # if cliff top is highest point, not a cliff, likely a barrier
        if self.CliffTopInd == MaxInd:
            self.Cliff = False

        elif np.abs(self.Distance[self.CliffTopInd]-self.Distance[MaxInd]) < 10.:
            self.Cliff = False

        elif (self.CliffSlope > 0.6) or (self.CliffHeight > 15.):
            self.Cliff = True
                    
        else:
            self.Cliff = False

    def AnalyseRoughness(self, Elev):

        """
        Isolates intertidal elevations and looks at their roughness to determine
        if rocky (rough) or sandy (smooth)

        MDH, July 2019

        """

        # mask by elevation
        Mask = self.Elevation.mask.copy()
        Mask[self.Elevation > Elev] = True
        Mask[self.Elevation < -1] = True
        
        # apply mask
        ElevMasked = ma.masked_where(Mask, self.Elevation)
        
        # calculate slope along the transect
        Start, End = ma.notmasked_edges(self.Distance)
        self.DistanceSpacing = self.Distance[Start+1]-self.Distance[Start] # temporary fix
        Slope = np.diff(ElevMasked)/self.DistanceSpacing
        Slope = Slope.compressed()

        # calculate roughness and take mean value
        #self.SlopeRoughness = np.max(Slope)-np.min(Slope)
        #print(np.percentile(Slope, 95),np.percentile(Slope, 5),np.std(Slope))
        self.SlopeRoughness = np.percentile(Slope, 95) - np.percentile(Slope, 5)
        self.ElevationRoughness = np.mean(self.ElevStd)

        if self.SlopeRoughness > 10.:
            print("ARGH!!!")

        #self.ElevationRoughness = np.mean(self.ElevStd.compressed())
        #self.ElevationRoughness = ma.mean(self.ElevationMax-self.ElevationMin)
        #print(self.SlopeRoughness, end=", ")

        #print(self.SlopeRoughness, self.ElevationRoughness)
        if (self.SlopeRoughness > 0.05) and (self.ElevationRoughness > 0.2):
            self.Rocky = True

    def FindBarrier(self):
        
        """
        Description goes here
        MDH, June 2019
        """
        # Check if rocky and dont look for barrier on rocky coast
        if self.Rocky:
            #print("Rocky")
            self.Barrier = False
            return

        # Check if a cliff is present and only analyse topography up to the cliff toe
        # when looking for a barrier
        Mask = self.Elevation.mask.copy()
        if self.Cliff:
            Mask[self.CliffToeInd+1:] = True

        # mask below sea level, including tide, in future
        Mask[self.Elevation < 0] = True

        # apply mask
        ElevMasked = ma.masked_where(Mask, self.Elevation)
        DistanceMasked = ma.masked_where(Mask, self.Distance)

        # check that the whole topography has not been masked
        # this would indicate there is no barrier
        if ElevMasked.mask.all():
            print("\n\tNot a barrier 1")
            self.Barrier = False
            return

        # Find the highest point to start from
        MaxInd = np.argmax(ElevMasked)
        self.FrontTopInd = MaxInd

        # Find first real elevation location in masked array
        FirstInd = np.transpose(ElevMasked.nonzero())[0][0]
        self.FrontToeInd = FirstInd
        
        # Find last real elevation location in masked array
        LastInd = np.transpose(ElevMasked.nonzero())[-1][0]

        # flag for changing position
        # we'll keep applygin the barrier finder until the 
        # top and toe positions dont change
        BarrierPositionChangeFlag = True

        while BarrierPositionChangeFlag:

            # reset flag
            BarrierPositionChangeFlag = False

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[MaxInd] == DistanceMasked[self.FrontToeInd]:
                print("")
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
            NewInd = np.argmax(ElevDetrend)
            
            # Find Maximum detrended elevation. 
            # if at end of transect then not a barrier
            if (NewInd == LastInd):
                self.Barrier = False
                return

            # Must be above MHWS to be considered a change in barrier top position
            elif ((NewInd < self.FrontTopInd) and (ElevDetrend[NewInd] > 0.001) and (ElevMasked[NewInd] > self.MHWS)):
                self.FrontTopInd = np.argmax(ElevDetrend)
                BarrierPositionChangeFlag = True
                
            # THEN Barrier TOE

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[self.FrontTopInd] == DistanceMasked[FirstInd]:
                print(self.ID)
                print(DistanceMasked[self.FrontTopInd], DistanceMasked[FirstInd])
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
                self.FrontToeInd = np.argmin(ElevDetrend)
                BarrierPositionChangeFlag = True

        # Check if found a cliff by mistake
        # this needs more work
        self.FrontHeight = self.Elevation[self.FrontTopInd]-self.Elevation[self.FrontToeInd]
        self.FrontSlope = self.FrontHeight/(self.Distance[self.FrontTopInd]-self.Distance[self.FrontToeInd])
        
        #if self.FrontSlope > 0.6:
            #print("\nSteeper than 40 degrees, therefore likely a cliff!")
            #self.Cliff = True
        
        #elif self.FrontHeight > 15.:
            #print("\nHigher than 15 m, therefore likely a cliff!")
            #self.Cliff = True
        
        if not self.FrontTopInd > self.FrontToeInd:
            self.Barrier = False
            print(self.FrontTopInd, self.FrontToeInd)
            print("Error: Not a barrier 3")
            return

        # NOW DEFINE THE BACK BARRIER
        
        # default back barrier positions
        self.BackTopInd = self.FrontTopInd
        Mask = ElevMasked.mask.copy()
        Mask[0:self.FrontTopInd] = True

        MinInd = np.argmin(ma.masked_where(Mask, ElevMasked))
        self.BackToeInd = MinInd
        #plt.plot(DistanceMasked[MinInd],ElevMasked[MinInd],'k+',ms=20)

        # catch where Minimum Elevation coincides with "barrier" front
        # when looking for a "back barrier"2
        if MinInd == self.FrontTopInd:
            print("not a barrier 2")
            #plt.plot(self.Distance,self.Elevation,'k-')
            #plt.plot(self.Distance[self.FrontTopInd],self.Elevation[self.FrontTopInd],'bo')
            #plt.plot(self.Distance[self.FrontToeInd],self.Elevation[self.FrontToeInd],'bs')
            #plt.plot(self.Distance[self.BackTopInd],self.Elevation[self.BackTopInd],'ro')
            #plt.plot(self.Distance[self.BackToeInd],self.Elevation[self.BackToeInd],'rs')
            #plt.plot(self.Distance,ElevDetrend,'r-')
            #plt.show()
            self.Barrier = False
            return

        # flag for changing position
        BarrierPositionChangeFlag = True

        while BarrierPositionChangeFlag:

            # reset flag
            BarrierPositionChangeFlag = False

            # Get Angle to detrend towards away from the coast
            # catch divide by zero
            if DistanceMasked[MinInd] == DistanceMasked[self.FrontTopInd]:
                print("Divide by zero getting top!")
                print(MinInd, self.FrontTopInd)
                print(DistanceMasked[MinInd],DistanceMasked[self.FrontTopInd])
                sys.exit()

            #################################################################################################
            # !!!!!!!!!!!!!!!!!!might change this to look to back toe ind incrementally!!!!!!!!!!!!!!!!!!!!!!
            #################################################################################################

            Angle = np.degrees(np.arctan((ElevMasked[self.BackToeInd]-ElevMasked[self.FrontTopInd])
                                        / (DistanceMasked[self.BackToeInd]-DistanceMasked[self.FrontTopInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.FrontTopInd])+(DistanceMasked[self.FrontTopInd]-DistanceMasked) \
                            * np.tan(np.radians(Angle)))

            # mask values up to the peak
            Mask = ElevMasked.mask.copy()
            Mask[self.BackToeInd+1:] = True
            ElevDetrend = ma.masked_where(Mask,ElevDetrend)

            # Find Maximum detrended elevation. Must be positive to be considered a change in barrier back top position
            if ((np.argmax(ElevDetrend) > self.BackTopInd) and (ElevDetrend[np.argmax(ElevDetrend)] > 0.001)):
                self.BackTopInd = np.argmax(ElevDetrend)
                BarrierPositionChangeFlag = True
                
            # THEN Barrier TOE

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[MinInd] == DistanceMasked[self.BackTopInd]:
                print("Divide by zero getting toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((ElevMasked[self.BackToeInd]-ElevMasked[self.FrontTopInd]) 
                                        / (DistanceMasked[self.BackToeInd]-DistanceMasked[self.FrontTopInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.FrontTopInd]) + (DistanceMasked[self.FrontTopInd] - DistanceMasked) \
                            * np.tan(np.radians(Angle)))

            # mask values seaward of the barrier front top
            Mask = ElevMasked.mask.copy()
            Mask[0:self.BackTopInd] = True
            Mask[self.BackToeInd+1:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            NewInd = np.argmin(ElevDetrend)
            #plt.plot(DistanceMasked,ElevDetrend,'r-')
            
            # Find Minimum detrended elevation, must be negative to be considered a low (probably never a worry)
            if ((NewInd < self.BackToeInd) and (ElevDetrend[NewInd] < -0.001) and (NewInd > self.BackTopInd)):
                self.BackToeInd = NewInd
                BarrierPositionChangeFlag = True
                
        # print("\nHERE\n")
        # plt.plot(self.Distance,self.Elevation,'k-')
        # plt.plot(self.Distance[self.FrontTopInd],self.Elevation[self.FrontTopInd],'bo')
        # plt.plot(self.Distance[self.FrontToeInd],self.Elevation[self.FrontToeInd],'bs')
        # plt.plot(self.Distance[self.BackTopInd],self.Elevation[self.BackTopInd],'ro')
        # plt.plot(self.Distance[self.BackToeInd],self.Elevation[self.BackToeInd],'rs')
        # plt.plot(self.Distance,ElevDetrend,'r-')
        # plt.show()

        # Get Barrier Crest
        Mask = ElevMasked.mask.copy()
        Mask[0:self.FrontToeInd] = True
        Mask[self.BackToeInd] = True
        ElevMasked = ma.masked_where(Mask,self.Elevation)
        self.CrestInd = ma.argmax(ElevMasked)
        self.CrestElevation = ElevMasked[self.CrestInd]
            
        # Calculate Barrier Height, front and back
        self.FrontHeight = self.Elevation[self.FrontTopInd]-self.Elevation[self.FrontToeInd]
        self.BackHeight = self.Elevation[self.BackTopInd]-self.Elevation[self.BackToeInd]
        
        # Calculate Barrier Width, top and bottom
        self.ToeWidth = np.abs(self.Distance[self.FrontToeInd]-self.Distance[self.BackToeInd])
        self.TopWidth = np.abs(self.Distance[self.FrontTopInd]-self.Distance[self.BackTopInd])
        
        # Calculate Slope, front and back
        self.FrontSlope = self.FrontHeight/(self.Distance[self.FrontTopInd]-self.Distance[self.FrontToeInd])
        self.BackSlope = self.BackHeight/(self.Distance[self.BackTopInd]-self.Distance[self.BackToeInd])
        
        # Volume m3/m
        Start, End = ma.notmasked_edges(self.Distance)
        self.DistanceSpacing = self.Distance[Start+1]-self.Distance[Start] # temporary fix
        
        self.BarrierVolume = ma.sum(ElevMasked)*self.DistanceSpacing
        
        self.BarrierVolume -= 0.5 * (ElevMasked[self.FrontToeInd] + ElevMasked[self.BackToeInd-1]) \
                                 * np.abs(self.Distance[self.BackToeInd-1] - self.Distance[self.FrontToeInd])
        

        # switch flag to indicate a barrier has been found
        self.Barrier = True
        
    def ExtractBarrierWidths(self,WaterElevations=[0, 2.5, 5]):

        """
        Extract Barrier widths at all given elevations
        e.g. variable extreme water or projected extreme water

        MDH, June 2019
        
        """

        # check if WaterElevs is single value or list
        if not isinstance(WaterElevations, list):
            self.ExtremeWaterLevels = [WaterElevations]
        else:
            self.ExtremeWaterLevels = WaterElevations
        
        # setup empty lists
        self.ExtremeDistances = ["","",""]
        self.ExtremeIndices = ["","",""]
        self.ExtremeInterpFractions = ["","",""]
        self.ExtremeWidths = ["","",""]
        self.ExtremeVolumes = ["","",""]
        self.ExtremeFrontNodes = ["","",""]
        self.ExtremeBackNodes = ["","",""]
        self.Intersections = ["","",""]

        # loop across elevations and perform analysis
        for i, Elevation in enumerate(self.ExtremeWaterLevels):
            
            self.ExtractBarrierWidth(Elevation)

            # add results to lists
            self.ExtremeDistances[i] = self.ExtremeDistance
            self.ExtremeIndices[i] = self.ExtremeIndex
            self.ExtremeInterpFractions[i] = self.InterpolateFractions
            self.ExtremeWidths[i] = self.ExtremeWidth
            self.ExtremeVolumes[i] = self.ExtremeVolume
            self.ExtremeFrontNodes[i] = self.FrontNode
            self.ExtremeBackNodes[i] = self.BackNode
            self.Intersections[i] = self.Intersection
        
    def ExtractBarrierWidth(self, Elev):

        """
        Extract barrier width at a given elevation (e.g. extreme water level)

        MDH, June 2019
        """

        # add results to lists
        NDV = -9999
        self.ExtremeDistance = [None,None]
        self.ExtremeIndex = [None,None]
        self.InterpolateFractions = [None,None]
        self.ExtremeWidth = None
        self.ExtremeVolume = None
        self.FrontNode = None
        self.BackNode = None
        
        if self.Barrier == False:
            return

        # vector at fixed elevation running the length of the transect
        Start, End = ma.notmasked_edges(self.Distance)
        X1, Y1 = self.Distance[Start], Elev
        X2, Y2 = self.Distance[End], Elev
        
        dX12 = X2-X1
        dY12 = Y2-Y1
        
        # count and record locations of intersection
        IntersectionCounter = 0
        IntersectionIndices = []
        InterpolateFractions = []
        
        # temporary fix for no assignment, need a function for reading in transect topo
        # rather than having it set externally?
        self.NoValues = len(self.Distance)
        self.DistanceSpacing = self.Distance[Start+1]-self.Distance[Start]

        # loop across barrier topography
        for i in range(Start, self.NoValues-1):

            # cut and paste interesction analysis
            # do we want this to be a separate function somewhere?
            # Loop through transects and count no of intersections with the barrier
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
                S = dX12*dY31 - dY12*dX31
                T = dX34*dY31 - dY34*dX31
                
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
                    Fraction = np.abs((Elev-Y3)/dY34)
                    InterpolateFractions.append(Fraction)
        
        # calculate width and volume at this elevation
        # if no intersection then either barrier crest is too low
        # or back barrier is too high
        if IntersectionCounter == 0:
            if (self.CrestElevation < Elev):
                self.ExtremeWidth = 0.
                self.ExtremeVolume = 0.
                self.Intersection = False

        elif IntersectionCounter > 1:
            
            # Define Intersection Distance and Elevation by Interpolating
            ExtremeDist1 = self.Distance[IntersectionIndices[0]] + InterpolateFractions[0]*self.DistanceSpacing
            ExtremeDist2 = self.Distance[IntersectionIndices[1]] + InterpolateFractions[1]*self.DistanceSpacing
            
            # Record distances
            self.ExtremeDistance = [ExtremeDist1,ExtremeDist2]
            self.ExtremeIndex = [IntersectionIndices[0], IntersectionIndices[1]]
            self.InterpolationFractions = [InterpolateFractions[0], InterpolateFractions[1]]
            
            # Define Intersection X and Y coordinates by Interpolating
            # Calculate position of front intersection
            X1 = self.StartNode.X + ExtremeDist1 * np.sin( np.radians( self.Orientation ) )
            Y1 = self.StartNode.Y + ExtremeDist1 * np.cos( np.radians( self.Orientation ) )
            self.FrontNode = Node(X1,Y1,Elev)

            # Calculate position of back intersection
            X2 = self.StartNode.X + ExtremeDist2 * np.sin( np.radians( self.Orientation ) )
            Y2 = self.StartNode.Y + ExtremeDist2 * np.cos( np.radians( self.Orientation ) )
            self.BackNode = Node(X2,Y2,Elev)

            # Calculate Width
            self.ExtremeWidth = self.Distance[IntersectionIndices[1]] + InterpolateFractions[1]*self.DistanceSpacing \
                                - self.Distance[IntersectionIndices[0]] + InterpolateFractions[0]*self.DistanceSpacing
            
            # Calculate Volume
            self.ExtremeVolume = np.sum(self.Elevation[IntersectionIndices[0]+1:IntersectionIndices[1]+1]-Elev)*self.DistanceSpacing
        
            # flag that an intersection has occurred
            self.Intersection = True

    def Plot(self, PlotFolder):
        
        """
        
        MDH, June 2019

        """

        # grab colour map
        ColourMap = cm.viridis

        # create figure
        fig = plt.figure(1,figsize=(6,3))
                
        # create 4 subplots
        ax = plt.subplot(111)
                
        # temp fix to masked array legacy problem
        self.Distance = ma.masked_where(self.Elevation.mask,self.Distance)

        # plot raw data
        ax.plot(self.Distance, self.Elevation, '-', lw=1., c=[0.5,0.5,0.5], zorder=21)
                
        # plot range
        #ax.fill_between(self.Distance, self.ElevationMin, self.ElevationMax, color=[0.8,0.8,0.8], zorder=10)
        
        # add cliff details here
        if self.Cliff:
            
            # plot top to toe
            CliffColour = [0.6,0.4,0.1]
            ax.plot(self.Distance[self.CliffToeInd:self.CliffTopInd], self.Elevation[self.CliffToeInd:self.CliffTopInd], '-', c=CliffColour, lw=1., zorder=22)
            ax.plot(self.Distance[self.CliffTopInd], self.Elevation[self.CliffTopInd], 'ko', mfc=CliffColour, zorder=31)
            ax.plot(self.Distance[self.CliffToeInd], self.Elevation[self.CliffToeInd], 'ko', mfc=CliffColour, zorder=31)
            
        # # add barrier details here
        if self.Barrier:
        
            # create array for filling in geometry
            DistFill = self.Distance[self.FrontToeInd:self.BackToeInd+1]
            ElevFill = self.Elevation[self.FrontToeInd:self.BackToeInd+1]
            LowerFill = np.linspace(ElevFill[0],ElevFill[-1],len(ElevFill)) 
        
            # plot the barrier profile and points
            ax.fill_between(DistFill, ElevFill, LowerFill, color=[0.8,0.8,0.8], zorder=10)
            ax.plot(DistFill, ElevFill, 'k-', lw=1., zorder=22)
            ax.plot(self.Distance[self.FrontTopInd], self.Elevation[self.FrontTopInd], 'ko', ms=2, zorder=32)
            ax.plot(self.Distance[self.FrontToeInd], self.Elevation[self.FrontToeInd], 'ko', ms=2, zorder=32)
            ax.plot(self.Distance[self.BackTopInd], self.Elevation[self.BackTopInd], 'ko', ms=2, zorder=32)
            ax.plot(self.Distance[self.BackToeInd], self.Elevation[self.BackToeInd], 'ko', ms=2, zorder=32)
        
        # add extreme water lines and volumes
        if self.Intersection:
            
            for i, WaterLevel in enumerate(self.ExtremeWaterLevels):
                
                if self.ExtremeWidths[i] is None:
                    continue

                # get colour
                Colour = 1.5*float(i)/(len(self.ExtremeWaterLevels))
                LineColour = ColourMap(Colour)
    
                # plot line and extend seaward
                LineDists = self.ExtremeDistances[i].copy()
                LineDists[0] -= 20.
                ax.plot(LineDists, [WaterLevel,WaterLevel], '-', lw=1., color=LineColour, zorder=20)
                
                # colour in, this will have minor bug for now due to abs argmin returning either node before or node after
                Inds = self.ExtremeIndices[i]
                DistFill = np.insert(self.ExtremeDistances[i], 1, self.Distance[Inds[0]+1:Inds[1]])
                ElevFill = np.insert(np.array([WaterLevel, WaterLevel]), 1, self.Elevation[Inds[0]+1:Inds[1]])
                LowerFill = np.linspace(ElevFill[0],ElevFill[-1],len(ElevFill))
                
                # lighten the colour slightly
                LighterColour = ColourMap(Colour+0.1)
                
                # and shade in the region above the extreme elevation
                ax.fill_between(DistFill, ElevFill, LowerFill, color=LighterColour, zorder=11+i)

        # label axes
        ax.set_aspect(10.)
        ax.set_ylabel("Elevation (m)")
        ax.set_xlabel("Distance (m)")

        # set axis limits 
        Start, End = ma.notmasked_edges(self.Distance)
        
        try:
            ax.set_xlim([self.Distance[Start],self.Distance[self.CliffToeInd]])
            
        except:
            ax.set_xlim([self.Distance[Start],self.Distance[End]])
        
        # add text
        plt.title("Transect "+str(self.ID))

        # tight layout!
        plt.tight_layout()

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

    def get_BarrierPosition(self):

        """
        Calculates the position of nodes that define the barrier based on the top and toe
        on the front and back side, plus the crest of the barrier

        MDH, July 2019

        """

        if not self.Barrier:
            sys.exit("Transect.get_BarrierPosition: Not a barrier!")

        # get distances
        BarrierFrontTopDist = self.Distance[self.FrontTopInd]
        BarrierFrontToeDist = self.Distance[self.FrontToeInd]
        BarrierBackTopDist = self.Distance[self.BackTopInd]
        BarrierBackToeDist = self.Distance[self.BackToeInd]
        CrestDist = self.Distance[self.CrestInd]
        
        # Calculate position of barrier front top
        X1 = self.StartNode.X + BarrierFrontTopDist * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y + BarrierFrontTopDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of barrier front toe
        X2 = self.StartNode.X + BarrierFrontToeDist * np.sin( np.radians( self.Orientation ) )
        Y2 = self.StartNode.Y + BarrierFrontToeDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of barrier back top
        X3 = self.StartNode.X + BarrierBackTopDist * np.sin( np.radians( self.Orientation ) )
        Y3 = self.StartNode.Y + BarrierBackTopDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of barrier back toe
        X4 = self.StartNode.X + BarrierBackToeDist * np.sin( np.radians( self.Orientation ) )
        Y4 = self.StartNode.Y + BarrierBackToeDist * np.cos( np.radians( self.Orientation ) )
        
        # Calculate position of crest
        X5 = self.StartNode.X + CrestDist * np.sin( np.radians( self.Orientation ) )
        Y5 = self.StartNode.Y + CrestDist * np.cos( np.radians( self.Orientation ) )
        Z5 = self.Elevation[self.CrestInd]

        return Node(X1, Y1), Node(X2, Y2), Node(X3, Y3), Node(X4, Y4), Node(X5, Y5, Z5)

    def get_ExtremePosition(self,Ind):
        
        """
        return nodes for extreme front position and back position and index Ind
        Ind must be 0, 1, or 2, for low, medium and high water levels

        MDH, July 2019
        
        """
        if not Ind in [0,1,2]:
            sys,exit("Transect.get_ExtremePosition (Error): mist be an integer for extreme water (0,1, or 2)") 
            
        FrontDist = self.ExtremeDistances[Ind][0]
        BackDist = self.ExtremeDistances[Ind][1]

        if not isinstance(FrontDist,float):
            return
        elif not isinstance(BackDist,float):
            return

        # Calculate position of barrier front top
        X1 = self.StartNode.X + FrontDist * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y + FrontDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of barrier front top
        X2 = self.StartNode.X + BackDist * np.sin( np.radians( self.Orientation ) )
        Y2 = self.StartNode.Y + BackDist * np.cos( np.radians( self.Orientation ) )

        return Node(X1,Y1), Node(X2,Y2)

    def get_CrestPosition(self):

        """
        MDH, July 2019
        
        """
        if self.Barrier:

            # Get Distance
            CrestDistance = self.Distance[self.CrestInd]

            # Calculate position of barrier front top
            X = self.StartNode.X + CrestDistance * np.sin( np.radians( self.Orientation ) )
            Y = self.StartNode.Y + CrestDistance * np.cos( np.radians( self.Orientation ) )
            Z = self.Elevation[self.CrestInd]
            return X, Y, Z
        
        else:
            return

    def get_FrontPosition(self):

        """
        MDH, July 2019
        
        """
        if self.Barrier:

            # Get Distance
            FrontDistance = self.Distance[self.FrontTopInd]

            # Calculate position of barrier front top
            X = self.StartNode.X + FrontDistance * np.sin( np.radians( self.Orientation ) )
            Y = self.StartNode.Y + FrontDistance * np.cos( np.radians( self.Orientation ) )
            Z = self.Elevation[self.FrontTopInd]
            return X, Y, Z
        
        else:
            return


    def Write(self, Folder=os.getcwd(), delimiter=","):
        
        """
        
        Write transect topography to file

        Can sepcify filename or create using default name + ID
        
        MDH, July 2019

        """

        # define filename and open for writing
        Filename=Folder+"Transect_"+str(self.ID)+".csv"
        f = open(Filename,'w')
        
        # write headers
        f.write("X" + delimiter + "Y" + "\n")
        f.write(str(self.StartNode.X) + delimiter + str(self.StartNode.Y) + "\n")
        f.write(str(self.EndNode.X) + delimiter + str(self.EndNode.Y) + "\n")
        f.write("Distance" + delimiter + "Z" + "\n")

        #loop through transect and write data
        for (dist, z) in zip(self.Distance, self.Elevation):
            f.write(str(dist) + delimiter + str(z) + "\n")

        f.close()