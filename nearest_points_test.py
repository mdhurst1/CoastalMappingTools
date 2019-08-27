# import shapely module tools and geoms
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString, MultiLineString

# plotting modules
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

# create a temporary LineString
Lines = MultiLineString([((0.,0.),(2.5,2.5)),((2.8,2.9),(0.2,3.6))])
Point = Point(2.,4.)

# plot geometries
for Line in Lines:
    xl, yl = Line.xy
    plt.plot(xl,yl,'k-')

xp, yp = Point.xy
plt.plot(xp,yp,'ko')

# run nearest points test
NP = nearest_points(Lines, Point)
for P in NP:
    x,y = P.xy
    plt.plot(x,y,'ro')

#Result = Line.interpolate(Line.project(Point))
#x2,y2 = Result.xy
#plt.plot(x2,y2,'bo')

plt.axis('equal')
plt.savefig("temp.png")



