#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 26 12:54:07 2025

@author: gelenag
"""

from NeuralUTM.SymbolicDynamics import TMVersatileShift
from NeuralUTM.Helpers import write_turing_machine_to_txt

#%% TM Description
states = ['q0', 'q1',  'q2',  'q3',  'q4',  'q5', 'q6',  'q7',  'q8',  'q9', 'end']
symbols = ['#', '0', '1', 'A', 'B']
transitions = {('q0', '#'): ('q0', '#', 'R'),
               ('q0', '0'): ('q1', '0', 'R'),
               ('q0', '1'): ('q1', '1', 'R'),
               ('q1', '#'): ('q2', '#', 'R'),
               ('q1', '0'): ('q1', '0', 'R'),
               ('q1', '1'): ('q1', '1', 'R'),
               ('q1', 'A'): ('q1', 'A', 'R'),
               ('q1', 'B'): ('q1', 'B', 'R'),
               ('q2', '#'): ('q3', '#', 'L'),
               ('q2', '0'): ('q2', '0', 'R'),
               ('q2', '1'): ('q2', '1', 'R'),
               ('q3', '#'): ('q9', '#', 'L'),
               ('q3', '0'): ('q4', '#', 'L'),
               ('q3', '1'): ('q6', '#', 'L'),
               ('q4', '#'): ('q5', '#', 'L'),
               ('q4', '0'): ('q4', '0', 'L'),
               ('q4', '1'): ('q4', '1', 'L'),
               ('q5', 'A'): ('q5', 'A', 'L'),
               ('q5', 'B'): ('q5', 'B', 'L'),
               ('q5', '0'): ('q1', 'A', 'R'),
               ('q5', '1'): ('q1', 'B', 'R'),
               ('q6', '0'): ('q6', '0', 'L'),
               ('q6', '1'): ('q6', '1', 'L'),
               ('q6', '#'): ('q7', '#', 'L'),
               ('q7', 'A'): ('q7', 'A', 'L'),
               ('q7', 'B'): ('q7', 'B', 'L'),
               ('q7', '0'): ('q1', 'B', 'R'),
               ('q7', '1'): ('q8', 'A', 'L'),
               ('q8', '1'): ('q8', '0', 'L'),
               ('q8', '0'): ('q1', '1', 'R'),
               ('q8', '#'): ('q1', '1', 'R'),
               ('q9', 'A'): ('q9', '0', 'L'),
               ('q9', 'B'): ('q9', '1', 'L'),
               ('q9', '#'): ('end', '#', 'R'),
               ('q9', '0'): ('end', '0', 'R'),
               ('q9', '1'): ('end', '1', 'R')}

q_accept = 'end'
blank_symbol = '#'

# write_turing_machine_to_txt(states, symbols, transitions, q_accept, blank_symbol, 'TuringMachines/binary_adder.txt')

#%% Verstaile Shift
initial_state='q0'
initial_tape='00000011#00001000'
vs = TMVersatileShift(states, symbols, transitions, q_accept, blank_symbol)
vs.simulate(initial_state, initial_tape)






