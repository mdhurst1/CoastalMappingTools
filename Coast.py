"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import numpy as np
import numpy.ma as ma
import shapefile
import itertools
import rasterio
from Line import *
from IPython.display import clear_output

class Coast:
    """
    Description of object goes here

    """

    def __init__(self, CoastShp=""):
        """
        MDH, June 2019
        """

        print("Coast: Initialising Coast object")

        self.CoastShp = CoastShp
        self.Shapes = []
        self.Fields = []
        self.Records = []
        self.NoCoastLines = 0
        self.CoastLines = []
        self.Projection = ""
        self.OverallOrientation = 0.
        self.TransectsSpacing = 10.
        self.TransectsLength2Sea = 200.
        self.TransectsLength2Land = 1000.

        if CoastShp:
            self.ReadCoastShp(CoastShp)

        else:
            print("Coast: Generating empty coast object")

    def __str__(self):
        String = "Coast Object:\n\tFile: %s\n\tNumber of Coastlines:%d\n\t" % (str(self.CoastShp), self.NoCoastLines)
        return String

    # read coast from a shapefile
    def ReadCoastShp(self,CoastShp):

        # Open coast polyline file for reading
        SF = shapefile.Reader(CoastShp)
        self.Shapes = SF.shapes()
        self.Fields = SF.fields
        self.Records = SF.records()

        # Get number of coast segments to work on
        self.NoCoastLines = len(self.Shapes)
        print("Coast.ReadCoastShp: Read Coastline, no of coast segments is", self.NoCoastLines)
    
        # Generate coast nodes for each segment
        for i in range(0,self.NoCoastLines):
            
            # get X and Y coordinates of segment
            X, Y = np.array(self.Shapes[i].points).T
            
            # Set up a line object for each
            ThisLine = Line(str(i), X, Y)

            # append to list of coast lines
            self.CoastLines.append(ThisLine)
            
        # get projection strings
        f = open(CoastShp.rstrip("shp")+"prj")
        self.Projection = f.read()
        f.close()
 
    def WriteCoastShp(self,CoastShp):
        """
        Writes the contents of a Coast object to polyline shape file

        MDH, June 2019

        """

        # open new shapefile        
        WL = shapefile.Writer(CoastShp,shapeType=shapefile.POLYLINE)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0]]
        WL.fields = self.Fields[1:] 

        for Line in self.CoastLines:
            
            # get line node positions
            X, Y = Line.get_XY()
            WriteLine = [np.column_stack([X,Y]).tolist()]
            
            # generate record
            Record = [str(Line.ID)]

            # write line and record
            WL.line(WriteLine)
            WL.record(*Record) ####### ISSUE WITH RECORDS NEEDS FIXING ########
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(CoastShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WriteTransectsShp(self, TransectsShp):

        """
        Writes the transects of a Coast object to polyline shape file

        MDH, June 2019

        """

        # open new shapefile        
        WL = shapefile.Writer(TransectsShp,shapeType=shapefile.POLYLINE)
        
        # Create Fields
        Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0],['Transect_ID', 'C', 3, 0]] #['Segment_ID','C', 3, 0], might add
        WL.fields = Fields[1:]

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                # get transect node positions
                X, Y = Transect.get_XY()
                WriteTransect = [np.column_stack([X,Y]).tolist()]

                # Create the record
                Record = [str(Line.ID), str(Transect.ID)]

                # write transect and record
                WL.line(WriteTransect)
                WL.record(*Record) 
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(TransectsShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()


    def WritePointsShp(self, PointsShp):
        """
        Function to write transect points to a point shape file

        MDH, June 2019
        
        """

        WP = shapefile.Writer(PointsShp, shapeType=shapefile.POINT)
        
        # Create Fields
        Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0],['Transect_ID', 'C', 3, 0]] #['Segment_ID','C', 3, 0], might add 
        WP.fields = Fields[1:]

        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # Create the record
                Record = [str(Line.ID), str(Transect.ID)]

                # add the line and record
                WP.point(Transect.CoastNode.X, Transect.CoastNode.Y)
                WP.record(*Record)

        # close the shapefiles and clean up
        WP.close()
            
        # create the projection file    
        f = open(PointsShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def MergeCoastLines(self):

        """
        Identifies individual coast Lines that are touching at one end 
        and combines them into a single Line

        Reversal of line directions might cause bugs, works so far

        MDH, June 2019
        """

        print("Coast: Merging coastlines")

        # set up Flag for lines being flipped
        FlagReverse = 1

        while FlagReverse:

            # Update Flag
            FlagReverse = 0

            # Empty lists to populate with new shapes and records
            NewCoastLines = []
            NewShapes = []
            NewRecords = []

            # create list of joins
            JoinsList = np.zeros(self.NoCoastLines,dtype=int)-9999
            JoinedByList = np.zeros(self.NoCoastLines,dtype=int)-9999
            ReversedList = []
            
            # get start and end nodes from line sections
            StartNodes = [CoastLine.Nodes[0] for CoastLine in self.CoastLines]
            EndNodes = [CoastLine.Nodes[-1] for CoastLine in self.CoastLines]
            
            # compare start nodes and end nodes to populate join list
            # this could probably be done better!
            for i, StartNode in enumerate(StartNodes):
                for j, EndNode in enumerate(EndNodes):
                    if i == j:
                        continue
                    elif StartNode == EndNode:
                        JoinsList[j] = i
                        JoinedByList[i] = j

                # check for line direction reversals
                for k, TestNode in enumerate(StartNodes):
                    if i == k:
                        continue
                    elif StartNode == TestNode:
                        if not i in ReversedList:
                            ReversedList.append(k)
                            FlagReverse = 1
            
            # get list of line sections to start at
            StartList = np.where(JoinedByList < 0)[0]
            for StartLine in StartList:
                
                # get vector of line section
                X1, Y1 = self.CoastLines[StartLine].get_XY()
                
                # get first line section to join
                JoinLine = JoinsList[StartLine]

                while JoinLine > -1:
                    
                    # get next line
                    X2, Y2 = self.CoastLines[JoinLine].get_XY()

                    # join the lines
                    X1 = np.concatenate((X1,X2[1:]))
                    Y1 = np.concatenate((Y1,Y2[1:]))

                    # get next n
                    JoinLine = JoinsList[JoinLine]

                # reverse any vectors needing reversing
                if StartLine in ReversedList:
                    X1 = X1[::-1]
                    Y1 = Y1[::-1]

                # write new line, and update shape and records lists
                NewCoastLines.append(Line(self.CoastLines[StartLine].ID, X1, Y1))
                NewShapes.append(np.column_stack([X1,Y1]).tolist())
                NewRecords.append(self.Records[StartLine])
                    
            # update object properties with merged geometries
            self.CoastLines = NewCoastLines
            self.Shapes = NewShapes
            self.Records = NewRecords

            # update number of shapes
            if len(self.CoastLines) != len(self.Shapes):
                sys.exit("Coast.MergeCoastlines(ERROR): Number of shapes and number of lines doesn't match!")
            self.NoCoastLines = len(self.CoastLines)

    def SmoothCoastLines(self, WindowSize=101, PolyOrder=4):
        
        """
        Smooths the CoastLines contained in Coast object
        Wrapper to the function in the Line object
        Calls scipy.signal.savgol_filter

        Savitzky and Golay (1964) smoothing filter
    
        Savitzky, A. and Golay, M. J.: Smoothing and differentiation of data
        by simplified least squares procedures, Anal. Chem., 36, 1627-
        1639, 1964.

        https://docs.scipy.org/doc/scipy-0.15.1/reference/generated/scipy.signal.savgol_filter.html

        MDH, June 2019

        Parameters
        ----------
        WindowLength : int
            The length of the filter window (i.e. the number of coefficients). 
            WindowLength must be a positive odd integer.
        PolyOrder : int
            The order of the polynomial used to fit the samples. 
            PolyOrder must be less than window_length.
        
        """

        print("Coast: Smoothing CoastLines")

        for i, Line in enumerate(self.CoastLines):
            
            # smooth the line
            Line.SmoothLine(WindowSize, PolyOrder)

            # update the shape object list
            X, Y = Line.get_XY()
            self.Shapes[i] = np.column_stack([X,Y]).tolist()

    def ReconfigureCoastLines(self, Direction2OpenWater):
        """
        Function to arrange coastline so that lines are ordered along the coast
        and line segments progress along the coast. The "along coast" direction
        is always that which results in the water being on the left as you look
        down the coastal vector.

        This might be buggy as anything and need lots more work. Should be run
        after MergeCoast and SmoothCoast but before Transects are built, though 
        if Transects have been built they will get rebuilt

        MDH, June 2019

        Parameters
        ----------
        Direction2OpenWater: str
            Text-based description of the general direction to open water
            Cardinal direction
            e.g. "E", "east", "East"
        """

        # get start nodes and end nodes of each line
        StartNodes = []
        EndNodes = []

        for Line in self.CoastLines:

            # check line is oriented in the correct order
            StartNode = Line.Nodes[0]
            EndNode = Line.Nodes[-1]

            if str(Direction2OpenWater).lower()[0] == "e":
                
                # reverse the line and update start and end nodes if required
                if StartNode.Y < EndNode.Y:
                    Line.ReverseLine()
                    StartNode = Line.Nodes[0]
                    EndNode = Line.Nodes[-1]
                
            elif Direction2OpenWater.lower()[0] == "s":
                ErrorString = ("Coast.ReconfigureCoastLine (ERROR): "
                    "This direction top open water [s] has not been implemented yet")
                sys.exit(ErrorString)

            elif Direction2OpenWater.lower()[0] == "w":
                ErrorString = ("Coast.ReconfigureCoastLine (ERROR): "
                    "This direction top open water [w] has not been implemented yet")
                sys.exit(ErrorString)

            elif Direction2OpenWater.lower()[0] == "n":
                ErrorString = ("Coast.ReconfigureCoastLine (ERROR): "
                    "This direction top open water [n] has not been implemented yet")
                sys.exit(ErrorString)

            else:
                ErrorString = ("Coast.ReconfigureCoastLine (ERROR): "
                    "The string representing direction to open water not recognised; "
                    "\n\tshould be [e]ast, [s]outh, [w]est or [n]orth")
                sys.exit(ErrorString)

            StartNodes.append(Line.Nodes[0])
            EndNodes.append(Line.Nodes[-1])
        
        # check the lines are organised in the correct order
        if Direction2OpenWater.lower()[0] == "e":
            
            # sort the lines based on Y or their start node
            # needs to be an array to apply negative sign in order to get descending order
            DescendingIndices = np.argsort(-np.array([Node.Y for Node in StartNodes]))
            
            # here comes some bullshit to convert list to numpy array 
            # in order to sort and then turn back into a list :(
            self.CoastLines = list(np.array(self.CoastLines)[DescendingIndices])
            self.Records = list(np.array(self.Records)[DescendingIndices])
            for i, Line in enumerate(self.CoastLines):
                Line.ID = str(i)

        if len(self.CoastLines[0].Transects) != 0:
            self.GenerateNormals(self.TransectsSpacing, self.TransectsLength2Sea, self.TransectsLength2Land)

        # calculate overall orientation
        StartNode = self.CoastLines[0].Nodes[0]
        EndNode = self.CoastLines[-1].Nodes[-1]

        #calculate the spatial change
        dx = EndNode.X - StartNode.X
        dy = EndNode.Y - StartNode.Y

        #Calculate the orientation of the line from ThisNode to NextNode
        if dx > 0 and dy > 0:
            self.OverallOrientation = np.degrees( np.arctan( dx / dy ) )
        elif dx > 0 and dy < 0:
            self.OverallOrientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy < 0:
            self.OverallOrientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy > 0:
            self.OverallOrientation = 360 + np.degrees( np.arctan( dx / dy ) )

    # function to do something    
    def GenerateNormals(self, TransectSpacing, TransectLength2Sea, TransectLength2Land):
        """
        Wrapper to the function in the Line object

        Generates transects perpendicular to the coastline

        MDH, June 2019

        Parameters
        ----------
        TransectSpacing : float
            The distance between consecutive transects along the CoastLines
            in map units, spatial units depend on units of the CoastLine read in,
            Should be [m]
        TransectLength2Sea : float
            The length of the transect in the direction of sea in map units, 
            spatial units depend on units of the CoastLine read in, Should be [m]
        TransectLength2Land : float
            The length of the transect in the direction of land in map units, 
            spatial units depend on units of the CoastLine read in, Should be [m]
                    
        """
        print("Coast: Generating CoastLine transects perpendicular to the coast")

        self.TransectsSpacing = TransectSpacing
        self.TransectsLength2Sea = TransectLength2Sea
        self.TransectsLength2Land = TransectLength2Land

        for Line in self.CoastLines:

            # generate transects along each line
            Line.GenerateTransects(TransectSpacing, TransectLength2Sea, TransectLength2Land)

    def ExtractTransectTopography(self, DEMFile, SwathDistance=-9999):
        """
        Profile to populate transects with topographic data
        Uses swath profile routine to collect elevations within a certain distance
        of each transect line then takes IDW values for the transect topography

        MDH, June 2019
        
        Parameters
        ----------
        DEMFile : str
            Name of DEM File, must be a *.tif

        SwathDistance : float
            Distance away from transect line to sample elevations in DEM
            Default is 2 times the resolution of the DTM

        """
        
        print("Coast.EstractTransectTopography: Sampling the DTM for each transect")
        
        # load the DTM and get its properties
        print("\tLoading DTM... ", end="")
        DTM_Dataset = rasterio.open(DEMFile)
        DTMArray = DTM_Dataset.read(1)
        NCols = DTM_Dataset.width
        NRows = DTM_Dataset.height
        NDV = DTM_Dataset.nodata
        Resolutions = DTM_Dataset.res
        print("Done")

        # check for square pixels
        if not DTM_Dataset.res[0] == DTM_Dataset.res[1]:
            raise SystemExit("DTM has non-square cells")
        
        # get resolution
        DTM_Resolution = DTM_Dataset.res[0]

        # check swath distance
        if SwathDistance < 0:
            SwathDistance = DTM_Resolution*2.

        # get extent of DTM
        XMin = DTM_Dataset.bounds[0]
        XMax = DTM_Dataset.bounds[2]
        YMin = DTM_Dataset.bounds[1]
        YMax = DTM_Dataset.bounds[3]

        # Get vectors of X and Y coordinates, NB reversal of Y in line with 
        # DTM indexing from top left
        XVector = XMin+np.arange(0,NCols)*DTM_Resolution+0.5*DTM_Resolution
        YVector = YMin+DTM_Resolution*np.arange(0,NRows)[::-1]+0.5*DTM_Resolution

        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])
        CurrentTransect = 0
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # pass DTM
                # this needs to be changed to pass to transect object
                # fix this later

                # print progress to screen
                print("\tTransect %d / %d" % (CurrentTransect, NoTransects), end="\r")
                clear_output()

                #Get line points
                X1, Y1 = Transect.StartNode.get_XY()
                X2, Y2 = Transect.EndNode.get_XY()

                #find indices for bounding box
                #need to be careful with reverse indexing
                iStart = np.argmin(np.abs(YVector-np.max([Y1,Y2])))-1
                iEnd = np.argmin(np.abs(YVector-np.min([Y1,Y2])))+1
                jStart = np.argmin(np.abs(XVector-np.min([X1,X2])))-1
                jEnd = np.argmin(np.abs(XVector-np.max([X1,X2])))+1

                #Get Vector X and Y
                dX12 = X2-X1
                dY12 = Y2-Y1

                #Declare list holders for profile data
                X = []
                Y = []
                Z = []
                DistAlong = []
                DistTo = []
                
                for i in range(iStart,iEnd):

                    #get Y position
                    YNode = YMax-DTM_Resolution*i-0.5*DTM_Resolution

                    for j in range(jStart,jEnd):
                        
                        #get X position
                        XNode = XMin + j*DTM_Resolution + 0.5*DTM_Resolution;

                        #Get 2nd Vector Properties in Array
                        dX13 = XNode-X1
                        dY13 = YNode-Y1

                        #Find Dot Product
                        DotProduct = dX12*dX13 + dY12*dY13;

                        #calculate fraction of distance along line
                        t = DotProduct/(dX12*dX12 + dY12*dY12)
                        if ((t < 0.) or (t > 1.)):
                            continue
                    
                        #Find point along line
                        XLine = X1 + t*dX12
                        YLine = Y1 + t*dY12
                        DistanceAlongLine = t*np.sqrt(dX12*dX12 + dY12*dY12)

                        #find distance to point
                        DistanceToLine = np.sqrt((XLine-XNode)*(XLine-XNode) + (YLine-YNode)*(YLine-YNode))

                        if ((DistanceToLine < SwathDistance) and (DTMArray[i][j] != NDV)):
                            X.append(XNode)
                            Y.append(YNode)
                            DistAlong.append(DistanceAlongLine)
                            DistTo.append(DistanceToLine)
                            Z.append(DTMArray[i][j])
                                
                #Sort by distance along line, need to convert to numpy arrays as we go to sort
                Sortedi = np.argsort(DistAlong)
                X = np.asarray(X)[Sortedi]
                Y = np.asarray(Y)[Sortedi]
                DistAlong = np.asarray(DistAlong)[Sortedi]
                DistTo = np.asarray(DistTo)[Sortedi]
                Z = np.asarray(Z)[Sortedi]
                
                #if (WriteSwathDataFlag):
                    # Write results to text file using pandas (easier) for each profile
                    #DF = pd.DataFrame({"X": X, "Y": Y, "Z": Z, "DistAlong": DistAlong, "DistTo": DistTo})
                    #DF.to_pickle(SwathProfsFolder+"Swath_"+str(Transect.ID)+".pkl")
                
                #Create a line for interpolating to
                LineLength = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
                NoPoints = (int)(LineLength/(DTM_Resolution*2.))
                XLine = np.linspace(X1,X2,NoPoints)
                YLine = np.linspace(Y1,Y2,NoPoints)
                DistAlongTransect = np.zeros(len(XLine))
                ZIDW = np.zeros(len(XLine))
                ZMin = np.zeros(len(XLine))
                ZMax = np.zeros(len(XLine))
                                
                #Loop along line
                for i in range(0,NoPoints):
                    
                    #Calculate distance along the line
                    DistAlongTransect[i] = i*DTM_Resolution*2.
                    
                    # Sample a reduced array here i.e. a neighbourhood to reduce computation time
                    Neighbourhood = np.abs(DistAlongTransect[i]-DistAlong) < DTM_Resolution*2.
                    ZLocal = Z[Neighbourhood]
                    
                    if len(ZLocal) == 0:
                        
                        # Set to NDV
                        ZIDW[i] = NDV
                        ZMin[i] = NDV
                        ZMax[i] = NDV
                        continue
                    
                    # Do IDW
                    # Create a distance vector
                    Dist = np.sqrt(DistAlong[Neighbourhood]**2. + DistTo[Neighbourhood]**2.)
                    
                    # Weights are inverse
                    Weights = 1./Dist**2.
                    
                    # Interpolate Z
                    ZIDW[i]  = np.sum(Z[Neighbourhood]*Weights)/np.sum(Weights)
                    
                    # Other Z Values
                    ZMin[i] = np.min(ZLocal)
                    ZMax[i] = np.max(ZLocal)
                    
                # Set up the mask from NDVs
                Mask = ZIDW == -9999
                DistAlongTransect = ma.masked_where(Mask,DistAlongTransect)
                ZIDW = ma.masked_where(Mask,ZIDW)
                ZMin = ma.masked_where(Mask,ZMin)
                ZMax = ma.masked_where(Mask,ZMax)
                
                Transect.Distance = DistAlongTransect
                Transect.Elevation = ZIDW
                Transect.ElevationMin = ZMin
                Transect.ElevationMax = ZMax

                # update transect no
                CurrentTransect += 1

    def AnalyseTransectMorphology(self):

        """

        Barrier focus for now

        MDH, June 2019

        """

        print("Coast.AnalyseTransectMorphology: Finding barrier positions and calculating metrics")

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                # do something or call something
                Transect.AnalyseMorphology()

    def PlotTransects(self, PlotFolder):
        
        """

        Description goes here

        MDH, June 2019

        """

        print("Coast.PlotTransects: Plotting each transect topographic profile")

        # loop through lines and plot profiles #
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                    
                # call plotting function
                Transect.Plot(PlotFolder)


    def PlotBarrierProperties(self, PlotFolder):
        """
        """

        #import figure plotting stuff here not globally!
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt

        # set up a figure
        # in time might want to automatically adjust figure for coast orientation
        fig, ax = plt.figure(1,figsize=(8,4))
        
        for Line in self.Coastlines:
            
            # get property to plot
            W  = [Transect.ToeWidth for Transect in Line.Transects]
            plt.plot(W,range(0,len(W)),'k-',lw=2)
        
        plt.xlabel("Barrier Width at Toe (m)")
        plt.ylabel("Transect ID")
        plt.savefig(PlotFolder + "BarrierWidth.png")