#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 15:39:37 2020

@author: mhurst
"""

class HelloWorld:
    
    def __init__(self):
        
        Message = "default"
    
    def __str__(self):
        
        return self.Message
    
def SetMessage(MyString):
    
    Message = MyString
    print(Message)