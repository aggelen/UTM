#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 12:59:02 2025

@author: gelenag

The Turing Machine
uses the second number as a counter
decrements the second number by one
increments the first number by one
till the second number becomes 0.
"""

from Utils import TMDescriptor, BinaryTMEncoder, read_program
from Machines import TuringMachine


M = TMDescriptor(Q=['q0', 'q1',  'q2',  'q3',  'q4',  'q5', 'q6', 'STOP'], 
                 sigma=['_', '0', '1', '$', '-'], 
                 gamma=['_', '0', '1', '$', '-'], 
                 delta = {
                            ('q1', '_'): ('q1', '_', 'R'),
                            ('q1', '1'): ('q1', '1', 'R'),
                            ('q1', '0'): ('q1', '0', 'R'),
                            ('q1', '-'): ('q2', '-', 'R'),
                            ('q2', '0'): ('q2', '$', 'R'),
                            ('q2', '$'): ('q2', '$', 'R'),
                            ('q2', '_'): ('STOP', '_', 'N'),
                            ('q2', '1'): ('q3', '1', 'R'),
                            ('q3', '1'): ('q3', '1', 'R'),
                            ('q3', '0'): ('q3', '0', 'R'),
                            ('q3', '_'): ('q4', '_', 'L'),
                            ('q4', '0'): ('q4', '1', 'L'),
                            ('q4', '1'): ('q5', '0', 'L'),
                            ('q5', '$'): ('q5', '$', 'L'),
                            ('q5', '1'): ('q5', '1', 'L'),
                            ('q5', '0'): ('q5', '0', 'L'),
                            ('q5', '-'): ('q6', '-', 'L'),
                            ('q5', '_'): ('q1', '_', 'R'),
                            ('q6', '0'): ('q6', '1', 'L'),
                            ('q6', '1'): ('q5', '0', 'L'),
                            ('q6', '_'): ('q5', '1', 'L')
                        },
                 q0='q0', 
                 q_accept='STOP',
                 blank_symbol='_')

T = '00001000-00000011'
# T = '111_11'

E = BinaryTMEncoder(M)
encoded_machine = E.encode()  #encoded machine description
encoded_tape = E.encode_tape(T)

tape = E.encode_all(encoded_machine, encoded_tape)

#%% UTM
states, symbols, transitions = read_program('Programs.py/aykut_utm.txt')

desc = TMDescriptor(Q=states, 
                    sigma=symbols, 
                    gamma=symbols, 
                    delta = transitions,
                    q0='q0', 
                    q_accept=['OK'],
                    blank_symbol='0')

encoded_halting_state = E.encoded_halting_state()

TM = TuringMachine(desc, tape, encoded_halting_state)

TM.execute(20000000, False)
TM.show_tape()

final_tape = TM.read_simulated_tape(tape_index=494)
decoded_tape = E.decode_tape(final_tape)