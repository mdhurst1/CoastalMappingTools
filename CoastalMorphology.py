"""
Description of file goes here

Martin D. Hurst
Unviersity of Glasgow
Febraury 2019

"""

# import modules
import numpy as np
from scipy.signal import savgol_filter
import rasterio
import shapefile

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
    
    # open writer object for polyline and assign fields
    WL = shapefile.Writer(shapefile.POLYLINE)
    WL.fields = Fields[1:]
        
    # check if shapefiles already exist and if so copy shapes across to new shapefile
    try:
        # Copy over the existing shapes and records
        RL = shapefile.Reader(CoastLineShp)
        WL.records.extend(RL.records())
        WL._shapes.extend(RL.shapes())
        #print("\tUpdating existing polyline shapefile...")

    except shapefile.ShapefileException:
        print("\tCreating new polyline shapefile...")
      
    # add the line and record
    WL.line(parts=[np.column_stack([X,Y]).tolist()])
    WL.record(*Record)
    
    # save the shapefile
    WL.save(CoastLineShp)

    # create the projection file    
    f = open(CoastLineShp.rstrip("shp")+"prj","w")
    f.write(Projection)
    f.close()

def WritePointShp(PointsShp,Projection,point_x,point_y,Fields,Record):
    
    """
    """
    
    # open writer object for polyline and assign fields
    WP = shapefile.Writer(shapefile.POINT)
    WP.fields = Fields[1:]
        
    # check if shapefiles already exist and if so copy shapes across to new shapefile
    try:
        # Copy over the existing shapes and records
        RP = shapefile.Reader(PointsShp)
        WP.records.extend(RP.records())
        WP._shapes.extend(RP.shapes())
        #print("\tUpdating existing point shapefile...")

    except shapefile.ShapefileException:
        print("\tCreating new point shapefile...")
      
    # add the line and record
    WP.point(point_x,point_y)
    WP.record(*Record)
    
    # save the shapefile
    WP.save(PointsShp)

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
        
        # write results to new shapefile
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
    WP = shapefile.Writer(shapefile.POINT)
    WP.fields = Fields[1:]
        
     # open writer object for polyline and assign fields
    WL = shapefile.Writer(shapefile.POLYLINE)
    WL.fields = Fields[1:]
        
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
        TransectCount = 0
        
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
                WL.line(parts=[[[x,y],[end_point_x,end_point_y]]])
                WL.record(*Record)
    
                # update to find next transect
                TransectCount += 1
                next_point += ProfSpacing
    
    # save the shapefiles
    WP.save(PointsShp)
    WL.save(CoastTransectsShp)

    # create the projection files
    f = open(PointsShp.rstrip("shp")+"prj","w")
    f.write(Projection)
    f.close()
    
    # create the projection file    
    f = open(CoastTransectsShp.rstrip("shp")+"prj","w")
    f.write(Projection)
    f.close()

def ExtractSwathProfiles(CoastTransectsShp,DTM,SwathDist):
    
    """
    
    Function to extract swath profile elevation data for each coastal transect
    
    Martin Hurst, February 2019
    University of Glasgow
    
    """
    
    print("ExtractSwathProfiles: Generating Elevation Swath Profiles perpendicular to the coast")

    # load the DTM
    DTM_Dataset = rasterio.open(DTM)
    DTMArray = DTM_Dataset.read(1)
    NCols = DTM_Dataset.height
    NRows = DTM_Dataset.width
    NDV = DTM_Dataset.nodata
    Resolution = DTM_Dataset.res
    
    print(NCols,NRows,NDV,Resolution)
    
#    DEM_Resolution = 5.
#    PointSpacing = DEM_Resolution/2.
#    
#    # Set up workspace
#    JunkFolder = Path + "Junk\\"
#    ProfsFolder = Path + "Profs\\"
#
#    if os.path.exists(JunkFolder) is False:
#        os.mkdir(JunkFolder)
#
#    if os.path.exists(ProfsFolder) is False:
#        os.mkdir(ProfsFolder)
#
#    #Declare variables
#    DEM = Path+DEM
#    #DEM = "S:/NextMap/merged/dtm/" + DEM.lower()
#    ProfLinesShp = ProfsFolder+"profile_lines.shp"
#
#    # Open coast polyline file for reading
#    sf = shp.Reader(ProfLinesShp)
#
#    # Get line segment shapes
#    Shapes = sf.shapes()
#    NoLines = len(Shapes)
#
#    #Get DEM properties
#    Description = arcpy.Describe(DEM)
#    Extent = Description.Extent
#    DataResolution = Description.meanCellHeight
#    XMin = Extent.XMin
#    YMin = Extent.YMin
#    YMax = Extent.YMax
#    XMax = Extent.XMax
#    
#    NCols = int(Extent.width/DataResolution)
#    NRows = int(Extent.height/DataResolution)
#
#    #Convert DEM to numpy array
#    #Downloaded ArcGIS 10.1 SP1 for Desktop Background Geoprocessing (64-bit) from
#    #http://support.esri.com/en/downloads/patches-servicepacks/view/productid/189/metaid/1913
#    DEMArray = arcpy.RasterToNumPyArray(DEM)
#    XVector = XMin+np.arange(0,NCols)*DataResolution
#    YVector = YMin+DataResolution*np.arange(0,NRows)[::-1]
#
#    #loop through lines and get Swath Profile Elevations
#    for l in range(0,NoLines):
#
#        #Get line points
#        X1,Y1 = Shapes[l].points[0]
#        X2,Y2 = Shapes[l].points[1]
#
#        #find indices for bounding box
#        #need to be careful with reverse indexing
#        iStart = np.argmin(np.abs(YVector-np.max([Y1,Y2])))-1
#        iEnd = np.argmin(np.abs(YVector-np.min([Y1,Y2])))+1
#        jStart = np.argmin(np.abs(XVector-np.min([X1,X2])))-1
#        jEnd = np.argmin(np.abs(XVector-np.max([X1,X2])))+1
#
#        #Get Vector X and Y
#        dX12 = X2-X1
#        dY12 = Y2-Y1
#
#        #Declare list holders for profile data
#        X = []
#        Y = []
#        Z = []
#        DistAlong = []
#        DistTo = []
#        
#        f = open(ProfsFolder+"Prof" + str(l) + ".txt","w")
#        f.write("X Y DistAlong DistTo Z\n")
#        
#        for i in range(iStart,iEnd):
#
#            #get Y position
#            YNode = YMax-DataResolution*(i)
#
#            for j in range(jStart,jEnd):
#                
#                #get X position
#                XNode = XMin + j*DataResolution;
#
#                #Get 2nd Vector Properties in Array
#                dX13 = XNode-X1
#                dY13 = YNode-Y1
#
#                #Find Dot Product
#                DotProduct = dX12*dX13 + dY12*dY13;
#
#                #calculate fraction of distance along line
#                t = DotProduct/(dX12*dX12 + dY12*dY12)
#                if ((t < 0.) or (t > 1.)):
#                    continue
#
#                #Find point along line
#                XLine = X1 + t*dX12
#                YLine = Y1 + t*dY12
#                DistanceAlongLine = t*np.sqrt(dX12*dX12 + dY12*dY12)
#
#                #find distance to point
#                DistanceToLine = np.sqrt((XLine-XNode)*(XLine-XNode) + (YLine-YNode)*(YLine-YNode))
#
#                if (DistanceToLine < SwathDist):
#                    X.append(XNode)
#                    Y.append(YNode)
#                    DistAlong.append(DistanceAlongLine)
#                    DistTo.append(DistanceToLine)
#                    Z.append(DEMArray[i][j])
#                        
#        #Sort by distance along line
#        Sortedi = np.argsort(DistAlong)
#        X = X[Sortedi]
#        Y = Y[Sortedi]
#        DistAlong = DistAlong[Sortedi]
#        DistTo = DistTo[Sortedi]
#        Z = Z[Sortedi]
#        
#        #Create a line for interpolating to
#        LineLength = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
#        NoPoints = LineLength/PointSpacing
#        XLine = np.linspace(X1,X2,NoPoints)
#        YLine = np.linspace(Y1,Y2,NoPoints)
#        ZLine = np.zeros(len(XLine))
#        DistAlongLine = np.zeros(len(XLine))
#        
#        #Loop along line
#        for i in range(0,NoPoints):
#            
#            #Calculate distance along the line
#            DistAlongLine[i] = i*PointSpacing
#            
#            #Could sample a reduced array here i.e. a neighbourhood?
#            Neighbourhood = np.abs(DistAlongLine-DistAlong) < SwathDist
#            
#            #Create a distance vector
#            Dist = np.sqrt(DistAlong[Neighbourhood]**2. + DistTo[Neighbourhood]**2.)
#            
#            #Weights are inverse
#            Weights = 1./Dist**2.
#            
#            #Interpolate Z
#            ZLine[i]  = np.sum(Z[Neighbourhood]*Weights)/np.sum(Weights)
#        
#        #Save IDW profile to a file
#        f.write(str(XNode)+" "+str(YNode)+" "+str(DistanceAlongLine)+" "+str(DistanceToLine)+" "+str(DEMArray[i][j])+"\n")
#                        
#        #close file
#        f.close()
        
if __name__ == "__main__":
    
    # declare file names
    CoastLineShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018_Dissolve.shp"
    MergedCoastLineShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018_Merged.shp"
    SmoothCoastLineShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018_Smooth.shp"
    CoastTransectsShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018_Smooth_transects.shp"
    DTM = "D:/NCCA2/StAndrews/DTM/StAn_2018_DTM.tif"
    
    # launch merging
    #MergeCoastline(CoastLineShp, MergedCoastLineShp)
    
    # launch smoothing
    #SmoothCoastline(CoastLineShp,SmoothCoastLineShp)
    
    # generate normals
    #GenerateCoastalNormals(SmoothCoastLineShp,50.,200.,50.)
    
    # extract swath profiles
    ExtractSwathProfiles(CoastTransectsShp,DTM,SwathDist)
        