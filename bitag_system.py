#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 14:00:51 2024

@author: gelenag

Example: 2-Tag system simulation
"""

from UNN.Post import BiTagSystem

T1 = BiTagSystem(alphabet=['a1', 'a2', 'a3'], 
                 production=["a1 -> a2a1a3",
                             "a2 -> a1",
                             "a3 -> *"],         # * means STOP
                 verbose=True)       

initial_word = "a2a1a1"
print("i/p: {}".format(initial_word))
print("o/p: " + T1.forward(initial_word))

