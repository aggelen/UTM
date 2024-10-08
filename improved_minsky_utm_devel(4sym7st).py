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
from UNN.Post import TwoTagSystem
from UNN.Turing import Minsky47UniversalTuringMachine

utm = Minsky47UniversalTuringMachine()

compiled_machine = TwoTagSystem().from_turing_machine('TMs/toggle_bit_TM.txt')
compiled_machine.run()