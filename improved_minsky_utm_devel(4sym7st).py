#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 11:06:35 2024

@author: gelenag

Small Universal Turing Machine by M. Minsky
4 symbols 7 states
can simulate the action of any set of tag productions with deletion no: 2

Minskys original small UTM has an unsolveble halting problem [Rogozhin1996]
This implements a modified version.
"""

# tag system alphabet a0, a1, ..., ap
# a0 halting letter

# for 1 <= i <= m
# ai -> ai1 ai2 ... ain_i  n_i > 0

# tag word ar as ... az

#%%
from UNN.Post import BiTagSystem

T1 = BiTagSystem(alphabet=['E', 'O', 'X'], 
                 production=["X -> _",
                             "E -> E",
                             "O -> EO"],         # * means STOP
                 verbose=True)       

initial_word = "OOXXX"
print("i/p: {}".format(initial_word))
print("o/p: " + T1.forward(initial_word))


#%%
from UNN.Turing import Minsky47UniversalTuringMachine

utm = Minsky47UniversalTuringMachine()

# utm.encode('Programs/toggle_bits.txt')
# utm.run("110010110")