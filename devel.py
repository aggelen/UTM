#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# %%
"""

Created on Sun Mar 30 19:32:04 2025

@author: gelenag

Consider the following program, which inputs a nonempty string without
blanks from the alphabet A = {t, 1, 2, 3, B}. 

This program outputs that same string with all of the 1’s replaced with 2’s, and changes the rightmost
cell to a “3”

〈q0, B〉  → 〈q0, B, R〉
〈q0, 1〉  → 〈q0, 2, R〉
〈q0, 2〉  → 〈q0, 2, R〉
〈q0, 3〉  → 〈q0, 3, R〉
〈q0, t〉  → 〈q1, t, L〉
〈q1, 1〉  → 〈qh, 3, N 〉
〈q1, 2〉  → 〈qh, 3, N 〉
〈q1, 3〉  → 〈qh, 3, N 〉

"""
from Utils import TMDescriptor, BinaryTMEncoder
from Machines import UniversalTuringMachine

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

# T = 'B111111131t'

E = BinaryTMEncoder(M)
M = E.encode()  #encoded machine description
T = E.encode_tape(T)

U = UniversalTuringMachine(M, T, E.encoded_states[-1])  #last state: halting state
# U.show_tape()
U.execute()
# U.show_tape()

tape = U.read_tape()
tape = E.decode_tape(tape)