# testing stuff
class Coast():
    
    """
    Description of object goes here

    """

    def __init__(self):
        self.X = -9999.
        self.Y = -9999.
        self.NoNodse = 0;
        self.Orientation = -9999.
        self.FluxOrientation = -9999.
        
# read a shapefile
import shapefile

CoastLineShp = "D:/NCCA2/StAndrews/MHWS/MHWS_2018.shp"

# Open coast polyline file for reading
sf = shapefile.Reader(CoastLineShp)
Shapes = sf.shapes()
Records = sf.records()
NoShapes = len(Shapes)
print("Number of records = ", NoShapes)

