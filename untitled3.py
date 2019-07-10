# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 15:33:45 2019

@author: mh322u
"""

import pickle

# define file names for analysis
Folder = r"C:\\Users\\mh322u\\OneDrive - University of Glasgow\\Projects\\DynamicCoast2\\WP1_TopographicAnalysis\\"
Site = "BayOfSkail"
SiteFolder = Folder+Site+"\\"

# set up a file name to save the coast object
Filename2SaveCoast = SiteFolder+ "Coast.pydata"

ThisCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )