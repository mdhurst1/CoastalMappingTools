#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 10:43:46 2020

@author: mhurst
"""

import numpy as np
import rasterio

# dummy raster
x = np.linspace(-4.0, 4.0, 240)
y = np.linspace(-3.0, 3.0, 180)
X, Y = np.meshgrid(x, y)
Z1 = np.exp(-2 * np.log(2) * ((X - 0.5) ** 2 + (Y - 0.5) ** 2) / 1 ** 2)
Z2 = np.exp(-3 * np.log(2) * ((X + 0.5) ** 2 + (Y + 0.5) ** 2) / 2.5 ** 2)
Z = 10.0 * (Z2 - Z1)

# create as raster dataset
with rasterio.open('new.tif',
                            'w',
                            driver='GTiff',
                            height=Z.shape[0],
                            width=Z.shape[1],
                            count=1,
                            dtype=Z.dtype,
                            nodata=-9999
                            ) as dst:
    dst.write(Z, 1)

SRC = rasterio.open('new.tif')
    

# get polygon of extent
XMin = SRC.bounds[0]
XMax = SRC.bounds[2]
YMin = SRC.bounds[1]
YMax = SRC.bounds[3]

# set up some points to sample
X = np.arange(XMin-10, XMax+20, 10)
Y = np.arange(YMin+10, YMax-20, -10)

""" These work
X = np.arange(-1000, -900, 10)
Y = np.arange(-1000, -900, 10)
"""

""" And these work
X = np.arange(XMin+10, XMax-10, 10)
Y = np.arange(YMin-10, YMax+10, -10)
"""

Points = [(x,y) for x, y in zip(X, Y)]
Result = [Sample[0] for Sample in SRC.sample(Points)]
print(Result)