
"""
Testing.py
MDH, June 2019
"""

import numpy as np
from Node import *
from Transect import *
from Line import *
from Coast import *

TESTFILE = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018.shp"
ThisCoast = Coast(TESTFILE)
ThisCoast.MergeCoastlines()
TESTFILE2 = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018_TEST.shp"
ThisCoast.WriteCoastShp(TESTFILE2)