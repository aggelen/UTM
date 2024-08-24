#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 13:57:15 2024

@author: gelenag
"""

from UNN.Turing import TuringMachine

input_string = 'abaaba'  

states = ['q0', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8']
alphabet = ['a', 'b', 'B']
tape_alphabet = ['a', 'b', '_']
start_state = 'q0'
accept_states = ['q8']

tm = TuringMachine(states, alphabet, tape_alphabet, start_state, accept_states, verbose=True)
tm.load_program('Programs/palindrome_checker.txt')

tm.run(input_string)