
"""
Script to use Coast.py objects to create regular transects along a line,
can be used for rivers as requested by Craig

RiverCrossSections.py
MDH, July 2021
"""

from Coast import *

InputLine = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018.shp"
ThisCoast = Coast(InputLine)
ThisCoast.SmoothCoastLines()

SmoothedLine = "D:\\NCCA2\\StAndrews\\MHWS\\coast.shp"
ThisCoast.WriteCoastShp(SmoothedLine)

# generate perpendicular lines every 10 m extending by 100 m in both directions
ThisCoast.GenerateTransects(10.,100.,100.)
OutputFile = "D:\\NCCA2\\StAndrews\\MHWS\\transects.shp"
ThisCoast.WriteTransectsShp(OutputFile)
