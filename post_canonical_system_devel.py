#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 14:00:51 2024

@author: gelenag

Example: Minsky's book, sec 12.7 Unary Squares Generator
"""

from UNN.Post import PostCanonicalSystem

unarysquares = PostCanonicalSystem(alphabet=['1', 'P'], 
                                   production=["($1)P($2) -> ($1)11P($2)($1)"])


print("i/p: 1P")
print("o/p: " + unarysquares.forward('1P'))

print("i/p: 111P1")
print("o/p: " + unarysquares.forward('111P1'))

#%% We can use prod. rules sequentially. To remove axuxilary character P
unarysquares = PostCanonicalSystem(alphabet=['1', 'P'], 
                                   production=["($1)P($2) -> ($1)11P($2)($1)", 
                                               "($1)P($2) -> ($1)($2)"])

print("i/p: 11111P1111")
print("o/p: " + unarysquares.forward('11111P1111'))