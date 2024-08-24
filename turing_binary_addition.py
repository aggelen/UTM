#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 11:26:15 2024

@author: gelenag
"""

from UNN.Turing import TuringMachine

input_string = '1101_101'  #trying to add 1101 + 101 = 10010: 13 + 5 = 18

states = ['q0', 'q1', 'q2', 'q3', 'q4', 'q5', 'H']
alphabet = ['0', '1']
tape_alphabet = ['0', '1', '_']     # _ is for blank
start_state = 'q0'
accept_states = ['H']

tm = TuringMachine(states, alphabet, tape_alphabet, start_state, accept_states, verbose=True)
tm.load_program('Programs/binary_addition.txt')

tm.run(input_string)