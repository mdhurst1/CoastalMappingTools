
"""
Testing.py
MDH, June 2019
"""

import numpy as np
import itertools
from Node import *
from Transect import *
from Line import *


TESTFILE = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018.shp"
ThisCoast = Coast(TESTFILE)
ThisCoast.MergeCoastLines()
ThisCoast.SmoothCoastLines()

SmoothedLine = "D:\\NCCA2\\StAndrews\\MHWS\\coast.shp"
ThisCoast.WriteCoastShp(TESTFILE2)

# generate perpendicular lines every 10 m extending by 100 m in both directions
ThisCoast.GenerateNormals(10.,100.,100.)
TESTFILE3 = "D:\\NCCA2\\StAndrews\\MHWS\\transects.shp"
ThisCoast.WriteTransectsShp(TESTFILE3)
