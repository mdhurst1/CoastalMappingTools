# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 14:04:48 2019

@author: mh322u
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 11:25:01 2019

@author: mh322u
"""

import pickle
import pathlib
from Coast import *
import numpy as np
from numpy import ma
import matplotlib.pyplot as plt

# import KMeans
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN

# define file names for analysis
Folder = "C:\\Users\\mh322u\\OneDrive - University of Glasgow\\Projects\\DynamicCoast2\\WP1_TopographicAnalysis\\"
Site = "Montrose"
SiteFolder = Folder+Site+"\\"
PlotFolder = SiteFolder+"Plots\\" 
LineShp = "Montrose_CoastTrend.shp"
DTM = "DTM_1m.tif"

# make folder for plots if it doesnt already exist
p = pathlib.Path(PlotFolder)
p.mkdir(parents=True, exist_ok=True)

# set up a file name to save the coast object
Filename2SaveCoast = SiteFolder+ "Coast.pydata"
#Filename2SaveCoast = SiteFolder+ "Coast.pydata_DUMMY"

# this checks to see whether coast object already exists
try:
    ThisCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object " + Filename2SaveCoast)

except:
    print("Creating New Coast Object")
    
    # SET UP THE COAST
    ThisCoast = Coast(SiteFolder+LineShp)
    
    # SIMPLIFY COASTLINE
    ThisCoast.MergeCoastLines()
    ThisCoast.SmoothCoastLines(WindowSize=51)
    ThisCoast.ReconfigureCoastLines("E")
    
    # WRITE COASTLINE TO SHAPEFILE
    ThisCoast.WriteCoastShp(SiteFolder+"Coast.shp")
    
    # GENERATE TRANSECTS
    ThisCoast.GenerateNormals(10.,200.,300.)
    ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
    ThisCoast.ExtractTransectTopography(SiteFolder+DTM)
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as " + Filename2SaveCoast)
    with open(Filename2SaveCoast, 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)
 

       
## ANALYSE TRANSECTS
ThisCoast.FindRockyCoast()

SlopeRoughness = [Transect.SlopeRoughness for Line in ThisCoast.CoastLines for Transect in Line.Transects]
#print(SlopeRoughness)
#ValueLocs = (np.isnan(SlopeRoughness) == False)
#SlopeRoughness = SlopeRoughness[ValueLocs]
ElevationRoughness = np.array([Transect.ElevationRoughness for Line in ThisCoast.CoastLines for Transect in Line.Transects])
ElevationRoughness = ma.array(ElevationRoughness)
#ElevationRoughness = ElevationRoughness[ValueLocs]

#Rocky = np.array([Transect.Rocky for Line in ThisCoast.CoastLines for Transect in Line.Transects])
plt.plot(SlopeRoughness,ElevationRoughness,'k.',zorder=-1)
#plt.plot(SlopeRoughness[Rocky],ElevationRoughness[Rocky],'r.')

points = np.column_stack((SlopeRoughness,ElevationRoughness))
#print("\n\n")
#print(np.shape(SlopeRoughness))
#print(np.shape(points))
#print("\n\n")
kmeans = KMeans(n_clusters=4)
kmeans.fit(points)
y_km = kmeans.fit_predict(points)
print(y_km)

plt.scatter(points[y_km ==0,0], points[y_km == 0,1], s=10, c='red')
plt.scatter(points[y_km ==1,0], points[y_km == 1,1], s=10, c='black')
plt.scatter(points[y_km ==2,0], points[y_km == 2,1], s=10, c='blue')
plt.scatter(points[y_km ==3,0], points[y_km == 3,1], s=10, c='green')

plt.show()

#
#Dist = 0.01
#
#db = DBSCAN(eps=Dist, min_samples=2).fit(points)
#core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
#core_samples_mask[db.core_sample_indices_] = True
#labels = db.labels_
#
## Number of clusters in labels, ignoring noise if present.
#n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
#n_noise_ = list(labels).count(-1)
#
#unique_labels = set(labels)
#colors = [plt.cm.Spectral(each)
#          for each in np.linspace(0, 1, len(unique_labels))]
#
#for k, col in zip(unique_labels, colors):
#    if k == -1:
#        # Black used for noise.
#        col = [0, 0, 0, 1]
#
#    class_member_mask = (labels == k)
#
#    xy = points[class_member_mask & core_samples_mask]
#    plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
#             markeredgecolor='k', markersize=6)
#
#    xy = points[class_member_mask & ~core_samples_mask]
#    plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
#             markeredgecolor='k', markersize=6)

plt.show()
#ThisCoast.AnalyseTransectMorphology()
#ThisCoast.AnalyseBarrierWidths([4.,5.,6.])

# SAVE
#with open(Filename2SaveCoast, 'wb') as PFile:
#        pickle.dump(ThisCoast, PFile)
    
# plot the results
#ThisCoast.PlotTransects(PlotFolder)
