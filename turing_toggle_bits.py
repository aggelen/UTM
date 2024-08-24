#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 11:26:15 2024

@author: gelenag
"""

from UNN.Turing import TuringMachine

input_string = '110010110'  

states = ['q0', 'q1']
alphabet = ['0', '1']
tape_alphabet = ['0', '1', '_']     
start_state = 'q0'
accept_states = ['q1']

tm = TuringMachine(states, alphabet, tape_alphabet, start_state, accept_states,  blank_symbol='_', verbose=True)
tm.load_program('Programs/toggle_bits.txt')

tm.run(input_string)