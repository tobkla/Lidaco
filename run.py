# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 12:58:05 2018

@author: skulla
"""

from lidaco.core.Builder import Builder

file1 = r'C:\Users\skulla\Documents\test\config.yaml' #windcubev2 rtd


builder = Builder(config_file = file1)
builder.build()


