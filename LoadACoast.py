#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 15:06:27 2020

@author: mhurst
"""

import pickle, pathlib
from Coast import *


# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
Cell = "2a"
Filename2LoadCoast = WorkingPath / "CoastalCells" / ("Cell_"+Cell+"_Change.pydata")
CellCoast = pickle.load( open( Filename2LoadCoast, "rb" ) )

# Open coast polyline file for reading
        SF = shapefile.Reader(CoastShp)
        Shapes = SF.shapes()
        
        # I HAVE DELETED THE RECORDING OF SHAPES AND RECORDS INTO THE OBJECT DUE TO COMPATIBILITY ISSUES
        # WITH PICKLING THAT I CANT UNDERSTAND!!!!

        # Get number of coast segments to work on
        self.NoCoastLines = len(Shapes)
        print("Coast.ReadCoastShp: Read Coastline, no of coast segments is", self.NoCoastLines)
    
        # Generate coast nodes for each segment
        for i in range(0,self.NoCoastLines):
            
            print(" \r\tCoastline %4d / %4d" % (i+1, self.NoCoastLines), end="")

            # get X and Y coordinates of segment
            X, Y = np.array(Shapes[i].points).T
            
            # Set up a line object for each
            ThisLine = Line(str(i), X, Y)

            # append to list of coast lines
            if ThisLine.TotalLength > MinLength:
                self.CoastLines.append(ThisLine)

        # get new number of coastal segments based on the list built
        self.NoCoastLines = len(self.CoastLines)

        print("")    

        # get projection strings
        f = open(CoastShp.rstrip("shp")+"prj")
        self.Projection = f.read()
        f.close()
