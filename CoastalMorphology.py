"""
Description of file goes here

Martin D. Hurst
Unviersity of Glasgow
Febraury 2019

"""

# import modules

# system level
import os

# numerical and statistical packages
import numpy as np
from scipy.signal import savgol_filter
import pandas as pd

# spatial packages
import rasterio
import shapefile

# plotting packages
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

def ReadCoastlineShp(CoastLineShp):

    """
    """
    
    # Open coast polyline file for reading
    SF = shapefile.Reader(CoastLineShp)
    Shapes = SF.shapes()
    Fields = SF.fields
    Records = SF.records()
    NoShapes = len(Shapes)
    print("\tReadCoastlineShp: Read Coastline, no of segments is", NoShapes)
    
    # get projection strings
    f = open(CoastLineShp.rstrip("shp")+"prj")
    Projection = f.read()
    f.close()
    
    return Shapes, Fields, Records, NoShapes, Projection

def WriteCoastlineShp(CoastLineShp,Projection,X,Y,Fields,Record):
    
    """
    """
    
    # check if updating existing shapefile
    Update = os.path.exists(CoastLineShp)
    
    # if so we need to make a temporary copy of the old file to read
    # we then overwrite the existing file
    if Update:
        RL = shapefile.Reader(CoastLineShp)
        ShapeRecs = RL.shapeRecords()
        RL.close()
    
    # open new shapefile        
    WL = shapefile.Writer(CoastLineShp,shapeType=shapefile.POLYLINE)
    WL.fields = Fields[1:]
    
    if Update:
        for ShapeRec in ShapeRecs:
            WL.record(*ShapeRec.record)
            WL.shape(ShapeRec.shape)
      
    # add the line and record
    WL.line([np.column_stack([X,Y]).tolist()])
    WL.record(*Record)
    
    # close the shapefiles and clean up
    WL.close()
        
    # create the projection file    
    f = open(CoastLineShp.rstrip("shp")+"prj","w")
    f.write(Projection)
    f.close()

def WritePointShp(PointsShp,Projection,point_x,point_y,Fields,Record):
    
    """
    """
    
    # check if updating existing shapefile
    Update = os.path.exists(PointsShp)
    
    # if so we need to make a temporary copy of the old file to read
    # we then overwrite the existing file
    if Update:
        RP = shapefile.Reader(PointsShp)
        ShapeRecs = RP.shapeRecords()
        RP.close()
    
    # open writer object for polyline and assign fields
    WP = shapefile.Writer(PointsShp, shapeType=shapefile.POINT)
    WP.fields = Fields[1:]
    
    if Update:
        for ShapeRec in ShapeRecs:
            WP.record(*ShapeRec.record)
            WP.shape(ShapeRec.shape)
            
    # add the line and record
    WP.point(point_x,point_y)
    WP.record(*Record)
    
    # save the shapefile
    WP.close()

    # create the projection file    
    f = open(PointsShp.rstrip("shp")+"prj","w")
    f.write(Projection)
    f.close()
    

def MergeCoastline(CoastLineShp,MergedCoastLineShp):
    
    """
    Merges coastal segments if they are touching
    Drops attributes as a result since unique to segments
    
    THIS NEEDS MORE WORK AS CURRENTLY SEGMENTS NOT IN ORDER DOWN THE COAST!
    
    """
    
    print("MergeCoastline: ", CoastLineShp)
    
    # Read coastline 
    Shapes, Fields, Records, NoShapes, Projection = ReadCoastlineShp(CoastLineShp)
    
    # Replace  Fields
    Fields = [('DeletionFlag','C',1,0),['Segment_ID', 'C', 3, 0]]
    ID = 0
    
    # loop through each coastline segment starting at segment #1 and check
    # for start and edn points being identical within floating point precision
    for i in range(0, NoShapes):
        
        print("\tSegment #" +str(i),)
        
        # get X and Y coordinates of both segments
        # segment 1 only needs defining first time round as will be dynamic
        if i == 0:
            X1, Y1 = np.array(Shapes[i].points).T
        
        # only define second segment and test if not at the end of the file
        if i < NoShapes-1:
            X2, Y2 = np.array(Shapes[i+1].points).T

            # check for a match
            if ((X1[-1] == X2[0]) and (Y1[-1] == Y2[0])):
                X1 = np.concatenate((X1,X2[1:]))
                Y1 = np.concatenate((Y1,Y2[1:]))
            
            else:
                # write results to new shapefile
                Record = [str(ID)]
                print(Record)
                WriteCoastlineShp(MergedCoastLineShp,Projection,X1,Y1,Fields,Record)
                ID += 1
                X1 = X2
                Y1 = Y2
        else:
            # write results to new shapefile
            Record = [str(ID)]
            WriteCoastlineShp(MergedCoastLineShp,Projection,X1,Y1,Fields,Record)    
            ID += 1
    
def SmoothCoastline(CoastLineShp,SmoothedCoastLineShp):
    
    """
    Savitzky and Golay (1964) smoothing filter
    
    Savitzky, A. and Golay, M. J.: Smoothing and differentiation of data
    by simplified least squares procedures, Anal. Chem., 36, 1627–
    1639, 1964.

    """
    
    print("SmoothCoastline: ", CoastLineShp)
    
    # Read coastline 
    Shapes, Fields, Records, NoShapes, Projection = ReadCoastlineShp(CoastLineShp)
    
    if os.path.exists(SmoothedCoastLineShp):
        print("\tSmoothed coast shapefile already exists, overwriting")
        os.remove(SmoothedCoastLineShp)
        
    # loop through each coastline segment and smooth
    for i in range(0, NoShapes):
        
        print("\tSegment #" +str(i),)
        
        # get X and Y coordinates of segment
        X, Y = np.array(Shapes[i].points).T
        
        # smooth X and Y individually with Savitzky Golay filter
        # window size and polyorder must be integers you idiot!
        WindowSize = 1001
        PolyOrder = 4
        XSmooth = savgol_filter(X,WindowSize,PolyOrder, mode="nearest")
        YSmooth = savgol_filter(Y,WindowSize,PolyOrder, mode="nearest")
        
        # write results to shapefile
        WriteCoastlineShp(SmoothedCoastLineShp,Projection,XSmooth,YSmooth,Fields,Records[i])        

def GenerateCoastalNormals(CoastLineShp,ProfSpacing,l2sea = 1500.0,l2land = 200.0):

    """

    Function to generate coast normal profiles

    l2sea is length of profile in the seaward direction
    l2land is length of profile in the landward direction

    Martin Hurst, September 2012

    """

    print("GenerateCoastalNormals: Generating Transects perpendicular to the coast")

    # Read coastline 
    Shapes, Fields, Records, NoShapes, Projection = ReadCoastlineShp(CoastLineShp)

    # Generate output file names
    PointsShp = CoastLineShp.rsplit(".")[0]+"_points.shp"
    CoastTransectsShp = CoastLineShp.rsplit(".")[0]+"_transects.shp"
    
    # Replace  Fields
    Fields = [('DeletionFlag','C',1,0),['Transect_ID', 'C', 3, 0]]
    
    # open writer object for polyline and assign fields
    WP = shapefile.Writer(PointsShp, shapeType=shapefile.POINT)
    WP.fields = Fields[1:]
        
     # open writer object for polyline and assign fields
    WL = shapefile.Writer(CoastTransectsShp, shapeType=shapefile.POLYLINE)
    WL.fields = Fields[1:]
    
    # Give each transect unique ID
    TransectCount = 0
    
    # Loop through each row in the shapefile, obtain the name of the associated grid tile from the
    # NG_GRID_RE field and use this to get the NextMap tile from the S drive
    # field = "TILE_NAME"
    for i in range(0, NoShapes):
        
        Shape = Shapes[i]
        NoSegs = len(Shape.points)-1
        
        print("\tShape number: " + str(i) + "; number of segments: " + str(NoSegs))
        # Parameters for tracing along length
        cum_length = 0.0
        next_point = ProfSpacing
        
        # print "Done\n\tGenerating orientations and getting profiles..."
        # Cycle through segments and get their orientation
        # Track spacing and generate profile at desired distances
        for i in range(0, NoSegs):

            #Get start and end coordinates of the segment
            x1, y1 = Shape.points[i]
            x2, y2 = Shape.points[i+1]

            #calculate the spatial change
            dx = x2 - x1
            dy = y2 - y1

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

            #Calculate the length of the segment
            length = np.sqrt( (x2 - x1)**2.0 + (y2 - y1)**2.0)

            #Update the cumulative length of the line
            cum_length += length

            # Test to see if we're going to create a cross section
            while cum_length > next_point:

                #calculate point for section
                distance_to_step_back = cum_length - next_point

                dx = distance_to_step_back * np.sin( np.radians( Orientation ) )
                dy = distance_to_step_back * np.cos( np.radians( Orientation ) )
                
                # find the point for the transect
                point_x = x2 - dx
                point_y = y2 - dy

                #Create cross section line
                #Get line orientation
                if Orientation < 0:
                    TransectOrientation = Orientation + 90.0
                else:
                    TransectOrientation = Orientation - 90.0

                #Calculate start and end nodes
                x = point_x + l2sea * np.sin( np.radians( TransectOrientation ) )
                y = point_y + l2sea * np.cos( np.radians( TransectOrientation ) )
                end_point_x = point_x - l2land * np.sin( np.radians( TransectOrientation ) )
                end_point_y = point_y - l2land * np.cos( np.radians( TransectOrientation ) )

                # Create the record
                Record = [str(TransectCount)]
                
                # add the line and record
                WP.point(point_x,point_y)
                WP.record(*Record)
                
                # add the line and record
                WL.line([[[x,y],[end_point_x,end_point_y]]])
                WL.record(*Record)
    
                # update to find next transect
                TransectCount += 1
                next_point += ProfSpacing
    
    # save the shapefiles
    WP.close()
    WL.close()

    # create the projection files
    f = open(PointsShp.rstrip("shp")+"prj","w")
    f.write(Projection)
    f.close()
    
    # create the projection file    
    f = open(CoastTransectsShp.rstrip("shp")+"prj","w")
    f.write(Projection)
    f.close()

def ExtractSwathProfiles(Folder,CoastTransectsShp,DTM,SwathDist):
    
    """
    
    Function to extract swath profile elevation data for each coastal transect
    
    Martin Hurst, February 2019
    University of Glasgow
    
    """
    
    print("ExtractSwathProfiles: Generating Elevation Swath Profiles perpendicular to the coast")

    # load the DTM and get its properties
    DTM_Dataset = rasterio.open(DTM)
    DTMArray = DTM_Dataset.read(1)
    NCols = DTM_Dataset.width
    NRows = DTM_Dataset.height
    NDV = DTM_Dataset.nodata
    Resolutions = DTM_Dataset.res
    
    # check for square pixels
    if Resolutions[0] == Resolutions[1]:
        DTM_Resolution = Resolutions[0]
        
    else:
         raise SystemExit("DTM has non-square cells")
    
    # get extent of DTM
    XMin = DTM_Dataset.bounds[0]
    XMax = DTM_Dataset.bounds[2]
    YMin = DTM_Dataset.bounds[1]
    YMax = DTM_Dataset.bounds[3]
    
    # set up the workspace
    SwathProfsFolder = Folder + "SwathProfs/"

    if os.path.exists(SwathProfsFolder) is False:
        os.mkdir(SwathProfsFolder)
        

    # Open transects file and read shapes and records
    RL = shapefile.Reader(CoastTransectsShp)
    ShapeRecs = RL.shapeRecords()
    RL.close()
    
    # Get vectors of X and Y coordinates, NB reversal of Y in line with 
    # DTM indexing from top left
    XVector = XMin+np.arange(0,NCols)*DTM_Resolution+0.5*DTM_Resolution
    YVector = YMin+DTM_Resolution*np.arange(0,NRows)[::-1]+0.5*DTM_Resolution

    #######################################################
    # loop through lines and get Swath Profile Elevations #
    #######################################################
    
    for l, ShapeRec in enumerate(ShapeRecs):
        
        #Get line points
        X1,Y1 = ShapeRec.shape.points[0]
        X2,Y2 = ShapeRec.shape.points[1]

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

                if (DistanceToLine < SwathDist):
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
        
        # Write results to text file using pandas (easier) for each profile
        DF = pd.DataFrame({"X": X, "Y": Y, "Z": Z, "DistAlong": DistAlong, "DistTo": DistTo})
        DF.to_csv(SwathProfsFolder+"Swath_"+str(l)+".csv")

def TransectProfilesIDW(Folder,CoastTransectsShp,DTM,SwathDist):
    
    """
    
    Function to peform inverse distance weighting to swath profile data
    to generate the coastal elevation profile
    
    Martin Hurst, December 2015
    
    """
    
    print("TransectProfilesIDW: Generating Elevation Profiles from swath profiles")

    # Open transects file and read shapes and records
    RL = shapefile.Reader(CoastTransectsShp)
    ShapeRecs = RL.shapeRecords()
    RL.close()
    
    # Get DTM properties (but not elevation array)
    DTM_Dataset = rasterio.open(DTM)
    Resolutions = DTM_Dataset.res
    
    # check for square pixels
    if Resolutions[0] == Resolutions[1]:
        DTM_Resolution = Resolutions[0]
        
    else:
         raise SystemExit("DTM has non-square cells")
         
    # set up the workspace
    SwathProfsFolder = Folder + "SwathProfs/"
    ProfsFolder = Folder + "Profiles/"
    
    if os.path.exists(SwathProfsFolder) is False:
        raise SystemExit("No swath profiles to analyse. Run ExtractSwathProfiles function first.")

    if os.path.exists(ProfsFolder) is False:
        os.mkdir(ProfsFolder)
        
    ###########################################################
    # loop through lines and analyse Swath Profile Elevations #
    ###########################################################
    
    for l, ShapeRec in enumerate(ShapeRecs):
        
        # load transect csv file
        DF = pd.read_csv(SwathProfsFolder+"Swath_"+str(l)+".csv")
        DistAlong = DF['DistAlong'].values
        DistTo = DF['DistTo'].values
        Z = DF['Z'].values
        
        #Get line points
        X1,Y1 = ShapeRec.shape.points[0]
        X2,Y2 = ShapeRec.shape.points[1]
        
        #Create a line for interpolating to
        LineLength = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
        NoPoints = (int)(LineLength/DTM_Resolution)
        XLine = np.linspace(X1,X2,NoPoints)
        YLine = np.linspace(Y1,Y2,NoPoints)
        DistAlongLine = np.zeros(len(XLine))
        ZMin = np.zeros(len(XLine))
        ZMax = np.zeros(len(XLine))
        Z16 = np.zeros(len(XLine))
        Z50 = np.zeros(len(XLine))
        Z84 = np.zeros(len(XLine))
        ZMean = np.zeros(len(XLine))
        ZStd = np.zeros(len(XLine))
        ZIDW = np.zeros(len(XLine))
        
        #Loop along line
        for i in range(0,NoPoints):
            
            #Calculate distance along the line
            DistAlongLine[i] = i*DTM_Resolution
            
            #Could sample a reduced array here i.e. a neighbourhood?
            Neighbourhood = np.abs(DistAlongLine[i]-DistAlong) < SwathDist
            ZLocal = Z[Neighbourhood]
            
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
            Z16[i] = np.percentile(ZLocal,16)
            Z50[i] = np.percentile(ZLocal,50)
            Z84[i] = np.percentile(ZLocal,84)
            ZMean[i] = np.mean(ZLocal)
            ZStd[i] = np.std(ZLocal)
        
        # Calculate Slope and Curvature of IDW profile
        Slope = np.gradient(ZIDW,DTM_Resolution)
        Curvature = np.gradient(Slope,DTM_Resolution)
        
        # Write results to text file using pandas (easier) for each profile
        DF = pd.DataFrame({"X": XLine, "Y": YLine, "DistAlong": DistAlongLine,
                           "ZIDW": ZIDW, "ZMin": ZMin, "ZMax": ZMax, 
                           "Z16": Z16, "Z50": Z50, "Z84": Z84, 
                           "ZMean": ZMean, "ZStd": ZStd,
                           "Slope": Slope, "Curvature": Curvature})
    
        DF.to_csv(ProfsFolder+"Profile_"+str(l)+".csv")

def PlotProfiles(Folder,CoastTransectsShp):
    
    # Open transects file and read shapes and records
    RL = shapefile.Reader(CoastTransectsShp)
    ShapeRecs = RL.shapeRecords()
    RL.close()
    
    # set up the workspace
    ProfsFolder = Folder + "Profiles/"
    if os.path.exists(ProfsFolder) is False:
        raise SystemExit("No profiles to analyse. Run TransectProfilesIDW first.")

    ########################################
    # loop through lines and plot profiles #
    ########################################
    
    for l, ShapeRec in enumerate(ShapeRecs):
        
        # load transect csv file
        DF = pd.read_csv(ProfsFolder+"Profile_"+str(l)+".csv")
        
        # create figure
        fig = plt.figure(1,figsize=(8,10))
        
        # create 4 subplots
        ax1 = fig.add_subplot(411)
        ax2 = fig.add_subplot(412)
        ax3 = fig.add_subplot(413)
        ax4 = fig.add_subplot(414)
        
        # plot profile
        ax1.plot(DF["DistAlong"], DF["ZIDW"],'k-')
        plt.ylabel("Elevation (m)")
        
        # plot slope
        ax2.plot(DF["DistAlong"],DF["Slope"],'b-')
        plt.ylabel("Slope (m/m)")
        
        # plot curvature
        ax3.plot(DF["DistAlong"],DF["Curvature"],'r-')
        plt.ylabel("Curvature (1/m)")
        
        # plot roughness
        ax4.plot(DF["DistAlong"],DF["ZStd"],'m-')
        plt.xlabel("Distance (m)")
        plt.ylabel("Roughness (m/m)")
        
        plt.savefig(ProfsFolder+"Profile_"+str(l)+".png")
        raise SystemExit
          
if __name__ == "__main__":
    
    # declare folder name for storing results
    Folder = "D:/NCCA2/StAndrews/CoastalMorphology/"
    if os.path.exists(Folder) is False:
        os.mkdir(Folder)
        
    # declare some file names
    CoastLineShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018_Dissolve.shp"
    MergedCoastLineShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018_Merged.shp"
    SmoothCoastLineShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018_Smooth.shp"
    CoastTransectsShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018_Smooth_transects.shp"
    DTM = "D:/NCCA2/StAndrews/DTM/StAn_2018_DTM.tif"
    
    # launch merging
    #MergeCoastline(Folder,CoastLineShp, MergedCoastLineShp)
    
    # launch smoothing
    #SmoothCoastline(CoastLineShp,SmoothCoastLineShp)
    
    # generate normals
    #GenerateCoastalNormals(SmoothCoastLineShp,50.,200.,50.)
    
    # extract swath profiles
    SwathDist = 2. # 1/2 width of swath profile in map units (probably metres)
    #ExtractSwathProfiles(Folder,CoastTransectsShp,DTM,SwathDist)
    
    # analyse swath profiles to create transect porfiles
    #TransectProfilesIDW(Folder,CoastTransectsShp,DTM,SwathDist)
    
    # plot the resulting profiles
    PlotProfiles(Folder,CoastTransectsShp)
    