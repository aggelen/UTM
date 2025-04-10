#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sun Mar 30 19:32:04 2025

@author: gelenag

Devel abstract UTM as real TM with state transitions

"""
from Utils import TMDescriptor, BinaryTMEncoder, read_program
from Machines import TuringMachine

#%% TM 
M = TMDescriptor(Q=['q0', 'q1', 'qh'], 
                 sigma=['t', '1', '2', '3'], 
                 gamma=['t', '1', '2', '3', 'B'], 
                 delta = {('q0', 'B'): ('q0', 'B', 'R'),
                           ('q0', '1'): ('q0', '2', 'R'),
                           ('q0', '2'): ('q0', '2', 'R'),
                           ('q0', '3'): ('q0', '3', 'R'),
                           ('q0', 't'): ('q1', 't', 'L'),
                           ('q1', '1'): ('qh', '3', 'N'),
                           ('q1', '2'): ('qh', '3', 'N'),
                           ('q1', '3'): ('qh', '3', 'N')},
                 q0='q0', 
                 q_accept='qh',
                 blank_symbol='t')

T = 'B11t'
E = BinaryTMEncoder(M)
encoded_machine = E.encode()  
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

encoded_halting_state = '111'

TM = TuringMachine(desc, tape, encoded_halting_state)

TM.execute(500000, True)
TM.show_tape()

final_tape = TM.read_simulated_tape(tape_index=171)
decoded_tape = E.decode_tape(final_tape)
