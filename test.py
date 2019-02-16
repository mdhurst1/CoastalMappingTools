# testing stuff

# read a shapefile
import cartopy.io.shapereader as shpreader
import shapely
import fiona


Shapefile = "D:/NCCA2/StAndrews/MHWS/MHWS_2018.shp"

CoastShp = shpreader(Shapefile)


# write a shapefile