"""

Tools for extracting cross-shore coastal profiles

Martin Hurst, September 2015

"""

# Import arcpy module
import arcpy, os, sys

#Change the path here for wherever you keep shapefile.py
sys.path.append("C:\\Python27")
sys.path.append("C:\\Users\\Martin Hurst\\Dropbox\\Code\\python_code_active\\")

import shapefile as shp
import numpy as np
import matplotlib.pyplot as plt
import bin_data

#from arcpy.sa import *

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

#allow overwrite
arcpy.env.overwriteOutput = True

##########################
# Customise figure style #
##########################
from matplotlib import rc
#rc('font',**{'family':'sans-serif','sans-serif':['Arial']})
rc('font',size=8)
rc('ytick.major',pad=5)
rc('xtick.major',pad=5)
#rc('xtick', direction='out')
#rc('ytick', direction='out')
#rc('text', usetex=True)
#rc('pdf',fonttype=42)
padding = 5

# Modified function for creating a smoothed coastline from OS Boundary Line
def SmoothCoastline(Path, CoastLineShp):

    JunkFolder = Path + "Junk\\"
    if os.path.exists(JunkFolder) == False:
        os.mkdir(JunkFolder)

    # Declare variables:
    Coast = Path + CoastLineShp
    SmoothedCoast = Path + "SmoothedCoastline.shp"

    # Process: Smooth Line
    arcpy.SmoothLine_cartography(Coast, SmoothedCoast, "PAEK", "1000 Meters", "NO_FIXED", "NO_CHECK")
    
    return SmoothedCoast    

def GetSmoothedCoastlineFromContour(Path, DEM, Contour):

    """
    This function takes a DEM and extracts the 2m elevation contour
    It calculates contour line length and finds the longest individual
    which should coincide with the coastline. It then smooths this line
    and generates a route to define the smoothed coastline.

    Martin Hurst, September 2015
    """

    print "GetSmoothCoastline: Generating a smoothed coastline from", DEM

    ### SETUP WORKSPACE ###
    JunkFolder = Path + "Junk\\"
    if os.path.exists(JunkFolder) == False:
        os.mkdir(JunkFolder)

    # Declare variables:
    DEM = Path + DEM
    Contours = JunkFolder + "Contours.shp"
    SelectedContour = JunkFolder + "SelectedContour.shp"
    SmoothedContour = JunkFolder + "SmoothedContour.shp"
    SmoothedCoast = Path + "SmoothedCoast.shp"

    # Process: Contour
    arcpy.gp.Contour_sa(DEM, Contours, "500", str(Contour), "1")

    # Process: Add Field
    arcpy.AddField_management(Contours, "Length", "DOUBLE", "8", "2", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Calculate Field
    arcpy.CalculateField_management(Contours, "Length", "!Shape.length!", "PYTHON", "")

    # Process: Add Field (2)
    arcpy.AddField_management(Contours, "MaxLength", "DOUBLE", "8", "2", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Calculate Field (2)
    arcpy.CalculateField_management(Contours, "MaxLength", "Maximum(\""+Contours+"\",\"Length\")", "PYTHON", "def Maximum(inputData, FieldName):\\n    import arcgisscripting\\n    gp = arcgisscripting.create()\\n    # Open a Search Cursor using field name and sort the field in descending order.\\n    rows = gp.SearchCursor(inputData, \"\", \"\", FieldName, FieldName + \" D\")\\n    #Get the first row and maximum value.\\n    row = rows.Next()\\n    return row.GetValue(FieldName)")

    # Process: Select
    arcpy.Select_analysis(Contours, SelectedContour, "\"LENGTH\" = \"MAXLENGTH\"")

    # Process: Smooth Line
    arcpy.SmoothLine_cartography(SelectedContour, SmoothedContour, "PAEK", "1000 Meters", "NO_FIXED", "NO_CHECK")

    # Process: Create Routes
    arcpy.CreateRoutes_lr(SmoothedContour, "ID", SmoothedCoast, "LENGTH", "", "", "UPPER_LEFT", "1", "0", "IGNORE", "INDEX")


def GenerateCoastalNormals(Path,CoastLineShp,ProfSpacing,l2sea = 1500.0,l2land = 200.0):

    """

    Function to generate coast normal profiles

    l2sea is length of profile in the seaward direction
    l2land is length of profile in the landward direction

    Martin Hurst, September 2012

    """

    print "GenerateCoastalProfiles: Generating Transects perpendicular to the coast"

    # Set up workspace
    JunkFolder = Path + "Junk\\"
    ProfsFolder = Path + "Profs\\"

    if os.path.exists(JunkFolder) is False:
        os.mkdir(JunkFolder)

    if os.path.exists(ProfsFolder) is False:
        os.mkdir(ProfsFolder)

    #Declare variables
    #prof_lines = ProfsFolder + "profile_lines.shp"
    #prof_point = ProfsFolder + "profile_point.shp"

    CoastLineShp = Path+CoastLineShp

    # Open coast polyline file for reading
    sf = shp.Reader(CoastLineShp)
    NoShapes = len(sf.shapes())
    Records = sf.records()

    print "\tNumber of lines: " + str(len(sf.shapes()))

    # Moved file declaration out top so that all segments amalgamated
    #Declare variables
    ProfLines = ProfsFolder + "profile_lines.shp"
    ProfPoints = ProfsFolder + "profile_point.shp"
    
    # Create point file writer object
    w_point = shp.Writer(shp.POINT)
    w_point.field("line_ID","C","8")
    w_line = shp.Writer(shp.POLYLINE)
    w_line.field("line_ID","C","8")

    # check if shapefiles already exist and if do copy shapes across to new shapefiles
    try:
        # Copy over the existing shapes and records
        r_line = shp.Reader(ProfLines)
        w_line.records.extend(r_line.records())
        w_line._shapes.extend(r_line.shapes())

    except shp.ShapefileException:
        print "\tShapefile does not exist"

    # Loop through each row in the shapefile, obtain the name of the associated grid tile from the
    # NG_GRID_RE field and use this to get the NextMap tile from the S drive
    # field = "TILE_NAME"
    for i in range(0, NoShapes):
    #for i in range(4, NoShapes):

        print "\tShape number: " + str(i)
        Shape = sf.shapes()[i]
        NoSegs = len(Shape.points)-1
        print "\tPolyline length: " + str(NoSegs)

        Rec = sf.record(i)

        # Parameters for tracing along length
        cum_length = 0.0
        next_point = ProfSpacing
        xsection_counter = 1
        prof_point_space = 2.0
        no_points = (l2sea + l2land) / prof_point_space
        a = 0

        # print "Done\n\tGenerating orientations and getting profiles..."
        # Cycle through segments and get their orientation
        # Track spacing and generate profile at desired distances
        for i in range(0, NoSegs):

            #Get start and end coordinates of the segment
            x1, y1 = Shape.points[i]
            x2, y2 = Shape.points[i+1]

            #plt.plot(x1,y1,'k+')
            #plt.plot(x2,y2,'ko',mfc='None')

            #calculate the spatial change
            dx = x2 - x1
            dy = y2 - y1

            #Calculate the orientation of the line
            #N.B. this will depend on where the start segment is
            #so that 270 is esseintially the same as 90 but depends
            #which end of the line the cycle starts at
            if dx > 0 and dy > 0:
                d = np.degrees( np.arctan( dx / dy ) )
            elif dx > 0 and dy < 0:
                d = 180.0 + np.degrees( np.arctan( dx / dy ) )
            elif dx < 0 and dy < 0:
                d = 180.0 + np.degrees( np.arctan( dx / dy ) )
            elif dx < 0 and dy > 0:
                d = 360 + np.degrees( np.arctan( dx / dy ) )

            #print "orientation d = ", d,

            #Calculate the length of the segment
            length = np.sqrt( (x2 - x1)**2.0 + (y2 - y1)**2.0)

            #Update the cumulative length of the line
            cum_length += length

            # Test to see if we're going to create a cross section
            while cum_length > next_point:

                #calculate point for section
                distance_to_step_back = cum_length - next_point

                dx = distance_to_step_back * np.sin( np.radians( d ) )
                dy = distance_to_step_back * np.cos( np.radians( d ) )

                point_x = x2 - dx
                point_y = y2 - dy

                #Create cross section line
                #Get line orientation
                if d < 0:
                    perp_d = d + 90.0
                else:
                    perp_d = d - 90.0

                #Calculate start and end nodes
                x = point_x + l2sea * np.sin( np.radians( perp_d ) )
                y = point_y + l2sea * np.cos( np.radians( perp_d ) )
                end_point_x = point_x - l2land * np.sin( np.radians( perp_d ) )
                end_point_y = point_y - l2land * np.cos( np.radians( perp_d ) )

                w_point.point(point_x,point_y)
                w_point.record(str(a))

                #Create line file writer object

                w_line.line(parts=[[[x,y],[end_point_x,end_point_y]]])
                w_line.record(str(a))
                a += 1

                #Create point file writer object
                w = shp.Writer(shp.POINT)
                w.field("POINT_ID","C","8")

                #Loop to write all nodes for cross section
                n = 0
                while n < no_points:

                    # Write point to shapefile
                    w.point(x,y)
                    w.record(str(n))

                    # update x and y
                    x = x - prof_point_space * np.sin( np.radians( perp_d ) )
                    y = y - prof_point_space * np.cos( np.radians( perp_d ) )

                    n += 1

                #Update to next_point
                next_point += ProfSpacing
                xsection_counter += 1

    #save
    w_point.save(ProfPoints)
    w_line.save(ProfLines)

        #DEM = Rec[3]
        # Calls following functions for each section of coastline
        # GenerateCoastalSwathProfiles(Path,DEM,SwathDist)
        # FindCliffTopPosition(Path)

def GenerateCoastalSwathProfiles(Path,DEM,SwathDist):

    """

    Function to generate coastal profiles from DEM and lines file

    Martin Hurst, September 2015
    
    """

    print "GenerateCoastalProfiles: Generating Elevation Profiles perpendicular to the coast"

    # Set up workspace
    JunkFolder = Path + "Junk\\"
    ProfsFolder = Path + "Profs\\"

    if os.path.exists(JunkFolder) is False:
        os.mkdir(JunkFolder)

    if os.path.exists(ProfsFolder) is False:
        os.mkdir(ProfsFolder)

    #Declare variables
    DEM = Path+DEM
    #DEM = "S:/NextMap/merged/dtm/" + DEM.lower()
    ProfLinesShp = ProfsFolder+"profile_lines.shp"

    # Open coast polyline file for reading
    sf = shp.Reader(ProfLinesShp)

    # Get line segment shapes
    Shapes = sf.shapes()
    NoLines = len(Shapes)

    #Get DEM properties
    Description = arcpy.Describe(DEM)
    Extent = Description.Extent
    DataResolution = Description.meanCellHeight
    XMin = Extent.XMin
    YMin = Extent.YMin
    YMax = Extent.YMax
    XMax = Extent.XMax
    
    NCols = int(Extent.width/DataResolution)
    NRows = int(Extent.height/DataResolution)

    #Convert DEM to numpy array
    #Downloaded ArcGIS 10.1 SP1 for Desktop Background Geoprocessing (64-bit) from
    #http://support.esri.com/en/downloads/patches-servicepacks/view/productid/189/metaid/1913
    DEMArray = arcpy.RasterToNumPyArray(DEM)
    XVector = XMin+np.arange(0,NCols)*DataResolution
    YVector = YMin+DataResolution*np.arange(0,NRows)[::-1]

    #loop through lines and get Swath Profile Elevations
    for l in range(0,NoLines):

        #Get line points
        X1,Y1 = Shapes[l].points[0]
        X2,Y2 = Shapes[l].points[1]

        #find indices for bounding box
        #need to be careful with reverse indexing
        iStart = np.argmin(np.abs(YVector-np.max([Y1,Y2])))-1
        iEnd = np.argmin(np.abs(YVector-np.min([Y1,Y2])))+1
        jStart = np.argmin(np.abs(XVector-np.min([X1,X2])))-1
        jEnd = np.argmin(np.abs(XVector-np.max([X1,X2])))+1

        #Get Vector X and Y
        dX12 = X2-X1
        dY12 = Y2-Y1

        f = open(ProfsFolder+"Prof" + str(l) + ".txt","w")
        f.write("X Y DistAlong DistTo Z\n")
        
        for i in range(iStart,iEnd):

            #get Y position
            YNode = YMax-DataResolution*(i)

            for j in range(jStart,jEnd):
                
                #get X position
                XNode = XMin + j*DataResolution;

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

                if (DistanceToLine > SwathDist):
                    continue

                f.write(str(XNode)+" "+str(YNode)+" "+str(DistanceAlongLine)+" "+str(DistanceToLine)+" "+str(DEMArray[i][j])+"\n")
                        
        #close file
        f.close()
        
def IDWCoastalProfiles(FileName):
    
    """
    
    Function to peform inverse distance weighting to swath profile data
    to generate the coastal elevation profile
    
    Martin Hurst, December 2015
    
    """
    
    print "IDWCoastalProfiles: Generating Elevation Profiles perpendicular to the coast"

    DEM_Resolution = 5.
    PointSpacing = DEM_Resolution/2.
    
    # Set up workspace
    JunkFolder = Path + "Junk\\"
    ProfsFolder = Path + "Profs\\"

    if os.path.exists(JunkFolder) is False:
        os.mkdir(JunkFolder)

    if os.path.exists(ProfsFolder) is False:
        os.mkdir(ProfsFolder)

    #Declare variables
    DEM = Path+DEM
    #DEM = "S:/NextMap/merged/dtm/" + DEM.lower()
    ProfLinesShp = ProfsFolder+"profile_lines.shp"

    # Open coast polyline file for reading
    sf = shp.Reader(ProfLinesShp)

    # Get line segment shapes
    Shapes = sf.shapes()
    NoLines = len(Shapes)

    #Get DEM properties
    Description = arcpy.Describe(DEM)
    Extent = Description.Extent
    DataResolution = Description.meanCellHeight
    XMin = Extent.XMin
    YMin = Extent.YMin
    YMax = Extent.YMax
    XMax = Extent.XMax
    
    NCols = int(Extent.width/DataResolution)
    NRows = int(Extent.height/DataResolution)

    #Convert DEM to numpy array
    #Downloaded ArcGIS 10.1 SP1 for Desktop Background Geoprocessing (64-bit) from
    #http://support.esri.com/en/downloads/patches-servicepacks/view/productid/189/metaid/1913
    DEMArray = arcpy.RasterToNumPyArray(DEM)
    XVector = XMin+np.arange(0,NCols)*DataResolution
    YVector = YMin+DataResolution*np.arange(0,NRows)[::-1]

    #loop through lines and get Swath Profile Elevations
    for l in range(0,NoLines):

        #Get line points
        X1,Y1 = Shapes[l].points[0]
        X2,Y2 = Shapes[l].points[1]

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
        
        f = open(ProfsFolder+"Prof" + str(l) + ".txt","w")
        f.write("X Y DistAlong DistTo Z\n")
        
        for i in range(iStart,iEnd):

            #get Y position
            YNode = YMax-DataResolution*(i)

            for j in range(jStart,jEnd):
                
                #get X position
                XNode = XMin + j*DataResolution;

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
                    Z.append(DEMArray[i][j])
                        
        #Sort by distance along line
        Sortedi = np.argsort(DistAlong)
        X = X[Sortedi]
        Y = Y[Sortedi]
        DistAlong = DistAlong[Sortedi]
        DistTo = DistTo[Sortedi]
        Z = Z[Sortedi]
        
        #Create a line for interpolating to
        LineLength = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
        NoPoints = LineLength/PointSpacing
        XLine = np.linspace(X1,X2,NoPoints)
        YLine = np.linspace(Y1,Y2,NoPoints)
        ZLine = np.zeros(len(XLine))
        DistAlongLine = np.zeros(len(XLine))
        
        #Loop along line
        for i in range(0,NoPoints):
            
            #Calculate distance along the line
            DistAlongLine[i] = i*PointSpacing
            
            #Could sample a reduced array here i.e. a neighbourhood?
            Neighbourhood = np.abs(DistAlongLine-DistAlong) < SwathDist
            
            #Create a distance vector
            Dist = np.sqrt(DistAlong[Neighbourhood]**2. + DistTo[Neighbourhood]**2.)
            
            #Weights are inverse
            Weights = 1./Dist**2.
            
            #Interpolate Z
            ZLine[i]  = np.sum(Z[Neighbourhood]*Weights)/np.sum(Weights)
        
        #Save IDW profile to a file
        f.write(str(XNode)+" "+str(YNode)+" "+str(DistanceAlongLine)+" "+str(DistanceToLine)+" "+str(DEMArray[i][j])+"\n")
                        
        #close file
        f.close()
    
def FindCliffTopPosition(Path):

    """

    Function to find clifftop from elevation profiles at the coast

    Martin Hurst, September 2015

    """

    print "FindCliffTopPosition: Finding the position of the cliff top",

    # Set up workspace
    JunkFolder = Path + "Junk\\"
    ProfsFolder = Path + "Profs\\"

    if os.path.exists(JunkFolder) is False:
        os.mkdir(JunkFolder)

    if os.path.exists(ProfsFolder) is False:
        os.mkdir(ProfsFolder)

    #Declare variables
    ProfLinesShp = ProfsFolder+"profile_lines.shp"
    CliffPoints = Path + "CliffPoints.shp"
    CliffLine = Path + "CliffLine.shp"

    # Open coast polyline file for reading
    sf = shp.Reader(ProfLinesShp)

    # Get line segment shapes
    Shapes = sf.shapes()
    NoLines = len(Shapes)
    
    #Create point file writer object
    w_point_clifftop = shp.Writer(shp.POINT)
    w_point_clifftop.field("ID","C","8")
    w_point_clifftop.field("CliffTopZ","C","8")
    w_point_clifftop.field("CliffToeZ","C","8")
    w_point_clifftop.field("CliffHeight","C","8")
    w_point_clifftop.field("CliffSlope","C","8")
    
    #Create point file writer object
    w_point_clifftoe = shp.Writer(shp.POINT)
    w_point_clifftoe.field("ID","C","8")
    w_point_clifftoe.field("CliffTopZ","C","8")
    w_point_clifftoe.field("CliffToeZ","C","8")
    w_point_clifftoe.field("CliffHeight","C","8")
    w_point_clifftoe.field("CliffSlope","C","8")
    
    #Create line file writer object
    w_line = shp.Writer(shp.POLYLINE)
    w_line.field("line_ID","C","8")
    w_line.field("CliffTopZ","C","8")
    w_line.field("CliffToeZ","C","8")
    w_line.field("CliffHeight","C","8")
    w_line.field("CliffSlope","C","8")

#    #check if shapefiles already exist and if do copy shapes across to new shapefiles
#    try:
#        r_line = shp.Reader(CliffLine)
#        # Copy over the existing dbf records
#        w_line.records.extend(r_line.records())
#        # Copy over the existing lines
#        w_line._shapes.extend(r_line.shapes())
#
#        r_point = shp.Reader(CliffPoints)
#        # Copy over the existing dbf records
#        w_point.records.extend(r_point.records())
#        # Copy over the existing lines
#        w_point._shapes.extend(r_point.shapes())
#
#        ##raise shp.ShapefileException
#
#    except shp.ShapefileException:
#        print "Shapefile does not exist"

    print "Line#",
    for i in range(0,NoLines):
        
        print i,
        
        #Added in some error handling to deal with empty files and an IndexError
        FileName = ProfsFolder + "Prof"+str(i)+".txt"
        
        X, Y, Dist, Z = np.loadtxt(FileName,skiprows=1,unpack=True,usecols=(0,1,2,4))
        
        #Sort in order of Dist along line
        IndArray = np.argsort(Dist)
        X = X[IndArray]
        Y = Y[IndArray]
        Dist = Dist[IndArray]
        Z = Z[IndArray]
        
        #Bin the data
        Numbins = np.int(np.abs((np.max(Dist)-np.min(Dist))/5))
        DistMean, DistStd, ZMean, ZStd, Count = bin_data.bin_data(Dist,Z,Numbins)
        
        #Run through sorted profile and remove data below sea level
        #if we return to sea level again truncate the profile
        
        # Sea level flag to track while we're still in the sea
        # Don't start recording the profile til we get above sea level
        # If sea level returns after this has been violated the trace stops (to handle barriers)
        # Note this relies on the cross section always starting in the sea and proceeding in land!
        # This could cause bugs later!!
        
        #find start of topodata
        CoastInd = -1
        SLNodes2Keep = 5
        for j in range(0,len(DistMean)):
            if ZMean[j] > 0:
                if j>SLNodes2Keep: CoastInd = j-SLNodes2Keep
                else: CoastInd = 0
                break
        
        if CoastInd == -1: 
            continue
            
            
        #Check for return of sea level
        for j in range(CoastInd+SLNodes2Keep,len(DistMean)):
            EndInd = j
            if ZMean[j] <= 0:   break
        
        #Truncate the profile data
        DistMean = DistMean[CoastInd:EndInd]
        ZMean = ZMean[CoastInd:EndInd]
        
        #Will need to write the truncated profiles to a shapefile
        
        #Check for downslopes
        Ind = len(DistMean)
        Count = 0
        for j in range(1,len(DistMean)):
            if ZMean[j] < ZMean[j-1]:
                Count += 1
            else:
                Count = 0
            if Count == 8:
                Ind = j
                break
        
        #Truncate to downslope
        DistMean = DistMean[0:Ind]
        ZMean = ZMean[0:Ind]
        
        #Get Angle to detrend
        Angle = np.degrees(np.arctan((ZMean[0]-ZMean[-1])/(DistMean[-1]-DistMean[0])))
       
        #Get detrended elevation
        Ztrend = ZMean-(DistMean[-1]-DistMean)*np.tan(np.radians(Angle))
        
        #Find Minimum and Maximum Ztrend
        MaxInd = np.argmax(Ztrend)
        while ZMean[MaxInd] == 0:
            DistMean = np.delete(DistMean,MaxInd)
            ZMean = np.delete(ZMean,MaxInd)
            Ztrend = np.delete(Ztrend,MaxInd)
            MaxInd = np.argmax(Ztrend)
        
        MinInd = 0        
        for j in range(0,len(ZMean)):
            if ZMean[j] > 0:
                break
            else:   MinInd = j
                
        #Calculate Cliff height and slope
        Elevation = Ztrend[MaxInd]
        CliffHeight = Ztrend[MaxInd]-Ztrend[MinInd]
        CliffSlope = np.degrees(np.arctan(CliffHeight/np.abs(DistMean[MaxInd]-DistMean[MinInd])))
        
#        #plot the profile and points
#        plt.figure(1,figsize=(6,6))
#        plt.subplot(211)            
#        plt.plot(DistMean,ZMean,'k.')
#        plt.ylabel('Elevation (m)')
#        plt.subplot(212)
#        plt.plot(DistMean,Ztrend,'k.')
#        plt.plot(DistMean[MaxInd],Ztrend[MaxInd],'ro')
#        plt.plot(DistMean[MinInd],Ztrend[MinInd],'bo')
#        plt.xlabel('Cross-shore Distance (m)')
#        plt.ylabel('Detrended Elevation (m)')
#        plt.savefig(ProfsFolder + "prof" + str(i) + ".png")
#        plt.clf()
        
        #find nearest position and create point for cliff edge
        CliffInd = np.argmin(np.abs(Dist-DistMean[MaxInd]))
        ToeInd = np.argmin(np.abs(Dist-DistMean[MinInd]))
        
        #add point to shapefile (This needs fixing!)
        w_point_clifftop.point(X[CliffInd],Y[CliffInd])
        w_point_clifftop.record(str(i),str(Ztrend[MaxInd]),str(Ztrend[MinInd]),str(CliffHeight),str(CliffSlope))
        
        w_point_clifftoe.point(X[ToeInd],Y[ToeInd])
        w_point_clifftoe.record(str(i),str(Ztrend[MaxInd]),str(Ztrend[MinInd]),str(CliffHeight),str(CliffSlope))


        #add line to shapefile if the first poitn has already been created
        if (i > 0):
            w_line.line(parts=[[[point_x,point_y],[X[CliffInd],Y[CliffInd]]]])
            w_line.record(str(i),str(Ztrend[MaxInd]),str(Ztrend[MinInd]),str(CliffHeight),str(CliffSlope))
            
        #define point for next line segment
        point_x = X[CliffInd]
        point_y = Y[CliffInd]
    
    #save!
    w_point_clifftop.save(CliffPoints)
    w_point_clifftoe.save(CliffPoints)
    w_line.save(CliffLine)

    print "Done!"
    
if __name__ == "__main__":

    #Declare workspace
    Path = "E:\\PROJECTS\\Coastal\\CVI\\"
    #Path = "C:\\CVI\\"

    #declare filenames for DEM and coastline
    DEM = "sy2.tif"
    CoastLineShp = "SmoothedCoastSY.shp"

    #Declare Contour elevation to use as the coast
    Contour = 0.5

    #Declare profile spacing
    ProfSpacing = 50

    #Distance to extend proflies onshore and offshore
    ProfLengthOffshore = 200
    ProfLengthOnshore = 1000

    #Swath profile width
    SwathDist = 5

    #Launch
    #GetSmoothedCoastline(Path,DEM,Contour)
    #SmoothedCoast = SmoothCoastline(Path, CoastLineShp)
    #GenerateCoastalNormals(Path, CoastLineShp, ProfSpacing, ProfLengthOffshore, ProfLengthOnshore)
    #GenerateCoastalSwathProfiles(Path,DEM,SwathDist)
    FindCliffTopPosition(Path)
    print "Done"
