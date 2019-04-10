# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 12:58:05 2018

@author: skulla
"""

from lidaco.core.Builder import Builder

file1 = r'E:\Wind Scanner Data\yaml\scenario 2\tulip_Drantum_WS59_FFT64_middle_acc1000.yaml' #windcubev2 rtd


builder = Builder(config_file = file1)
builder.build()