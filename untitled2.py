#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 14:37:24 2020

@author: mhurst
"""

from shapely.ops import linemerge, unary_union, polygonize



merged = linemerge([poly.boundary, line])
borders = unary_union(merged)
polygons = polygonize(borders)
for p in polygons:
    print(p)
