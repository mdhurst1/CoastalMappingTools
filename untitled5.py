# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 14:32:17 2019

@author: mh322u
"""

import numpy as np
from math import pi,exp,sqrt
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d


def Gauss(Sigma,x):
    expVal = -1. * (x*x) / ((2.*Sigma)*(2.*Sigma))
    divider = sqrt(2.*pi*(Sigma*Sigma))
    return (1./divider)*exp(expVal)

Values = [0, 0, 0.0033623285527909848, 0.00058165736564909191, 0.0019923608926182401, -0.0020335584168816867, 0.0023297545693953272, -0.0047527485044977094, 
  0.0053076223254038268, 0.003777148460130963, 0.003117125516751629, -0.0046289987177207514, 0.006072338298986962, 0.0022741538924473475, -0.0075977877206310426, -0.00074545266829773027, 
  0.0030172638771314123, -0.0014481157554176122, -0.0020834243926489944, 0.0036430102098292585, -0.0015040494247918889, 0.00020795959060258173, 0.0052021720893751268, -0.004207018973628799, 
  0.010321462246906776, 0.0015624563091760552, -0.0010906206396330024, -0.0040844220703028043, 0.015860277869635626, -0.0025864012906547614, -0.0072463894579070818, -0.0061768341273685419, 
  0.012105620175859502, -0.0015943452774422413, -0.00067606119061037117, 0.0048466272087870814, -0.0040739418222467622, -0.0037390460021242689, 0.0058802722312238593, 0.008120672272476934, 
  -0.0059605048087782312, 0, 0]
Sigma = 1. #1,5
Samples = 5.
    
def Smooth(Values,Sigma,Samples):
    doubleCenter = False
    v = []
    if Samples % 2 == 0:
        doubleCenter = True
        Samples -= 1
        
    steps = int((Samples-1)/2.)
    print(steps)
    
    stepSize = float(3*Sigma)/steps
    print(stepSize)
    
    for i in range(steps,0,-1):
        v.append(Gauss(Sigma,i*stepSize*-1))
    
    print(v)
    
    v.append(Gauss(Sigma,0))
    
    if (doubleCenter == True):
        v.append(Gauss(Sigma,0))
    
    print(v)
    
    for i in range(1,steps):
        v.append(Gauss(Sigma,i*stepSize))
        
    v.append(Gauss(Sigma,1))
    
    Kernel = np.array(v,dtype=np.float)
    print(v)
    print(Kernel)
            
    Sampleside = int(Samples/2)
    valueIdx = int(Samples/2+1)
    ubound = int(len(Values))
    SmoothedValues = []
    
    for i in range(0,ubound):
        sample = float(0)
        sampleCtr = int(0)
        for j in range((i-Sampleside),(i+Sampleside)):
            #print((i-Sampleside),(i+Sampleside))
            if (j>0 and j < ubound):
                sampleWeightIndex = int(Sampleside + (j-i))
                sample += Kernel[sampleWeightIndex] * Values[j]
                sampleCtr += 1
        SmoothedValues.append(sample/sampleCtr)
    return np.array(SmoothedValues,dtype=np.float)

Nodes = np.arange(0,len(Values))
SmoothedValues = Smooth(Values,Sigma/4.,Samples)
plt.plot(Nodes,Values,'--k',label='Position Change')
plt.plot(Nodes,SmoothedValues,'-xk',label='C++ algorithm')
plt.plot(Nodes,gaussian_filter1d(Values, Sigma, mode='constant'),'r',label='Scipy Gaussian')
plt.legend()
plt.show() 