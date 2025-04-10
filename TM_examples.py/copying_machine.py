#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# %%
"""

Created on Sun Mar 30 19:32:04 2025

@author: gelenag

Devel abstract UTM as real TM with state transitions

"""
import sys
sys.path.append('..')

from Utils import TMDescriptor, BinaryTMEncoder
from Machines import TuringMachine

desc = TMDescriptor(Q=['q0', 'q1', 'q2', 'q3', 'q4', 'q5'], 
                    sigma=['0', '1', 'X', 'Y', 'Z', 'B'], 
                    gamma=['0', '1', 'X', 'Y', 'Z', 'B'], 
                    delta = {('q0', '0'): ('q0', '0', 'R'),
                             ('q0', '1'): ('q0', '1', 'R'),
                             ('q0', 'X'): ('q0', 'X', 'R'),
                             ('q0', 'Y'): ('q1', 'Y', 'R'),
                             ('q0', 'Z'): ('q0', 'Z', 'R'),
                             ('q0', 'B'): ('q0', 'B', 'R'),
                             ('q1', '0'): ('q4', '0', 'L'),
                             ('q1', '1'): ('q2', 'B', 'L'),
                             ('q1', 'X'): ('q1', 'X', 'R'),
                             ('q1', 'Y'): ('q1', 'Y', 'R'),
                             ('q1', 'Z'): ('q1', 'Z', 'R'),
                             ('q1', 'B'): ('q1', 'B', 'R'),
                             ('q2', '0'): ('q2', '0', 'L'),
                             ('q2', '1'): ('q2', '1', 'L'),
                             ('q2', 'X'): ('q3', 'X', 'R'),
                             ('q2', 'Y'): ('q2', 'Y', 'L'),
                             ('q2', 'Z'): ('q2', 'Z', 'L'),
                             ('q2', 'B'): ('q2', 'B', 'L'),
                             ('q3', '0'): ('q0', '1', 'R'),
                             ('q3', '1'): ('q3', '1', 'R'),
                             ('q3', 'X'): ('q3', 'X', 'R'),
                             ('q3', 'Y'): ('q3', 'Y', 'R'),
                             ('q3', 'Z'): ('q3', 'Z', 'R'),
                             ('q3', 'B'): ('q3', 'B', 'R'),
                             ('q4', '0'): ('q4', '0', 'L'),
                             ('q4', '1'): ('q4', '1', 'L'),
                             ('q4', 'X'): ('q4', 'X', 'L'),
                             ('q4', 'Y'): ('q5', 'Y', 'N'),
                             ('q4', 'Z'): ('q4', 'Z', 'L'),
                             ('q4', 'B'): ('q4', '1', 'L')},
                    q0='q0', 
                    q_accept='q5',
                    blank_symbol='0')

# tape = 'X000000000000Y11111011111010111110111001011010111011100110111101110111101100000Z1111101101101101101101101101111011010'
tape = 'X000000000000Y1111101111101011111011100'

TM = TuringMachine(desc, tape)

TM.execute(1000)